from telegram import InlineKeyboardButton


def menu_keyboard():
    return [[InlineKeyboardButton("🏠 Menu", callback_data="menu")]]


def back_menu_keyboard():
    return [[
        InlineKeyboardButton("⬅ Back", callback_data="back"),
        InlineKeyboardButton("🏠 Menu", callback_data="menu")
    ]]


def back_only_keyboard():
    return [[InlineKeyboardButton("⬅ Back", callback_data="back")]]


def yes_no_keyboard(yes_cb, no_cb):
    return [[
        InlineKeyboardButton("Yes", callback_data=yes_cb),
        InlineKeyboardButton("No", callback_data=no_cb)
    ]]