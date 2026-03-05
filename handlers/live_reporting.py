from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup
)

from telegram.ext import ContextTypes, ConversationHandler

import sqlite3
import math

from utils.sheets_logger import log_attendance


LIVE_ROLE_SELECT, CLASS_SELECT, LOCATION = range(3)


ROLE_RADIUS = {
    "Internal Instructor": 100,
    "Student Mentor": 100,
    "External Instructor": 1000,
    "AEP Performer": 1000,
    "Private Instructor": 100,
    "Admin": 100
}


def calculate_distance(lat1, lon1, lat2, lon2):

    R = 6371000

    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)

    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)

    a = math.sin(dphi/2)**2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda/2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))

    return R * c


async def start_live(update: Update, context: ContextTypes.DEFAULT_TYPE):

    user_id = update.effective_user.id

    conn = sqlite3.connect("attendance.db")
    c = conn.cursor()

    c.execute("""
    SELECT role_name FROM user_roles
    WHERE telegram_user_id=?
    """, (user_id,))

    roles = c.fetchall()
    conn.close()

    keyboard = []

    for role in roles:
        keyboard.append([
            InlineKeyboardButton(role[0], callback_data=f"role|{role[0]}")
        ])

    await update.message.reply_text(
        "Select role:",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

    return LIVE_ROLE_SELECT


async def live_select_role(update: Update, context: ContextTypes.DEFAULT_TYPE):

    query = update.callback_query
    await query.answer()

    role = query.data.split("|")[1]

    context.user_data["selected_role"] = role

    user_id = query.from_user.id

    conn = sqlite3.connect("attendance.db")
    c = conn.cursor()

    c.execute("""
    SELECT id FROM user_roles
    WHERE telegram_user_id=? AND role_name=?
    """, (user_id, role))

    role_id = c.fetchone()[0]

    c.execute("""
    SELECT class_code FROM class_codes
    WHERE user_role_id=?
    """, (role_id,))

    classes = c.fetchall()
    conn.close()

    keyboard = []

    for code in classes:
        keyboard.append([
            InlineKeyboardButton(code[0], callback_data=f"class|{code[0]}")
        ])

    await query.edit_message_text(
        "Select class:",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

    return CLASS_SELECT


async def select_class(update: Update, context: ContextTypes.DEFAULT_TYPE):

    query = update.callback_query
    await query.answer()

    class_code = query.data.split("|")[1]

    context.user_data["selected_class"] = class_code

    await query.edit_message_text(
        "Send your LIVE location."
    )

    return LOCATION


async def receive_location(update: Update, context: ContextTypes.DEFAULT_TYPE):

    location = update.message.location

    user_lat = location.latitude
    user_lng = location.longitude

    class_code = context.user_data["selected_class"]
    role = context.user_data["selected_role"]

    user_id = update.effective_user.id
    name = update.effective_user.first_name

    conn = sqlite3.connect("attendance.db")
    c = conn.cursor()

    # Duplicate attendance protection
    c.execute("""
    SELECT id FROM attendance_logs
    WHERE telegram_user_id=?
    AND class_code=?
    AND date(timestamp)=date('now')
    """, (user_id, class_code))

    existing = c.fetchone()

    if existing:

        conn.close()

        await update.message.reply_text(
            "Attendance already recorded for this class today."
        )

        return ConversationHandler.END

    c.execute("""
    SELECT id FROM user_roles
    WHERE telegram_user_id=? AND role_name=?
    """, (user_id, role))

    role_id = c.fetchone()[0]

    c.execute("""
    SELECT venue_lat, venue_lng
    FROM class_codes
    WHERE user_role_id=? AND class_code=?
    """, (role_id, class_code))

    venue = c.fetchone()

    venue_lat = venue[0]
    venue_lng = venue[1]

    distance = calculate_distance(
        user_lat,
        user_lng,
        venue_lat,
        venue_lng
    )

    allowed_radius = ROLE_RADIUS.get(role, 100)

    if distance > allowed_radius:
        status = "OUTSIDE_RADIUS"
    else:
        status = "SUCCESS"

    c.execute("""
    INSERT INTO attendance_logs
    (telegram_user_id, role_name, class_code, distance, status)
    VALUES (?,?,?,?,?)
    """, (user_id, role, class_code, distance, status))

    conn.commit()
    conn.close()

    log_attendance(name, role, class_code, int(distance), status)

    message = (
        "ATTENDANCE LOG\n\n"
        f"Name: {name}\n"
        f"Role: {role}\n"
        f"Class: {class_code}\n"
        f"Distance: {int(distance)}m\n"
        f"Status: {status}"
    )

    topic_map = context.bot_data["ROLE_TOPICS"]

    thread_id = topic_map.get(role)

    await context.bot.send_message(
        chat_id=context.bot_data["ADMIN_CHAT_ID"],
        message_thread_id=thread_id,
        text=message
    )

    await update.message.reply_text(
        f"Attendance recorded\nDistance: {int(distance)}m"
    )

    return ConversationHandler.END