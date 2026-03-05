from navigation import push, back, reset
from screens import main_menu, onboarding, live
from database import get_connection


SCREEN_MAP = {
    "menu": main_menu.show_menu,
    "onboarding_name": onboarding.ask_name,
    "onboarding_dob": onboarding.ask_dob,
    "onboarding_role": onboarding.ask_roles,
    "onboarding_notes": onboarding.ask_notes,
    "onboarding_config_role": onboarding.ask_config_role,
    "onboarding_class_code": onboarding.ask_class_code,
    "onboarding_venue": onboarding.ask_venue_name
}


async def navigate(update, context, screen):

    context.user_data["screen"] = screen
    push(context, screen)

    func = SCREEN_MAP.get(screen)

    if func:
        await func(update, context)


async def handle_text(update, context):

    screen = context.user_data.get("screen")

    next_screen = None

    if screen == "onboarding_name":
        next_screen = await onboarding.save_name(update, context)

    elif screen == "onboarding_dob":
        next_screen = await onboarding.save_dob(update, context)

    elif screen == "onboarding_notes":
        next_screen = await onboarding.save_notes(update, context)

    elif screen == "onboarding_class_code":
        next_screen = await onboarding.save_class_code(update, context)

    elif screen == "onboarding_venue":
        next_screen = await onboarding.save_venue_name(update, context)

    if next_screen:
        await navigate(update, context, next_screen)


async def handle_location(update, context):

    screen = context.user_data.get("screen")

    if screen == "onboarding_class_code":

        next_screen = await onboarding.save_venue_location(update, context)

        if next_screen:
            await navigate(update, context, next_screen)

    elif context.user_data.get("live_state") == "location":

        await live.save_live_location(update, context)


async def handle_callback(update, context):

    query = update.callback_query
    data = query.data

    await query.answer()


    # MENU
    if data == "menu":

        context.user_data.clear()
        await main_menu.show_menu(update, context)
        return


    # START LIVE
    if data == "menu_live":

        await live.start_live(update, context)
        return


    # BACK BUTTON
    if data == "back":

        state = context.user_data.get("live_state")

        if state == "location":

            context.user_data["live_state"] = "class"
            await live.show_class_screen(update, context)
            return

        if state == "class":

            context.user_data["live_state"] = "role"
            await live.start_live(update, context)
            return

        prev = back(context)

        if prev:
            func = SCREEN_MAP.get(prev)
            if func:
                await func(update, context)

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
                "You already have an account.\n\nUse /status to view your classes."
            )

            return

        reset(context)
        await navigate(update, context, "onboarding_name")
        return


    # ROLE TOGGLE
    if data.startswith("role_toggle"):

        await onboarding.toggle_role(update, context)
        return


    if data == "role_done":

        await navigate(update, context, "onboarding_notes")
        return


    if data == "add_class_yes":

        await navigate(update, context, "onboarding_class_code")
        return


    if data == "add_class_no":

        context.user_data["role_index"] += 1

        if context.user_data["role_index"] < len(context.user_data["roles"]):

            await navigate(update, context, "onboarding_config_role")

        else:

            next_screen = await onboarding.finish_onboarding(update, context)

            await navigate(update, context, next_screen)

        return


    # LIVE ROLE SELECT
    if data.startswith("live_role|"):

        await live.select_class(update, context)
        return


    # LIVE CLASS SELECT
    if data.startswith("live_class|"):

        await live.request_location(update, context)
        return