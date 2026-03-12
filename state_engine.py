from screens import main_menu, onboarding, live, late, status, manage_classes, edit_profile
from database import get_connection
from admin_commands import today, who, who_class


def log(msg):
    print("[ENGINE]", msg)


async def handle_text(update, context):

    log("TEXT EVENT")

    if not context.user_data.get("verified"):
        log("User not verified")
        return

    try:
        await update.message.delete()
    except:
        pass

    screen = context.user_data.get("screen")

    # ---------------------
    # EDIT PROFILE INPUT
    # ---------------------

    if screen == "edit_name_input":
        await edit_profile.save_name(update, context)
        return

    if screen == "edit_dob_input":
        await edit_profile.save_dob(update, context)
        return

    if screen == "edit_notes_input":
        await edit_profile.save_notes(update, context)
        return

    # ---------------------
    # LIVE STUDENT NAME
    # ---------------------

    if screen == "live_student_name":
        context.user_data["student_name"] = update.message.text
        context.user_data["screen"] = "live_location"
        await live.request_location(update, context)
        return

    # ---------------------
    # LATE STUDENT NAME
    # ---------------------

    if screen == "late_student_name":
        context.user_data["student_name"] = update.message.text
        context.user_data["screen"] = "late_eta"
        await late.request_eta(update, context)
        return

    # ---------------------
    # MANAGE CLASS CODE
    # ---------------------

    if screen == "manage_add_class_code":

        context.user_data["manage_class_code"] = update.message.text.strip()
        context.user_data["screen"] = "manage_location"

        await manage_classes.ask_location(update, context)
        return

    if screen == "manage_venue":

        await manage_classes.save_new_class(update, context)
        return

    button_only_screens = [
        "onboarding_role",
        "onboarding_add_class",
        "live_role",
        "live_class",
        "late_role",
        "late_class",
        "menu",
        "live_admin_hours",
        "manage_classes",
        "manage_role_select",
        "manage_delete_role",
        "manage_delete_class",
        "edit_profile_menu",
        "edit_roles_menu",
        "add_role_menu",
        "remove_role_menu"
    ]

    if screen in button_only_screens:
        return

    log(f"Current screen: {screen}")

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

    elif screen == "late_eta":
        await late.save_eta(update, context)
        return

    else:
        return

    if not next_screen:
        return

    context.user_data["screen"] = next_screen

    if next_screen == "onboarding_dob":
        await onboarding.ask_dob(update, context)

    elif next_screen == "onboarding_role":
        await onboarding.ask_roles(update, context)

    elif next_screen == "onboarding_notes":
        await onboarding.ask_notes(update, context)

    elif next_screen == "onboarding_config_role":
        await onboarding.ask_config_role(update, context)

    elif next_screen == "onboarding_class_code":
        await onboarding.ask_class_code(update, context)

    elif next_screen == "onboarding_venue":
        await onboarding.ask_venue_name(update, context)

    elif next_screen == "menu":
        context.user_data["screen"] = "menu"
        await main_menu.show_menu(update, context)


async def handle_location(update, context):

    log("LOCATION EVENT")

    if not context.user_data.get("verified"):
        return

    try:
        await update.message.delete()
    except:
        pass

    screen = context.user_data.get("screen")

    if screen == "onboarding_location":

        next_screen = await onboarding.save_venue_location(update, context)
        context.user_data["screen"] = next_screen

        if next_screen == "onboarding_venue":
            await onboarding.ask_venue_name(update, context)

        return

    if screen == "live_location":
        await live.save_live_location(update, context)
        return

    if screen == "manage_location":

        location = update.message.location

        context.user_data["venue_lat"] = location.latitude
        context.user_data["venue_lng"] = location.longitude

        context.user_data["screen"] = "manage_venue"

        await manage_classes.ask_venue_name(update, context)
        return


async def handle_callback(update, context):

    log("CALLBACK EVENT")

    if not context.user_data.get("verified"):
        return

    query = update.callback_query
    data = query.data

    await query.answer()

    screen = context.user_data.get("screen")

    if data == "menu":
        context.user_data["screen"] = "menu"
        await main_menu.show_menu(update, context)
        return

    if data == "menu_today":
        await today(update, context)
        return

    if data == "menu_who":
        await who(update, context)
        return

    if data.startswith("who_class|"):
        await who_class(update, context)
        return

    if data == "menu_manage_classes":
        await manage_classes.start(update, context)
        return

    # -------------------------
    # EDIT PROFILE
    # -------------------------

    if data == "menu_edit_profile":
        context.user_data["screen"] = "edit_profile_menu"
        await edit_profile.show_profile(update, context)
        return

    if data == "edit_name":
        context.user_data["screen"] = "edit_name_input"
        await edit_profile.ask_name(update, context)
        return

    if data == "edit_dob":
        context.user_data["screen"] = "edit_dob_input"
        await edit_profile.ask_dob(update, context)
        return

    if data == "edit_notes":
        context.user_data["screen"] = "edit_notes_input"
        await edit_profile.ask_notes(update, context)
        return

    # -------------------------
    # EDIT ROLES / CLASSES
    # -------------------------

    if data == "edit_roles":
        context.user_data["screen"] = "edit_roles_menu"
        await edit_profile.edit_roles_menu(update, context)
        return

    if data == "add_role":
        context.user_data["screen"] = "add_role_menu"
        await edit_profile.add_role_menu(update, context)
        return

    if data.startswith("add_role_confirm|"):
        await edit_profile.add_role(update, context)
        return

    if data == "remove_role":
        context.user_data["screen"] = "remove_role_menu"
        await edit_profile.remove_role_menu(update, context)
        return

    if data.startswith("remove_role_confirm|"):
        await edit_profile.remove_role(update, context)
        return

    # -------------------------
    # MANAGE CLASSES FLOW
    # -------------------------

    if data == "manage_add_class":
        context.user_data["screen"] = "manage_role_select"
        await manage_classes.select_role(update, context)
        return

    if data == "manage_delete_class":
        context.user_data["screen"] = "manage_delete_role"
        await manage_classes.select_role_delete(update, context)
        return

    if data.startswith("manage_role|"):
        context.user_data["screen"] = "manage_add_class_code"
        await manage_classes.ask_class_code(update, context)
        return

    if data.startswith("manage_delete_role|"):
        context.user_data["screen"] = "manage_delete_class"
        await manage_classes.select_class_delete(update, context)
        return

    if data.startswith("manage_delete_class|"):
        await manage_classes.delete_class(update, context)
        return

    # -------------------------

    if data == "create_account":

        user_id = update.effective_user.id

        conn = get_connection()
        c = conn.cursor()

        c.execute(
            "SELECT name FROM users WHERE telegram_user_id=?",
            (user_id,)
        )

        row = c.fetchone()

        conn.close()

        if row and row[0] is not None:
            return

        context.user_data["screen"] = "onboarding_name"
        await onboarding.ask_name(update, context)
        return

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

        next_screen = await onboarding.next_role(update, context)

        context.user_data["screen"] = next_screen

        if next_screen == "onboarding_config_role":
            await onboarding.ask_config_role(update, context)

        elif next_screen == "menu":
            context.user_data["screen"] = "menu"
            await main_menu.show_menu(update, context)

        return

    if data == "back":

        if screen.startswith("manage"):
            context.user_data["screen"] = "manage_classes"
            await manage_classes.start(update, context)
            return

        if screen.startswith("edit"):
            context.user_data["screen"] = "edit_profile_menu"
            await edit_profile.show_profile(update, context)
            return

        if screen == "onboarding_dob":
            context.user_data["screen"] = "onboarding_name"
            await onboarding.ask_name(update, context)
            return

        if screen == "onboarding_role":
            context.user_data["screen"] = "onboarding_dob"
            await onboarding.ask_dob(update, context)
            return

        if screen == "onboarding_notes":
            context.user_data["screen"] = "onboarding_role"
            await onboarding.ask_roles(update, context)
            return

        if screen == "onboarding_class_code":
            context.user_data["screen"] = "onboarding_config_role"
            await onboarding.ask_config_role(update, context)
            return

        if screen == "onboarding_location":
            context.user_data["screen"] = "onboarding_class_code"
            await onboarding.ask_class_code(update, context)
            return

        if screen == "onboarding_venue":
            context.user_data["screen"] = "onboarding_location"
            await onboarding.ask_class_code(update, context)
            return

        if screen == "live_location":
            context.user_data["screen"] = "live_class"
            await live.start_live(update, context)
            return

        if screen == "live_class":
            context.user_data["screen"] = "live_role"
            await live.start_live(update, context)
            return

        if screen == "late_eta":
            context.user_data["screen"] = "late_class"
            await late.start_late(update, context)
            return

        if screen == "late_class":
            context.user_data["screen"] = "late_role"
            await late.start_late(update, context)
            return

    if data == "menu_live":
        context.user_data["screen"] = "live_role"
        await live.start_live(update, context)
        return

    if data == "menu_late":
        context.user_data["screen"] = "late_role"
        await late.start_late(update, context)
        return

    if data == "menu_status":
        await status.show_status(update, context)
        return

    if data.startswith("live_role|"):
        context.user_data["screen"] = "live_class"
        await live.select_class(update, context)
        return

    if data.startswith("live_class|"):

        role = context.user_data.get("live_role")

        if role == "Private Instructor":
            context.user_data["screen"] = "live_student_name"

            cls = data.split("|")[1]
            context.user_data["live_class"] = cls

            await live.ask_student_name(update, context)
            return

        if role == "Admin":
            context.user_data["screen"] = "live_admin_hours"

            cls = data.split("|")[1]
            context.user_data["live_class"] = cls

            await live.ask_admin_hours(update, context)
            return

        context.user_data["screen"] = "live_location"
        await live.request_location(update, context)
        return

    if data.startswith("admin_hours|"):

        hours = int(data.split("|")[1])
        context.user_data["admin_hours"] = hours

        context.user_data["screen"] = "live_location"
        await live.request_location(update, context)
        return

    if data.startswith("late_role|"):
        context.user_data["screen"] = "late_class"
        await late.select_class(update, context)
        return

    if data.startswith("late_class|"):

        role = context.user_data.get("late_role")

        if role == "Private Instructor":
            context.user_data["screen"] = "late_student_name"

            cls = data.split("|")[1]
            context.user_data["late_class"] = cls

            await late.ask_student_name(update, context)
            return

        context.user_data["screen"] = "late_eta"
        await late.request_eta(update, context)
        return