import re
from os import environ

# .env file support (local run). On Render just set env variables in the dashboard.
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

id_pattern = re.compile(r'^-?\d+$')


def _required(name):
    value = environ.get(name, '').strip()
    if not value:
        raise SystemExit(f"❌ Missing required environment variable: {name}")
    return value


def _bool(name, default=False):
    return environ.get(name, str(default)).strip().lower() in ('true', '1', 'yes', 'on')


def _int(name, default):
    try:
        return int(environ.get(name, str(default)).strip())
    except ValueError:
        return default


# ---------------------------------------------------------------- Bot
SESSION = environ.get('SESSION', 'XiaoDownloadBot')
API_ID = int(_required('API_ID'))
API_HASH = _required('API_HASH')
BOT_TOKEN = _required('BOT_TOKEN')

# ---------------------------------------------------------------- Web server
PORT = _int('PORT', 8080)                      # Render sets this automatically
SLEEP_THRESHOLD = _int('SLEEP_THRESHOLD', 60)
PING_INTERVAL = _int('PING_INTERVAL', 300)     # 5 min (Render free sleeps after 15 min idle, so this leaves a safe margin)

# Public URL of the app. On Render, RENDER_EXTERNAL_URL is filled in automatically.
URL = (environ.get('URL') or environ.get('RENDER_EXTERNAL_URL') or '').strip()
if URL and not URL.endswith('/'):
    URL += '/'
KEEP_ALIVE = bool(URL) and _bool('KEEP_ALIVE', True)

# ---------------------------------------------------------------- Admins / channels / DB
# STORAGE_CHANNEL = private channel where (1) every file is copied (the download link streams from it)
# and (2) all bot logs are posted (new users, /start, links, errors). LOG_CHANNEL is the old name.
_sc = (environ.get('STORAGE_CHANNEL') or environ.get('LOG_CHANNEL') or '').strip()
if not _sc:
    raise SystemExit("❌ Missing required environment variable: STORAGE_CHANNEL")
LOG_CHANNEL = int(_sc)          # internal name used everywhere in the code
STORAGE_CHANNEL = LOG_CHANNEL
ADMINS = [int(a) for a in environ.get('ADMINS', '7475888984').split() if id_pattern.search(a)]
OWNER_ID = _int('OWNER_ID', ADMINS[0] if ADMINS else 0)

DATABASE_URI = _required('DATABASE_URI')
DATABASE_NAME = environ.get('DATABASE_NAME', 'XiaoDownloadBot')

# ---------------------------------------------------------------- Branding
WEBSITE_URL = environ.get('WEBSITE_URL', 'https://xiaobhaidonghua.com')
SITE_NAME = environ.get('SITE_NAME', 'Xiao Bhai Donghua')

START_IMAGE = environ.get('START_IMAGE', 'https://imgyx.pages.dev/vfoEY').strip()
DISCUSSION_URL = environ.get('DISCUSSION_URL', 'https://t.me/ongoingdonghuachat')
DONGHUA_URL = environ.get('DONGHUA_URL', 'https://t.me/donghuagalaxy1')
UPDATES_URL = environ.get('UPDATES_URL', 'https://t.me/xiao_botz')
CUSTOM_BOT_URL = environ.get('CUSTOM_BOT_URL', 'https://t.me/Xiao_bhai')

# ---------------------------------------------------------------- Rules
# Every normal user can make ONE link per RATE_LIMIT_SECONDS. Admins are exempt.
RATE_LIMIT_SECONDS = _int('RATE_LIMIT_SECONDS', 120)

# Download page: 0 = stay on the nice download page (recommended).
# N > 0 = after the download starts, send the visitor to WEBSITE_URL after N seconds.
REDIRECT_AFTER_SECONDS = _int('REDIRECT_AFTER_SECONDS', 0)

# ---------------------------------------------------------------- Force Subscribe (multi)
# Space separated. Channel IDs (-100...) or @usernames. The bot must be ADMIN in each channel.
# Example: FORCE_SUB_CHANNELS=@ongoingdonghuachat @donghuagalaxy1 @xiao_botz
FORCE_SUB_CHANNELS = [int(c) if id_pattern.search(c) else c.lstrip('@')
                      for c in environ.get('FORCE_SUB_CHANNELS', '').split()]
# Optional join links in the SAME order (only needed for private channels)
FORCE_SUB_LINKS = environ.get('FORCE_SUB_LINKS', '').split()

# ---------------------------------------------------------------- Shortlink (optional, default OFF)
SHORTLINK = _bool('SHORTLINK', False)
SHORTLINK_URL = environ.get('SHORTLINK_URL', 'api.shareus.io')
SHORTLINK_API = environ.get('SHORTLINK_API', '')

# ---------------------------------------------------------------- Render redeploy for /restart (optional)
RENDER_API_KEY = environ.get('RENDER_API_KEY', '').strip()
RENDER_SERVICE_ID = environ.get('RENDER_SERVICE_ID', '').strip()
