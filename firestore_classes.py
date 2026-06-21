from firestore_db import db
from google.cloud.firestore_v1 import FieldFilter

def get_classes(user_id):

    docs = (
        db.collection("users")
        .document(str(user_id))
        .collection("classes")
        .stream()
    )

    return [
        {
            "id": doc.id,
            **doc.to_dict()
        }
        for doc in docs
    ]


def add_class(
    user_id,
    role,
    class_code,
    venue_name,
    venue_lat,
    venue_lng
):

    db.collection("users") \
        .document(str(user_id)) \
        .collection("classes") \
        .add({
            "role": role,
            "class_code": class_code,
            "venue_name": venue_name,
            "venue_lat": venue_lat,
            "venue_lng": venue_lng
        })


def delete_class(user_id, class_id):

    db.collection("users") \
        .document(str(user_id)) \
        .collection("classes") \
        .document(class_id) \
        .delete()


def get_classes_for_role(user_id, role):

    docs = (
        db.collection("users")
        .document(str(user_id))
        .collection("classes")
        .where(filter=FieldFilter("role", "==", role))
        .stream()
    )

    return [
        {
            "id": doc.id,
            **doc.to_dict()
        }
        for doc in docs
    ]