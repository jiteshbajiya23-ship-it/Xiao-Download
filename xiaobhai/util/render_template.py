import logging
import urllib.parse
from pathlib import Path

import jinja2

from info import (LOG_CHANNEL, URL, WEBSITE_URL, SITE_NAME, REDIRECT_AFTER_SECONDS,
                  DISCUSSION_URL, DONGHUA_URL, UPDATES_URL)
from xiaobhai.bot import StreamBot
from xiaobhai.server.exceptions import InvalidHash
from xiaobhai.util.file_properties import get_file_ids
from xiaobhai.util.human_readable import humanbytes

TEMPLATE_DIR = Path(__file__).resolve().parent.parent / "template"

# autoescape=True -> a file named "<script>..." can not inject HTML into the page
_env = jinja2.Environment(
    loader=jinja2.FileSystemLoader(str(TEMPLATE_DIR)),
    autoescape=True,
)

_COMMON = dict(site_name=SITE_NAME, website_url=WEBSITE_URL, discussion_url=DISCUSSION_URL,
               donghua_url=DONGHUA_URL, updates_url=UPDATES_URL)


def _kind(mime: str, name: str) -> str:
    mime = (mime or "").lower()
    if mime.startswith("video"):
        return "VIDEO"
    if mime.startswith("audio"):
        return "AUDIO"
    ext = name.rsplit(".", 1)[-1].upper() if "." in name else "FILE"
    return ext[:5]


async def render_page(id, secure_hash):
    file_data = await get_file_ids(StreamBot, int(LOG_CHANNEL), int(id))
    if file_data.unique_id[:6] != secure_hash:
        logging.debug(f"Invalid hash for message with ID {id}")
        raise InvalidHash

    src = urllib.parse.urljoin(
        URL, f"file/{id}/{urllib.parse.quote(file_data.file_name, safe='')}?hash={secure_hash}")

    return _env.get_template("dl.html").render(
        file_name=file_data.file_name.replace("_", " "),
        file_url=src,
        file_size=humanbytes(file_data.file_size) or "—",
        file_kind=_kind(file_data.mime_type, file_data.file_name),
        redirect_after=REDIRECT_AFTER_SECONDS,
        **_COMMON,
    )


def render_error(title: str, message: str) -> str:
    return _env.get_template("error.html").render(title=title, message=message, **_COMMON)
