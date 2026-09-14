import os
import sqlite3
import tempfile
import unittest

from app import app
from ussd_app import handle_ussd_request, init_db


class UssdAppTests(unittest.TestCase):
    def setUp(self):
        self.database = tempfile.NamedTemporaryFile(delete=False)
        self.database.close()
        init_db(self.database.name)
        app.config.update(TESTING=True, DB_NAME=self.database.name)
        self.client = app.test_client()

    def tearDown(self):
        os.unlink(self.database.name)

    def test_home_menu(self):
        response = handle_ussd_request("", "0772000000", self.database.name)
        self.assertTrue(response.startswith("CON "))
        self.assertIn("1. Check Crop Market Prices", response)

    def test_seed_order_is_logged(self):
        response = handle_ussd_request("2*1*2*1", "0772000000", self.database.name, "session-1")
        self.assertTrue(response.startswith("END Order KM-000001 received."))

        connection = sqlite3.connect(self.database.name)
        try:
            row = connection.execute(
                "SELECT phone_number, service_type, selection_details, session_id, status, quantity, location "
                "FROM agriculture_orders"
            ).fetchone()
        finally:
            connection.close()
        self.assertEqual(row, (
            "0772000000", "Seed Order", "Longe 5 Maize (5KG)",
            "session-1", "pending", 2, "Nakasongola town",
        ))

    def test_seed_order_collects_quantity_before_completion(self):
        response = handle_ussd_request("2*1", "0772000000", self.database.name)
        self.assertTrue(response.startswith("CON Select quantity"))

    def test_gateway_passes_session_id_to_completed_order(self):
        response = self.client.post(
            "/ussd",
            data={
                "sessionId": "gateway-session",
                "phoneNumber": "0772000000",
                "text": "2*2*1*2",
            },
        )
        self.assertIn("Order KM-000001", response.data.decode())
        connection = sqlite3.connect(self.database.name)
        try:
            session_id = connection.execute(
                "SELECT session_id FROM agriculture_orders"
            ).fetchone()[0]
        finally:
            connection.close()
        self.assertEqual(session_id, "gateway-session")

    def test_invalid_selection_does_not_create_transaction(self):
        response = handle_ussd_request("2*9", "0772000000", self.database.name)
        self.assertEqual(response, "END Invalid selection. Please redial and try again.")

        connection = sqlite3.connect(self.database.name)
        try:
            count = connection.execute("SELECT COUNT(*) FROM agriculture_orders").fetchone()[0]
        finally:
            connection.close()
        self.assertEqual(count, 0)

    def test_flask_endpoint_accepts_form_payload(self):
        response = self.client.post(
            "/ussd",
            data={"sessionId": "session-1", "phoneNumber": "0772000000", "text": "1"},
        )
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.data.decode().startswith("CON Select Regional District:"))
        self.assertTrue(response.content_type.startswith("text/plain"))

    def test_health_check_reports_service_status(self):
        response = self.client.get("/health")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json["status"], "ok")


if __name__ == "__main__":
    unittest.main()
