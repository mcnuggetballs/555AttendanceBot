from firestore_roles import add_role, get_roles

add_role(123, "Admin")

print(get_roles(123))