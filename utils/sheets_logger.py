import gspread
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime
from zoneinfo import ZoneInfo

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
        "Student/School Name",
        "Venue",
        "Status",
        "Hours/Pax"   # ✅ UPDATED
    ]

    first_row = sheet.row_values(1)

    if not first_row:
        sheet.insert_row(headers, 1)


def log_attendance(name, role, cls, student, venue, status, admin_hours=None):

    ensure_headers()

    now = datetime.now(ZoneInfo("Asia/Singapore"))

    date = now.strftime("%m/%d/%Y")
    time = now.strftime("%H:%M")

    date = str(date)
    time = str(time)

    row = [
        date,
        time,
        name,
        role,
        cls,
        student,
        venue,
        status,
        admin_hours if admin_hours is not None else ""   # ✅ FIXED
    ]

    sheet.append_row(row, value_input_option="USER_ENTERED")