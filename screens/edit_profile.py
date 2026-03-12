from telegram import InlineKeyboardButton
from database import get_connection
from ui import show_screen
from screens.onboarding import ROLES


async def show_profile(update, context):

    user_id = update.effective_user.id

    conn = get_connection()
    c = conn.cursor()

    # -------------------------
    # BASIC USER INFO
    # -------------------------

    c.execute("""
    SELECT name, dob, notes
    FROM users
    WHERE telegram_user_id=?
    """, (user_id,))

    row = c.fetchone()

    if not row:

        conn.close()

        keyboard = [
            [InlineKeyboardButton("🏠 Menu", callback_data="menu")]
        ]

        await show_screen(
            update,
            context,
            "You must create an account first.",
            keyboard
        )
        return

    name, dob, notes = row

    if not notes:
        notes = "None"

    # -------------------------
    # ROLES + CLASSES
    # -------------------------

    c.execute("""
    SELECT id, role_name
    FROM user_roles
    WHERE telegram_user_id=?
    """, (user_id,))

    roles = c.fetchall()

    role_text = ""

    for role_id, role_name in roles:

        role_text += f"\n• {role_name}\n"

        c.execute("""
        SELECT class_code, venue_name
        FROM class_codes
        WHERE role_id=?
        """, (role_id,))

        classes = c.fetchall()

        for cls, venue in classes:
            role_text += f"    - {cls} ({venue})\n"

    conn.close()

    if not role_text:
        role_text = "None"

    # -------------------------
    # PROFILE TEXT
    # -------------------------

    text = (
        "👤 *Profile*\n\n"
        f"*Name:* {name}\n"
        f"*DOB:* {dob}\n"
        f"*Notes:* {notes}\n\n"
        "*Roles & Classes:*"
        f"{role_text}"
    )

    keyboard = [
        [InlineKeyboardButton("Edit Name", callback_data="edit_name")],
        [InlineKeyboardButton("Edit DOB", callback_data="edit_dob")],
        [InlineKeyboardButton("Edit Notes", callback_data="edit_notes")],
        [InlineKeyboardButton("Edit Roles / Classes", callback_data="edit_roles")],
        [
            InlineKeyboardButton("⬅ Back", callback_data="menu"),
            InlineKeyboardButton("🏠 Menu", callback_data="menu")
        ]
    ]

    context.user_data["screen"] = "edit_profile_menu"

    await show_screen(update, context, text, keyboard)


# -------------------------
# EDIT NAME
# -------------------------

async def ask_name(update, context):

    keyboard = [
        [
            InlineKeyboardButton("⬅ Back", callback_data="menu_edit_profile"),
            InlineKeyboardButton("🏠 Menu", callback_data="menu")
        ]
    ]

    await show_screen(
        update,
        context,
        "Enter your new name:",
        keyboard
    )


async def save_name(update, context):

    new_name = update.message.text

    conn = get_connection()
    c = conn.cursor()

    c.execute("""
    UPDATE users
    SET name=?
    WHERE telegram_user_id=?
    """, (new_name, update.effective_user.id))

    conn.commit()
    conn.close()

    await show_profile(update, context)


# -------------------------
# EDIT DOB
# -------------------------

async def ask_dob(update, context):

    keyboard = [
        [
            InlineKeyboardButton("⬅ Back", callback_data="menu_edit_profile"),
            InlineKeyboardButton("🏠 Menu", callback_data="menu")
        ]
    ]

    await show_screen(
        update,
        context,
        "Enter new DOB (DDMMYYYY):",
        keyboard
    )


async def save_dob(update, context):

    dob = update.message.text

    conn = get_connection()
    c = conn.cursor()

    c.execute("""
    UPDATE users
    SET dob=?
    WHERE telegram_user_id=?
    """, (dob, update.effective_user.id))

    conn.commit()
    conn.close()

    await show_profile(update, context)


# -------------------------
# EDIT NOTES
# -------------------------

async def ask_notes(update, context):

    keyboard = [
        [
            InlineKeyboardButton("⬅ Back", callback_data="menu_edit_profile"),
            InlineKeyboardButton("🏠 Menu", callback_data="menu")
        ]
    ]

    await show_screen(
        update,
        context,
        "Enter new notes.\nType 'skip' to clear notes.",
        keyboard
    )


async def save_notes(update, context):

    notes = update.message.text

    if notes.lower() == "skip":
        notes = ""

    conn = get_connection()
    c = conn.cursor()

    c.execute("""
    UPDATE users
    SET notes=?
    WHERE telegram_user_id=?
    """, (notes, update.effective_user.id))

    conn.commit()
    conn.close()

    await show_profile(update, context)


# =========================================================
# NEW ROLE MANAGEMENT FEATURES
# =========================================================

async def edit_roles_menu(update, context):

    keyboard = [
        [InlineKeyboardButton("Add Role", callback_data="add_role")],
        [InlineKeyboardButton("Remove Role", callback_data="remove_role")],
        [
            InlineKeyboardButton("⬅ Back", callback_data="menu_edit_profile"),
            InlineKeyboardButton("🏠 Menu", callback_data="menu")
        ]
    ]

    await show_screen(
        update,
        context,
        "Manage your roles:",
        keyboard
    )


# -------------------------
# ADD ROLE
# -------------------------

async def add_role_menu(update, context):

    conn = get_connection()
    c = conn.cursor()

    c.execute("""
    SELECT role_name
    FROM user_roles
    WHERE telegram_user_id=?
    """, (update.effective_user.id,))

    existing = [r[0] for r in c.fetchall()]

    conn.close()

    keyboard = []

    for role in ROLES:
        if role not in existing:
            keyboard.append([
                InlineKeyboardButton(role, callback_data=f"add_role_confirm|{role}")
            ])

    keyboard.append([
        InlineKeyboardButton("⬅ Back", callback_data="edit_roles")
    ])

    await show_screen(update, context, "Select role to add:", keyboard)


async def add_role(update, context):

    role = update.callback_query.data.split("|")[1]

    conn = get_connection()
    c = conn.cursor()

    c.execute("""
    INSERT INTO user_roles (telegram_user_id, role_name)
    VALUES (?,?)
    """, (update.effective_user.id, role))

    conn.commit()
    conn.close()

    await show_profile(update, context)


# -------------------------
# REMOVE ROLE
# -------------------------

async def remove_role_menu(update, context):

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
        keyboard.append([
            InlineKeyboardButton(role, callback_data=f"remove_role_confirm|{role}")
        ])

    keyboard.append([
        InlineKeyboardButton("⬅ Back", callback_data="edit_roles")
    ])

    await show_screen(update, context, "Select role to remove:", keyboard)


async def remove_role(update, context):

    role = update.callback_query.data.split("|")[1]

    conn = get_connection()
    c = conn.cursor()

    c.execute("""
    SELECT id
    FROM user_roles
    WHERE telegram_user_id=? AND role_name=?
    """, (update.effective_user.id, role))

    role_id = c.fetchone()[0]

    # delete classes first
    c.execute("""
    DELETE FROM class_codes
    WHERE role_id=?
    """, (role_id,))

    # delete role
    c.execute("""
    DELETE FROM user_roles
    WHERE id=?
    """, (role_id,))

    conn.commit()
    conn.close()

    await show_profile(update, context)