from telegram import InlineKeyboardButton
from ui import show_screen
from firestore_users import get_user
from firestore_roles import get_roles
from firestore_classes import (
    add_class,
    get_classes_for_role,
    delete_class as delete_firestore_class
)


async def start(update, context):

    user_id = update.effective_user.id

    user = get_user(user_id)

    # If account not created
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

    context.user_data["screen"] = "manage_classes"

    keyboard = [
        [InlineKeyboardButton("Add Class", callback_data="manage_add_class")],
        [InlineKeyboardButton("Delete Class", callback_data="manage_delete_class")],
        [
            InlineKeyboardButton("⬅ Back", callback_data="menu"),
            InlineKeyboardButton("🏠 Menu", callback_data="menu")
        ]
    ]

    await show_screen(
        update,
        context,
        "Manage Classes",
        keyboard
    )


# -------------------------
# ADD CLASS FLOW
# -------------------------

async def select_role(update, context):

    roles = get_roles(update.effective_user.id)

    keyboard = []

    for role in roles:
        keyboard.append([
            InlineKeyboardButton(role, callback_data=f"manage_role|{role}")
        ])

    keyboard.append([
        InlineKeyboardButton("⬅ Back", callback_data="menu_manage_classes"),
        InlineKeyboardButton("🏠 Menu", callback_data="menu")
    ])

    await show_screen(update, context, "Select role:", keyboard)


async def ask_class_code(update, context):

    role = update.callback_query.data.split("|")[1]
    context.user_data["manage_role"] = role

    context.user_data["screen"] = "manage_add_class_code"

    keyboard = [
        [
            InlineKeyboardButton("⬅ Back", callback_data="menu_manage_classes"),
            InlineKeyboardButton("🏠 Menu", callback_data="menu")
        ]
    ]

    await show_screen(
        update,
        context,
        f"Enter new class code for {role}:",
        keyboard
    )


async def ask_location(update, context):

    keyboard = [
        [
            InlineKeyboardButton("⬅ Back", callback_data="menu_manage_classes"),
            InlineKeyboardButton("🏠 Menu", callback_data="menu")
        ]
    ]

    await show_screen(
        update,
        context,
        "Send venue location.\n(Use Telegram's Send Location feature)",
        keyboard
    )


async def ask_venue_name(update, context):

    context.user_data["screen"] = "manage_venue"

    keyboard = [
        [
            InlineKeyboardButton("⬅ Back", callback_data="menu_manage_classes"),
            InlineKeyboardButton("🏠 Menu", callback_data="menu")
        ]
    ]

    await show_screen(
        update,
        context,
        "Enter venue address name:",
        keyboard
    )


async def save_new_class(update, context):

    venue_name = update.message.text

    role = context.user_data.get("manage_role")
    class_code = context.user_data.get("manage_class_code")

    venue_lat = context.user_data.get("venue_lat")
    venue_lng = context.user_data.get("venue_lng")

    existing_classes = get_classes_for_role(
        update.effective_user.id,
        role
    )

    duplicate = any(
        c["class_code"] == class_code
        for c in existing_classes
    )

    if duplicate:

        await show_screen(
            update,
            context,
            "⚠ Class code already exists.",
            [[InlineKeyboardButton("🏠 Menu", callback_data="menu")]]
        )
        return

    add_class(
        update.effective_user.id,
        role,
        class_code,
        venue_name,
        venue_lat,
        venue_lng
    )

    keyboard = [
        [InlineKeyboardButton("🏠 Menu", callback_data="menu")]
    ]

    await show_screen(
        update,
        context,
        f"✅ Class {class_code} added.",
        keyboard
    )


# -------------------------
# DELETE CLASS FLOW
# -------------------------

async def select_role_delete(update, context):

    roles = get_roles(update.effective_user.id)

    keyboard = []

    for role in roles:
        keyboard.append([
            InlineKeyboardButton(role, callback_data=f"manage_delete_role|{role}")
        ])

    keyboard.append([
        InlineKeyboardButton("⬅ Back", callback_data="menu_manage_classes"),
        InlineKeyboardButton("🏠 Menu", callback_data="menu")
    ])

    await show_screen(update, context, "Select role:", keyboard)


async def select_class_delete(update, context):

    role = update.callback_query.data.split("|")[1]
    context.user_data["manage_role"] = role

    classes = get_classes_for_role(
        update.effective_user.id,
        role
    )

    classes = [c["class_code"] for c in classes]

    keyboard = []

    for cls in classes:
        keyboard.append([
            InlineKeyboardButton(cls, callback_data=f"manage_delete_class|{cls}")
        ])

    keyboard.append([
        InlineKeyboardButton("⬅ Back", callback_data="menu_manage_classes"),
        InlineKeyboardButton("🏠 Menu", callback_data="menu")
    ])

    await show_screen(update, context, "Select class to delete:", keyboard)


async def delete_class(update, context):

    cls = update.callback_query.data.split("|")[1]
    role = context.user_data.get("manage_role")

    classes = get_classes_for_role(
        update.effective_user.id,
        role
    )

    class_to_delete = next(
        c for c in classes
        if c["class_code"] == cls
    )

    delete_firestore_class(
        update.effective_user.id,
        class_to_delete["id"]
    )

    keyboard = [
        [InlineKeyboardButton("🏠 Menu", callback_data="menu")]
    ]

    await show_screen(
        update,
        context,
        f"✅ Class {cls} deleted.",
        keyboard
    )