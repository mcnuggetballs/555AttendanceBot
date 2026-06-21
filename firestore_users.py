from firestore_db import db


def get_user(user_id):

    doc = db.collection("users").document(str(user_id)).get()

    if not doc.exists:
        return None

    return doc.to_dict()


def save_user(user_id, name, dob, notes, verified=1):

    db.collection("users").document(str(user_id)).set({
        "telegram_user_id": user_id,
        "name": name,
        "dob": dob,
        "notes": notes,
        "verified": verified
    })


def update_name(user_id, name):

    db.collection("users").document(str(user_id)).update({
        "name": name
    })


def update_dob(user_id, dob):

    db.collection("users").document(str(user_id)).update({
        "dob": dob
    })


def update_notes(user_id, notes):

    db.collection("users").document(str(user_id)).update({
        "notes": notes
    })