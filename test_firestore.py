from firestore_db import db

db.collection("test").document("hello").set({
    "message": "it works"
})

print("success")