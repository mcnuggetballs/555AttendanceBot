from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    ContextTypes,
    filters
)

from database import init_db
from state_engine import handle_text, handle_callback, handle_location
from screens.main_menu import show_menu
from screens.live import start_live
from screens import status


BOT_TOKEN = "8495877260:AAEKSGfSn9_imFhEFTdSdNtit_XY18OGoDA"


async def start(update, context: ContextTypes.DEFAULT_TYPE):

    context.user_data.clear()

    await show_menu(update, context)


def main():

    init_db()

    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("live", start_live))
    app.add_handler(CommandHandler("status", status.show_status))

    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))
    app.add_handler(MessageHandler(filters.LOCATION, handle_location))

    app.add_handler(CallbackQueryHandler(handle_callback))

    print("Bot running...")

    app.run_polling()


if __name__ == "__main__":
    main()