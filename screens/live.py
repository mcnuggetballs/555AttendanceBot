from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from database import get_connection
from utils.sheets_logger import log_attendance
import math
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


ATTENDANCE_RADIUS = 120


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


def distance_m(lat1, lon1, lat2, lon2):

    R = 6371000

    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)

    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)

    a = math.sin(dphi/2)**2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda/2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))

    return R * c


# -------------------------
# ROLE SCREEN
# -------------------------

async def start_live(update, context):

    user_id = update.effective_user.id

    context.user_data["live_state"] = "role"

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
            InlineKeyboardButton(role, callback_data=f"live_role|{role}")
        ])

    keyboard.append([
        InlineKeyboardButton("🏠 Menu", callback_data="menu")
    ])

    await get_msg(update).reply_text(
        "Select role:",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )


# -------------------------
# CLASS SCREEN
# -------------------------

async def show_class_screen(update, context):

    role = context.user_data.get("live_role")

    conn = get_connection()
    c = conn.cursor()

    c.execute("""
    SELECT class_codes.class_code
    FROM class_codes
    JOIN user_roles
    ON class_codes.role_id = user_roles.id
    WHERE user_roles.telegram_user_id=?
    AND user_roles.role_name=?
    """, (update.effective_user.id, role))

    classes = [r[0] for r in c.fetchall()]

    conn.close()

    keyboard = []

    for cls in classes:
        keyboard.append([
            InlineKeyboardButton(cls, callback_data=f"live_class|{cls}")
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

    context.user_data["live_role"] = role
    context.user_data["live_state"] = "class"

    await show_class_screen(update, context)


# -------------------------
# LOCATION SCREEN
# -------------------------

async def request_location(update, context):

    query = update.callback_query
    cls = query.data.split("|")[1]

    context.user_data["live_class"] = cls
    context.user_data["live_state"] = "location"

    await query.message.reply_text(
        "Send your location for attendance.",
        reply_markup=nav_buttons()
    )


# -------------------------
# LOCATION HANDLER
# -------------------------

async def save_live_location(update, context):

    user_lat = update.message.location.latitude
    user_lon = update.message.location.longitude

    role = context.user_data.get("live_role")
    cls = context.user_data.get("live_class")

    if not role or not cls:
        return

    conn = get_connection()
    c = conn.cursor()

    today = datetime.now().strftime("%Y-%m-%d")

    c.execute("""
    SELECT id
    FROM attendance_logs
    WHERE telegram_user_id=?
    AND class_code=?
    AND date=?
    """, (update.effective_user.id, cls, today))

    if c.fetchone():

        await update.message.reply_text(
            "Attendance already submitted today for this class."
        )

        conn.close()
        return

    c.execute("""
    SELECT venue_name, venue_lat, venue_lng
    FROM class_codes
    JOIN user_roles
    ON class_codes.role_id = user_roles.id
    WHERE user_roles.telegram_user_id=?
    AND user_roles.role_name=?
    AND class_codes.class_code=?
    """, (update.effective_user.id, role, cls))

    venue = c.fetchone()

    venue_name, venue_lat, venue_lng = venue

    dist = distance_m(user_lat, user_lon, venue_lat, venue_lng)

    if dist > ATTENDANCE_RADIUS:

        await update.message.reply_text(
            "You are too far from the venue."
        )

        conn.close()
        return

    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")

    c.execute("""
    INSERT INTO attendance_logs
    (telegram_user_id, role_name, class_code, latitude, longitude, date, timestamp)
    VALUES (?,?,?,?,?,?,?)
    """, (
        update.effective_user.id,
        role,
        cls,
        user_lat,
        user_lon,
        today,
        timestamp
    ))

    conn.commit()

    c.execute("""
    SELECT name
    FROM users
    WHERE telegram_user_id=?
    """, (update.effective_user.id,))

    name = c.fetchone()[0]

    conn.close()

    await update.message.reply_text(
        f"Attendance recorded for {cls}."
    )

    log_attendance(name, role, cls, venue_name, "Present")

    log_message = f"""
ATTENDANCE LOG

Name: {name}
Role: {role}
Class: {cls}
Venue: {venue_name}
Status: Present
Time: {timestamp}
"""

    topic_id = ROLE_TOPICS.get(role)

    await context.bot.send_message(
        chat_id=ADMIN_GROUP_ID,
        message_thread_id=topic_id,
        text=log_message
    )

    context.user_data.pop("live_role", None)
    context.user_data.pop("live_class", None)