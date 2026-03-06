from telegram import InlineKeyboardButton
from database import get_connection
from utils.sheets_logger import log_attendance
from datetime import datetime
from ui import show_screen


ADMIN_GROUP_ID = -1003584358970


async def start_late(update, context):

    conn = get_connection()
    c = conn.cursor()

    c.execute("""
    SELECT role_name
    FROM user_roles
    WHERE telegram_user_id=?
    """, (update.effective_user.id,))

    roles = [r[0] for r in c.fetchall()]

    conn.close()

    keyboard = []

    for role in roles:
        keyboard.append([InlineKeyboardButton(role, callback_data=f"late_role|{role}")])

    keyboard.append([InlineKeyboardButton("🏠 Menu", callback_data="menu")])

    await show_screen(update, context, "Select role for late report:", keyboard)


async def select_class(update, context):

    role = update.callback_query.data.split("|")[1]
    context.user_data["late_role"] = role

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
        keyboard.append([InlineKeyboardButton(cls, callback_data=f"late_class|{cls}")])

    keyboard.append([
        InlineKeyboardButton("⬅ Back", callback_data="menu_late"),
        InlineKeyboardButton("🏠 Menu", callback_data="menu")
    ])

    await show_screen(update, context, "Select class:", keyboard)


async def request_eta(update, context):

    cls = update.callback_query.data.split("|")[1]
    context.user_data["late_class"] = cls

    keyboard = [
        [InlineKeyboardButton("⬅ Back", callback_data="menu_late")],
        [InlineKeyboardButton("🏠 Menu", callback_data="menu")]
    ]

    await show_screen(update, context, "Enter your ETA (example: 10 minutes / 18:45)", keyboard)


async def save_eta(update, context):

    eta = update.message.text
    role = context.user_data.get("late_role")
    cls = context.user_data.get("late_class")

    conn = get_connection()
    c = conn.cursor()

    today = datetime.now().strftime("%Y-%m-%d")
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")

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

    keyboard = [[InlineKeyboardButton("🏠 Menu", callback_data="menu")]]

    await show_screen(
        update,
        context,
        "✅ Late report submitted.",
        keyboard
    )

    context.user_data.pop("late_role", None)
    context.user_data.pop("late_class", None)