import os
import config
from core import crypto


def _path() -> str:
    os.makedirs(config.DATA_DIR, exist_ok=True)
    return os.path.join(config.DATA_DIR, "accounts.json.enc")


def load_accounts() -> dict:
    return crypto.decrypt_from(_path(), {})


def save_accounts(accounts: dict) -> None:
    crypto.encrypt_to(_path(), accounts)


def add_account(owner_id: int, email: str, app_password: str) -> None:
    accs = load_accounts()
    accs[email] = {"owner_id": owner_id, "email": email, "app_password": app_password}
    save_accounts(accs)


def get_accounts(owner_id: int = None) -> dict:
    accs = load_accounts()
    if owner_id is None:
        return accs
    return {k: v for k, v in accs.items() if v["owner_id"] == owner_id}


def delete_account(email: str) -> bool:
    accs = load_accounts()
    if email in accs:
        del accs[email]
        save_accounts(accs)
        return True
    return False
