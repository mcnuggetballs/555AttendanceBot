from telegram import Update
from telegram.ext import ContextTypes
import sqlite3


async def today(update: Update, context: ContextTypes.DEFAULT_TYPE):

    conn = sqlite3.connect("attendance.db")
    c = conn.cursor()

    c.execute("""
    SELECT users.name, attendance_logs.role_name, attendance_logs.class_code,
           attendance_logs.status
    FROM attendance_logs
    JOIN users
    ON attendance_logs.telegram_user_id = users.telegram_user_id
    WHERE date(attendance_logs.timestamp) = date('now')
    ORDER BY attendance_logs.timestamp DESC
    """)

    rows = c.fetchall()

    conn.close()

    if not rows:

        await update.message.reply_text("No attendance recorded today.")
        return

    message = "TODAY'S ATTENDANCE\n\n"

    for row in rows:

        name = row[0]
        role = row[1]
        class_code = row[2]
        status = row[3]

        message += f"{name} — {role} — {class_code} — {status}\n"

    await update.message.reply_text(message)


async def who(update: Update, context: ContextTypes.DEFAULT_TYPE):

    if not context.args:

        await update.message.reply_text(
            "Usage:\n/who CLASSCODE\nExample:\n/who K61"
        )
        return

    class_code = context.args[0].upper()

    conn = sqlite3.connect("attendance.db")
    c = conn.cursor()

    c.execute("""
    SELECT users.name, attendance_logs.status
    FROM attendance_logs
    JOIN users
    ON attendance_logs.telegram_user_id = users.telegram_user_id
    WHERE attendance_logs.class_code=?
    AND date(attendance_logs.timestamp) = date('now')
    """, (class_code,))

    rows = c.fetchall()

    conn.close()

    if not rows:

        await update.message.reply_text(
            f"No attendance recorded for {class_code} today."
        )
        return

    message = f"ATTENDANCE FOR {class_code}\n\n"

    for row in rows:

        name = row[0]
        status = row[1]

        message += f"{name} — {status}\n"

    await update.message.reply_text(message)