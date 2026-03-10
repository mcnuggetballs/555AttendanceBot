import gspread
from google.auth import compute_engine
from datetime import datetime

SHEET_NAME = "Attendance Logs"

# Force Compute Engine credentials
creds = compute_engine.Credentials()

client = gspread.authorize(creds)

sheet = client.open(SHEET_NAME).sheet1


def log_attendance(name, role, cls, student, venue, status, admin_hours=None):

    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")

    row = [
        timestamp,
        name,
        role,
        cls,
        student,
        venue,
        status,
        admin_hours if role == "Admin" else ""
    ]

    sheet.append_row(row)