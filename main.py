from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    ContextTypes,
    ConversationHandler,
    filters
)

import sqlite3

from handlers.onboarding import (
    start_onboarding,
    get_name,
    get_dob,
    onboarding_select_role,
    get_notes,
    get_class_code,
    save_venue,
    more_codes,
    NAME,
    DOB,
    ROLE_SELECT,
    NOTES,
    CLASS_CODE,
    VENUE,
    MORE_CODES
)

from handlers.live_reporting import (
    start_live,
    live_select_role,
    select_class,
    receive_location,
    LIVE_ROLE_SELECT,
    CLASS_SELECT,
    LOCATION
)

from handlers.late_reporting import (
    start_late,
    late_select_role,
    late_select_class,
    receive_eta,
    LATE_ROLE_SELECT,
    LATE_CLASS_SELECT,
    ETA_INPUT
)

from handlers.admin_commands import today, who
from handlers.status import status
from database import init_db

ROLE_TOPICS = {
    "Internal Instructor": 35,
    "External Instructor": 36,
    "Private Instructor": 37,
    "Admin": 38,
    "Student Mentor": 39,
    "AEP Performer": 40
}

ADMIN_CHAT_ID = -1003584358970
BOT_TOKEN = "8495877260:AAEKSGfSn9_imFhEFTdSdNtit_XY18OGoDA"
PASSCODE = "wearerising555!"

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):

    user_id = update.effective_user.id

    conn = sqlite3.connect("attendance.db")
    c = conn.cursor()

    c.execute(
        "SELECT is_verified FROM users WHERE telegram_user_id=?",
        (user_id,)
    )

    result = c.fetchone()

    if result and result[0] == 1:

        await update.message.reply_text(
            "Welcome back! ✅\n\nUse /create_account if you haven't created your profile."
        )

    else:

        await update.message.reply_text(
            "This bot is only for 555Beatbox employees.\n\nEnter passcode to continue:"
        )

        context.user_data["awaiting_passcode"] = True

    conn.close()


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):

    if context.user_data.get("awaiting_passcode"):

        if update.message.text == PASSCODE:

            user_id = update.effective_user.id

            conn = sqlite3.connect("attendance.db")
            c = conn.cursor()

            c.execute("""
            INSERT OR REPLACE INTO users
            (telegram_user_id, is_verified)
            VALUES (?,1)
            """, (user_id,))

            conn.commit()
            conn.close()

            context.user_data["awaiting_passcode"] = False

            await update.message.reply_text(
                "Passcode verified ✅\n\nNow create your account using:\n/create_account"
            )

        else:

            await update.message.reply_text(
                "❌ Incorrect passcode.\nPlease try again."
            )


def main():

    init_db()

    onboarding_handler = ConversationHandler(

        entry_points=[
            CommandHandler("create_account", start_onboarding)
        ],

        states={

            NAME: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, get_name)
            ],

            DOB: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, get_dob)
            ],

            ROLE_SELECT: [
                CallbackQueryHandler(onboarding_select_role)
            ],

            NOTES: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, get_notes)
            ],

            CLASS_CODE: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, get_class_code)
            ],

            VENUE: [
                MessageHandler(filters.LOCATION, save_venue)
            ],

            MORE_CODES: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, more_codes)
            ],
        },

        fallbacks=[]
    )

    live_handler = ConversationHandler(

        entry_points=[
            CommandHandler("live", start_live)
        ],

        states={

            LIVE_ROLE_SELECT: [
                CallbackQueryHandler(live_select_role)
            ],

            CLASS_SELECT: [
                CallbackQueryHandler(select_class)
            ],

            LOCATION: [
                MessageHandler(filters.LOCATION, receive_location)
            ],
        },

        fallbacks=[]
    )
    
    late_handler = ConversationHandler(

        entry_points=[
            CommandHandler("late", start_late)
        ],

        states={

            LATE_ROLE_SELECT: [
                CallbackQueryHandler(late_select_role)
            ],

            LATE_CLASS_SELECT: [
                CallbackQueryHandler(late_select_class)
            ],

            ETA_INPUT: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, receive_eta)
            ],
        },

        fallbacks=[]
    )

    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.bot_data["ADMIN_CHAT_ID"] = ADMIN_CHAT_ID
    app.bot_data["ROLE_TOPICS"] = ROLE_TOPICS

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("status", status))
    app.add_handler(onboarding_handler)
    app.add_handler(live_handler)
    app.add_handler(late_handler)
    app.add_handler(CommandHandler("today", today))
    app.add_handler(CommandHandler("who", who))
    app.add_handler(
        MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message)
    )

    print("Bot running...")

    app.run_polling()


if __name__ == "__main__":
    main()