import gspread
from oauth2client.service_account import ServiceAccountCredentials


scope = [
    "https://spreadsheets.google.com/feeds",
    "https://www.googleapis.com/auth/drive"
]

creds = ServiceAccountCredentials.from_json_keyfile_name(
    "credentials.json",
    scope
)

client = gspread.authorize(creds)

sheet = client.open("555 Attendance").sheet1


def log_attendance(name, role, class_code, distance, status):

    sheet.append_row([
        name,
        role,
        class_code,
        distance,
        status
    ])