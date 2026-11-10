import logging, logging.config, asyncio, threading, time
from http.server import BaseHTTPRequestHandler, HTTPServer
from datetime import date, datetime

import pytz

# uvloop = a much faster event loop (less CPU, which matters on Render's tiny free CPU).
# It must be installed BEFORE pyrogram is imported. Falls back silently if it is not available.
try:
    import uvloop
    uvloop.install()
except Exception:
    pass

logging.config.fileConfig('logging.conf')
logging.getLogger().setLevel(logging.INFO)
logging.getLogger("pyrogram").setLevel(logging.WARNING)
logging.getLogger("aiohttp").setLevel(logging.ERROR)
logging.getLogger("aiohttp.web").setLevel(logging.ERROR)

from aiohttp import web
from pyrogram import idle, enums
from pyrogram.errors import FloodWait

from info import *
from utils import temp
from Script import script
from database.users_chats_db import db
from plugins import web_server
from xiaobhai.bot import StreamBot
from xiaobhai.bot.clients import initialize_clients
from xiaobhai.util.keepalive import ping_server
from xiaobhai.util.alerts import send_alert
from xiaobhai.util.access import load_runtime, apply_commands

# Handlers in /plugins are loaded by Pyrogram itself (plugins={"root": "plugins"}).


def _start_with_floodwait():
    """Telegram can rate-limit bot logins (FloodWait). Instead of crashing (the host would restart
    us and re-trigger the limit) wait it out while answering health checks."""
    for attempt in range(5):
        try:
            StreamBot.start()
            return
        except FloodWait as e:
            wait = int(e.value) + 5
            logging.warning(f"FloodWait: waiting {wait}s (attempt {attempt + 1}/5)...")

            class _Health(BaseHTTPRequestHandler):
                def do_GET(self):
                    self.send_response(200)
                    self.end_headers()
                    self.wfile.write(b"waiting for Telegram flood limit")

                def log_message(self, *a):
                    pass

            httpd = None
            try:
                httpd = HTTPServer(("0.0.0.0", PORT), _Health)
                threading.Thread(target=httpd.serve_forever, daemon=True).start()
            except Exception as ex:
                logging.warning(f"Health server not started: {ex}")
            time.sleep(wait)
            if httpd:
                httpd.shutdown()
                httpd.server_close()
    raise SystemExit("Could not log in to Telegram after repeated FloodWait")


_start_with_floodwait()
loop = asyncio.get_event_loop()


async def start():
    print('\nInitializing Xiao Bhai Download Bot')
    me = await StreamBot.get_me()
    await initialize_clients()

    temp.BOT = StreamBot
    temp.ME = me.id
    temp.U_NAME = me.username
    temp.B_NAME = me.first_name

    def _on_loop_error(_loop, ctx):
        exc = ctx.get("exception")
        logging.error("Unhandled error: %s", ctx.get("message"), exc_info=exc)
        asyncio.ensure_future(send_alert("Unhandled error", detail=str(ctx.get("message", "")), exc=exc, key="loop"))
    asyncio.get_running_loop().set_exception_handler(_on_loop_error)

    if KEEP_ALIVE:
        asyncio.create_task(ping_server())
    if not URL:
        logging.warning("URL env variable is empty - generated links will be broken!")

    db_error = None
    try:
        await db.ping()
        await db.ensure_indexes()
        logging.info("MongoDB connected ✅")
    except Exception as e:
        db_error = e
        logging.error(f"MongoDB connection FAILED ❌ : {e}")

    # admins / bans / limit / extra force-sub channels saved by the owner + command menus
    await load_runtime()
    asyncio.create_task(apply_commands(StreamBot))

    try:
        now = datetime.now(pytz.timezone('Asia/Kolkata'))
        await StreamBot.send_message(
            chat_id=LOG_CHANNEL, parse_mode=enums.ParseMode.HTML,
            text=script.RESTART_TXT.format(date.today(), now.strftime("%I:%M:%S %p")))
        if db_error:
            await StreamBot.send_message(
                chat_id=LOG_CHANNEL, parse_mode=enums.ParseMode.HTML,
                text=f"⚠️ <b>MongoDB is not connecting</b>\n\n<code>{str(db_error)[:900]}</code>\n\n"
                     f"Check DATABASE_URI and Atlas Network Access (0.0.0.0/0).")
    except Exception as e:
        logging.warning(f"Could not send message to LOG_CHANNEL (is the bot an admin in the storage channel?): {e}")

    app = web.AppRunner(await web_server(), access_log=None)   # no per-request access log = less CPU
    await app.setup()
    await web.TCPSite(app, "0.0.0.0", PORT).start()
    logging.info(f"Web server running on port {PORT}")
    await idle()


if __name__ == '__main__':
    try:
        loop.run_until_complete(start())
    except KeyboardInterrupt:
        logging.info('Service Stopped Bye 👋')
