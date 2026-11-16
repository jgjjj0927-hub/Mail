import os
import json
import base64
import hashlib
import binascii
from cryptography.fernet import Fernet
import settings


def _fernet() -> Fernet:
    try:
        raw = base64.urlsafe_b64decode(settings.ENC_KEY)
    except (binascii.Error, ValueError) as e:
        raise ValueError(f"ENC_KEY не base64: {e}")
    if len(raw) != 32:
        raise ValueError("ENC_KEY должен быть 32-байтным")
    return Fernet(settings.ENC_KEY.encode())


def encrypt_to(path: str, data) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    raw = json.dumps(data, ensure_ascii=False, indent=2).encode("utf-8")
    tmp = path + ".tmp"
    with open(tmp, "wb") as f:
        f.write(_fernet().encrypt(raw))
    os.replace(tmp, path)


def decrypt_from(path: str, default):
    if not os.path.exists(path):
        return default
    try:
        with open(path, "rb") as f:
            raw = _fernet().decrypt(f.read())
        return json.loads(raw.decode("utf-8"))
    except Exception:
        return default


def hash_key(key: str) -> str:
    return hashlib.sha256(key.encode("utf-8")).hexdigest()


def gen_key() -> str:
    return base64.urlsafe_b64encode(os.urandom(18)).decode("ascii").rstrip("=")
