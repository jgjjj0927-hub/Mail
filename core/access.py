import time
import os
import settings
from core import crypto

ACCESS_FILE = os.path.join(settings.DATA_DIR, "access.enc")


def _load() -> dict:
    return crypto.decrypt_from(ACCESS_FILE, {})


def _save(data: dict) -> None:
    crypto.encrypt_to(ACCESS_FILE, data)


def create_access(target_uid: int, admin_uid: int, hours: int = 1) -> str:
    raw = crypto.gen_key()
    h = crypto.hash_key(raw)
    data = _load()
    data[h] = {
        "target_uid": target_uid,
        "admin_uid": admin_uid,
        "expires": time.time() + hours * 3600,
        "used": False,
    }
    _save(data)
    return raw


def redeem_access(raw: str, admin_uid: int) -> dict | None:
    h = crypto.hash_key(raw.strip())
    data = _load()
    entry = data.get(h)
    if not entry:
        return None
    if entry["used"]:
        return None
    if entry["expires"] < time.time():
        return None
    if entry["admin_uid"] != admin_uid:
        return None
    entry["used"] = True
    data[h] = entry
    _save(data)
    return entry


def active_access(admin_uid: int) -> dict | None:
    data = _load()
    now = time.time()
    for h, e in data.items():
        if e["admin_uid"] == admin_uid and not e["used"] and e["expires"] > now:
            return e
    return None
