import os
from google.cloud import firestore
from google.oauth2 import service_account

creds = service_account.Credentials.from_service_account_file(
    "attendance-bot.json"
)

db = firestore.Client(
    credentials=creds,
    project=creds.project_id,
    database="attendance-database"
)