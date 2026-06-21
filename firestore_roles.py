from firestore_db import db

def add_role(user_id, role_name):

    db.collection("users") \
        .document(str(user_id)) \
        .collection("roles") \
        .document(role_name) \
        .set({
            "role_name": role_name
        })


def remove_role(user_id, role_name):

    db.collection("users") \
        .document(str(user_id)) \
        .collection("roles") \
        .document(role_name) \
        .delete()


def has_role(user_id, role_name):

    doc = (
        db.collection("users")
        .document(str(user_id))
        .collection("roles")
        .document(role_name)
        .get()
    )

    return doc.exists

def get_roles(user_id):

    docs = (
        db.collection("users")
        .document(str(user_id))
        .collection("roles")
        .stream()
    )

    return [
        doc.to_dict()["role_name"]
        for doc in docs
    ]
