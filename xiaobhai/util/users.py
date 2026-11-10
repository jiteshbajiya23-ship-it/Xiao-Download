import logging
import time

from Script import LINE
from database.users_chats_db import db
from xiaobhai.util.access import is_admin
from xiaobhai.util.logger import log_event, user_line, now_ist

_SAVED: dict = {}        # user_id -> last time we wrote this user to MongoDB
SAVE_EVERY = 600         # a known user is refreshed at most once per 10 minutes (saves DB calls)


async def track_user(user, started: bool, note: str = "") -> bool:
    """Save / update the user and log to the storage channel. Returns True if the user is new.
    DB or log problems never stop the bot."""
    now = time.time()
    if not started and now - _SAVED.get(user.id, 0) < SAVE_EVERY:
        return False                      # seen very recently: nothing to save, nothing to log

    is_new = False
    total = "?"
    try:
        is_new = await db.upsert_user(user.id, user.first_name, user.username)   # 1 round trip
        if is_new or started:
            total = await db.total_users_count()                                  # only needed for the log
        _SAVED[user.id] = now
        if len(_SAVED) > 5000:
            _SAVED.clear()
    except Exception:
        logging.exception("track_user: DB error (user not saved)")

    if is_new:
        title = "🆕 <b>New user joined</b>"
    elif started:
        title = "▶️ <b>Bot started</b>"
    else:
        return is_new
    role = "👑 Admin" if is_admin(user.id) else ("🆕 New user" if is_new else "🔁 Returning user")
    extra = f"\n{note}" if note else ""
    await log_event(f"{title}\n{LINE}\n{user_line(user)}\n{LINE}\n"
                    f"🏷 {role}\n👥 Total users: <code>{total}</code>{extra}\n🕒 <i>{now_ist()}</i>")
    return is_new
