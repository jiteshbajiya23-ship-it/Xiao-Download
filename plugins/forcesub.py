"""Multi Force Subscribe gate (group -101) + Ban gate (group -102).

A normal user must be a member of ALL force-sub channels (env FORCE_SUB_CHANNELS + channels the owner
added with /addfsub). Otherwise they only see the join buttons (joined channels show a green tick).
Admins are never checked. If there are no channels the gate is off. The bot must be ADMIN in every
force-sub channel so it can read members.
"""
import asyncio
import logging
import time

from pyrogram import Client, filters, enums, StopPropagation
from pyrogram.errors import UserNotParticipant
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from info import FORCE_SUB_CHANNELS, FORCE_SUB_LINKS
from xiaobhai.util.access import (ADMIN_F, BANNED_F, fsub_channels, FSUB_OK_UNTIL as _ok_until,
                                  FSUB_LINKS as _link_cache)
from xiaobhai.util.alerts import send_alert
from xiaobhai.util.logger import log_event, user_line, now_ist
from xiaobhai.util.users import track_user

HTML = enums.ParseMode.HTML
CACHE_SECONDS = 120          # a verified user is not re-checked for 2 minutes
_ban_note: dict = {}

JOIN_TXT = (
    "🔒 <b>Join our channels first!</b>\n"
    "━━━━━━━━━━━━━━━━━━\n"
    "To use this bot, please join the <b>{n}</b> channel(s) below.\n"
    "Then tap <b>✅ I've Joined</b>.\n\n"
    "{status}"
)


# ------------------------------------------------------------------ ban gate
@Client.on_message(filters.private & filters.incoming & BANNED_F, group=-102)
async def ban_gate(client, message):
    uid = message.from_user.id
    if time.time() - _ban_note.get(uid, 0) > 60:
        _ban_note[uid] = time.time()
        try:
            await message.reply_text("🚫 <b>You are banned from this bot.</b>\n<i>Contact the owner if you think this is a mistake.</i>", parse_mode=HTML)
        except Exception:
            pass
    raise StopPropagation


@Client.on_callback_query(BANNED_F, group=-102)
async def ban_gate_buttons(client, query):
    try:
        await query.answer("🚫 You are banned.", show_alert=True)
    except Exception:
        pass
    raise StopPropagation


# ------------------------------------------------------------------ force-sub helpers
async def _is_member(client, channel, user_id) -> bool:
    """True if member. If the check itself fails (bot not admin etc.) the user is let in and the
    owner is alerted, so one broken channel never locks everybody out."""
    try:
        m = await client.get_chat_member(channel, user_id)
        if m.status in (enums.ChatMemberStatus.LEFT, enums.ChatMemberStatus.BANNED):
            return False
        if m.status == enums.ChatMemberStatus.RESTRICTED:
            return bool(getattr(m, "is_member", True))
        return True
    except UserNotParticipant:
        return False
    except Exception as e:
        logging.exception(f"Force-sub check failed for {channel}")
        await send_alert(f"Force-sub: cannot check channel {channel}",
                         detail="Make the bot ADMIN in this channel / check the ID.",
                         exc=e, key=f"fs-{channel}")
        return True


async def _status(client, user_id) -> dict:
    chans = fsub_channels()
    results = await asyncio.gather(*[_is_member(client, ch, user_id) for ch in chans])   # all channels at once
    return dict(zip(chans, results))


async def _missing(client, user_id, fresh: bool = False) -> list:
    """Channels the user has NOT joined. fresh=True skips the cache (used when a file is sent)."""
    if not fsub_channels():
        return []
    if fresh:
        _ok_until.pop(user_id, None)
    elif time.time() < _ok_until.get(user_id, 0):
        return []
    st = await _status(client, user_id)
    missing = [ch for ch, ok in st.items() if not ok]
    if not missing:
        _ok_until[user_id] = time.time() + CACHE_SECONDS
        if len(_ok_until) > 5000:
            _ok_until.clear()
    return missing


async def _join_info(client, channel):
    """(title, join_link) for a channel, cached."""
    if channel in _link_cache:
        return _link_cache[channel]
    manual = None
    if channel in FORCE_SUB_CHANNELS:
        idx = FORCE_SUB_CHANNELS.index(channel)
        manual = FORCE_SUB_LINKS[idx] if idx < len(FORCE_SUB_LINKS) else None
    title, link = str(channel), manual
    try:
        chat = await client.get_chat(channel)
        title = chat.title or title
        if not link:
            link = f"https://t.me/{chat.username}" if chat.username else await client.export_chat_invite_link(channel)
    except Exception as e:
        logging.exception(f"Could not build join link for {channel}")
        await send_alert(f"Force-sub: no join link for {channel}",
                         detail="Make the bot admin with 'invite users' right, or set FORCE_SUB_LINKS.",
                         exc=e, key=f"fslink-{channel}")
    if link:
        _link_cache[channel] = (title, link)
    return title, link


async def _join_view(client, user_id):
    """(text, markup) showing every channel with ✅ / ❌."""
    st = await _status(client, user_id)
    rows, lines, pair = [], [], []
    for ch, ok in st.items():
        title, link = await _join_info(client, ch)
        lines.append(f"{'✅' if ok else '❌'} {title}")
        if link and not ok:
            pair.append(InlineKeyboardButton(f"📢 Join {title}"[:30], url=link))
            if len(pair) == 2:
                rows.append(pair)
                pair = []
    if pair:
        rows.append(pair)
    rows.append([InlineKeyboardButton("✅ I've Joined", callback_data="fs|check")])
    missing = sum(1 for ok in st.values() if not ok)
    return JOIN_TXT.format(n=missing or len(st), status="\n".join(lines)), InlineKeyboardMarkup(rows)


# ------------------------------------------------------------------ left a channel -> forget the cached "verified"
@Client.on_chat_member_updated(group=-100)
async def member_left(client, update):
    """When someone leaves (or is removed from) a channel, drop their cache so the next message re-checks them.
    Works for channels where the bot is an admin (the same requirement as force-sub itself)."""
    try:
        old, new = update.old_chat_member, update.new_chat_member
        user = (new or old).user if (new or old) else None
        if not user:
            return
        if new is None or new.status in (enums.ChatMemberStatus.LEFT, enums.ChatMemberStatus.BANNED):
            _ok_until.pop(user.id, None)
    except Exception:
        logging.debug("member_left handler failed", exc_info=True)


# ------------------------------------------------------------------ force-sub gate
@Client.on_message(filters.private & filters.incoming & ~ADMIN_F, group=-101)
async def force_sub_gate(client, message):
    user = message.from_user
    if not user or not fsub_channels():
        return
    # Sending a file = creating a link, so ALWAYS re-check live (no cache). This stops someone who joined,
    # then left the channel, from still making links during the 2-minute cache window.
    fresh = bool(message.media)
    if not await _missing(client, user.id, fresh=fresh):
        return  # all joined -> normal handlers run
    started = bool(message.text and message.text.startswith("/start"))
    await track_user(user, started, note="🔒 Force-sub pending (has not joined all channels)")
    try:
        text, markup = await _join_view(client, user.id)
        await message.reply_text(text, parse_mode=HTML, quote=True, reply_markup=markup,
                                 disable_web_page_preview=True)
    except Exception:
        logging.exception("Could not send force-sub message")
    raise StopPropagation


@Client.on_callback_query(filters.regex(r"^fs\|check$"), group=-101)
async def force_sub_check(client, query):
    user = query.from_user
    _ok_until.pop(user.id, None)           # force a fresh check
    if await _missing(client, user.id):
        await query.answer("❌ You haven't joined all the channels yet!", show_alert=True)
        try:
            text, markup = await _join_view(client, user.id)
            await query.message.edit_text(text, parse_mode=HTML, reply_markup=markup,
                                          disable_web_page_preview=True)
        except Exception:
            pass            # "message not modified" when nothing changed
    else:
        await query.answer("✅ Verified! Welcome 🎉")
        try:
            await query.message.delete()
        except Exception:
            pass
        await log_event(f"✅ <b>Force-sub completed</b>\n━━━━━━━━━━━━━━━━━━\n{user_line(user)}\n🕒 <i>{now_ist()}</i>")
        from plugins.start import send_start
        await send_start(client, query.message.chat.id, user)
    raise StopPropagation


@Client.on_callback_query(~ADMIN_F & ~filters.regex(r"^fs\|"), group=-101)
async def force_sub_buttons(client, query):
    if await _missing(client, query.from_user.id):
        try:
            await query.answer("🔒 Join the required channels first, then send /start.", show_alert=True)
        except Exception:
            pass
        raise StopPropagation
