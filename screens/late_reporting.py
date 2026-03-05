from telegram import InlineKeyboardButton, InlineKeyboardMarkup


def nav():

    return InlineKeyboardMarkup([

        [
            InlineKeyboardButton("⬅ Back", callback_data="back"),
            InlineKeyboardButton("🏠 Menu", callback_data="menu")
        ]
    ])


async def select_role(update, context):

    keyboard = [

        [InlineKeyboardButton("Instructor", callback_data="role_instructor")]

    ]

    keyboard.append([
        InlineKeyboardButton("⬅ Back", callback_data="back")
    ])

    await update.callback_query.message.reply_text(
        "Select role",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )


async def select_class(update, context):

    await update.callback_query.message.reply_text(
        "Select class",
        reply_markup=nav()
    )


async def ask_eta(update, context):

    await update.callback_query.message.reply_text(
        "Enter ETA (HHMM)",
        reply_markup=nav()
    )


async def submit_eta(update, context):

    eta = update.message.text

    await update.message.reply_text(
        f"Late report submitted. ETA {eta}"
    )