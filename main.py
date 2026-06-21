from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    filters
)

from flask import Flask, request
from telegram import Update
import asyncio
import threading
import time

from state_engine import handle_text, handle_callback, handle_location
from screens import main_menu
from ui import show_screen
import os
from dotenv import load_dotenv
from firestore_users import get_user, save_user

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
BOT_PASSWORD = "wearerising555!"

flask_app = Flask(__name__)

telegram_app = None
bot_loop = None

async def start(update, context):

    total = time.time()

    print("START received", flush=True)

    t = time.time()
    user_id = update.effective_user.id
    user = get_user(user_id)
    print("get_user:", time.time() - t, flush=True)

    if user and user.get("verified") == 1:

        context.user_data["verified"] = True
        context.user_data["screen"] = "menu"

        t = time.time()
        await main_menu.show_menu(update, context)
        print("show_menu:", time.time() - t, flush=True)

        print("TOTAL:", time.time() - total, flush=True)
        return

    context.user_data["screen"] = "password"

    t = time.time()
    await show_screen(
        update,
        context,
        "Enter access password:"
    )
    print("show_screen:", time.time() - t, flush=True)

    print("TOTAL:", time.time() - total, flush=True)


async def menu(update, context):

    if not context.user_data.get("verified"):
        return

    context.user_data["screen"] = "menu"

    await main_menu.show_menu(update, context)


async def text_router(update, context):

    screen = context.user_data.get("screen")

    # ---------- PASSWORD SCREEN ----------
    if screen == "password":

        password = update.message.text

        # delete user message
        try:
            await update.message.delete()
        except:
            pass

        if password != BOT_PASSWORD:

            await show_screen(
                update,
                context,
                "Incorrect password. Try again."
            )
            return

        user_id = update.effective_user.id

        existing = get_user(user_id)

        save_user(
            user_id,
            existing.get("name") if existing else "",
            existing.get("dob") if existing else "",
            existing.get("notes") if existing else "",
            1
        )

        context.user_data["verified"] = True
        context.user_data["screen"] = "menu"

        await main_menu.show_menu(update, context)

        return

    # ---------- ALL OTHER TEXT ----------
    await handle_text(update, context)


def build_bot():

    global telegram_app

    telegram_app = ApplicationBuilder().token(BOT_TOKEN).build()

    telegram_app.add_handler(CommandHandler("start", start))
    telegram_app.add_handler(CommandHandler("menu", menu))

    telegram_app.add_handler(
        CallbackQueryHandler(handle_callback)
    )

    telegram_app.add_handler(
        MessageHandler(filters.LOCATION, handle_location)
    )

    telegram_app.add_handler(
        MessageHandler(
            filters.TEXT & ~filters.COMMAND,
            text_router
        )
    )

    return telegram_app

@flask_app.route("/")
def health():
    return "Attendance Bot Running", 200


@flask_app.route("/webhook", methods=["POST"])
def webhook():

    print("WEBHOOK RECEIVED", time.time(), flush=True)

    data = request.get_json(force=True)

    update = Update.de_json(
        data,
        telegram_app.bot
    )

    asyncio.run_coroutine_threadsafe(
        telegram_app.process_update(update),
        bot_loop
    )

    print("UPDATE QUEUED", flush=True)

    return "OK", 200

if __name__ == "__main__":

    build_bot()

    bot_loop = asyncio.new_event_loop()

    def run_loop():
        asyncio.set_event_loop(bot_loop)

        bot_loop.run_until_complete(
            telegram_app.initialize()
        )

        bot_loop.run_until_complete(
            telegram_app.start()
        )

        bot_loop.run_forever()

    threading.Thread(
        target=run_loop,
        daemon=True
    ).start()

    flask_app.run(
        host="0.0.0.0",
        port=int(os.environ.get("PORT", 8080))
    )