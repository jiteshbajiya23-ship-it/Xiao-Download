"""Everything that happens is logged to the STORAGE channel (same place the files live)."""
import html
import logging
import time

from pyrogram import enums

from info import LOG_CHANNEL
from utils import temp


def now_ist() -> str:
    return time.strftime("%d %b %Y, %I:%M:%S %p", time.gmtime(time.time() + 19800)) + " IST"


def user_line(user) -> str:
    uname = f"@{user.username}" if getattr(user, "username", None) else "no username"
    return f"👤 {user.mention(style=enums.ParseMode.HTML)}\n🔖 {html.escape(uname)}\n🆔 <code>{user.id}</code>"


async def log_event(text: str, reply_markup=None) -> None:
    """Never raises."""
    try:
        if temp.BOT is None:
            return
        await temp.BOT.send_message(LOG_CHANNEL, text, parse_mode=enums.ParseMode.HTML,
                                    disable_web_page_preview=True, reply_markup=reply_markup)
    except Exception as e:
        logging.warning(f"Could not write to storage channel: {e}")
