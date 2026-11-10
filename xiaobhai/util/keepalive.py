import asyncio
import logging

import aiohttp

from info import PING_INTERVAL, URL


async def ping_server():
    """Pings our own /health so Render's free plan does not put the app to sleep (it sleeps after 15 min
    without incoming traffic). One reusable HTTP session, no per-ping setup cost."""
    async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=10)) as session:
        while True:
            await asyncio.sleep(PING_INTERVAL)
            try:
                async with session.get(URL + "health") as resp:
                    logging.info(f"Pinged server, status: {resp.status}")
            except Exception as e:
                logging.warning(f"Keep-alive ping failed: {e}")
