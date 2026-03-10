import gspread
from google.auth import default
from datetime import datetime

SHEET_NAME = "Attendance Logs"

# Use VM credentials instead of JSON key
creds, _ = default(scopes=[
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive"
])

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