import asyncio
import collections
import logging
import time

from pyrogram.errors import FloodWait
from shortzy import Shortzy

from info import SHORTLINK_URL, SHORTLINK_API


class temp(object):
    ME = None
    BOT = None
    U_NAME = None
    B_NAME = None
    START_FILE_ID = None                    # cached Telegram file_id of the start image
    START_TIME = time.time()
    ERRORS = collections.deque(maxlen=15)   # (timestamp, title, reason)
    ERROR_COUNT = 0
    LINKS = 0                               # links made since the last restart
    LIMITED = 0                             # requests refused by the 2-minute rule


async def get_shortlink(link):
    """Shorten a link. If the shortener fails, return the original so the bot never breaks."""
    try:
        shortzy = Shortzy(api_key=SHORTLINK_API, base_site=SHORTLINK_URL)
        return await shortzy.convert(link)
    except Exception as e:
        logging.warning(f"Shortlink failed, using original link: {e}")
        return link


async def retry_async(func, *args, attempts: int = 3, base_delay: float = 2.0, **kwargs):
    """Run an async function with retries. FloodWait is waited out properly."""
    last = None
    for i in range(1, attempts + 1):
        try:
            return await func(*args, **kwargs)
        except FloodWait as e:
            last = e
            wait = getattr(e, "value", None) or getattr(e, "x", 5)
            await asyncio.sleep(min(int(wait) + 1, 60))
        except Exception as e:
            last = e
            if i == attempts:
                break
            await asyncio.sleep(base_delay * i)
    raise last


def bar(fraction: float, width: int = 10) -> str:
    fraction = max(0.0, min(1.0, fraction or 0.0))
    filled = int(round(fraction * width))
    return "▰" * filled + "▱" * (width - filled)


def fmt_uptime(seconds: float) -> str:
    seconds = int(seconds)
    d, r = divmod(seconds, 86400)
    h, r = divmod(r, 3600)
    m, s = divmod(r, 60)
    if d:
        return f"{d}d {h}h {m}m"
    if h:
        return f"{h}h {m}m"
    return f"{m}m {s}s"


def fmt_duration(seconds: int) -> str:
    """120 -> '2 min', 90 -> '1 min 30 sec', 45 -> '45 sec'"""
    seconds = int(seconds)
    m, s = divmod(seconds, 60)
    if m and s:
        return f"{m} min {s} sec"
    return f"{m} min" if m else f"{s} sec"
