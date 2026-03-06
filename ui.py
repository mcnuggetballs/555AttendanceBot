from telegram import InlineKeyboardMarkup


async def show_screen(update, context, text, keyboard=None):

    chat_id = update.effective_chat.id
    msg_id = context.user_data.get("ui_message_id")

    markup = None
    if keyboard:
        markup = InlineKeyboardMarkup(keyboard)

    try:

        if msg_id:

            await context.bot.edit_message_text(
                chat_id=chat_id,
                message_id=msg_id,
                text=text,
                reply_markup=markup
            )

            return

    except:
        pass

    if update.message:
        msg = await update.message.reply_text(text, reply_markup=markup)
    else:
        msg = await update.callback_query.message.reply_text(
            text,
            reply_markup=markup
        )

    context.user_data["ui_message_id"] = msg.message_id