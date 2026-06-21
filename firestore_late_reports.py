from firestore_db import db


def late_report_exists(user_id, class_code, date):

    docs = (
        db.collection("late_reports")
        .where("telegram_user_id", "==", user_id)
        .where("class_code", "==", class_code)
        .where("date", "==", date)
        .limit(1)
        .stream()
    )

    return any(docs)


def add_late_report(
    user_id,
    role,
    class_code,
    student,
    eta,
    date,
    timestamp
):

    db.collection("late_reports").add({
        "telegram_user_id": user_id,
        "role_name": role,
        "class_code": class_code,
        "student_name": student,
        "eta": eta,
        "date": date,
        "timestamp": timestamp
    })