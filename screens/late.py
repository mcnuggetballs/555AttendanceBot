from telegram import InlineKeyboardButton
from firestore_roles import get_roles
from firestore_classes import get_classes_for_role
from firestore_users import get_user
from firestore_attendance import attendance_exists
from firestore_late_reports import (
    late_report_exists,
    add_late_report
)
from utils.sheets_logger import log_attendance
from datetime import datetime
from zoneinfo import ZoneInfo
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


async def start_late(update, context):

    roles = get_roles(
        update.effective_user.id
    )

    keyboard = []

    for role in roles:
        keyboard.append([InlineKeyboardButton(role, callback_data=f"late_role|{role}")])

    keyboard.append([InlineKeyboardButton("🏠 Menu", callback_data="menu")])

    await show_screen(update, context, "Select role for late report:", keyboard)


async def select_class(update, context):

    role = update.callback_query.data.split("|")[1]
    context.user_data["late_role"] = role

    classes = get_classes_for_role(
        update.effective_user.id,
        role
    )

    classes = [c["class_code"] for c in classes]

    keyboard = []

    for cls in classes:
        keyboard.append([InlineKeyboardButton(cls, callback_data=f"late_class|{cls}")])

    keyboard.append([
        InlineKeyboardButton("⬅ Back", callback_data="menu_late"),
        InlineKeyboardButton("🏠 Menu", callback_data="menu")
    ])

    await show_screen(update, context, "Select class:", keyboard)


async def ask_student_name(update, context):

    keyboard = [
        [InlineKeyboardButton("⬅ Back", callback_data="menu_late")],
        [InlineKeyboardButton("🏠 Menu", callback_data="menu")]
    ]

    await show_screen(update, context, "Enter student name:", keyboard)


async def request_eta(update, context):

    if update.callback_query:
        cls = update.callback_query.data.split("|")[1]
        context.user_data["late_class"] = cls

    context.user_data["screen"] = "late_eta"

    keyboard = [
        [InlineKeyboardButton("⬅ Back", callback_data="menu_late")],
        [InlineKeyboardButton("🏠 Menu", callback_data="menu")]
    ]

    await show_screen(update, context, "Enter your ETA (example: 10 minutes / 18:45)", keyboard)


async def save_eta(update, context):

    eta = update.message.text

    role = context.user_data.get("late_role")
    cls = context.user_data.get("late_class")

    student = context.user_data.get("student_name")

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
            "⚠ You already submitted attendance for this class today.",
            keyboard
        )

        return


    if late_report_exists(
        update.effective_user.id,
        cls,
        today
    ):

        keyboard = [[InlineKeyboardButton("🏠 Menu", callback_data="menu")]]

        await show_screen(
            update,
            context,
            "⚠ You already submitted a late report for this class today.",
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

    venue_name = class_info.get(
        "venue_name",
        "Unknown Venue"
    )

    # GET NAME
    user = get_user(
        update.effective_user.id
    )

    name = user.get(
        "name",
        "Unknown"
    )

    timestamp = datetime.now(ZoneInfo("Asia/Singapore")).strftime("%Y-%m-%d %H:%M")

    add_late_report(
        update.effective_user.id,
        role,
        cls,
        student,
        eta,
        today,
        timestamp
    )

    keyboard = [[InlineKeyboardButton("🏠 Menu", callback_data="menu")]]

    await show_screen(
        update,
        context,
        "✅ Late report submitted.",
        keyboard
    )


    log_attendance(name, role, cls, student, venue_name, "Late")


    log_message = f"""
    LATE REPORT

    Name: {name}
    Role: {role}
    Class: {cls}
    """

    if student:
        log_message += f"Student: {student}\n"

    log_message += f"""Venue: {venue_name}
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
    context.user_data.pop("student_name", None)