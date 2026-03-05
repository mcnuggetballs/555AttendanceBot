import gspread
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime

scope = [
    "https://spreadsheets.google.com/feeds",
    "https://www.googleapis.com/auth/drive"
]

creds = ServiceAccountCredentials.from_json_keyfile_name(
    "service_account.json", scope)

client = gspread.authorize(creds)
sheet = client.open("555 Attendance Log").worksheet("LOG")

def log_attendance(data):
    sheet.append_row(data)