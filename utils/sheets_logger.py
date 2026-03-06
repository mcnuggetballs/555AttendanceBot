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


def log_attendance(name, role, cls, student, venue, status):

    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")

    row = [
        timestamp,
        name,
        role,
        cls,
        student,
        venue,
        status
    ]

    sheet.append_row(row)