import html
import logging
import time
from urllib.parse import quote

from pyrogram import Client, filters, enums, StopPropagation
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from Script import script, LINE
from info import (URL, LOG_CHANNEL, SHORTLINK, WEBSITE_URL, SITE_NAME, START_IMAGE,
                  DISCUSSION_URL, DONGHUA_URL, UPDATES_URL, CUSTOM_BOT_URL)
from database.users_chats_db import db
from utils import temp, get_shortlink, retry_async, fmt_duration
from xiaobhai.util.access import is_admin, ADMIN_F, state
from xiaobhai.util.alerts import send_alert
from xiaobhai.util.file_properties import get_name, get_hash, get_media_file_size
from xiaobhai.util.human_readable import humanbytes
from xiaobhai.util.linksign import sign_query
from xiaobhai.util.logger import log_event, user_line, now_ist
from xiaobhai.util.maintenance import revoke_link
from xiaobhai.util.users import track_user

HTML = enums.ParseMode.HTML
_last_limit_note: dict = {}   # user_id -> time of the last "wait" message (no spam on albums)


# ------------------------------------------------------------------ keyboards
def start_markup() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("💬 Discussion", url=DISCUSSION_URL),
         InlineKeyboardButton("🎬 Donghua", url=DONGHUA_URL)],
        [InlineKeyboardButton("📢 Updates", url=UPDATES_URL),
         InlineKeyboardButton("🤖 Custom Bot [PAID]", url=CUSTOM_BOT_URL)],
        [InlineKeyboardButton(f"🌐 {SITE_NAME}", url=WEBSITE_URL)],
    ])


def _gap() -> str:
    return fmt_duration(state.rate) if state.rate > 0 else "no limit"


def rule_text() -> str:
    return f"1 link per {fmt_duration(state.rate)}" if state.rate > 0 else "Unlimited links"


# ------------------------------------------------------------------ /start
async def send_start(client, chat_id, user):
    """Start screen: image + text + buttons. Falls back to plain text if the image can't be sent."""
    tmpl = script.ADMIN_START_TXT if is_admin(user.id) else script.START_TXT
    caption = tmpl.format(user.mention(style=HTML), WEBSITE_URL, html.escape(SITE_NAME), rule_text())
    markup = start_markup()

    # image priority: cached file_id -> /setstart image -> START_IMAGE url
    photo = temp.START_FILE_ID or await db.get_setting("start_image") or START_IMAGE
    if photo:
        try:
            sent = await client.send_photo(chat_id, photo, caption=caption, parse_mode=HTML, reply_markup=markup)
            if not temp.START_FILE_ID and sent.photo:
                temp.START_FILE_ID = sent.photo.file_id
            return
        except Exception as e:
            temp.START_FILE_ID = None
            logging.warning(f"Start image failed ({e}). Sending text instead. "
                            f"Use a DIRECT image link (ends in .jpg/.png) or /setstart.")
    await client.send_message(chat_id, caption, parse_mode=HTML, reply_markup=markup,
                              disable_web_page_preview=True)


@Client.on_message(filters.command("start") & filters.incoming & filters.private)
async def start(client, message):
    user = message.from_user
    if not user:
        return
    await track_user(user, started=True)          # saves the user + logs to the storage channel
    await send_start(client, message.chat.id, user)


@Client.on_message(filters.command("id") & filters.incoming & filters.private)
async def my_id(client, message):
    await message.reply_text(f"🆔 Your ID: <code>{message.from_user.id}</code>", parse_mode=HTML, quote=True)


@Client.on_message(filters.private & filters.incoming & filters.forwarded & filters.text & ADMIN_F, group=-1)
async def forwarded_channel_id(client, message):
    """Admin forwards a text message from a channel -> bot replies with that channel's ID."""
    chat = getattr(message, "forward_from_chat", None) or getattr(getattr(message, "forward_origin", None), "chat", None)
    if not chat:
        return
    await message.reply_text(
        f"📢 <b>{html.escape(chat.title or 'Channel')}</b>\nChannel ID: <code>{chat.id}</code>",
        parse_mode=HTML, quote=True)
    raise StopPropagation


# ------------------------------------------------------------------ link creation
async def create_links(client, message):
    """Forward the file into the STORAGE channel and reply with the DOWNLOAD link (no stream link)."""
    media = getattr(message, message.media.value)
    user = message.from_user

    # Forward the ORIGINAL message so the storage channel shows who sent the file ("Forwarded from ...")
    # together with the file and its caption. If forwarding fails, fall back to a plain copy.
    try:
        log_msg = await retry_async(message.forward, LOG_CHANNEL)
    except Exception:
        logging.warning("Forward to the storage channel failed, copying the file instead", exc_info=True)
        log_msg = await retry_async(client.send_cached_media, LOG_CHANNEL, media.file_id)

    name = get_name(log_msg)
    file_hash = get_hash(log_msg)
    size = humanbytes(get_media_file_size(message)) or "—"
    # /dl/ = our nice download page (never a raw file URL -> no black screen / Google)
    download = f"{URL}dl/{log_msg.id}/{quote(name, safe='')}?{sign_query(log_msg.id, file_hash)}"
    if SHORTLINK:
        download = await get_shortlink(download)

    try:
        await log_msg.reply_text(
            text=(f"🔗 <b>Link generated</b>\n{LINE}\n{user_line(user)}\n{LINE}\n"
                  f"📂 <code>{html.escape(name)}</code>\n📦 <code>{size}</code>\n"
                  f"🕒 <i>{now_ist()}</i>"),
            quote=True, parse_mode=HTML, disable_web_page_preview=True,
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("📥 Download", url=download),
                InlineKeyboardButton("🗑 Revoke", callback_data=f"rv|{log_msg.id}"),
            ]]),
        )
    except Exception:
        logging.warning("Could not post the log line (link still works)")

    await message.reply_text(
        text=script.LINK_TXT.format(line=LINE, name=html.escape(name), size=size,
                                    url=html.escape(download), gap=_gap()),
        quote=True, parse_mode=HTML, disable_web_page_preview=True,
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("📥 Download Now", url=download)],
            [InlineKeyboardButton("📢 Updates", url=UPDATES_URL),
             InlineKeyboardButton("🌐 Website", url=WEBSITE_URL)],
        ]),
    )
    temp.LINKS += 1
    await db.inc_stat("links")
    await db.inc_user_links(user.id)


@Client.on_message(filters.private & filters.incoming & (filters.document | filters.video | filters.audio))
async def file_handler(client, message):
    user = message.from_user
    if not user:
        return
    await track_user(user, started=False)         # registers the user if they never pressed /start

    # ---- RULE: 1 link per N seconds per user (admins are free) ----
    limited = (not is_admin(user.id)) and state.rate > 0
    if limited:
        allowed, wait = await db.try_acquire(user.id, state.rate)
        if not allowed:
            temp.LIMITED += 1
            now = time.time()
            if now - _last_limit_note.get(user.id, 0) > 5:   # albums: reply once, not 10 times
                _last_limit_note[user.id] = now
                if len(_last_limit_note) > 5000:
                    _last_limit_note.clear()
                await message.reply_text(
                    script.LIMIT_TXT.format(line=LINE, gap=fmt_duration(state.rate), wait=fmt_duration(wait)),
                    quote=True, parse_mode=HTML)
            return

    try:
        await create_links(client, message)
    except Exception as e:
        logging.exception("Link generation failed")
        if limited:
            await db.release(user.id)               # failed -> user does not lose the slot
        await send_alert("Link generation failed", exc=e, key="linkgen")
        await message.reply_text("❌ <b>Couldn't create your link.</b>\n<i>The owner has been notified. "
                                 "Please try again in a little while.</i>", parse_mode=HTML, quote=True)


@Client.on_message(filters.private & filters.incoming & filters.text & ~filters.regex(r"^/"))
async def text_hint(client, message):
    await message.reply_text(script.HINT_TXT, parse_mode=HTML, quote=True, reply_markup=start_markup(),
                             disable_web_page_preview=True)


@Client.on_callback_query(filters.regex(r"^rv\|"))
async def revoke_button(client, query):
    if not is_admin(query.from_user.id):
        return await query.answer("⛔ You are not an admin / owner.", show_alert=True)
    try:
        await revoke_link(client, int(query.data.split("|")[1]))
        await query.answer("Link revoked")
        await query.message.edit_text("🗑 <b>Link revoked</b>\n<i>The download link no longer works.</i>", parse_mode=HTML)
    except Exception as e:
        await query.answer(f"Could not revoke: {str(e)[:100]}", show_alert=True)
