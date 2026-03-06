from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    filters
)

from database import init_db, get_connection
from state_engine import handle_text, handle_callback, handle_location
from screens import main_menu
from ui import show_screen


BOT_TOKEN = "8495877260:AAEKSGfSn9_imFhEFTdSdNtit_XY18OGoDA"
BOT_PASSWORD = "wearerising555!"


async def start(update, context):

    user_id = update.effective_user.id

    conn = get_connection()
    c = conn.cursor()

    c.execute(
        "SELECT verified FROM users WHERE telegram_user_id=?",
        (user_id,)
    )

    row = c.fetchone()

    conn.close()

    if row and row[0] == 1:

        context.user_data["verified"] = True
        context.user_data["screen"] = "menu"

        await main_menu.show_menu(update, context)
        return

    context.user_data["screen"] = "password"

    await show_screen(
        update,
        context,
        "Enter access password:"
    )


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

        conn = get_connection()
        c = conn.cursor()

        c.execute(
            """
            INSERT INTO users (telegram_user_id, verified)
            VALUES (?,1)
            ON CONFLICT(telegram_user_id)
            DO UPDATE SET verified=1
            """,
            (user_id,)
        )

        conn.commit()
        conn.close()

        context.user_data["verified"] = True
        context.user_data["screen"] = "menu"

        await main_menu.show_menu(update, context)

        return

    # ---------- ALL OTHER TEXT ----------
    await handle_text(update, context)


def main():

    init_db()

    app = ApplicationBuilder().token(BOT_TOKEN).build()

    # COMMANDS
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("menu", menu))

    # BUTTON CALLBACKS
    app.add_handler(CallbackQueryHandler(handle_callback))

    # LOCATION
    app.add_handler(MessageHandler(filters.LOCATION, handle_location))

    # TEXT INPUT
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, text_router))

    print("Bot running...")

    app.run_polling()


if __name__ == "__main__":
    main()