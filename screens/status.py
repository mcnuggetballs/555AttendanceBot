from ui import show_screen
from keyboards import menu_keyboard
from firestore_users import get_user
from firestore_roles import get_roles
from firestore_classes import get_classes_for_role


async def show_status(update, context):

    user_id = update.effective_user.id

    user = get_user(user_id)

    if not user:

        await show_screen(
            update,
            context,
            "You do not have an account yet.\n\nUse Create Account from the menu.",
            menu_keyboard()
        )

        return

    name = user["name"]

    text = f"ACCOUNT STATUS\n\nName: {name}\n\nRoles:\n"

    roles = get_roles(user_id)

    for role_name in roles:

        text += f"\n• {role_name}\n"

        classes = get_classes_for_role(
            user_id,
            role_name
        )

        for cls in classes:

            venue = cls.get("venue_name", "")

            text += (
                f"   - {cls['class_code']} "
                f"({venue})\n"
            )

    await show_screen(update, context, text, menu_keyboard())