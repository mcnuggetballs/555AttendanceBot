from database import get_connection


def get_msg(update):
    if update.message:
        return update.message
    return update.callback_query.message


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

        await get_msg(update).reply_text(
            "You do not have an account yet.\n\nUse Create Account from the menu."
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

    await get_msg(update).reply_text(text)