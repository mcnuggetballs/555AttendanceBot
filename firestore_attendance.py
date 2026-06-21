from firestore_db import db


def attendance_exists(user_id, class_code, date):

    docs = (
        db.collection("attendance_logs")
        .where("telegram_user_id", "==", user_id)
        .where("class_code", "==", class_code)
        .where("date", "==", date)
        .limit(1)
        .stream()
    )

    return any(True for _ in docs)


def add_attendance(
    user_id,
    role_name,
    class_code,
    student_name,
    latitude,
    longitude,
    hours,
    date,
    timestamp
):

    db.collection("attendance_logs").add({
        "telegram_user_id": user_id,
        "role_name": role_name,
        "class_code": class_code,
        "student_name": student_name,
        "latitude": latitude,
        "longitude": longitude,
        "hours": hours,
        "date": date,
        "timestamp": timestamp
    })