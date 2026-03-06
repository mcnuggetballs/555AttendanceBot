from telegram import InlineKeyboardButton
from ui import show_screen
from database import get_connection
from keyboards import menu_keyboard
import sqlite3


async def today(update, context):

    conn = get_connection()
    c = conn.cursor()

    c.execute("""
    SELECT users.name, attendance_logs.role_name, attendance_logs.class_code
    FROM attendance_logs
    JOIN users
    ON attendance_logs.telegram_user_id = users.telegram_user_id
    WHERE date = date('now')
    """)

    present = c.fetchall()

    c.execute("""
    SELECT users.name, late_reports.role_name, late_reports.class_code
    FROM late_reports
    JOIN users
    ON late_reports.telegram_user_id = users.telegram_user_id
    WHERE date = date('now')
    """)

    late = c.fetchall()

    conn.close()

    if not present and not late:

        await show_screen(
            update,
            context,
            "No attendance recorded today.",
            menu_keyboard()
        )
        return

    message = "📋 TODAY'S ATTENDANCE\n\n"

    for name, role, cls in present:
        message += f"{name} — {role} — {cls} — ✅ Present\n"

    for name, role, cls in late:
        message += f"{name} — {role} — {cls} — ⏰ Late\n"

    await show_screen(update, context, message, menu_keyboard())


async def who(update, context):

    conn = get_connection()
    c = conn.cursor()

    c.execute("""
    SELECT DISTINCT class_code
    FROM class_codes
    ORDER BY class_code
    """)

    classes = [row[0] for row in c.fetchall()]

    conn.close()

    keyboard = []

    for cls in classes:
        keyboard.append([InlineKeyboardButton(cls, callback_data=f"who_class|{cls}")])

    keyboard.append([InlineKeyboardButton("🏠 Menu", callback_data="menu")])

    await show_screen(update, context, "Select class:", keyboard)


async def who_class(update, context):

    query = update.callback_query
    cls = query.data.split("|")[1]

    conn = get_connection()
    c = conn.cursor()

    c.execute("""
    SELECT users.name
    FROM attendance_logs
    JOIN users
    ON attendance_logs.telegram_user_id = users.telegram_user_id
    WHERE class_code=? AND date = date('now')
    """, (cls,))

    present = c.fetchall()

    c.execute("""
    SELECT users.name
    FROM late_reports
    JOIN users
    ON late_reports.telegram_user_id = users.telegram_user_id
    WHERE class_code=? AND date = date('now')
    """, (cls,))

    late = c.fetchall()

    conn.close()

    if not present and not late:

        await show_screen(
            update,
            context,
            f"No attendance recorded for {cls} today.",
            [[InlineKeyboardButton("⬅ Back", callback_data="menu_who")]]
        )
        return

    text = f"ATTENDANCE FOR {cls}\n\n"

    for (name,) in present:
        text += f"{name} — Present\n"

    for (name,) in late:
        text += f"{name} — Late\n"

    keyboard = [
        [InlineKeyboardButton("⬅ Back", callback_data="menu_who")],
        [InlineKeyboardButton("🏠 Menu", callback_data="menu")]
    ]

    await show_screen(update, context, text, keyboard)