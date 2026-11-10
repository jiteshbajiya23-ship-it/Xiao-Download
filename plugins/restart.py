"""/restart - OWNER ONLY. Redeploys on Render (or restarts the process as a fallback).

Optional env variables (Render dashboard):
  OWNER_ID=123456789        (your Telegram ID)
  RENDER_API_KEY=rnd_...    (Render -> Account Settings -> API Keys)
  RENDER_SERVICE_ID=srv-... (the id in your service URL: dashboard.render.com/web/srv-xxxx)
"""
import asyncio
import logging
import os
import sys

import requests
from pyrogram import Client, filters, enums

from info import RENDER_API_KEY, RENDER_SERVICE_ID
from xiaobhai.util.access import OWNER_F

log = logging.getLogger("restart")
HTML = enums.ParseMode.HTML


def _render_redeploy() -> str:
    """Trigger a fresh deploy. Returns '' on success, else an error text."""
    try:
        r = requests.post(
            f"https://api.render.com/v1/services/{RENDER_SERVICE_ID}/deploys",
            headers={"Authorization": f"Bearer {RENDER_API_KEY}", "Content-Type": "application/json",
                     "Accept": "application/json"},
            json={"clearCache": "do_not_clear"},
            timeout=30,
        )
        if r.status_code in (200, 201, 202):
            return ""
        return f"Render API {r.status_code}: {r.text[:200]}"
    except Exception as e:
        return f"{type(e).__name__}: {e}"


@Client.on_message(filters.command("restart") & filters.private & OWNER_F)
async def restart_cmd(client: Client, message):
    if RENDER_API_KEY and RENDER_SERVICE_ID:
        note = await message.reply_text("♻️ Requesting a redeploy from Render… the bot will be back in 1–2 minutes.")
        err = await asyncio.to_thread(_render_redeploy)
        if err:
            log.error("Render redeploy failed: %s", err)
            await note.edit_text(f"❌ <b>Redeploy failed</b>\n<code>{err}</code>", parse_mode=HTML)
        return

    await message.reply_text("♻️ Restarting the process… (set RENDER_API_KEY + RENDER_SERVICE_ID for a full redeploy)")
    await asyncio.sleep(1)
    os.execv(sys.executable, [sys.executable] + sys.argv)
