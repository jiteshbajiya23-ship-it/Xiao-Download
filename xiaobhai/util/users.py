import logging

from Script import LINE
from database.users_chats_db import db
from xiaobhai.util.access import is_admin
from xiaobhai.util.logger import log_event, user_line, now_ist


async def track_user(user, started: bool, note: str = "") -> bool:
    """Save / update the user and log to the storage channel. Returns True if the user is new.
    DB or log problems never stop the bot."""
    is_new = False
    total = "?"
    try:
        is_new = not await db.is_user_exist(user.id)
        if is_new:
            await db.add_user(user.id, user.first_name, user.username)
        else:
            await db.touch_user(user.id, user.first_name, user.username)
        total = await db.total_users_count()
    except Exception:
        logging.exception("track_user: DB error (user not saved)")
    role = "👑 Admin" if is_admin(user.id) else ("🆕 New user" if is_new else "🔁 Returning user")
    if is_new:
        title = "🆕 <b>New user joined</b>"
    elif started:
        title = "▶️ <b>Bot started</b>"
    else:
        return is_new
    extra = f"\n{note}" if note else ""
    await log_event(f"{title}\n{LINE}\n{user_line(user)}\n{LINE}\n"
                    f"🏷 {role}\n👥 Total users: <code>{total}</code>{extra}\n🕒 <i>{now_ist()}</i>")
    return is_new
