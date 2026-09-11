import os
import sqlite3
from datetime import datetime, timezone

DB_NAME = os.environ.get("USSD_DB_NAME", "ussd_transactions.db")

def init_db(db_name=None):
    """Creates a database table to log incoming USSD requests."""
    conn = sqlite3.connect(db_name or DB_NAME)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS agriculture_orders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            phone_number TEXT NOT NULL,
            service_type TEXT NOT NULL,
            selection_details TEXT NOT NULL,
            timestamp TEXT NOT NULL
        )
    """)
    conn.commit()
    conn.close()

def log_transaction(phone_number, service_type, selection_details, db_name=None):
    """Inserts a confirmed offline order/query into the database warehouse."""
    conn = sqlite3.connect(db_name or DB_NAME)
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO agriculture_orders (phone_number, service_type, selection_details, timestamp)
        VALUES (?, ?, ?, ?)
    """, (phone_number, service_type, selection_details, datetime.now(timezone.utc).isoformat()))
    conn.commit()
    conn.close()

def handle_ussd_request(text_input, phone_number="0770000000", db_name=None):
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
                log_transaction(phone_number, "Price Check", "Central (Nakasongola)", db_name)
                return "END Current Prices (Nakasongola):\nMaize: UGX 1,200/KG\nCassava: UGX 800/KG"
            elif sub_choice == "2":
                log_transaction(phone_number, "Price Check", "Eastern (Kapchorwa)", db_name)
                return "END Current Prices (Kapchorwa):\nMaize: UGX 1,400/KG\nBarley: UGX 1,900/KG"
            
        # Path: Seed Orders
        elif main_choice == "2":
            if sub_choice == "1":
                log_transaction(phone_number, "Seed Order", "Longe 5 Maize (5KG)", db_name)
                return "END Request Logged!\nLonge 5 Maize order initiated. You will receive an SMS confirmation."
            elif sub_choice == "2":
                log_transaction(phone_number, "Seed Order", "NARO Bean 1 (5KG)", db_name)
                return "END Request Logged!\nNARO Bean 1 order initiated. You will receive an SMS confirmation."

    return "END Invalid selection. Please redial and try again."

# Initialize database on startup
init_db()
