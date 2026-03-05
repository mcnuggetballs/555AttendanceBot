from telegram import Update
from telegram.ext import ContextTypes
import sqlite3


async def status(update: Update, context: ContextTypes.DEFAULT_TYPE):

    user_id = update.effective_user.id

    conn = sqlite3.connect("attendance.db")
    c = conn.cursor()

    c.execute("""
    SELECT role_name, id
    FROM user_roles
    WHERE telegram_user_id=?
    """, (user_id,))

    roles = c.fetchall()

    if not roles:

        await update.message.reply_text(
            "No roles found. Please create your account first."
        )

        conn.close()
        return

    message = "YOUR ASSIGNED CLASSES\n\n"

    for role in roles:

        role_name = role[0]
        role_id = role[1]

        message += f"{role_name}\n"

        c.execute("""
        SELECT class_code
        FROM class_codes
        WHERE user_role_id=?
        """, (role_id,))

        classes = c.fetchall()

        for cls in classes:

            message += f"• {cls[0]}\n"

        message += "\n"

    conn.close()

    await update.message.reply_text(message)