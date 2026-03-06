from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from database import get_connection


ROLES = [
    "Internal Instructor",
    "External Instructor",
    "Private Instructor",
    "Admin",
    "Student Mentor",
    "AEP Performer"
]


def get_msg(update):
    if update.message:
        return update.message
    return update.callback_query.message


def nav():
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("⬅ Back", callback_data="back"),
            InlineKeyboardButton("🏠 Menu", callback_data="menu")
        ]
    ])


async def ask_name(update, context):

    msg = get_msg(update)
    context.user_data["screen"] = "onboarding_name"

    await msg.reply_text("Enter your name:", reply_markup=nav())


async def save_name(update, context):

    context.user_data["name"] = update.message.text

    return "onboarding_dob"


async def ask_dob(update, context):

    msg = get_msg(update)
    context.user_data["screen"] = "onboarding_dob"

    await msg.reply_text("Enter DOB (DDMMYYYY):", reply_markup=nav())


async def save_dob(update, context):

    context.user_data["dob"] = update.message.text
    context.user_data["roles"] = []

    return "onboarding_role"


def build_role_keyboard(selected):

    keyboard = []

    for role in ROLES:

        if role in selected:
            text = f"✅ {role}"
        else:
            text = f"⬜ {role}"

        keyboard.append([
            InlineKeyboardButton(text, callback_data=f"role_toggle|{role}")
        ])

    keyboard.append([InlineKeyboardButton("Done", callback_data="role_done")])

    return InlineKeyboardMarkup(keyboard)


async def ask_roles(update, context):

    msg = get_msg(update)
    context.user_data["screen"] = "onboarding_role"

    keyboard = build_role_keyboard(context.user_data["roles"])

    await msg.reply_text("Select your roles:", reply_markup=keyboard)


async def toggle_role(update, context):

    query = update.callback_query
    role = query.data.split("|")[1]

    roles = context.user_data["roles"]

    if role in roles:
        roles.remove(role)
    else:
        roles.append(role)

    keyboard = build_role_keyboard(roles)

    await query.message.edit_reply_markup(reply_markup=keyboard)


async def ask_notes(update, context):

    msg = get_msg(update)
    context.user_data["screen"] = "onboarding_notes"

    await msg.reply_text("Any notes? (type skip)", reply_markup=nav())


async def save_notes(update, context):

    notes = update.message.text

    if notes.lower() == "skip":
        notes = ""

    context.user_data["notes"] = notes

    context.user_data["role_index"] = 0
    context.user_data["role_classes"] = {}

    return "onboarding_config_role"


async def ask_config_role(update, context):

    msg = get_msg(update)

    roles = context.user_data["roles"]
    index = context.user_data["role_index"]

    role = roles[index]

    await msg.reply_text(
        f"Configure class codes for role:\n{role}"
    )

    context.user_data["screen"] = "onboarding_class_code"

    await msg.reply_text(
        "Enter class code:",
        reply_markup=nav()
    )


async def ask_class_code(update, context):

    msg = get_msg(update)

    context.user_data["screen"] = "onboarding_class_code"

    await msg.reply_text("Enter class code:", reply_markup=nav())


async def save_class_code(update, context):

    class_code = update.message.text.strip()

    context.user_data["current_class"] = class_code

    await update.message.reply_text(
        "Send venue location."
    )

    return "onboarding_location"


async def save_venue_location(update, context):

    location = update.message.location

    context.user_data["venue_lat"] = location.latitude
    context.user_data["venue_lng"] = location.longitude

    await update.message.reply_text(
        "Enter venue name:"
    )

    return "onboarding_venue"


async def ask_venue_name(update, context):

    msg = get_msg(update)

    context.user_data["screen"] = "onboarding_venue"

    await msg.reply_text("Enter venue name:", reply_markup=nav())


async def save_venue_name(update, context):

    venue_name = update.message.text

    role_index = context.user_data["role_index"]
    role = context.user_data["roles"][role_index]

    class_data = {
        "class_code": context.user_data["current_class"],
        "venue_name": venue_name,
        "venue_lat": context.user_data["venue_lat"],
        "venue_lng": context.user_data["venue_lng"]
    }

    context.user_data["role_classes"].setdefault(role, []).append(class_data)

    keyboard = InlineKeyboardMarkup([
        [
            InlineKeyboardButton("Yes", callback_data="add_class_yes"),
            InlineKeyboardButton("No", callback_data="add_class_no")
        ]
    ])

    await update.message.reply_text(
        f"Add another class code for {role}?",
        reply_markup=keyboard
    )

    return None


async def next_role(update, context):

    context.user_data["role_index"] += 1

    roles = context.user_data["roles"]

    if context.user_data["role_index"] >= len(roles):
        return await finish_onboarding(update, context)

    return "onboarding_config_role"


async def finish_onboarding(update, context):

    conn = get_connection()
    c = conn.cursor()

    user_id = update.effective_user.id

    # FIX: preserve verified flag instead of replacing row
    c.execute("""
    INSERT INTO users
    (telegram_user_id, name, dob, notes, verified)
    VALUES (?,?,?,?,1)
    ON CONFLICT(telegram_user_id)
    DO UPDATE SET
        name=excluded.name,
        dob=excluded.dob,
        notes=excluded.notes
    """, (
        user_id,
        context.user_data["name"],
        context.user_data["dob"],
        context.user_data["notes"]
    ))

    role_ids = {}

    for role in context.user_data["roles"]:

        c.execute("""
        INSERT INTO user_roles (telegram_user_id, role_name)
        VALUES (?,?)
        """, (user_id, role))

        role_ids[role] = c.lastrowid

    for role, classes in context.user_data["role_classes"].items():

        role_id = role_ids[role]

        for cls in classes:

            c.execute("""
            INSERT INTO class_codes
            (role_id, class_code, venue_name, venue_lat, venue_lng)
            VALUES (?,?,?,?,?)
            """, (
                role_id,
                cls["class_code"],
                cls["venue_name"],
                cls["venue_lat"],
                cls["venue_lng"]
            ))

    conn.commit()
    conn.close()

    await get_msg(update).reply_text("Account setup complete.")

    verified = context.user_data.get("verified")

    context.user_data.clear()

    context.user_data["verified"] = verified

    return "menu"