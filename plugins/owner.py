"""Moderator (admin) + owner commands.

Moderators: /users /userinfo /resetlimit /ban /unban /banlist
Owner     : /addadmin /deladmin /admins /setlimit /addfsub /delfsub /fsublist  (+ /restart in restart.py)
Every action is also logged to the storage channel.
"""
import html
import time

from pyrogram import Client, filters, enums

from Script import LINE
from database.users_chats_db import db
from info import ADMINS, OWNER_ID
from utils import temp, fmt_duration
from xiaobhai.util.access import (ADMIN_F, OWNER_F, ADMIN_IDS, BANNED, EXTRA_FSUB, state, is_admin, is_owner,
                                  fsub_channels, parse_channel, clear_fsub_cache, apply_commands)
from xiaobhai.util.logger import log_event, now_ist

HTML = enums.ParseMode.HTML


def _ts(ts) -> str:
    return time.strftime("%d %b %Y, %I:%M %p", time.gmtime(float(ts) + 19800)) + " IST" if ts else "—"


def _target(message):
    """User id from the command argument, or from the replied message."""
    if len(message.command) > 1 and message.command[1].lstrip("-").isdigit():
        return int(message.command[1])
    r = message.reply_to_message
    if r and r.from_user:
        return r.from_user.id
    return None


def _actor(message) -> str:
    return f"{message.from_user.mention(style=HTML)} (<code>{message.from_user.id}</code>)"


# =============================================================== MODERATOR COMMANDS
@Client.on_message(filters.command("users") & filters.private & ADMIN_F)
async def users_cmd(client, message):
    total = await db.total_users_count()
    rows = await db.recent_users(10)
    lines = []
    for u in rows:
        uname = f"@{u['username']}" if u.get("username") else "—"
        lines.append(f"• {html.escape(u.get('name') or '?')} · {html.escape(uname)} · <code>{u['id']}</code> · "
                     f"🔗{u.get('links', 0)}")
    await message.reply_text(
        f"👥 <b>Users</b>: <code>{total}</code>   🚫 Banned: <code>{len(BANNED)}</code>\n{LINE}\n"
        f"<b>Latest 10</b>\n" + ("\n".join(lines) or "<i>none yet</i>"), parse_mode=HTML)


@Client.on_message(filters.command("userinfo") & filters.private & ADMIN_F)
async def userinfo_cmd(client, message):
    uid = _target(message)
    if uid is None:
        return await message.reply_text("Use: <code>/userinfo &lt;id&gt;</code> (or reply to a user's message)", parse_mode=HTML)
    u = await db.get_user(uid)
    if not u:
        return await message.reply_text("❌ This user is not in the database.")
    cd = await db.cool.find_one({"_id": uid})
    wait = 0
    if cd and state.rate > 0:
        wait = max(0, int(state.rate - (time.time() - cd["ts"])))
    uname = f"@{u['username']}" if u.get("username") else "—"
    role = "👑 Owner" if is_owner(uid) else "🛡 Moderator" if is_admin(uid) else "👤 User"
    await message.reply_text(
        f"👤 <b>User info</b>\n{LINE}\n"
        f"📛 <b>Name</b>  {html.escape(u.get('name') or '?')}\n🔖 <b>Username</b>  {html.escape(uname)}\n"
        f"🆔 <b>ID</b>  <code>{uid}</code>\n"
        f"🏷 <b>Role</b>  {role}\n🚫 <b>Banned</b>  {'yes' if uid in BANNED else 'no'}\n"
        f"🔗 <b>Links made</b>  <code>{u.get('links', 0)}</code>\n📅 <b>Joined</b>  {_ts(u.get('joined'))}\n"
        f"👀 <b>Last seen</b>  {_ts(u.get('last_seen'))}\n"
        f"⏳ <b>Limit</b>  {fmt_duration(wait) + ' left' if wait else '✅ free'}", parse_mode=HTML)


@Client.on_message(filters.command("resetlimit") & filters.private & ADMIN_F)
async def resetlimit_cmd(client, message):
    uid = _target(message)
    if uid is None:
        return await message.reply_text("Use: <code>/resetlimit &lt;id&gt;</code>", parse_mode=HTML)
    await db.release(uid)
    await message.reply_text(f"♻️ Link limit reset for <code>{uid}</code>.", parse_mode=HTML)
    await log_event(f"♻️ <b>Limit reset</b>\n{LINE}\nUser: <code>{uid}</code>\nBy: {_actor(message)}\n🕒 <i>{now_ist()}</i>")


@Client.on_message(filters.command("ban") & filters.private & ADMIN_F)
async def ban_cmd(client, message):
    uid = _target(message)
    if uid is None:
        return await message.reply_text("Use: <code>/ban &lt;id&gt; [reason]</code>", parse_mode=HTML)
    if is_admin(uid):
        return await message.reply_text("❌ You can't ban an admin or the owner.")
    reason = " ".join(message.command[2:]) if len(message.command) > 2 else ""
    await db.add_ban(uid, reason, message.from_user.id)
    BANNED.add(uid)
    await message.reply_text(f"🚫 <code>{uid}</code> has been banned.", parse_mode=HTML)
    await log_event(f"🚫 <b>User banned</b>\n{LINE}\nUser: <code>{uid}</code>\nReason: {html.escape(reason or '—')}\n"
                    f"By: {_actor(message)}\n🕒 <i>{now_ist()}</i>")


@Client.on_message(filters.command("unban") & filters.private & ADMIN_F)
async def unban_cmd(client, message):
    uid = _target(message)
    if uid is None:
        return await message.reply_text("Use: <code>/unban &lt;id&gt;</code>", parse_mode=HTML)
    await db.remove_ban(uid)
    BANNED.discard(uid)
    await message.reply_text(f"✅ <code>{uid}</code> has been unbanned.", parse_mode=HTML)
    await log_event(f"✅ <b>User unbanned</b>\n{LINE}\nUser: <code>{uid}</code>\nBy: {_actor(message)}\n🕒 <i>{now_ist()}</i>")


@Client.on_message(filters.command("banlist") & filters.private & ADMIN_F)
async def banlist_cmd(client, message):
    rows = await db.get_bans()
    if not rows:
        return await message.reply_text("✅ No banned users.")
    lines = [f"• <code>{r['_id']}</code> — {html.escape(r.get('reason') or '—')}" for r in rows[:50]]
    await message.reply_text(f"🚫 <b>Banned users</b> ({len(rows)})\n{LINE}\n" + "\n".join(lines), parse_mode=HTML)


# =============================================================== OWNER COMMANDS
async def _save_admins():
    dyn = sorted(ADMIN_IDS - set(ADMINS) - {OWNER_ID})
    await db.set_setting("admins", dyn)


@Client.on_message(filters.command("addadmin") & filters.private & OWNER_F)
async def addadmin_cmd(client, message):
    uid = _target(message)
    if uid is None:
        return await message.reply_text("Use: <code>/addadmin &lt;id&gt;</code>", parse_mode=HTML)
    ADMIN_IDS.add(uid)
    BANNED.discard(uid)
    await db.remove_ban(uid)
    await _save_admins()
    await apply_commands(client, only_user=uid)
    await message.reply_text(f"🛡 <code>{uid}</code> is now an admin.\n<i>They need to send /start to the bot once.</i>", parse_mode=HTML)
    await log_event(f"🛡 <b>Admin added</b>\n{LINE}\nUser: <code>{uid}</code>\nBy: {_actor(message)}\n🕒 <i>{now_ist()}</i>")


@Client.on_message(filters.command("deladmin") & filters.private & OWNER_F)
async def deladmin_cmd(client, message):
    uid = _target(message)
    if uid is None:
        return await message.reply_text("Use: <code>/deladmin &lt;id&gt;</code>", parse_mode=HTML)
    if is_owner(uid):
        return await message.reply_text("❌ The owner can't be removed.")
    if uid in ADMINS:
        return await message.reply_text("⚠️ This admin comes from the <code>ADMINS</code> environment variable — remove them there.", parse_mode=HTML)
    ADMIN_IDS.discard(uid)
    await _save_admins()
    try:
        from pyrogram.types import BotCommandScopeChat
        await client.delete_bot_commands(scope=BotCommandScopeChat(chat_id=uid))
    except Exception:
        pass
    await message.reply_text(f"✅ <code>{uid}</code> is no longer an admin.", parse_mode=HTML)
    await log_event(f"🛡 <b>Admin removed</b>\n{LINE}\nUser: <code>{uid}</code>\nBy: {_actor(message)}\n🕒 <i>{now_ist()}</i>")


@Client.on_message(filters.command("admins") & filters.private & OWNER_F)
async def admins_cmd(client, message):
    lines = [f"{'👑' if is_owner(a) else '🛡'} <code>{a}</code>" for a in sorted(ADMIN_IDS)]
    await message.reply_text(f"🛡 <b>Admins</b> ({len(lines)})\n{LINE}\n" + "\n".join(lines), parse_mode=HTML)


@Client.on_message(filters.command("setlimit") & filters.private & OWNER_F)
async def setlimit_cmd(client, message):
    if len(message.command) < 2 or not message.command[1].isdigit():
        cur = fmt_duration(state.rate) if state.rate > 0 else "off"
        return await message.reply_text(
            f"⏱ Current limit: <b>{cur}</b>\nUse: <code>/setlimit 120</code> (seconds, 0 = off)", parse_mode=HTML)
    n = int(message.command[1])
    if n > 86400:
        return await message.reply_text("❌ Maximum is 86400 seconds (1 day).")
    state.rate = n
    await db.set_setting("rate", n)
    now_txt = fmt_duration(n) if n > 0 else "off"
    await message.reply_text(f"✅ Now <b>1 link per {now_txt}</b>." if n else "✅ Link limit turned off.", parse_mode=HTML)
    await log_event(f"⏱ <b>Limit changed</b>\n{LINE}\nNew: <b>{now_txt}</b>\nBy: {_actor(message)}\n🕒 <i>{now_ist()}</i>")


@Client.on_message(filters.command("addfsub") & filters.private & OWNER_F)
async def addfsub_cmd(client, message):
    ch = parse_channel(message.command[1]) if len(message.command) > 1 else None
    if ch is None:
        return await message.reply_text("Use: <code>/addfsub @channel</code> or <code>/addfsub -100123...</code>", parse_mode=HTML)
    if str(ch).lower() in [str(c).lower() for c in fsub_channels()]:
        return await message.reply_text("⚠️ This channel is already in the force-sub list.")
    try:
        chat = await client.get_chat(ch)
    except Exception as e:
        return await message.reply_text(f"❌ Channel not found: <code>{html.escape(str(e)[:150])}</code>\n"
                                        f"Make the bot an admin of the channel first.", parse_mode=HTML)
    warn = ""
    try:
        m = await client.get_chat_member(chat.id, temp.ME)
        if m.status not in (enums.ChatMemberStatus.ADMINISTRATOR, enums.ChatMemberStatus.OWNER):
            warn = "\n⚠️ The bot is <b>not an admin</b> in this channel — member checks won't work."
    except Exception:
        warn = "\n⚠️ The bot is <b>not an admin</b> in this channel — member checks won't work."
    EXTRA_FSUB.append(ch)
    await db.set_setting("fsub", list(EXTRA_FSUB))
    clear_fsub_cache()
    await message.reply_text(f"🔒 Added to force-sub: <b>{html.escape(chat.title or str(ch))}</b>{warn}", parse_mode=HTML)
    await log_event(f"🔒 <b>Force-sub added</b>\n{LINE}\n{html.escape(chat.title or str(ch))} (<code>{chat.id}</code>)\n"
                    f"By: {_actor(message)}\n🕒 <i>{now_ist()}</i>")


@Client.on_message(filters.command("delfsub") & filters.private & OWNER_F)
async def delfsub_cmd(client, message):
    ch = parse_channel(message.command[1]) if len(message.command) > 1 else None
    if ch is None:
        return await message.reply_text("Use: <code>/delfsub @channel</code>", parse_mode=HTML)
    key = str(ch).lower()
    hit = [c for c in EXTRA_FSUB if str(c).lower() == key]
    if not hit:
        if key in [str(c).lower() for c in fsub_channels()]:
            return await message.reply_text("⚠️ This channel comes from the <code>FORCE_SUB_CHANNELS</code> environment variable — remove it there.", parse_mode=HTML)
        return await message.reply_text("❌ This channel is not in the force-sub list.")
    for c in hit:
        EXTRA_FSUB.remove(c)
    await db.set_setting("fsub", list(EXTRA_FSUB))
    clear_fsub_cache()
    await message.reply_text("🔓 Removed from force-sub.")
    await log_event(f"🔒 <b>Force-sub removed</b>\n{LINE}\n<code>{html.escape(str(ch))}</code>\nBy: {_actor(message)}\n🕒 <i>{now_ist()}</i>")


@Client.on_message(filters.command("fsublist") & filters.private & OWNER_F)
async def fsublist_cmd(client, message):
    chans = fsub_channels()
    if not chans:
        return await message.reply_text("🔓 Force-sub is off (no channels).")
    lines = []
    for ch in chans:
        src = "bot" if ch in EXTRA_FSUB else "env"
        try:
            chat = await client.get_chat(ch)
            lines.append(f"• <b>{html.escape(chat.title or str(ch))}</b> — <code>{ch}</code> ({src})")
        except Exception:
            lines.append(f"• <code>{ch}</code> ({src}) ❌ bot has no access")
    await message.reply_text(f"🔒 <b>Force-sub channels</b> ({len(chans)})\n{LINE}\n" + "\n".join(lines), parse_mode=HTML)
