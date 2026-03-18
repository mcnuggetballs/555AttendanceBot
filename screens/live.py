from telegram import InlineKeyboardButton
from database import get_connection
from utils.sheets_logger import log_attendance
from datetime import datetime
from zoneinfo import ZoneInfo
import math
from ui import show_screen


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


def distance_m(lat1, lon1, lat2, lon2):

    R = 6371000

    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)

    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)

    a = math.sin(dphi/2)**2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda/2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))

    return R * c


def admin_hours_keyboard():

    keyboard = []

    for i in range(1, 6):
        keyboard.append([
            InlineKeyboardButton(str(i), callback_data=f"admin_hours|{i}")
        ])

    keyboard.append([InlineKeyboardButton("⬅ Back", callback_data="menu_live")])
    keyboard.append([InlineKeyboardButton("🏠 Menu", callback_data="menu")])

    return keyboard


async def ask_admin_hours(update, context):

    context.user_data["screen"] = "live_admin_hours"

    await show_screen(
        update,
        context,
        "How many hours of Admin work are you doing today?",
        admin_hours_keyboard()
    )


async def start_live(update, context):

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
        keyboard.append([InlineKeyboardButton(role, callback_data=f"live_role|{role}")])

    keyboard.append([InlineKeyboardButton("🏠 Menu", callback_data="menu")])

    await show_screen(update, context, "Select role:", keyboard)


async def select_class(update, context):

    query = update.callback_query
    role = query.data.split("|")[1]

    context.user_data["live_role"] = role

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
        keyboard.append([InlineKeyboardButton(cls, callback_data=f"live_class|{cls}")])

    keyboard.append([
        InlineKeyboardButton("⬅ Back", callback_data="menu_live"),
        InlineKeyboardButton("🏠 Menu", callback_data="menu")
    ])

    await show_screen(update, context, "Select class:", keyboard)


async def ask_student_name(update, context):

    keyboard = [
        [InlineKeyboardButton("⬅ Back", callback_data="menu_live")],
        [InlineKeyboardButton("🏠 Menu", callback_data="menu")]
    ]

    await show_screen(update, context, "Enter student name:", keyboard)


async def request_location(update, context):

    # FIX: only update class if coming from live_class callback
    if update.callback_query and update.callback_query.data.startswith("live_class|"):
        query = update.callback_query
        cls = query.data.split("|")[1]
        context.user_data["live_class"] = cls

    keyboard = [
        [InlineKeyboardButton("⬅ Back", callback_data="menu_live")],
        [InlineKeyboardButton("🏠 Menu", callback_data="menu")]
    ]

    await show_screen(update, context, "Send your location for attendance.", keyboard)


async def save_live_location(update, context):
    # ---------------------
    # SECURITY CHECKS
    # ---------------------

    location = update.message.location

    # 1. Must be LIVE location
    if not location.live_period:
        keyboard = [[InlineKeyboardButton("🏠 Menu", callback_data="menu")]]

        await show_screen(
            update,
            context,
            "⚠ Please send a LIVE location (not a static/pinned one).",
            keyboard
        )
        return

    # 2. Reject forwarded locations
    if update.message.forward_date:
        keyboard = [[InlineKeyboardButton("🏠 Menu", callback_data="menu")]]

        await show_screen(
            update,
            context,
            "⚠ Forwarded locations are not allowed.",
            keyboard
        )
        return

    # 3. Check message freshness (within 30 seconds)
    now_utc = datetime.now(ZoneInfo("UTC"))
    msg_time = update.message.date

    if (now_utc - msg_time).total_seconds() > 30:
        keyboard = [[InlineKeyboardButton("🏠 Menu", callback_data="menu")]]

        await show_screen(
            update,
            context,
            "⚠ Location is too old. Please send again.",
            keyboard
        )
        return
    
    user_lat = location.latitude
    user_lon = location.longitude

    role = context.user_data.get("live_role")
    cls = context.user_data.get("live_class")
    student = context.user_data.get("student_name")
    admin_hours = context.user_data.get("admin_hours")

    conn = get_connection()
    c = conn.cursor()

    today = datetime.now(ZoneInfo("Asia/Singapore")).strftime("%Y-%m-%d")

    c.execute("""
    SELECT id
    FROM attendance_logs
    WHERE telegram_user_id=? AND class_code=? AND date=?
    """, (update.effective_user.id, cls, today))

    if c.fetchone():

        keyboard = [[InlineKeyboardButton("🏠 Menu", callback_data="menu")]]

        await show_screen(
            update,
            context,
            "⚠ Attendance already submitted today for this class.",
            keyboard
        )

        conn.close()
        return

    c.execute("""
    SELECT venue_name, venue_lat, venue_lng
    FROM class_codes
    JOIN user_roles ON class_codes.role_id = user_roles.id
    WHERE user_roles.telegram_user_id=? AND user_roles.role_name=? AND class_codes.class_code=?
    """, (update.effective_user.id, role, cls))

    venue_name, venue_lat, venue_lng = c.fetchone()

    dist = distance_m(user_lat, user_lon, venue_lat, venue_lng)

    if dist > ATTENDANCE_RADIUS:

        keyboard = [[InlineKeyboardButton("🏠 Menu", callback_data="menu")]]

        await show_screen(
            update,
            context,
            "⚠ You are too far from the venue.",
            keyboard
        )

        conn.close()
        return

    timestamp = datetime.now(ZoneInfo("Asia/Singapore")).strftime("%Y-%m-%d %H:%M")

    c.execute("""
    INSERT INTO attendance_logs
    (telegram_user_id, role_name, class_code, student_name, latitude, longitude, admin_hours, date, timestamp)
    VALUES (?,?,?,?,?,?,?,?,?)
    """, (
        update.effective_user.id,
        role,
        cls,
        student,
        user_lat,
        user_lon,
        admin_hours,
        today,
        timestamp
    ))

    conn.commit()

    c.execute("SELECT name FROM users WHERE telegram_user_id=?", (update.effective_user.id,))
    name = c.fetchone()[0]

    conn.close()

    keyboard = [[InlineKeyboardButton("🏠 Menu", callback_data="menu")]]

    await show_screen(
        update,
        context,
        f"✅ Attendance recorded for {cls}.",
        keyboard
    )

    log_attendance(name, role, cls, student, venue_name, "Present", admin_hours)

    topic_id = ROLE_TOPICS.get(role)

    log_message = (
        "ATTENDANCE LOG\n\n"
        f"Name: {name}\n"
        f"Role: {role}\n"
        f"Class: {cls}\n"
    )

    if student:
        log_message += f"Student: {student}\n"

    log_message += f"Venue: {venue_name}\n"

    if role == "Admin":
        log_message += f"Admin Hours: {admin_hours}\n"

    log_message += (
        "Status: Present\n"
        f"Time: {timestamp}"
    )

    await context.bot.send_message(
        chat_id=ADMIN_GROUP_ID,
        message_thread_id=topic_id,
        text=log_message
    )

    context.user_data.pop("live_role", None)
    context.user_data.pop("live_class", None)
    context.user_data.pop("student_name", None)
    context.user_data.pop("admin_hours", None)