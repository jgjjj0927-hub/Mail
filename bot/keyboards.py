from aiogram.types import (
    ReplyKeyboardMarkup, KeyboardButton,
    InlineKeyboardMarkup, InlineKeyboardButton
)
from core import subscriptions


def main_panel(is_admin: bool = False, subscribed: bool = False) -> ReplyKeyboardMarkup:
    kb = []
    if not subscribed:
        kb.append([KeyboardButton(text="💎 Купить подписку")])
        kb.append([KeyboardButton(text="🔑 Активировать ключ")])
    else:
        kb.append([KeyboardButton(text="📮 Добавить свою почту")])
        kb.append([KeyboardButton(text="🗑 Удалить почту")])
        kb.append([KeyboardButton(text="📨 Начать рассылку")])
        kb.append([KeyboardButton(text="📊 Статус")])
        kb.append([KeyboardButton(text="🎫 Моя подписка")])
    if is_admin:
        kb.append([KeyboardButton(text="⚙️ Админ панель")])
    return ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True)


def admin_panel() -> ReplyKeyboardMarkup:
    kb = [
        [KeyboardButton(text="🚀 Админ рассылка")],
        [KeyboardButton(text="🔑 Генерировать ключ")],
        [KeyboardButton(text="📡 Каналы подписки")],
        [KeyboardButton(text="➕ Добавить почту")],
        [KeyboardButton(text="🗑 Удалить почту")],
        [KeyboardButton(text="🆘 Помочь юзеру")],
        [KeyboardButton(text="➕ Добавить админа")],
        [KeyboardButton(text="📊 Общая статистика")],
        [KeyboardButton(text="⬅️ Назад")],
    ]
    return ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True)


def cancel_kb() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="❌ Отмена")]],
        resize_keyboard=True
    )


def subscribe_inline() -> InlineKeyboardMarkup:
    rows = []
    for ch in subscriptions.load_channels():
        rows.append([InlineKeyboardButton(text=ch["title"], url=ch["link"])])
    rows.append([InlineKeyboardButton(text="✅ Проверить подписку", callback_data="check_sub")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def accounts_kb(accs: dict, prefix: str) -> InlineKeyboardMarkup:
    rows = [[InlineKeyboardButton(text=e, callback_data=f"{prefix}:{e}")] for e in accs]
    rows.append([InlineKeyboardButton(text="❌ Отмена", callback_data="cancel")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def msg_count_kb(prefix: str = "cnt") -> InlineKeyboardMarkup:
    row1 = [InlineKeyboardButton(text=str(n), callback_data=f"{prefix}:{n}") for n in (1, 2, 3, 5)]
    row2 = [InlineKeyboardButton(text=str(n), callback_data=f"{prefix}:{n}") for n in (7, 10, 15, 20)]
    return InlineKeyboardMarkup(inline_keyboard=[row1, row2])


def duration_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Часы", callback_data="unit:hours"),
         InlineKeyboardButton(text="Дни", callback_data="unit:days")],
        [InlineKeyboardButton(text="Месяцы", callback_data="unit:months"),
         InlineKeyboardButton(text="Годы", callback_data="unit:years")],
        [InlineKeyboardButton(text="♾ Навсегда", callback_data="unit:forever")],
    ])
