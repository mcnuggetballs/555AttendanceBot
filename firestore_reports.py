from firestore_db import db
from firestore_users import get_user

def get_today_attendance(date):

    docs = (
        db.collection("attendance_logs")
        .where("date", "==", date)
        .stream()
    )

    results = []

    for doc in docs:

        data = doc.to_dict()

        user = get_user(data["telegram_user_id"])

        results.append({
            "name": user.get("name", "Unknown"),
            "role": data["role_name"],
            "class_code": data["class_code"]
        })

    return results


def get_today_late_reports(date):

    docs = (
        db.collection("late_reports")
        .where("date", "==", date)
        .stream()
    )

    results = []

    for doc in docs:

        data = doc.to_dict()

        user = get_user(data["telegram_user_id"])

        results.append({
            "name": user.get("name", "Unknown"),
            "role": data["role_name"],
            "class_code": data["class_code"]
        })

    return results

def get_attendance_for_class(class_code, date):

    docs = (
        db.collection("attendance_logs")
        .where("class_code", "==", class_code)
        .where("date", "==", date)
        .stream()
    )

    results = []

    for doc in docs:

        data = doc.to_dict()

        user = get_user(data["telegram_user_id"])

        results.append({
            "name": user.get("name", "Unknown")
        })

    return results


def get_late_for_class(class_code, date):

    docs = (
        db.collection("late_reports")
        .where("class_code", "==", class_code)
        .where("date", "==", date)
        .stream()
    )

    results = []

    for doc in docs:

        data = doc.to_dict()

        user = get_user(data["telegram_user_id"])

        results.append({
            "name": user.get("name", "Unknown")
        })

    return results