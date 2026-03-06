from telegram import InlineKeyboardButton
from ui import show_screen


async def show_menu(update, context):

    keyboard = [
        [InlineKeyboardButton("Create Account", callback_data="create_account")],
        [InlineKeyboardButton("Live Attendance", callback_data="menu_live")],
        [InlineKeyboardButton("Late Report", callback_data="menu_late")],
        [InlineKeyboardButton("Status", callback_data="menu_status")],
        [InlineKeyboardButton("Today's Attendance", callback_data="menu_today")],
        [InlineKeyboardButton("Who is Here?", callback_data="menu_who")]
    ]

    await show_screen(
        update,
        context,
        "📋 Main Menu",
        keyboard
    )