from telegram import InlineKeyboardButton, InlineKeyboardMarkup


async def show_menu(update, context):

    keyboard = [
        [InlineKeyboardButton("Create Account", callback_data="create_account")],
        [InlineKeyboardButton("Live Attendance", callback_data="menu_live")]
    ]

    markup = InlineKeyboardMarkup(keyboard)

    if update.message:
        await update.message.reply_text("Main Menu", reply_markup=markup)
    else:
        await update.callback_query.message.reply_text("Main Menu", reply_markup=markup)