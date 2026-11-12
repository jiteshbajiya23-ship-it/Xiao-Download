import re
from os import environ

# .env support for local runs. On Kerit / any host just set environment variables in the panel.
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
PORT = _int('PORT', 8080)
SLEEP_THRESHOLD = _int('SLEEP_THRESHOLD', 60)
PING_INTERVAL = _int('PING_INTERVAL', 300)     # self-ping every 5 min

# Public URL of the app (required on Kerit / most free hosts)
# On Render you can leave it empty (RENDER_EXTERNAL_URL is used automatically)
URL = (environ.get('URL') or environ.get('RENDER_EXTERNAL_URL') or '').strip()
if URL and not URL.endswith('/'):
    URL += '/'
KEEP_ALIVE = bool(URL) and _bool('KEEP_ALIVE', True)

# ---------------------------------------------------------------- Admins / channels / DB
_sc = (environ.get('STORAGE_CHANNEL') or environ.get('LOG_CHANNEL') or '').strip()
if not _sc:
    raise SystemExit("❌ Missing required environment variable: STORAGE_CHANNEL")
LOG_CHANNEL = int(_sc)
STORAGE_CHANNEL = LOG_CHANNEL
ADMINS = [int(a) for a in environ.get('ADMINS', '7475888984').split() if id_pattern.search(a)]
OWNER_ID = _int('OWNER_ID', ADMINS[0] if ADMINS else 0)

DATABASE_URI = _required('DATABASE_URI')
DATABASE_NAME = environ.get('DATABASE_NAME', 'XiaoDownloadBot')

# ---------------------------------------------------------------- Branding
WEBSITE_URL = environ.get('WEBSITE_URL', 'https://xiaobhaidonghua.com')
SITE_NAME = environ.get('SITE_NAME', 'Xiao Bhai Donghua')

# ---------------------------------------------------------------- Rate limit & links
RATE_LIMIT_SECONDS = _int('RATE_LIMIT_SECONDS', 120)
REDIRECT_AFTER_SECONDS = _int('REDIRECT_AFTER_SECONDS', 0)
LINK_EXPIRY_HOURS = _int('LINK_EXPIRY_HOURS', 2)
LINK_SECRET = environ.get('LINK_SECRET', '').strip() or BOT_TOKEN

# ---------------------------------------------------------------- Force sub
FORCE_SUB_CHANNELS = [
    c.strip() for c in environ.get('FORCE_SUB_CHANNELS', '').split() if c.strip()
]

# ---------------------------------------------------------------- Optional shortener
SHORTLINK_URL = environ.get('SHORTLINK_URL', '').strip()
SHORTLINK_API = environ.get('SHORTLINK_API', '').strip()

# ---------------------------------------------------------------- Start image
START_IMAGE = environ.get('START_IMAGE', '').strip()

# ---------------------------------------------------------------- Optional Render redeploy (still works if you use Render)
RENDER_API_KEY = environ.get('RENDER_API_KEY', '').strip()
RENDER_SERVICE_ID = environ.get('RENDER_SERVICE_ID', '').strip()
