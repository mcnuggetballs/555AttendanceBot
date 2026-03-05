from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup
)

from telegram.ext import ContextTypes, ConversationHandler
import sqlite3


NAME, DOB, ROLE_SELECT, NOTES, CLASS_CODE, VENUE, MORE_CODES = range(7)


ROLES = [
    "Internal Instructor",
    "External Instructor",
    "Private Instructor",
    "Admin",
    "Student Mentor",
    "AEP Performer"
]


def build_role_keyboard(selected_roles):

    keyboard = []

    for role in ROLES:

        if role in selected_roles:
            text = f"✅ {role}"
        else:
            text = f"⬜ {role}"

        keyboard.append([
            InlineKeyboardButton(text, callback_data=f"role|{role}")
        ])

    keyboard.append([InlineKeyboardButton("Done", callback_data="done")])
    keyboard.append([InlineKeyboardButton("Cancel", callback_data="cancel")])

    return InlineKeyboardMarkup(keyboard)


async def start_onboarding(update: Update, context: ContextTypes.DEFAULT_TYPE):

    user_id = update.effective_user.id

    conn = sqlite3.connect("attendance.db")
    c = conn.cursor()

    c.execute("""
    SELECT name FROM users
    WHERE telegram_user_id=?
    """, (user_id,))

    existing = c.fetchone()

    conn.close()

    if existing and existing[0]:

        await update.message.reply_text(
            "Account already created. Contact admin if you need changes."
        )

        return ConversationHandler.END

    await update.message.reply_text("Enter your name:")

    return NAME


async def get_name(update: Update, context: ContextTypes.DEFAULT_TYPE):

    context.user_data["name"] = update.message.text

    await update.message.reply_text("Enter your DOB (DDMMYYYY):")

    return DOB


async def get_dob(update: Update, context: ContextTypes.DEFAULT_TYPE):

    context.user_data["dob"] = update.message.text
    context.user_data["roles"] = []

    keyboard = build_role_keyboard([])

    await update.message.reply_text(
        "Select your roles:",
        reply_markup=keyboard
    )

    return ROLE_SELECT


async def onboarding_select_role(update: Update, context: ContextTypes.DEFAULT_TYPE):

    query = update.callback_query
    await query.answer()

    data = query.data
    selected_roles = context.user_data["roles"]

    if data.startswith("role|"):

        role = data.split("|")[1]

        if role in selected_roles:
            selected_roles.remove(role)
        else:
            selected_roles.append(role)

        keyboard = build_role_keyboard(selected_roles)

        await query.edit_message_reply_markup(reply_markup=keyboard)

        return ROLE_SELECT

    elif data == "done":

        if not selected_roles:
            await query.answer("Select at least one role")
            return ROLE_SELECT

        await query.edit_message_text(
            "Any notes? Type skip if none."
        )

        return NOTES

    elif data == "cancel":

        await query.edit_message_text("Cancelled.")

        return ConversationHandler.END


async def get_notes(update: Update, context: ContextTypes.DEFAULT_TYPE):

    notes = update.message.text

    if notes.lower() == "skip":
        notes = ""

    user_id = update.effective_user.id
    name = context.user_data["name"]
    dob = context.user_data["dob"]
    roles = context.user_data["roles"]

    conn = sqlite3.connect("attendance.db")
    c = conn.cursor()

    c.execute("""
        UPDATE users
        SET name=?, dob=?, notes=?
        WHERE telegram_user_id=?
    """, (name, dob, notes, user_id))

    for role in roles:

        c.execute("""
            INSERT INTO user_roles (telegram_user_id, role_name)
            VALUES (?,?)
        """, (user_id, role))

    conn.commit()
    conn.close()

    context.user_data["role_index"] = 0

    role = roles[0]

    await update.message.reply_text(
        f"Enter class code for role {role}"
    )

    return CLASS_CODE


async def get_class_code(update: Update, context: ContextTypes.DEFAULT_TYPE):

    class_code = update.message.text.upper()

    context.user_data["current_class_code"] = class_code

    await update.message.reply_text(
        "Send venue location."
    )

    return VENUE


async def save_venue(update: Update, context: ContextTypes.DEFAULT_TYPE):

    location = update.message.location

    lat = location.latitude
    lng = location.longitude

    class_code = context.user_data["current_class_code"]
    roles = context.user_data["roles"]
    role_index = context.user_data["role_index"]
    role = roles[role_index]

    user_id = update.effective_user.id

    conn = sqlite3.connect("attendance.db")
    c = conn.cursor()

    c.execute("""
        SELECT id FROM user_roles
        WHERE telegram_user_id=? AND role_name=?
    """, (user_id, role))

    role_id = c.fetchone()[0]

    c.execute("""
        INSERT INTO class_codes
        (user_role_id, class_code, venue_lat, venue_lng)
        VALUES (?,?,?,?)
    """, (role_id, class_code, lat, lng))

    conn.commit()
    conn.close()

    await update.message.reply_text(
        "Class saved. Add another class code? (yes/no)"
    )

    return MORE_CODES


async def more_codes(update: Update, context: ContextTypes.DEFAULT_TYPE):

    answer = update.message.text.lower()

    roles = context.user_data["roles"]
    role_index = context.user_data["role_index"]

    if answer == "yes":

        role = roles[role_index]

        await update.message.reply_text(
            f"Enter another class code for role {role}"
        )

        return CLASS_CODE

    elif answer == "no":

        role_index += 1
        context.user_data["role_index"] = role_index

        if role_index >= len(roles):

            await update.message.reply_text(
                "Account setup complete ✅"
            )

            return ConversationHandler.END

        next_role = roles[role_index]

        await update.message.reply_text(
            f"Enter class code for role {next_role}"
        )

        return CLASS_CODE

    else:

        await update.message.reply_text(
            "Please answer yes or no."
        )

        return MORE_CODES