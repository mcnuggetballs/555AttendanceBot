import gspread
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime

SHEET_NAME = "Attendance Logs"

scope = [
    "https://spreadsheets.google.com/feeds",
    "https://www.googleapis.com/auth/drive"
]

creds = ServiceAccountCredentials.from_json_keyfile_name(
    "service_account.json",
    scope
)

client = gspread.authorize(creds)

sheet = client.open(SHEET_NAME).sheet1


def ensure_headers():

    headers = [
        "Date",
        "Time",
        "Name",
        "Role",
        "Class",
        "Student",
        "Venue",
        "Status",
        "Admin Hours"
    ]

    first_row = sheet.row_values(1)

    if not first_row:
        sheet.insert_row(headers, 1)


def log_attendance(name, role, cls, student, venue, status, admin_hours=None):

    ensure_headers()

    now = datetime.now()

    date = now.strftime("%Y-%m-%d")
    time = now.strftime("%H:%M")

    row = [
        date,
        time,
        name,
        role,
        cls,
        student,
        venue,
        status,
        admin_hours if role == "Admin" else ""
    ]

    sheet.append_row(row)