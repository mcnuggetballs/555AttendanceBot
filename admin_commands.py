from telegram import InlineKeyboardButton
from ui import show_screen
from keyboards import menu_keyboard
from datetime import datetime
from zoneinfo import ZoneInfo

from firestore_reports import (
    get_today_attendance,
    get_today_late_reports,
    get_attendance_for_class,
    get_late_for_class
)

from firestore_classes import get_classes
from firestore_users import get_user
from firestore_db import db


async def today(update, context):

    today_date = datetime.now(
        ZoneInfo("Asia/Singapore")
    ).strftime("%Y-%m-%d")

    present = get_today_attendance(today_date)
    late = get_today_late_reports(today_date)

    if not present and not late:

        await show_screen(
            update,
            context,
            "No attendance recorded today.",
            menu_keyboard()
        )
        return

    message = "📋 TODAY'S ATTENDANCE\n\n"

    for row in present:
        message += (
            f"{row['name']} — "
            f"{row['role']} — "
            f"{row['class_code']} — ✅ Present\n"
        )

    for row in late:
        message += (
            f"{row['name']} — "
            f"{row['role']} — "
            f"{row['class_code']} — ⏰ Late\n"
        )

    await show_screen(
        update,
        context,
        message,
        menu_keyboard()
    )


async def who(update, context):
    docs = (
        db.collection_group("classes")
        .stream()
    )

    classes = sorted(
        list({
            doc.to_dict()["class_code"]
            for doc in docs
        })
    )

    keyboard = []

    for cls in classes:
        keyboard.append([InlineKeyboardButton(cls, callback_data=f"who_class|{cls}")])

    keyboard.append([InlineKeyboardButton("🏠 Menu", callback_data="menu")])

    await show_screen(update, context, "Select class:", keyboard)


async def who_class(update, context):

    query = update.callback_query
    cls = query.data.split("|")[1]

    today_date = datetime.now(
        ZoneInfo("Asia/Singapore")
    ).strftime("%Y-%m-%d")

    present = get_attendance_for_class(
        cls,
        today_date
    )

    late = get_late_for_class(
        cls,
        today_date
    )

    if not present and not late:

        await show_screen(
            update,
            context,
            f"No attendance recorded for {cls} today.",
            [[InlineKeyboardButton("⬅ Back", callback_data="menu_who")]]
        )
        return

    text = f"ATTENDANCE FOR {cls}\n\n"

    for row in present:
        text += f"{row['name']} — Present\n"

    for row in late:
        text += f"{row['name']} — Late\n"

    keyboard = [
        [InlineKeyboardButton("⬅ Back", callback_data="menu_who")],
        [InlineKeyboardButton("🏠 Menu", callback_data="menu")]
    ]

    await show_screen(
        update,
        context,
        text,
        keyboard
    )