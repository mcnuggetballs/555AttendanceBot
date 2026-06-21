from telegram import InlineKeyboardButton
from ui import show_screen
from screens.onboarding import ROLES
from firestore_users import (
    get_user,
    update_name,
    update_dob,
    update_notes
)

from firestore_roles import (
    get_roles,
    add_role as add_firestore_role,
    remove_role as remove_firestore_role
)

from firestore_classes import (
    get_classes_for_role,
    get_classes,
    delete_class as delete_firestore_class
)


MASTER_PASSWORD = "hbgw9unbwobnw"


async def show_profile(update, context):

    user_id = update.effective_user.id

    user = get_user(user_id)

    if not user:

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

    name = user.get("name", "")
    dob = user.get("dob", "")
    notes = user.get("notes", "")

    if not notes:
        notes = "None"

    roles = get_roles(user_id)

    role_text = ""

    for role_name in roles:

        role_text += f"\n• {role_name}\n"

        classes = get_classes_for_role(
            user_id,
            role_name
        )

        for cls in classes:

            venue = cls.get("venue_name", "")

            role_text += (
                f"    - {cls['class_code']} "
                f"({venue})\n"
            )

    if not role_text:
        role_text = "None"

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
        [InlineKeyboardButton("Edit Roles", callback_data="edit_roles")],
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

    await show_screen(update, context, "Enter your new name:", keyboard)


async def save_name(update, context):

    new_name = update.message.text

    update_name(
        update.effective_user.id,
        new_name
    )

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

    await show_screen(update, context, "Enter new DOB (DDMMYYYY):", keyboard)


async def save_dob(update, context):

    dob = update.message.text

    update_dob(
        update.effective_user.id,
        dob
    )

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

    update_notes(
        update.effective_user.id,
        notes
    )

    await show_profile(update, context)


# =========================================================
# ROLE MANAGEMENT
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

    await show_screen(update, context, "Manage your roles:", keyboard)


# -------------------------
# ADD ROLE
# -------------------------

async def add_role_menu(update, context):

    existing = get_roles(
        update.effective_user.id
    )

    keyboard = []

    AVAILABLE_ROLES = ROLES + ["Master Control"]  # ✅ ADD HERE

    for role in AVAILABLE_ROLES:
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

    # 🚨 MASTER CONTROL PROTECTION
    if role == "Master Control":
        context.user_data["pending_role"] = role
        context.user_data["screen"] = "master_add_password"

        await show_screen(update, context, "Enter Master Control password:")
        return

    add_firestore_role(
        update.effective_user.id,
        role
    )

    await show_profile(update, context)


# -------------------------
# REMOVE ROLE
# -------------------------

async def remove_role_menu(update, context):

    roles = get_roles(
        update.effective_user.id
    )

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

    classes = get_classes_for_role(
        update.effective_user.id,
        role
    )

    for cls in classes:

        delete_firestore_class(
            update.effective_user.id,
            cls["id"]
        )

    remove_firestore_role(
        update.effective_user.id,
        role
    )

    await show_profile(update, context)