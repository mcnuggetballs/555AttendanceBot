import gspread
from google.auth import compute_engine
from datetime import datetime

SPREADSHEET_ID = "1WN9gSiKFOgpJn6bZnyqeLVOFv8ybH3J_ZoyLVG_a6Yg"

creds = compute_engine.Credentials(
    scopes=[
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive"
    ]
)

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