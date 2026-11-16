import os
import sys
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN", "").strip()
ADMIN_IDS = [int(x.strip()) for x in os.getenv("ADMIN_IDS", "").split(",") if x.strip()]
ENC_KEY = os.getenv("ENC_KEY", "").strip()

if getattr(sys, "frozen", False):
    BASE_DIR = os.path.dirname(sys.executable)
else:
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))

DATA_DIR = os.path.join(BASE_DIR, "data")

SMTP_TIMEOUT = 30
SEND_DELAY = 1.5
MAX_ACCOUNTS_PER_BROADCAST = 10
DEFAULT_MSG_COUNT = 1
MAX_MSG_COUNT = 50

CHANNELS_FILE = os.path.join(DATA_DIR, "channels.json")
SUBS_FILE = os.path.join(DATA_DIR, "subs.enc")
KEYS_FILE = os.path.join(DATA_DIR, "keys.enc")

if not BOT_TOKEN:
    raise RuntimeError("BOT_TOKEN не задан в .env")
if not ENC_KEY:
    raise RuntimeError("ENC_KEY не задан в .env")
