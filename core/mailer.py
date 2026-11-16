import smtplib
import ssl
import time
import json
import os
import threading
import html as html_lib
import re
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.utils import formataddr
from typing import Callable, Optional
import config

_stats_lock = threading.Lock()

SMTP_MAP = {
    "gmail.com":   ("smtp.gmail.com", 587, False),
    "yandex.ru":   ("smtp.yandex.ru", 465, True),
    "yandex.com":  ("smtp.yandex.com", 465, True),
    "mail.ru":     ("smtp.mail.ru", 465, True),
    "outlook.com": ("smtp.office365.com", 587, False),
    "hotmail.com": ("smtp.office365.com", 587, False),
    "yahoo.com":   ("smtp.mail.yahoo.com", 587, False),
}


def _resolve_host(email: str):
    domain = email.split("@")[-1].lower()
    return SMTP_MAP.get(domain, (f"smtp.{domain}", 587, False))


def _stats_path() -> str:
    os.makedirs(config.DATA_DIR, exist_ok=True)
    return os.path.join(config.DATA_DIR, "stats.json")


def _load_stats() -> dict:
    p = _stats_path()
    with _stats_lock:
        if not os.path.exists(p):
            return {"sent": 0, "failed": 0, "active": False, "last": ""}
        try:
            with open(p, "r", encoding="utf-8") as f:
                data = json.load(f)
            return {
                "sent": int(data.get("sent", 0)),
                "failed": int(data.get("failed", 0)),
                "active": bool(data.get("active", False)),
                "last": data.get("last", ""),
            }
        except Exception:
            return {"sent": 0, "failed": 0, "active": False, "last": ""}


def _save_stats(stats: dict) -> None:
    p = _stats_path()
    with _stats_lock:
        tmp = p + ".tmp"
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(stats, f, ensure_ascii=False, indent=2)
        os.replace(tmp, p)


def _html_to_text(body: str) -> str:
    text = re.sub(r"<br\s*/?>", "\n", body, flags=re.I)
    text = re.sub(r"</p>", "\n\n", text, flags=re.I)
    text = re.sub(r"<[^>]+>", "", text)
    return html_lib.unescape(text).strip()


def _connect(email: str, app_password: str):
    host, port, use_ssl = _resolve_host(email)
    ctx = ssl.create_default_context()
    if use_ssl:
        server = smtplib.SMTP_SSL(host, port, timeout=config.SMTP_TIMEOUT, context=ctx)
    else:
        server = smtplib.SMTP(host, port, timeout=config.SMTP_TIMEOUT)
        server.ehlo()
        server.starttls(context=ctx)
        server.ehlo()
    server.login(email, app_password)
    return server


def validate_login(email: str, app_password: str) -> None:
    server = _connect(email, app_password)
    try:
        server.quit()
    except Exception:
        pass


def send_bulk(
    from_email: str,
    app_password: str,
    recipients: list[str],
    subject: str,
    body_html: str,
    body_text: Optional[str] = None,
    progress: Optional[Callable[[int, int], None]] = None,
) -> dict:
    stats = _load_stats()
    stats["active"] = True
    stats["last"] = time.strftime("%Y-%m-%d %H:%M:%S")
    _save_stats(stats)

    body_text = body_text or _html_to_text(body_html)
    ok, fail = 0, 0
    total = len(recipients)

    try:
        server = _connect(from_email, app_password)
    except Exception as e:
        stats["active"] = False
        _save_stats(stats)
        raise RuntimeError(f"SMTP login failed: {e}")

    for idx, rcpt in enumerate(recipients, start=1):
        msg = MIMEMultipart("alternative")
        msg["From"] = formataddr(("Stamp", from_email))
        msg["To"] = rcpt
        msg["Subject"] = subject
        msg.attach(MIMEText(body_text, "plain", "utf-8"))
        msg.attach(MIMEText(body_html, "html", "utf-8"))

        sent = False
        for attempt in range(3):
            try:
                server.sendmail(from_email, [rcpt], msg.as_string())
                sent = True
                break
            except smtplib.SMTPServerDisconnected:
                try:
                    server = _connect(from_email, app_password)
                except Exception:
                    pass
            except Exception:
                time.sleep(1 + attempt)

        if sent:
            ok += 1
            stats["sent"] += 1
        else:
            fail += 1
            stats["failed"] += 1

        _save_stats(stats)
        if progress:
            try:
                progress(idx, total)
            except Exception:
                pass
        time.sleep(config.SEND_DELAY)

    try:
        server.quit()
    except Exception:
        pass
    stats["active"] = False
    _save_stats(stats)
    return {"sent": ok, "failed": fail, "total": total}


def get_status() -> dict:
    return _load_stats()
