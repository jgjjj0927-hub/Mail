import time
from typing import Optional
import settings
from core import crypto

DURATION_UNITS = {
    "hours": 3600,
    "days": 86400,
    "months": 2592000,
    "years": 31536000,
    "forever": None,
}


def load_channels() -> list[dict]:
    return crypto.decrypt_from(settings.CHANNELS_FILE, [])


def save_channels(items: list[dict]) -> None:
    crypto.encrypt_to(settings.CHANNELS_FILE, items)


def add_channel(title: str, link: str, chat_id: str) -> None:
    items = load_channels()
    items.append({"title": title, "link": link, "chat_id": chat_id})
    save_channels(items)


def load_keys() -> dict:
    return crypto.decrypt_from(settings.KEYS_FILE, {})


def save_keys(data: dict) -> None:
    crypto.encrypt_to(settings.KEYS_FILE, data)


def create_key(unit: str, amount: int, created_by: int) -> str:
    if unit not in DURATION_UNITS:
        raise ValueError("Неверная единица срока")
    raw = crypto.gen_key()
    h = crypto.hash_key(raw)
    keys = load_keys()
    keys[h] = {
        "unit": unit,
        "amount": int(amount),
        "used": False,
        "used_by": None,
        "used_at": None,
        "created_by": created_by,
        "created_at": time.time(),
    }
    save_keys(keys)
    return raw


def load_subs() -> dict:
    return crypto.decrypt_from(settings.SUBS_FILE, {})


def save_subs(data: dict) -> None:
    crypto.encrypt_to(settings.SUBS_FILE, data)


def has_active_sub(user_id: int) -> bool:
    subs = load_subs()
    rec = subs.get(str(user_id))
    if not rec:
        return False
    if rec.get("until") is None:
        return True
    return rec["until"] > time.time()


def get_sub_info(user_id: int) -> Optional[dict]:
    return load_subs().get(str(user_id))


def activate_key(user_id: int, raw_key: str) -> dict:
    h = crypto.hash_key(raw_key.strip())
    keys = load_keys()
    entry = keys.get(h)
    if not entry:
        raise ValueError("Ключ не найден")
    if entry["used"]:
        raise ValueError("Ключ уже использован")

    now = time.time()
    subs = load_subs()
    current = subs.get(str(user_id), {"until": now})
    base = current["until"] if current["until"] and current["until"] > now else now

    if entry["unit"] == "forever":
        until = None
    else:
        until = base + DURATION_UNITS[entry["unit"]] * entry["amount"]

    subs[str(user_id)] = {"until": until, "activated_at": now}
    save_subs(subs)

    entry["used"] = True
    entry["used_by"] = user_id
    entry["used_at"] = now
    keys[h] = entry
    save_keys(keys)
    return subs[str(user_id)]
