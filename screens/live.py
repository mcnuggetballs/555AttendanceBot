from telegram import InlineKeyboardButton
from utils.sheets_logger import log_attendance
from datetime import datetime
from zoneinfo import ZoneInfo
import math
from ui import show_screen
from firestore_roles import get_roles
from firestore_classes import get_classes_for_role
from firestore_users import get_user
from firestore_attendance import attendance_exists, add_attendance


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
        "How many hours are you doing today?",
        admin_hours_keyboard()
    )


# ✅ NEW: AEP school input
async def ask_school_name(update, context):

    keyboard = [
        [InlineKeyboardButton("⬅ Back", callback_data="menu_live")],
        [InlineKeyboardButton("🏠 Menu", callback_data="menu")]
    ]

    await show_screen(update, context, "Enter school name:", keyboard)


async def start_live(update, context):

    user_id = update.effective_user.id

    roles = get_roles(user_id)

    keyboard = []

    for role in roles:
        keyboard.append([InlineKeyboardButton(role, callback_data=f"live_role|{role}")])

    keyboard.append([InlineKeyboardButton("🏠 Menu", callback_data="menu")])

    await show_screen(update, context, "Select role:", keyboard)


async def select_class(update, context):

    query = update.callback_query
    role = query.data.split("|")[1]

    context.user_data["live_role"] = role

    classes = get_classes_for_role(
        update.effective_user.id,
        role
    )

    classes = [c["class_code"] for c in classes]

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

    await show_screen(update, context, "Enter name:", keyboard)


async def request_location(update, context):

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

    if not location.live_period:

        keyboard = [[InlineKeyboardButton("🏠 Menu", callback_data="menu")]]

        await show_screen(
            update,
            context,
            "⚠ Please send a LIVE location (not a static/pinned one).",
            keyboard
        )
        return

    if getattr(update.message, "forward_date", None):

        keyboard = [[InlineKeyboardButton("🏠 Menu", callback_data="menu")]]

        await show_screen(
            update,
            context,
            "⚠ Forwarded locations are not allowed.",
            keyboard
        )
        return

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
    school_location = context.user_data.get("school_location")
    admin_hours = context.user_data.get("admin_hours")

    today = datetime.now(ZoneInfo("Asia/Singapore")).strftime("%Y-%m-%d")

    if attendance_exists(
        update.effective_user.id,
        cls,
        today
    ):
        keyboard = [[InlineKeyboardButton("🏠 Menu", callback_data="menu")]]

        await show_screen(
            update,
            context,
            "⚠ Attendance already submitted today for this class.",
            keyboard
        )

        return

    classes = get_classes_for_role(
        update.effective_user.id,
        role
    )

    class_info = next(
        c for c in classes
        if c["class_code"] == cls
    )

    venue_name = class_info["venue_name"]
    venue_lat = class_info["venue_lat"]
    venue_lng = class_info["venue_lng"]

    # AEP Performer does not use fixed venue coordinates
    if role == "AEP Performer":

        venue_name = school_location

    else:

        dist = distance_m(
            user_lat,
            user_lon,
            venue_lat,
            venue_lng
        )

        if dist > ATTENDANCE_RADIUS:

            keyboard = [[InlineKeyboardButton("🏠 Menu", callback_data="menu")]]

            await show_screen(
                update,
                context,
                "⚠ You are too far from the venue.",
                keyboard
            )

            return

    timestamp = datetime.now(ZoneInfo("Asia/Singapore")).strftime("%Y-%m-%d %H:%M")

    add_attendance(
        update.effective_user.id,
        role,
        cls,
        student,
        user_lat,
        user_lon,
        admin_hours,
        today,
        timestamp
    )

    user = get_user(update.effective_user.id)
    name = user["name"]

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
        log_message += f"Student/School Name: {student}\n"

    log_message += f"Venue: {venue_name}\n"

    if role in ["Admin", "External Instructor"]:
        log_message += f"Hours: {admin_hours}\n"

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
    context.user_data.pop("school_location", None)
    context.user_data.pop("admin_hours", None)

async def ask_school_location(update, context):

    keyboard = [
        [InlineKeyboardButton("⬅ Back", callback_data="menu_live")],
        [InlineKeyboardButton("🏠 Menu", callback_data="menu")]
    ]

    await show_screen(
        update,
        context,
        "Enter school location:",
        keyboard
    )