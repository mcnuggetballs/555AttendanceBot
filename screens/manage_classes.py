from telegram import InlineKeyboardButton
from database import get_connection
from ui import show_screen


async def start(update, context):

    user_id = update.effective_user.id

    conn = get_connection()
    c = conn.cursor()

    c.execute(
        "SELECT name FROM users WHERE telegram_user_id=?",
        (user_id,)
    )

    row = c.fetchone()

    conn.close()

    # If account not created
    if not row or row[0] is None:

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

    conn = get_connection()
    c = conn.cursor()

    # Get role id
    c.execute("""
    SELECT id
    FROM user_roles
    WHERE telegram_user_id=? AND role_name=?
    """, (update.effective_user.id, role))

    role_row = c.fetchone()

    if not role_row:

        conn.close()

        await show_screen(
            update,
            context,
            "Role not found.",
            [[InlineKeyboardButton("🏠 Menu", callback_data="menu")]]
        )
        return

    role_id = role_row[0]

    # Check duplicate
    c.execute("""
    SELECT id
    FROM class_codes
    WHERE role_id=? AND class_code=?
    """, (role_id, class_code))

    if c.fetchone():

        conn.close()

        await show_screen(
            update,
            context,
            "⚠ Class code already exists.",
            [[InlineKeyboardButton("🏠 Menu", callback_data="menu")]]
        )
        return

    # Insert class
    c.execute("""
    INSERT INTO class_codes
    (role_id, class_code, venue_name, venue_lat, venue_lng)
    VALUES (?,?,?,?,?)
    """, (
        role_id,
        class_code,
        venue_name,
        venue_lat,
        venue_lng
    ))

    conn.commit()
    conn.close()

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

    conn = get_connection()
    c = conn.cursor()

    c.execute("""
    DELETE FROM class_codes
    WHERE class_code=?
    AND role_id IN (
        SELECT id FROM user_roles
        WHERE telegram_user_id=? AND role_name=?
    )
    """, (cls, update.effective_user.id, role))

    conn.commit()
    conn.close()

    keyboard = [
        [InlineKeyboardButton("🏠 Menu", callback_data="menu")]
    ]

    await show_screen(
        update,
        context,
        f"✅ Class {cls} deleted.",
        keyboard
    )