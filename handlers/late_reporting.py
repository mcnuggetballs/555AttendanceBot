from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup
)

from telegram.ext import ContextTypes, ConversationHandler

import sqlite3

from utils.sheets_logger import log_attendance

LATE_ROLE_SELECT, LATE_CLASS_SELECT, ETA_INPUT = range(3)


async def start_late(update: Update, context: ContextTypes.DEFAULT_TYPE):

    user_id = update.effective_user.id

    conn = sqlite3.connect("attendance.db")
    c = conn.cursor()

    c.execute("""
    SELECT role_name FROM user_roles
    WHERE telegram_user_id=?
    """, (user_id,))

    roles = c.fetchall()
    conn.close()

    keyboard = []

    for role in roles:

        keyboard.append([
            InlineKeyboardButton(role[0], callback_data=f"role|{role[0]}")
        ])

    await update.message.reply_text(
        "Select role:",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

    return LATE_ROLE_SELECT


async def late_select_role(update: Update, context: ContextTypes.DEFAULT_TYPE):

    query = update.callback_query
    await query.answer()

    role = query.data.split("|")[1]

    context.user_data["late_role"] = role

    user_id = query.from_user.id

    conn = sqlite3.connect("attendance.db")
    c = conn.cursor()

    c.execute("""
    SELECT id FROM user_roles
    WHERE telegram_user_id=? AND role_name=?
    """, (user_id, role))

    role_id = c.fetchone()[0]

    c.execute("""
    SELECT class_code FROM class_codes
    WHERE user_role_id=?
    """, (role_id,))

    classes = c.fetchall()
    conn.close()

    keyboard = []

    for code in classes:

        keyboard.append([
            InlineKeyboardButton(code[0], callback_data=f"class|{code[0]}")
        ])

    await query.edit_message_text(
        "Select class:",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

    return LATE_CLASS_SELECT


async def late_select_class(update: Update, context: ContextTypes.DEFAULT_TYPE):

    query = update.callback_query
    await query.answer()

    class_code = query.data.split("|")[1]

    context.user_data["late_class"] = class_code

    await query.edit_message_text(
        "Enter ETA (HHMM)"
    )

    return ETA_INPUT


async def receive_eta(update: Update, context: ContextTypes.DEFAULT_TYPE):

    eta = update.message.text

    role = context.user_data["late_role"]
    class_code = context.user_data["late_class"]

    user_id = update.effective_user.id
    name = update.effective_user.first_name

    conn = sqlite3.connect("attendance.db")
    c = conn.cursor()

    # --------------------------------------------------
    # Prevent late report AFTER attendance submission
    # --------------------------------------------------

    c.execute("""
    SELECT id FROM attendance_logs
    WHERE telegram_user_id=?
    AND class_code=?
    AND status='Present'
    AND date(timestamp)=date('now')
    """, (user_id, class_code))

    already_attended = c.fetchone()

    if already_attended:

        conn.close()

        await update.message.reply_text(
            "Attendance already submitted. Late report not allowed."
        )

        return ConversationHandler.END

    # --------------------------------------------------
    # Duplicate late report protection
    # --------------------------------------------------

    c.execute("""
    SELECT id FROM attendance_logs
    WHERE telegram_user_id=?
    AND class_code=?
    AND status='LATE'
    AND date(timestamp)=date('now')
    """, (user_id, class_code))

    existing = c.fetchone()

    if existing:

        conn.close()

        await update.message.reply_text(
            "Late report already submitted for this class today."
        )

        return ConversationHandler.END

    # --------------------------------------------------
    # Insert late record
    # --------------------------------------------------

    c.execute("""
    INSERT INTO attendance_logs
    (telegram_user_id, role_name, class_code, distance, status)
    VALUES (?,?,?,?,?)
    """, (user_id, role, class_code, 0, "LATE"))

    conn.commit()
    conn.close()
    
    log_attendance(name, role, class_code, 0, "LATE")

    # --------------------------------------------------
    # Send message to correct topic
    # --------------------------------------------------

    message = (
        "⚠️ LATE REPORT\n\n"
        f"Name: {name}\n"
        f"Role: {role}\n"
        f"Class: {class_code}\n"
        f"ETA: {eta}"
    )

    topic_map = context.bot_data["ROLE_TOPICS"]

    thread_id = topic_map.get(role)

    await context.bot.send_message(
        chat_id=context.bot_data["ADMIN_CHAT_ID"],
        message_thread_id=thread_id,
        text=message
    )

    await update.message.reply_text(
        "Late report submitted."
    )

    return ConversationHandler.END