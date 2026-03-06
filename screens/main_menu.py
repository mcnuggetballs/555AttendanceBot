from telegram import InlineKeyboardButton, InlineKeyboardMarkup


async def show_menu(update, context):

    keyboard = [
        [InlineKeyboardButton("Create Account", callback_data="create_account")],
        [InlineKeyboardButton("Live Attendance", callback_data="menu_live")],
        [InlineKeyboardButton("Late Report", callback_data="menu_late")],
        [InlineKeyboardButton("Status", callback_data="menu_status")],
        [InlineKeyboardButton("Today's Attendance", callback_data="menu_today")],
        [InlineKeyboardButton("Who is Here?", callback_data="menu_who")]
    ]

    markup = InlineKeyboardMarkup(keyboard)

    if update.message:
        await update.message.reply_text("Main Menu", reply_markup=markup)
    else:
        await update.callback_query.message.reply_text("Main Menu", reply_markup=markup)