"""Signed, expiring download links.

A link carries  hash=<file hash>  exp=<unix time it dies>  sig=<HMAC of id + hash + exp>.
Nobody can change `exp` to make a link live longer, because the signature would no longer match.
"""
import hashlib
import hmac
import time

from info import LINK_EXPIRY_HOURS, LINK_SECRET
from xiaobhai.server.exceptions import InvalidHash, LinkExpired


def _sig(msg_id: int, file_hash: str, exp: int) -> str:
    raw = f"{msg_id}:{file_hash}:{exp}".encode()
    return hmac.new(LINK_SECRET.encode(), raw, hashlib.sha256).hexdigest()[:24]


def sign_query(msg_id: int, file_hash: str) -> str:
    """Query string for a brand-new link: hash + expiry + signature."""
    exp = int(time.time()) + LINK_EXPIRY_HOURS * 3600
    return f"hash={file_hash}&exp={exp}&sig={_sig(msg_id, file_hash, exp)}"


def verify(msg_id: int, file_hash: str, exp: str, sig: str) -> None:
    """Raises InvalidHash (tampered / old-style link) or LinkExpired. Returns None when the link is good."""
    try:
        exp_i = int(exp)
    except (TypeError, ValueError):
        raise LinkExpired            # links made before this update have no expiry -> treated as expired
    if not file_hash or not sig or not hmac.compare_digest(sig, _sig(msg_id, file_hash, exp_i)):
        raise InvalidHash
    if time.time() > exp_i:
        raise LinkExpired
