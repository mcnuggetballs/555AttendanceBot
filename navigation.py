def push(context, screen):

    stack = context.user_data.setdefault("nav_stack", [])

    stack.append(screen)

    context.user_data["screen"] = screen


def back(context):

    stack = context.user_data.get("nav_stack", [])

    if len(stack) <= 1:
        return None

    stack.pop()

    prev = stack[-1]

    context.user_data["screen"] = prev

    return prev


def reset(context):

    context.user_data["nav_stack"] = []
    context.user_data["screen"] = None