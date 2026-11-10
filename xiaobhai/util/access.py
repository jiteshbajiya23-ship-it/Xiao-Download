"""Runtime access state: admins, bans, live rate limit, extra force-sub channels, filters and command menus.
Everything here can be changed by the owner from inside the bot (no redeploy needed)."""
import logging

from pyrogram import filters
from pyrogram.types import BotCommand, BotCommandScopeChat, BotCommandScopeDefault

from info import ADMINS, OWNER_ID, RATE_LIMIT_SECONDS, FORCE_SUB_CHANNELS, id_pattern
from database.users_chats_db import db

ADMIN_IDS: set = set(ADMINS) | ({OWNER_ID} if OWNER_ID else set())
BANNED: set = set()
EXTRA_FSUB: list = []            # force-sub channels added with /addfsub (saved in MongoDB)
FSUB_OK_UNTIL: dict = {}         # user_id -> verified until (cache, cleared when channels change)
FSUB_LINKS: dict = {}            # channel -> (title, link)


class state:
    rate = RATE_LIMIT_SECONDS    # changed live with /setlimit


def is_admin(uid) -> bool:
    return uid in ADMIN_IDS


def is_owner(uid) -> bool:
    return bool(OWNER_ID) and uid == OWNER_ID


async def _admin(_, __, update):
    u = getattr(update, "from_user", None)
    return bool(u and u.id in ADMIN_IDS)


async def _owner(_, __, update):
    u = getattr(update, "from_user", None)
    return bool(u and is_owner(u.id))


async def _banned(_, __, update):
    u = getattr(update, "from_user", None)
    return bool(u and u.id in BANNED and u.id not in ADMIN_IDS)


ADMIN_F = filters.create(_admin)     # owner + admins
OWNER_F = filters.create(_owner)
BANNED_F = filters.create(_banned)


def parse_channel(text: str):
    """'@name', 't.me/name', 'https://t.me/name' or '-100123' -> int id or username (no @)."""
    t = (text or "").strip()
    for prefix in ("https://t.me/", "http://t.me/", "t.me/"):
        if t.startswith(prefix):
            t = t[len(prefix):]
    t = t.strip("/").lstrip("@")
    if not t:
        return None
    return int(t) if id_pattern.search(t) else t


def fsub_channels() -> list:
    """Env channels + channels added from the bot, without duplicates."""
    seen, out = set(), []
    for ch in list(FORCE_SUB_CHANNELS) + list(EXTRA_FSUB):
        key = str(ch).lower()
        if key not in seen:
            seen.add(key)
            out.append(ch)
    return out


def clear_fsub_cache():
    FSUB_OK_UNTIL.clear()
    FSUB_LINKS.clear()


async def load_runtime():
    """Load admins / bans / rate / extra force-sub from MongoDB (called at startup)."""
    try:
        for a in await db.get_setting("admins", []) or []:
            ADMIN_IDS.add(int(a))
        for b in await db.get_bans():
            BANNED.add(int(b["_id"]))
        rate = await db.get_setting("rate")
        if rate is not None:
            state.rate = int(rate)
        EXTRA_FSUB[:] = [c for c in (await db.get_setting("fsub", []) or [])]
    except Exception:
        logging.exception("Could not load runtime settings from MongoDB")


# ---- command menus -------------------------------------------------------------------------
# Everyone sees USER_CMDS. Moderator commands carry a "Moderator" tag and owner commands an "Owner" tag.
# Only admins / the owner get the extra rows (per-chat menu); normal users never see them.
USER_CMDS = [("start", "Start the bot"), ("id", "Show your Telegram ID"), ("help", "How to use the bot")]
_MOD = [
    ("status", "Bot status"), ("health", "Health check"), ("ping", "Bot speed"), ("errors", "Recent errors"),
    ("users", "User stats"), ("userinfo", "Info about a user"), ("resetlimit", "Reset a user's link limit"),
    ("ban", "Ban a user"), ("unban", "Unban a user"), ("banlist", "Banned users"),
    ("revoke", "Disable a download link"), ("broadcast", "Message all users"), ("setstart", "Change start image"),
]
_OWNER = [
    ("addadmin", "Add an admin"), ("deladmin", "Remove an admin"), ("admins", "List admins"),
    ("setlimit", "Change link limit (seconds)"), ("addfsub", "Add force-sub channel"),
    ("delfsub", "Remove force-sub channel"), ("fsublist", "List force-sub channels"), ("restart", "Restart / redeploy"),
]
ADMIN_CMDS = USER_CMDS + [(c, f"Moderator · {d}") for c, d in _MOD]
OWNER_CMDS = ADMIN_CMDS + [(c, f"Owner · {d}") for c, d in _OWNER]

MOD_ONLY_COMMANDS = [c for c, _ in _MOD]        # admins + owner
OWNER_ONLY_COMMANDS = [c for c, _ in _OWNER]    # owner only


async def apply_commands(client, only_user: int = None):
    """Per-admin command menus (override the BotFather menu only for admins/owner)."""
    try:
        if not only_user:
            # default menu (normal users) = public commands only, so no moderator / owner command is ever listed
            try:
                await client.set_bot_commands([BotCommand(c, d) for c, d in USER_CMDS], scope=BotCommandScopeDefault())
            except Exception:
                logging.warning("Could not set the default command menu", exc_info=True)
        targets = [only_user] if only_user else list(ADMIN_IDS)
        for uid in targets:
            cmds = OWNER_CMDS if is_owner(uid) else ADMIN_CMDS
            try:
                await client.set_bot_commands([BotCommand(c, d) for c, d in cmds], scope=BotCommandScopeChat(chat_id=uid))
            except Exception:
                pass       # admin has not started the bot yet
    except Exception:
        logging.warning("Could not set bot commands", exc_info=True)
