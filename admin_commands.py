from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
import sqlite3


def get_msg(update):
    if update.message:
        return update.message
    return update.callback_query.message


async def today(update: Update, context: ContextTypes.DEFAULT_TYPE):

    conn = sqlite3.connect("attendance.db")
    c = conn.cursor()

    # PRESENT
    c.execute("""
    SELECT users.name, attendance_logs.role_name, attendance_logs.class_code, 'Present'
    FROM attendance_logs
    JOIN users
    ON attendance_logs.telegram_user_id = users.telegram_user_id
    WHERE date = date('now')
    """)

    present_rows = c.fetchall()

    # LATE
    c.execute("""
    SELECT users.name, late_reports.role_name, late_reports.class_code, 'Late'
    FROM late_reports
    JOIN users
    ON late_reports.telegram_user_id = users.telegram_user_id
    WHERE date = date('now')
    """)

    late_rows = c.fetchall()

    conn.close()

    rows = present_rows + late_rows

    if not rows:
        await get_msg(update).reply_text("No attendance recorded today.")
        return

    message = "TODAY'S ATTENDANCE\n\n"

    for name, role, cls, status in rows:
        message += f"{name} — {role} — {cls} — {status}\n"

    await get_msg(update).reply_text(message)


async def who(update: Update, context: ContextTypes.DEFAULT_TYPE):

    conn = sqlite3.connect("attendance.db")
    c = conn.cursor()

    c.execute("""
    SELECT DISTINCT class_code
    FROM class_codes
    ORDER BY class_code
    """)

    classes = [row[0] for row in c.fetchall()]
    conn.close()

    if not classes:
        await get_msg(update).reply_text("No classes configured yet.")
        return

    keyboard = []

    for cls in classes:
        keyboard.append([
            InlineKeyboardButton(cls, callback_data=f"who_class|{cls}")
        ])

    keyboard.append([
        InlineKeyboardButton("🏠 Menu", callback_data="menu")
    ])

    await get_msg(update).reply_text(
        "Select class:",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )


async def who_class(update: Update, context: ContextTypes.DEFAULT_TYPE):

    query = update.callback_query
    cls = query.data.split("|")[1]

    conn = sqlite3.connect("attendance.db")
    c = conn.cursor()

    # PRESENT
    c.execute("""
    SELECT users.name, 'Present'
    FROM attendance_logs
    JOIN users
    ON attendance_logs.telegram_user_id = users.telegram_user_id
    WHERE class_code=? AND date = date('now')
    """, (cls,))

    present_rows = c.fetchall()

    # LATE
    c.execute("""
    SELECT users.name, 'Late'
    FROM late_reports
    JOIN users
    ON late_reports.telegram_user_id = users.telegram_user_id
    WHERE class_code=? AND date = date('now')
    """, (cls,))

    late_rows = c.fetchall()

    conn.close()

    rows = present_rows + late_rows

    if not rows:
        await query.message.reply_text(
            f"No attendance recorded for {cls} today."
        )
        return

    message = f"ATTENDANCE FOR {cls}\n\n"

    for name, status in rows:
        message += f"{name} — {status}\n"

    await query.message.reply_text(message)