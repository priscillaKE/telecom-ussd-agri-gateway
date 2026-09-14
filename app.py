import os
import re

from flask import Flask, jsonify, request
from ussd_app import handle_ussd_request

app = Flask(__name__)
app.config["DB_NAME"] = os.environ.get("USSD_DB_NAME", "ussd_transactions.db")


def valid_phone_number(phone_number):
    return bool(re.fullmatch(r"(?:0[17]\d{8}|\+256[17]\d{8})", phone_number))


@app.get("/health")
def health_check():
    return jsonify(status="ok", service="kilimomomo-ussd")

@app.route("/ussd", methods=["POST"])
def ussd_gateway():
    session_id = request.values.get("sessionId", "").strip()
    phone_number = request.values.get("phoneNumber", "").strip()
    text_input = request.values.get("text", "").strip()

    if not session_id or not phone_number or not valid_phone_number(phone_number):
        return "Invalid session or phone number.", 400, {"Content-Type": "text/plain; charset=utf-8"}

    app.logger.info("USSD request session=%s phone=%s input=%s", session_id, phone_number, text_input)

    response_menu = handle_ussd_request(
        text_input,
        phone_number,
        app.config["DB_NAME"],
        session_id,
    )
    return response_menu, 200, {"Content-Type": "text/plain; charset=utf-8"}

if __name__ == "__main__":
    print("Starting KilimoMoMo USSD service on port 5000...")
    app.run(host="0.0.0.0", port=5000, debug=True)
