import gspread
from google.auth import default
from datetime import datetime

SPREADSHEET_ID = "1abcDEFghiJKLmnopQRstuVWxyz123"

creds, _ = default(scopes=[
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive"
])

client = gspread.authorize(creds)

sheet = client.open_by_key(SPREADSHEET_ID).sheet1


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