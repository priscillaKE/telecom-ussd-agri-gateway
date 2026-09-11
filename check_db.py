import os
import sqlite3

database_name = os.environ.get("USSD_DB_NAME", "ussd_transactions.db")
conn = sqlite3.connect(database_name)
cursor = conn.cursor()

# Pull all logged seed orders from your warehouse table
cursor.execute("SELECT * FROM agriculture_orders")
records = cursor.fetchall()

print("\n--- KILIMOMOMO DATABASE AUDIT TRAILS ---")
print(f"Database: {database_name}")
print(f"Total Transactions Logged: {len(records)}")
for row in records:
    print(f"Order #{row[0]} | Phone: {row[1]} | Type: {row[2]} | Selection: {row[3]} | Time: {row[4]}")

conn.close()
