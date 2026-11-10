LINE = "━━━━━━━━━━━━━━━━━━"


class script(object):
    # {0}=user mention
    START_TXT = """<b>👋 Hello {0}!</b>

⚡ <b>Xiao Bhai Fast Download Bot</b>
Koi bhi <b>video / file</b> bhejo, main turant ek
<b>fast direct download link</b> bana dunga.

━━━━━━━━━━━━━━━━━━
📤 <b>File bhejo</b>  →  🔗 <b>Link lo</b>  →  ⚡ <b>Download karo</b>
⏱ Rule: <b>{3} me 1 link</b> per user
━━━━━━━━━━━━━━━━━━
🌐 <a href="{1}">{2}</a>"""

    ADMIN_START_TXT = """<b>👑 Welcome back, {0}!</b>

Admin panel ready hai. Aap par link limit lagu nahi hoti.

━━━━━━━━━━━━━━━━━━
📤 <b>File bhejo</b> → download link
📖 /help — saari commands
━━━━━━━━━━━━━━━━━━"""

    HELP_TXT = """<b>📖 Admin commands</b>
━━━━━━━━━━━━━━━━━━
<b>📊 Info</b>
/status — CPU, RAM, users, links
/health — Telegram, MongoDB, web, channels, force-sub
/ping — bot speed
/errors — last errors (<code>/errors clear</code>)
/users — total / recent users
/userinfo <code>&lt;id&gt;</code> — user details
<b>🛡 Control</b>
/ban <code>&lt;id&gt; [reason]</code>  /unban <code>&lt;id&gt;</code>  /banlist
/resetlimit <code>&lt;id&gt;</code> — user ka 2-min limit reset
/revoke <code>&lt;link or id&gt;</code> — download link band
/broadcast — kisi message par reply karo
/setstart — kisi photo par reply karo
/id — apna ID (channel ka ID: channel ka koi text message forward karo)
━━━━━━━━━━━━━━━━━━
Admins par link limit lagu nahi hoti."""

    OWNER_HELP_TXT = """

<b>👑 Owner only</b>
/addadmin <code>&lt;id&gt;</code>  /deladmin <code>&lt;id&gt;</code>  /admins
/setlimit <code>&lt;seconds&gt;</code> — link limit badlo (0 = off)
/addfsub <code>&lt;@channel ya -100id&gt;</code>
/delfsub <code>&lt;@channel ya -100id&gt;</code>
/fsublist — force-sub channels
/restart — redeploy / restart"""

    LINK_TXT = """✅ <b>Your download link is ready!</b>
{line}
📂 <b>File</b>   <code>{name}</code>
📦 <b>Size</b>   <code>{size}</code>
{line}
📥 <b>Download link</b>
<code>{url}</code>
{line}
⏱ <i>Next link in {gap}</i>"""

    LIMIT_TXT = """⏳ <b>Thoda ruko!</b>
{line}
Ek user <b>{gap} me sirf 1 link</b> bana sakta hai.

⌛ Next link in: <b>{wait}</b>"""

    HINT_TXT = """📤 <b>Mujhe koi video ya file bhejo</b>
Main uska fast download link bana dunga."""

    RESTART_TXT = """🔄 <b>Bot restarted</b>
━━━━━━━━━━━━━━━━━━
📅 <code>{}</code>
⏰ <code>{}</code>
🌐 <code>Asia/Kolkata</code>"""
