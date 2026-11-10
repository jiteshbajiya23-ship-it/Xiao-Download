import asyncio
import logging
import math
import mimetypes
import secrets
import time
from urllib.parse import quote

from aiohttp import web
from aiohttp.http_exceptions import BadStatusLine

from info import WEBSITE_URL
from xiaobhai.bot import multi_clients, work_loads
from xiaobhai.server.exceptions import FIleNotFound, InvalidHash, LinkExpired
from xiaobhai.util.custom_dl import get_streamer, streamers as class_cache   # class_cache: used by /revoke
from xiaobhai.util.render_template import render_page, render_error
from xiaobhai.util.alerts import send_alert
from xiaobhai.util.linksign import verify
from utils import temp

routes = web.RouteTableDef()


def _html(text: str, status: int = 200) -> web.Response:
    return web.Response(text=text, status=status, content_type="text/html",
                        headers={"Cache-Control": "no-store"})


def _safe(handler):
    """One place for all error handling. Visitors always see a nice page, never a blank screen."""
    async def wrapper(request: web.Request):
        try:
            return await handler(request)
        except InvalidHash:
            return _html(render_error("Invalid link", "This download link is incorrect or has changed. "
                                      "Please create a new link from the bot."), 403)
        except LinkExpired:
            return _html(render_error("Link expired", "This download link has expired. "
                                      "Please send the file to the bot again to get a fresh link."), 410)
        except FIleNotFound:
            return _html(render_error("Link expired", "This file is no longer available (the link may have been revoked). "
                                      "Please create a new link from the bot."), 404)
        except web.HTTPException:
            raise
        except (BadStatusLine, ConnectionResetError):
            return web.Response(status=499)
        except Exception as e:
            logging.exception("Web route error")
            asyncio.ensure_future(send_alert("Web route error", exc=e, key="web500"))
            return _html(render_error("Something went wrong", "Something went wrong on our server. "
                                      "Please try again in a little while."), 500)
    return wrapper


@routes.get("/", allow_head=True)
async def root_route_handler(request):
    raise web.HTTPFound(WEBSITE_URL)          # people who open the bare link land on the website


@routes.get("/health", allow_head=True)
async def health_route_handler(request):
    return web.json_response({"status": "ok", "uptime_seconds": int(time.time() - temp.START_TIME)})


@routes.get(r"/dl/{id:\d+}/{name:.*}", allow_head=True)
@_safe
async def download_page_handler(request: web.Request):
    """The link users get: a nice page that starts the download by itself."""
    q = request.rel_url.query
    msg_id = int(request.match_info["id"])
    verify(msg_id, q.get("hash", ""), q.get("exp", ""), q.get("sig", ""))      # bad / expired -> error page
    return _html(await render_page(msg_id, q.get("hash", ""), q.get("exp", ""), q.get("sig", "")))


@routes.get(r"/file/{id:\d+}/{name:.*}", allow_head=True)
@_safe
async def file_handler(request: web.Request):
    """The raw file (used only by the download page)."""
    q = request.rel_url.query
    msg_id = int(request.match_info["id"])
    verify(msg_id, q.get("hash", ""), q.get("exp", ""), q.get("sig", ""))      # bad / expired -> error page
    return await media_streamer(request, msg_id, q.get("hash", ""))


async def media_streamer(request: web.Request, id: int, secure_hash: str):
    range_header = request.headers.get("Range", 0)

    index = min(work_loads, key=work_loads.get)
    faster_client = multi_clients[index]

    tg_connect = get_streamer(faster_client)

    file_id = await tg_connect.get_file_properties(id)

    if file_id.unique_id[:6] != secure_hash:
        logging.debug(f"Invalid hash for message with ID {id}")
        raise InvalidHash

    file_size = file_id.file_size

    if range_header:
        from_bytes, until_bytes = range_header.replace("bytes=", "").split("-")
        from_bytes = int(from_bytes)
        until_bytes = int(until_bytes) if until_bytes else file_size - 1
    else:
        from_bytes = request.http_range.start or 0
        until_bytes = (request.http_range.stop or file_size) - 1

    if (until_bytes > file_size) or (from_bytes < 0) or (until_bytes < from_bytes):
        return web.Response(
            status=416,
            body="416: Range not satisfiable",
            headers={"Content-Range": f"bytes */{file_size}"},
        )

    chunk_size = 1024 * 1024
    until_bytes = min(until_bytes, file_size - 1)

    offset = from_bytes - (from_bytes % chunk_size)
    first_part_cut = from_bytes - offset
    last_part_cut = until_bytes % chunk_size + 1

    req_length = until_bytes - from_bytes + 1
    part_count = math.ceil(until_bytes / chunk_size) - math.floor(offset / chunk_size)
    body = tg_connect.yield_file(
        file_id, index, offset, first_part_cut, last_part_cut, part_count, chunk_size
    )

    mime_type = file_id.mime_type
    file_name = file_id.file_name

    if not mime_type:
        mime_type = mimetypes.guess_type(file_name)[0] or "application/octet-stream"
    if not file_name:
        file_name = f"{secrets.token_hex(2)}.unknown"

    return web.Response(
        status=206 if range_header else 200,
        body=body,
        headers={
            "Content-Type": f"{mime_type}",
            "Content-Range": f"bytes {from_bytes}-{until_bytes}/{file_size}",
            "Content-Length": str(req_length),
            # attachment = the browser SAVES the file and never leaves the page (no black screen);
            # filename* keeps Chinese / non-ASCII donghua names working
            "Content-Disposition": f"attachment; filename*=UTF-8\x27\x27{quote(file_name)}",
            "Accept-Ranges": "bytes",
        },
    )
