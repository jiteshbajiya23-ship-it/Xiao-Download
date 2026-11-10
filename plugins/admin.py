"""Admin commands: /status /health /ping /errors /revoke /setstart /help (+ refresh buttons)."""
import asyncio
import html
import re
import time

import aiohttp
import psutil
from pyrogram import Client, filters, enums
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from Script import script, LINE
from database.users_chats_db import db
from info import URL, LOG_CHANNEL
from utils import temp, bar, fmt_uptime, fmt_duration
from xiaobhai.util.access import ADMIN_F, ADMIN_IDS, BANNED, fsub_channels, is_admin, is_owner, state
from xiaobhai.util.maintenance import revoke_link

HTML = enums.ParseMode.HTML
ADMIN = ADMIN_F

NAV = InlineKeyboardMarkup([
    [InlineKeyboardButton("📊 Status", callback_data="ad|status"), InlineKeyboardButton("🩺 Health", callback_data="ad|health")],
    [InlineKeyboardButton("🐞 Errors", callback_data="ad|errors"), InlineKeyboardButton("📖 Help", callback_data="ad|help")],
])


# ------------------------------------------------------------------ STATUS
async def build_status() -> str:
    cpu = psutil.cpu_percent(interval=0.3)
    ram = psutil.virtual_memory()
    try:
        users = await db.total_users_count()
    except Exception:
        users = "❌ DB down"
    total_links = await db.get_stat("links")
    return (
        "📊 <b>Bot Status</b>\n"
        f"{LINE}\n"
        f"🟢 <b>Uptime</b>   <code>{fmt_uptime(time.time() - temp.START_TIME)}</code>\n"
        f"⚙️ <b>CPU</b>      <code>{cpu:.0f}%</code>  {bar(cpu / 100)}\n"
        f"🧠 <b>RAM</b>      <code>{ram.percent:.0f}%</code>  {bar(ram.percent / 100)}\n"
        f"{LINE}\n"
        f"👥 <b>Users</b>    <code>{users}</code>\n"
        f"🔗 <b>Links</b>    <code>{temp.LINKS}</code> now · <code>{total_links}</code> total\n"
        f"⏳ <b>Limited</b>  <code>{temp.LIMITED}</code> (rule: 1 per {fmt_duration(state.rate) if state.rate > 0 else 'off'})\n"
        f"🔒 <b>Force-sub</b> <code>{len(fsub_channels())}</code> channel(s)\n"
        f"👑 <b>Admins</b>   <code>{len(ADMIN_IDS)}</code>  ·  🚫 <b>Banned</b> <code>{len(BANNED)}</code>\n"
        f"🐞 <b>Errors</b>   <code>{temp.ERROR_COUNT}</code>\n"
        f"{LINE}\n"
        f"<i>Updated {time.strftime('%I:%M:%S %p', time.gmtime(time.time() + 19800))} IST</i>"
    )


@Client.on_message(filters.command("status") & filters.private & ADMIN)
async def status_cmd(client, message):
    await message.reply_text(await build_status(), parse_mode=HTML, reply_markup=NAV)


# ------------------------------------------------------------------ HEALTH
async def _timed(coro):
    t = time.perf_counter()
    await coro
    return (time.perf_counter() - t) * 1000


async def build_health() -> str:
    checks = []

    async def add(name, coro_fn):
        try:
            ms = await asyncio.wait_for(_timed(coro_fn()), timeout=10)
            checks.append((name, True, f"{ms:.0f} ms"))
        except Exception as e:
            checks.append((name, False, (str(e) or type(e).__name__)[:60]))

    await add("Telegram API", lambda: temp.BOT.get_me())
    await add("MongoDB", lambda: db.ping())
    await add("Log channel", lambda: temp.BOT.get_chat(LOG_CHANNEL))

    async def web():
        if not URL:
            raise RuntimeError("URL env variable is empty")
        async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=8)) as s:
            async with s.get(URL + "health") as r:
                if r.status != 200:
                    raise RuntimeError(f"HTTP {r.status}")
    await add("Web server", web)

    # force-sub: bot must be able to read members of every channel
    for ch in fsub_channels():
        async def chk(ch=ch):
            await temp.BOT.get_chat_member(ch, temp.ME)
        await add(f"Force-sub {ch}", chk)

    bad = sum(1 for _, ok, _ in checks if not ok)
    lines = [f"{'✅' if ok else '❌'} <b>{html.escape(str(n))}</b> — <code>{html.escape(d)}</code>" for n, ok, d in checks]
    verdict = "🟢 <b>All systems healthy</b>" if not bad else f"🟠 <b>{bad} problem(s) found</b>"
    return f"🩺 <b>Health Check</b>\n{LINE}\n" + "\n".join(lines) + f"\n{LINE}\n{verdict}"


@Client.on_message(filters.command("health") & filters.private & ADMIN)
async def health_cmd(client, message):
    sts = await message.reply_text("🩺 <i>Checking everything…</i>", parse_mode=HTML)
    await sts.edit_text(await build_health(), parse_mode=HTML, reply_markup=NAV)


# ------------------------------------------------------------------ PING / HELP
@Client.on_message(filters.command("ping") & filters.private & ADMIN)
async def ping_cmd(client, message):
    t = time.perf_counter()
    sts = await message.reply_text("🏓 …")
    await sts.edit_text(f"🏓 <b>Pong!</b>  <code>{(time.perf_counter() - t) * 1000:.0f} ms</code>", parse_mode=HTML)


@Client.on_message(filters.command("help") & filters.private & ADMIN)
async def help_cmd(client, message):
    text = script.HELP_TXT + (script.OWNER_HELP_TXT if is_owner(message.from_user.id) else "")
    await message.reply_text(text, parse_mode=HTML, reply_markup=NAV)


# ------------------------------------------------------------------ ERRORS
def build_errors() -> str:
    if not temp.ERRORS:
        return f"🐞 <b>Recent errors</b>\n{LINE}\n✅ <i>No errors since the last restart.</i>"
    rows = []
    for ts, title, reason in reversed(temp.ERRORS):
        t = time.strftime("%d %b %I:%M %p", time.gmtime(ts + 19800))
        rows.append(f"🕒 <i>{t}</i>\n<b>{html.escape(title)}</b>\n<code>{html.escape(reason[:160])}</code>")
    return f"🐞 <b>Recent errors</b> ({temp.ERROR_COUNT} total)\n{LINE}\n" + f"\n{LINE}\n".join(rows[:8])


@Client.on_message(filters.command("errors") & filters.private & ADMIN)
async def errors_cmd(client, message):
    if len(message.command) > 1 and message.command[1].lower() == "clear":
        temp.ERRORS.clear()
        temp.ERROR_COUNT = 0
        return await message.reply_text("✅ Error list cleared.")
    await message.reply_text(build_errors(), parse_mode=HTML, reply_markup=NAV)


# ------------------------------------------------------------------ REVOKE
@Client.on_message(filters.command("revoke") & filters.private & ADMIN)
async def revoke_cmd(client, message):
    arg = " ".join(message.command[1:]) or (message.reply_to_message.text if message.reply_to_message and message.reply_to_message.text else "")
    m = re.fullmatch(r"\s*(\d+)\s*", arg) or re.search(r"/(?:dl|file)/(\d+)/", arg)
    if not m:
        return await message.reply_text(
            "🗑 <b>Revoke a link</b>\nSend <code>/revoke &lt;link or id&gt;</code> or reply to a link with /revoke.",
            parse_mode=HTML)
    try:
        await revoke_link(client, int(m.group(1)))
        await message.reply_text(f"🗑 <b>Link revoked</b> — file <code>#{m.group(1)}</code> removed. The link is dead now.",
                                 parse_mode=HTML)
    except Exception as e:
        await message.reply_text(f"❌ Could not revoke: <code>{html.escape(str(e)[:200])}</code>", parse_mode=HTML)


# ------------------------------------------------------------------ SET START IMAGE
@Client.on_message(filters.command("setstart") & filters.private & ADMIN)
async def setstart_cmd(client, message):
    r = message.reply_to_message
    if not r or not r.photo:
        return await message.reply_text("🖼 Kisi <b>photo</b> par reply karke /setstart bhejo.", parse_mode=HTML)
    await db.set_setting("start_image", r.photo.file_id)
    temp.START_FILE_ID = r.photo.file_id
    await message.reply_text("✅ Start image update ho gayi. /start bhejke dekh lo.")


# ------------------------------------------------------------------ BUTTONS
@Client.on_callback_query(filters.regex(r"^ad\|"))
async def admin_buttons(client, query):
    if not is_admin(query.from_user.id):
        return await query.answer("Admins only.", show_alert=True)
    action = query.data.split("|")[1]
    await query.answer("Updating…" if action in ("status", "health") else None)
    if action == "status":
        text = await build_status()
    elif action == "health":
        text = await build_health()
    elif action == "errors":
        text = build_errors()
    else:
        text = script.HELP_TXT + (script.OWNER_HELP_TXT if is_owner(query.from_user.id) else "")
    try:
        await query.message.edit_text(text, parse_mode=HTML, reply_markup=NAV)
    except Exception:
        pass
