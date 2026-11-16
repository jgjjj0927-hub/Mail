from aiogram import Bot
from aiogram.exceptions import TelegramBadRequest

from core import subscriptions


async def check_all_channels(bot: Bot, user_id: int) -> list[dict]:
    """Возвращает список каналов, на которые юзер НЕ подписан."""
    missing = []
    for ch in subscriptions.load_channels():
        try:
            member = await bot.get_chat_member(chat_id=ch["chat_id"], user_id=user_id)
            status = member.status
            if status in ("left", "kicked"):
                missing.append(ch)
        except TelegramBadRequest:
            missing.append(ch)
        except Exception:
            missing.append(ch)
    return missing
