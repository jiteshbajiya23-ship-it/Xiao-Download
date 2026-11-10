LINE = "━━━━━━━━━━━━━━━━━━"


class script(object):
    # {0}=user mention  {1}=website url  {2}=site name  {3}=rule text (e.g. '1 link per 2 min')
    START_TXT = """<b>👋 Hello {0}!</b>

⚡ <b>Xiao Bhai Fast Download Bot</b>
Send me any <b>video or file</b> and I'll instantly turn it into a
<b>fast direct download link</b>.

━━━━━━━━━━━━━━━━━━
📤 <b>Send file</b>  ➜  🔗 <b>Get link</b>  ➜  ⚡ <b>Download</b>
⏱ Rule: <b>{3}</b> per user
━━━━━━━━━━━━━━━━━━
🌐 <a href=\"{1}\">{2}</a>"""

    ADMIN_START_TXT = """<b>👑 Welcome back, {0}!</b>

🛡 Your moderator panel is ready. The link limit does not apply to you.

━━━━━━━━━━━━━━━━━━
📤 <b>Send a file</b> ➜ get a download link
📖 /help — all commands
━━━━━━━━━━━━━━━━━━"""

    # ---- /help (what each role sees) ----
    USER_HELP_TXT = """<b>📖 Help</b>
━━━━━━━━━━━━━━━━━━
📤 Send me any <b>video, audio or file</b> and I'll give you a fast download link.

<b>🙋 Commands</b>
/start — open the home screen
/id — show your Telegram ID
/help — show this message
━━━━━━━━━━━━━━━━━━
⏱ Rule: <b>{gap}</b> per user."""

    HELP_TXT = """<b>📖 Moderator commands</b>
━━━━━━━━━━━━━━━━━━
<b>📊 Info</b>
/status — CPU, RAM, users, links
/health — Telegram, MongoDB, web, channels, force-sub
/ping — bot speed
/errors — recent errors (<code>/errors clear</code>)
/users — total / recent users
/userinfo <code>&lt;id&gt;</code> — user details

<b>🛡 Control</b>
/ban <code>&lt;id&gt; [reason]</code> · /unban <code>&lt;id&gt;</code> · /banlist
/resetlimit <code>&lt;id&gt;</code> — reset a user's link limit
/revoke <code>&lt;link or id&gt;</code> — disable a download link
/broadcast — reply to a message to send it to everyone
/setstart — reply to a photo to set the start image
/id — your ID (to get a channel ID, forward a text message from the channel)
━━━━━━━━━━━━━━━━━━
ℹ️ The link limit does not apply to moderators."""

    OWNER_HELP_TXT = """

<b>👑 Owner only</b>
/addadmin <code>&lt;id&gt;</code> · /deladmin <code>&lt;id&gt;</code> · /admins
/setlimit <code>&lt;seconds&gt;</code> — change the link limit (0 = off)
/addfsub <code>&lt;@channel or -100id&gt;</code>
/delfsub <code>&lt;@channel or -100id&gt;</code>
/fsublist — list force-sub channels
/restart — redeploy / restart"""

    NOT_ADMIN_TXT = "⛔ <b>Access denied</b>\nYou are not an admin / owner."
    NOT_OWNER_TXT = "⛔ <b>Access denied</b>\nThis command is for the <b>owner</b> only."

    LINK_TXT = """✅ <b>Your download link is ready!</b>
{line}
📂 <b>File</b>   <code>{name}</code>
📦 <b>Size</b>   <code>{size}</code>
{line}
📥 <b>Download link</b>
<code>{url}</code>
{line}
⏱ <i>Next link in {gap}</i>"""

    LIMIT_TXT = """⏳ <b>Please wait a moment!</b>
{line}
Each user can create <b>only 1 link per {gap}</b>.

⌛ Next link in: <b>{wait}</b>"""

    HINT_TXT = """📤 <b>Send me a video or file</b>
I'll turn it into a fast download link."""

    RESTART_TXT = """🔄 <b>Bot restarted</b>
━━━━━━━━━━━━━━━━━━
📅 <code>{}</code>
⏰ <code>{}</code>
🌐 <code>Asia/Kolkata</code>"""
