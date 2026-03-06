from database import get_connection
from ui import show_screen
from telegram import InlineKeyboardButton
from keyboards import menu_keyboard


async def show_status(update, context):

    user_id = update.effective_user.id

    conn = get_connection()
    c = conn.cursor()

    c.execute("""
    SELECT name
    FROM users
    WHERE telegram_user_id=?
    """, (user_id,))

    user = c.fetchone()

    if not user:

        await show_screen(
            update,
            context,
            "You do not have an account yet.\n\nUse Create Account from the menu.",
            menu_keyboard()
        )

        conn.close()
        return

    name = user[0]

    text = f"ACCOUNT STATUS\n\nName: {name}\n\nRoles:\n"

    c.execute("""
    SELECT id, role_name
    FROM user_roles
    WHERE telegram_user_id=?
    """, (user_id,))

    roles = c.fetchall()

    for role_id, role_name in roles:

        text += f"\n• {role_name}\n"

        c.execute("""
        SELECT class_code, venue_name
        FROM class_codes
        WHERE role_id=?
        """, (role_id,))

        classes = c.fetchall()

        for cls, venue in classes:
            text += f"   - {cls} ({venue})\n"

    conn.close()

    await show_screen(update, context, text, menu_keyboard())