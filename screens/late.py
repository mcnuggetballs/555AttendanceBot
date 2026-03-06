from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from database import get_connection
from utils.sheets_logger import log_attendance
from datetime import datetime


ADMIN_GROUP_ID = -1003584358970


ROLE_TOPICS = {
    "Internal Instructor": 35,
    "External Instructor": 36,
    "Private Instructor": 37,
    "Admin": 38,
    "Student Mentor": 39,
    "AEP Performer": 40
}


def nav_buttons():
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("⬅ Back", callback_data="back"),
            InlineKeyboardButton("🏠 Menu", callback_data="menu")
        ]
    ])


def get_msg(update):
    if update.message:
        return update.message
    return update.callback_query.message


# ROLE SCREEN

async def start_late(update, context):

    user_id = update.effective_user.id

    conn = get_connection()
    c = conn.cursor()

    c.execute("""
    SELECT role_name
    FROM user_roles
    WHERE telegram_user_id=?
    """, (user_id,))

    roles = [r[0] for r in c.fetchall()]

    conn.close()

    keyboard = []

    for role in roles:
        keyboard.append([
            InlineKeyboardButton(role, callback_data=f"late_role|{role}")
        ])

    keyboard.append([
        InlineKeyboardButton("🏠 Menu", callback_data="menu")
    ])

    await get_msg(update).reply_text(
        "Select role for late report:",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )


# CLASS SCREEN

async def show_class_screen(update, context):

    role = context.user_data.get("late_role")

    conn = get_connection()
    c = conn.cursor()

    c.execute("""
    SELECT class_code
    FROM class_codes
    WHERE role_id IN (
        SELECT id FROM user_roles
        WHERE telegram_user_id=? AND role_name=?
    )
    """, (update.effective_user.id, role))

    classes = [r[0] for r in c.fetchall()]

    conn.close()

    keyboard = []

    for cls in classes:
        keyboard.append([
            InlineKeyboardButton(cls, callback_data=f"late_class|{cls}")
        ])

    keyboard.append([
        InlineKeyboardButton("⬅ Back", callback_data="back"),
        InlineKeyboardButton("🏠 Menu", callback_data="menu")
    ])

    await get_msg(update).reply_text(
        "Select class:",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )


async def select_class(update, context):

    query = update.callback_query

    role = query.data.split("|")[1]

    context.user_data["late_role"] = role

    await show_class_screen(update, context)


# ETA SCREEN

async def request_eta(update, context):

    query = update.callback_query

    cls = query.data.split("|")[1]

    context.user_data["late_class"] = cls
    context.user_data["screen"] = "late_eta"

    await query.message.reply_text(
        "Enter your ETA (example: 10 minutes / 18:45)",
        reply_markup=nav_buttons()
    )


# ETA HANDLER

async def save_eta(update, context):

    eta = update.message.text

    role = context.user_data.get("late_role")
    cls = context.user_data.get("late_class")

    conn = get_connection()
    c = conn.cursor()

    today = datetime.now().strftime("%Y-%m-%d")

    # BLOCK IF ALREADY PRESENT
    c.execute("""
    SELECT id
    FROM attendance_logs
    WHERE telegram_user_id=? AND class_code=? AND date=?
    """, (update.effective_user.id, cls, today))

    if c.fetchone():

        await update.message.reply_text(
            "You have already submitted attendance for this class today."
        )

        conn.close()
        return


    # BLOCK DUPLICATE LATE REPORT
    c.execute("""
    SELECT id
    FROM late_reports
    WHERE telegram_user_id=? AND class_code=? AND date=?
    """, (update.effective_user.id, cls, today))

    if c.fetchone():

        await update.message.reply_text(
            "You have already submitted a late report for this class today."
        )

        conn.close()
        return


    # GET VENUE (SAFE)
    c.execute("""
    SELECT venue_name
    FROM class_codes
    JOIN user_roles ON class_codes.role_id = user_roles.id
    WHERE user_roles.telegram_user_id=? AND user_roles.role_name=? AND class_codes.class_code=?
    """, (update.effective_user.id, role, cls))

    venue_row = c.fetchone()

    if not venue_row:
        venue_name = "Unknown Venue"
    else:
        venue_name = venue_row[0]


    # GET NAME (SAFE)
    c.execute("""
    SELECT name
    FROM users
    WHERE telegram_user_id=?
    """, (update.effective_user.id,))

    name_row = c.fetchone()

    if not name_row:
        name = "Unknown"
    else:
        name = name_row[0]


    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")


    # SAVE LATE REPORT
    c.execute("""
    INSERT INTO late_reports
    (telegram_user_id, role_name, class_code, eta, date, timestamp)
    VALUES (?,?,?,?,?,?)
    """, (
        update.effective_user.id,
        role,
        cls,
        eta,
        today,
        timestamp
    ))

    conn.commit()
    conn.close()


    await update.message.reply_text("Late report submitted.")


    log_attendance(name, role, cls, venue_name, "Late")


    log_message = f"""
LATE REPORT

Name: {name}
Role: {role}
Class: {cls}
Venue: {venue_name}
Status: Late
ETA: {eta}
Time: {timestamp}
"""

    topic_id = ROLE_TOPICS.get(role)

    await context.bot.send_message(
        chat_id=ADMIN_GROUP_ID,
        message_thread_id=topic_id,
        text=log_message
    )


    context.user_data.pop("late_role", None)
    context.user_data.pop("late_class", None)