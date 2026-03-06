from screens import main_menu, onboarding, live, late
from database import get_connection


async def handle_text(update, context):

    screen = context.user_data.get("screen")

    if screen == "onboarding_name":
        await onboarding.save_name(update, context)

    elif screen == "onboarding_dob":
        await onboarding.save_dob(update, context)

    elif screen == "onboarding_notes":
        await onboarding.save_notes(update, context)

    elif screen == "onboarding_class_code":
        await onboarding.save_class_code(update, context)

    elif screen == "onboarding_venue":
        await onboarding.save_venue_name(update, context)

    elif screen == "late_eta":
        await late.save_eta(update, context)


async def handle_location(update, context):

    screen = context.user_data.get("screen")

    if screen == "onboarding_class_code":
        await onboarding.save_venue_location(update, context)

    elif screen == "live_location":
        await live.save_live_location(update, context)


async def handle_callback(update, context):

    query = update.callback_query
    data = query.data

    await query.answer()


    # MENU
    if data == "menu":

        context.user_data["screen"] = "menu"
        await main_menu.show_menu(update, context)
        return


    # LIVE BUTTON
    if data == "menu_live":

        context.user_data["screen"] = "live_role"
        await live.start_live(update, context)
        return


    # LATE BUTTON
    if data == "menu_late":

        context.user_data["screen"] = "late_role"
        await late.start_late(update, context)
        return


    # STATUS BUTTON
    if data == "menu_status":

        from screens import status
        await status.show_status(update, context)
        return


    # BACK BUTTON
    if data == "back":

        screen = context.user_data.get("screen")


        # LIVE NAVIGATION
        if screen == "live_location":

            context.user_data["screen"] = "live_class"
            await live.show_class_screen(update, context)
            return

        if screen == "live_class":

            context.user_data["screen"] = "live_role"
            await live.start_live(update, context)
            return


        # LATE NAVIGATION
        if screen == "late_eta":

            context.user_data["screen"] = "late_class"
            await late.show_class_screen(update, context)
            return

        if screen == "late_class":

            context.user_data["screen"] = "late_role"
            await late.start_late(update, context)
            return


        if screen == "late_role":

            context.user_data["screen"] = "menu"
            await main_menu.show_menu(update, context)
            return


        if screen == "live_role":

            context.user_data["screen"] = "menu"
            await main_menu.show_menu(update, context)
            return


    # CREATE ACCOUNT
    if data == "create_account":

        user_id = update.effective_user.id

        conn = get_connection()
        c = conn.cursor()

        c.execute(
            "SELECT telegram_user_id FROM users WHERE telegram_user_id=?",
            (user_id,)
        )

        exists = c.fetchone()

        conn.close()

        if exists:

            await query.message.reply_text(
                "You already have an account.\nUse /status to view your classes."
            )

            return

        context.user_data["screen"] = "onboarding_name"
        await onboarding.ask_name(update, context)
        return


    # ONBOARDING ROLE BUTTONS
    if data.startswith("role_toggle"):
        await onboarding.toggle_role(update, context)
        return


    if data == "role_done":

        context.user_data["screen"] = "onboarding_notes"
        await onboarding.ask_notes(update, context)
        return


    if data == "add_class_yes":

        context.user_data["screen"] = "onboarding_class_code"
        await onboarding.ask_class_code(update, context)
        return


    if data == "add_class_no":

        next_screen = await onboarding.finish_onboarding(update, context)
        context.user_data["screen"] = next_screen
        return


    # LIVE ROLE
    if data.startswith("live_role|"):

        context.user_data["screen"] = "live_class"
        await live.select_class(update, context)
        return


    # LIVE CLASS
    if data.startswith("live_class|"):

        context.user_data["screen"] = "live_location"
        await live.request_location(update, context)
        return


    # LATE ROLE
    if data.startswith("late_role|"):

        context.user_data["screen"] = "late_class"
        await late.select_class(update, context)
        return


    # LATE CLASS
    if data.startswith("late_class|"):

        context.user_data["screen"] = "late_eta"
        await late.request_eta(update, context)
        return