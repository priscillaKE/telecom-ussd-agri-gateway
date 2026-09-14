import os
import sqlite3
from datetime import datetime, timezone

DB_NAME = os.environ.get("USSD_DB_NAME", "ussd_transactions.db")

def init_db(db_name=None):
    """Create the transaction table and add fields needed for order tracking."""
    conn = sqlite3.connect(db_name or DB_NAME)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS agriculture_orders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            phone_number TEXT NOT NULL,
            service_type TEXT NOT NULL,
            selection_details TEXT NOT NULL,
            timestamp TEXT NOT NULL,
            session_id TEXT,
            status TEXT NOT NULL DEFAULT 'completed',
            quantity INTEGER,
            location TEXT
        )
    """)
    columns = {row[1] for row in cursor.execute("PRAGMA table_info(agriculture_orders)")}
    for name, definition in (
        ("session_id", "TEXT"),
        ("status", "TEXT NOT NULL DEFAULT 'completed'"),
        ("quantity", "INTEGER"),
        ("location", "TEXT"),
    ):
        if name not in columns:
            cursor.execute(f"ALTER TABLE agriculture_orders ADD COLUMN {name} {definition}")
    conn.commit()
    conn.close()

def log_transaction(
    phone_number,
    service_type,
    selection_details,
    db_name=None,
    session_id="",
    quantity=None,
    location=None,
):
    """Insert a completed price check or pending seed order."""
    conn = sqlite3.connect(db_name or DB_NAME)
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO agriculture_orders
        (phone_number, service_type, selection_details, timestamp, session_id, status, quantity, location)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        phone_number,
        service_type,
        selection_details,
        datetime.now(timezone.utc).isoformat(),
        session_id,
        "pending" if service_type == "Seed Order" else "completed",
        quantity,
        location,
    ))
    transaction_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return transaction_id

def handle_ussd_request(text_input, phone_number="0770000000", db_name=None, session_id=""):
    """
    Simulates a telecom core network GSM session handler.
    CON = Continue session | END = End session
    """
    inputs = text_input.strip().split("*") if text_input and text_input.strip() else []
    level = len(inputs)

    # Level 0: Root Menu
    if level == 0:
        response = "CON Welcome to KilimoMoMo Agri-Service\n"
        response += "1. Check Crop Market Prices\n"
        response += "2. Request Seed Delivery\n"
        response += "3. Exit"
        return response

    # Level 1: Main Selections
    elif level == 1:
        main_choice = inputs[0]
        if main_choice == "1":
            response = "CON Select Regional District:\n"
            response += "1. Central (Nakasongola)\n"
            response += "2. Eastern (Kapchorwa)"
            return response
        elif main_choice == "2":
            response = "CON Select Seed Variety:\n"
            response += "1. Longe 5 Maize (5KG)\n"
            response += "2. NARO Bean 1 (5KG)"
            return response
        elif main_choice == "3":
            return "END Thank you for using KilimoMoMo. Stay safe!"
        else:
            return "END Invalid choice. Please redial and try again."

    # Level 2: Final Actions & DB Logging
    elif level == 2:
        main_choice = inputs[0]
        sub_choice = inputs[1]

        # Path: Prices
        if main_choice == "1":
            if sub_choice == "1":
                log_transaction(phone_number, "Price Check", "Central (Nakasongola)", db_name, session_id)
                return "END Current Prices (Nakasongola):\nMaize: UGX 1,200/KG\nCassava: UGX 800/KG"
            elif sub_choice == "2":
                log_transaction(phone_number, "Price Check", "Eastern (Kapchorwa)", db_name, session_id)
                return "END Current Prices (Kapchorwa):\nMaize: UGX 1,400/KG\nBarley: UGX 1,900/KG"
            
        # Path: Seed Orders - choose the variety, then ask for quantity.
        elif main_choice == "2":
            if sub_choice == "1":
                return "CON Select quantity (5KG bags):\n1. 1 bag\n2. 2 bags\n3. 5 bags"
            elif sub_choice == "2":
                return "CON Select quantity (5KG bags):\n1. 1 bag\n2. 2 bags\n3. 5 bags"

    # Level 3: Seed quantity, followed by a pickup-point menu.
    elif level == 3 and inputs[0] == "2":
        if inputs[1] not in ("1", "2") or inputs[2] not in ("1", "2", "3"):
            return "END Invalid selection. Please redial and try again."
        return "CON Select pickup point:\n1. Nakasongola town\n2. Kapchorwa town"

    # Level 4: Complete the order and return a support-friendly order number.
    elif level == 4 and inputs[0] == "2":
        if inputs[1] not in ("1", "2") or inputs[2] not in ("1", "2", "3") or inputs[3] not in ("1", "2"):
            return "END Invalid selection. Please redial and try again."
        varieties = {"1": "Longe 5 Maize", "2": "NARO Bean 1"}
        quantities = {"1": 1, "2": 2, "3": 5}
        locations = {"1": "Nakasongola town", "2": "Kapchorwa town"}
        quantity = quantities[inputs[2]]
        location = locations[inputs[3]]
        transaction_id = log_transaction(
            phone_number,
            "Seed Order",
            f"{varieties[inputs[1]]} (5KG)",
            db_name,
            session_id,
            quantity,
            location,
        )
        return (
            f"END Order KM-{transaction_id:06d} received.\n"
            f"{quantity} bag(s) of {varieties[inputs[1]]}. Pickup: {location}.\n"
            "You will receive an SMS confirmation."
        )

    return "END Invalid selection. Please redial and try again."

# Initialize database on startup
init_db()
