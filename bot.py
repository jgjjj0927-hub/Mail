import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import asyncio
import json
import threading
import time
from typing import Optional

from aiogram import Bot, Dispatcher, F
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import Message, CallbackQuery

import settings
from core import accounts, mailer, templates, subscriptions, channel_check
from bot.keyboards import (
    main_panel, admin_panel, cancel_kb, accounts_kb,
    msg_count_kb, duration_kb, subscribe_inline
)

bot = Bot(token=settings.BOT_TOKEN)
dp = Dispatcher()
MAIN_LOOP: Optional[asyncio.AbstractEventLoop] = None


def is_admin(uid: int) -> bool:
    return uid in load_admins()


def load_admins() -> set[int]:
    p = os.path.join(settings.DATA_DIR, "admins.json")
    ids = set(settings.ADMIN_IDS)
    if os.path.exists(p):
        try:
            with open(p, "r", encoding="utf-8") as f:
                ids |= set(json.load(f))
        except Exception:
            pass
    return ids


def save_admins(ids: set[int]) -> None:
    os.makedirs(settings.DATA_DIR, exist_ok=True)
    with open(os.path.join(settings.DATA_DIR, "admins.json"), "w", encoding="utf-8") as f:
        json.dump(sorted(ids), f)


def notify(chat_id: int, text: str) -> None:
    if MAIN_LOOP is None:
        return
    asyncio.run_coroutine_threadsafe(
        bot.send_message(chat_id, text, reply_markup=main_panel(
            is_admin(chat_id), subscriptions.has_active_sub(chat_id)
        )),
        MAIN_LOOP,
    )


async def gate_subscription(msg_or_cb) -> bool:
    uid = msg_or_cb.from_user.id
    if subscriptions.has_active_sub(uid):
        return True
    await bot.send_message(
        uid,
        "💎 Для использования бота нужна подписка.\n"
        "Подпишись на каналы ниже и активируй ключ.",
        reply_markup=subscribe_inline()
    )
    return False


class UserAdd(StatesGroup):
    email = State()
    app_pass = State()


class UserBC(StatesGroup):
    account = State()
    subject = State()
    body = State()
    recipients = State()
    count = State()


class ActivateKey(StatesGroup):
    value = State()


class AdminAddMail(StatesGroup):
    owner = State()
    email = State()
    app_pass = State()


class AdminAddAdmin(StatesGroup):
    value = State()


class AdminAddChannel(StatesGroup):
    title = State()
    link = State()
    chat_id = State()


class AdminGenKey(StatesGroup):
    unit = State()
    amount = State()


@dp.message(CommandStart())
async def start(msg: Message):
    uid = msg.from_user.id
    if not subscriptions.has_active_sub(uid):
        missing = await channel_check.check_all_channels(bot, uid)
        if missing:
            await msg.answer(
                "👋 Привет, это stamp рассылка.\n"
                "Подпишись на каналы ниже и нажми «Проверить подписку».",
                reply_markup=subscribe_inline()
            )
            return
        await msg.answer(
            "✅ Подписка на каналы подтверждена.\n"
            "Активируй ключ доступа.",
            reply_markup=main_panel(is_admin(uid), False)
        )
        return
    await msg.answer(
        "👋 Привет, это stamp рассылка.",
        reply_markup=main_panel(is_admin(uid), True)
    )


@dp.callback_query(F.data == "check_sub")
async def check_sub_cb(cb: CallbackQuery):
    uid = cb.from_user.id
    missing = await channel_check.check_all_channels(bot, uid)
    if missing:
        await cb.answer("Ты ещё не подписан.", show_alert=True)
        return
    await cb.answer("✅ Подписка подтверждена!")
    await cb.message.edit_text("✅ Подписка подтверждена.")
    await bot.send_message(uid, "Главное меню:",
                           reply_markup=main_panel(is_admin(uid), subscriptions.has_active_sub(uid)))


@dp.message(F.text == "🔑 Активировать ключ")
async def activate_start(msg: Message, state: FSMContext):
    await state.set_state(ActivateKey.value)
    await msg.answer("Пришли ключ доступа:", reply_markup=cancel_kb())


@dp.message(ActivateKey.value)
async def activate_key(msg: Message, state: FSMContext):
    if msg.text == "❌ Отмена":
        await state.clear()
        await msg.answer("Отменено.", reply_markup=main_panel(
            is_admin(msg.from_user.id), subscriptions.has_active_sub(msg.from_user.id)))
        return
    try:
        info = subscriptions.activate_key(msg.from_user.id, msg.text)
    except ValueError as e:
        await msg.answer(f"❌ {e}")
        return
    await state.clear()
    until = "навсегда" if info["until"] is None else time.strftime(
        "%Y-%m-%d %H:%M", time.localtime(info["until"]))
    await msg.answer(f"✅ Ключ активирован. До: {until}",
                     reply_markup=main_panel(is_admin(msg.from_user.id), True))


@dp.message(F.text == "🎫 Моя подписка")
async def my_sub(msg: Message):
    info = subscriptions.get_sub_info(msg.from_user.id)
    if not info:
        await msg.answer("Подписки нет.")
        return
    until = "навсегда" if info["until"] is None else time.strftime(
        "%Y-%m-%d %H:%M", time.localtime(info["until"]))
    await msg.answer(f"🎫 Подписка активна до: {until}")


@dp.message(F.text == "📮 Добавить свою почту")
async def user_add_start(msg: Message, state: FSMContext):
    if not await gate_subscription(msg):
        return
    await state.set_state(UserAdd.email)
    await msg.answer("Введи email:", reply_markup=cancel_kb())


@dp.message(UserAdd.email)
async def user_add_email(msg: Message, state: FSMContext):
    if msg.text == "❌ Отмена":
        await state.clear()
        await msg.answer("Отменено.", reply_markup=main_panel(
            is_admin(msg.from_user.id), subscriptions.has_active_sub(msg.from_user.id)))
        return
    if "@" not in msg.text:
        await msg.answer("Не email. Ещё раз:")
        return
    await state.update_data(email=msg.text.strip())
    await state.set_state(UserAdd.app_pass)
    await msg.answer("Код приложения:", reply_markup=cancel_kb())


@dp.message(UserAdd.app_pass)
async def user_add_pass(msg: Message, state: FSMContext):
    if msg.text == "❌ Отмена":
        await state.clear()
        await msg.answer("Отменено.", reply_markup=main_panel(
            is_admin(msg.from_user.id), subscriptions.has_active_sub(msg.from_user.id)))
        return
    data = await state.get_data()
    accounts.add_account(msg.from_user.id, data["email"], msg.text.strip())
    await state.clear()
    await msg.answer("✅ Почта добавлена.", reply_markup=main_panel(
        is_admin(msg.from_user.id), subscriptions.has_active_sub(msg.from_user.id)))


@dp.message(F.text == "📨 Начать рассылку")
async def user_bc_start(msg: Message, state: FSMContext):
    if not await gate_subscription(msg):
        return
    accs = accounts.get_accounts(msg.from_user.id)
    if not accs:
        await msg.answer("Сначала добавь почту.")
        return
    await state.set_state(UserBC.account)
    await msg.answer("Выбери почту:", reply_markup=accounts_kb(accs, "ubc"))


@dp.callback_query(F.data.startswith("ubc:"))
async def user_bc_pick(cb: CallbackQuery, state: FSMContext):
    email = cb.data.split(":", 1)[1]
    await state.update_data(account=email)
    await state.set_state(UserBC.subject)
    await cb.message.edit_text(f"Почта: {email}\nВведи тему:")
    await cb.answer()


@dp.message(UserBC.subject)
async def user_bc_subject(msg: Message, state: FSMContext):
    if msg.text == "❌ Отмена":
        await state.clear()
        await msg.answer("Отменено.", reply_markup=main_panel(
            is_admin(msg.from_user.id), subscriptions.has_active_sub(msg.from_user.id)))
        return
    await state.update_data(subject=msg.text.strip())
    await state.set_state(UserBC.body)
    await msg.answer("Текст письма:", reply_markup=cancel_kb())


@dp.message(UserBC.body)
async def user_bc_body(msg: Message, state: FSMContext):
    if msg.text == "❌ Отмена":
        await state.clear()
        await msg.answer("Отменено.", reply_markup=main_panel(
            is_admin(msg.from_user.id), subscriptions.has_active_sub(msg.from_user.id)))
        return
    await state.update_data(body=msg.text.strip())
    await state.set_state(UserBC.recipients)
    await msg.answer("Получатели (.txt или через запятую):", reply_markup=cancel_kb())


async def _collect_recipients(msg: Message) -> list[str]:
    if msg.document:
        if not msg.document.file_name.endswith(".txt"):
            return []
        file = await bot.get_file(msg.document.file_id)
        local = os.path.join(settings.DATA_DIR, f"rcpt_{msg.from_user.id}.txt")
        await bot.download_file(file.file_path, local)
        with open(local, "r", encoding="utf-8") as f:
            return [l.strip() for l in f if "@" in l]
    if msg.text:
        return [x for x in msg.text.replace(",", " ").split() if "@" in x]
    return []


@dp.message(UserBC.recipients)
async def user_bc_recipients(msg: Message, state: FSMContext):
    if msg.text == "❌ Отмена":
        await state.clear()
        await msg.answer("Отменено.", reply_markup=main_panel(
            is_admin(msg.from_user.id), subscriptions.has_active_sub(msg.from_user.id)))
        return
    rcpts = await _collect_recipients(msg)
    if not rcpts:
        await msg.answer("Не вижу адресов. Ещё раз:")
        return
    await state.update_data(recipients=rcpts)
    await state.set_state(UserBC.count)
    await msg.answer(f"Адресов: {len(rcpts)}. Сколько сообщений каждому?",
                     reply_markup=msg_count_kb("cnt"))


@dp.callback_query(F.data.startswith("cnt:"))
async def user_bc_count(cb: CallbackQuery, state: FSMContext):
    n = int(cb.data.split(":", 1)[1])
    data = await state.get_data()
    await state.clear()
    await cb.message.edit_text(f"🚀 Старт: {len(data['recipients'])} адресов × {n}")
    await cb.answer()
    _start_broadcast(cb.from_user.id, data["account"], data["subject"],
                     data["body"], data["recipients"], n)


@dp.message(F.text == "⚙️ Админ панель")
async def admin_open(msg: Message):
    if not is_admin(msg.from_user.id):
        return
    await msg.answer("Админ панель:", reply_markup=admin_panel())


@dp.message(F.text == "⬅️ Назад")
async def admin_back(msg: Message):
    await msg.answer("Меню.", reply_markup=main_panel(
        is_admin(msg.from_user.id), subscriptions.has_active_sub(msg.from_user.id)))


@dp.message(F.text == "📊 Общая статистика")
async def admin_stats(msg: Message):
    if not is_admin(msg.from_user.id):
        return
    st = mailer.get_status()
    accs = accounts.get_accounts()
    subs = subscriptions.load_subs()
    await msg.answer(
        f"📊 Статистика\nАккаунтов: {len(accs)}\nПодписок: {len(subs)}\n"
        f"Отправлено: {st['sent']}\nОшибок: {st['failed']}")


@dp.message(F.text == "➕ Добавить админа")
async def admin_add_admin(msg: Message, state: FSMContext):
    if not is_admin(msg.from_user.id):
        return
    await state.set_state(AdminAddAdmin.value)
    await msg.answer("ID нового админа:", reply_markup=cancel_kb())


@dp.message(AdminAddAdmin.value)
async def admin_add_admin_value(msg: Message, state: FSMContext):
    if msg.text == "❌ Отмена":
        await state.clear()
        await msg.answer("Отменено.", reply_markup=admin_panel())
        return
    try:
        uid = int(msg.text.strip())
    except ValueError:
        await msg.answer("Числовой ID.")
        return
    ids = load_admins()
    ids.add(uid)
    save_admins(ids)
    await state.clear()
    await msg.answer(f"✅ {uid} админ.", reply_markup=admin_panel())


@dp.message(F.text == "➕ Добавить почту")
async def admin_add_mail(msg: Message, state: FSMContext):
    if not is_admin(msg.from_user.id):
        return
    await state.set_state(AdminAddMail.owner)
    await msg.answer("ID владельца (0 для системного):", reply_markup=cancel_kb())


@dp.message(AdminAddMail.owner)
async def admin_mail_owner(msg: Message, state: FSMContext):
    if msg.text == "❌ Отмена":
        await state.clear()
        await msg.answer("Отменено.", reply_markup=admin_panel())
        return
    try:
        uid = int(msg.text.strip())
    except ValueError:
        await msg.answer("Числовой ID.")
        return
    await state.update_data(owner=uid)
    await state.set_state(AdminAddMail.email)
    await msg.answer("Email:", reply_markup=cancel_kb())


@dp.message(AdminAddMail.email)
async def admin_mail_email(msg: Message, state: FSMContext):
    if msg.text == "❌ Отмена":
        await state.clear()
        await msg.answer("Отменено.", reply_markup=admin_panel())
        return
    if "@" not in msg.text:
        await msg.answer("Не email.")
        return
    await state.update_data(email=msg.text.strip())
    await state.set_state(AdminAddMail.app_pass)
    await msg.answer("Код приложения:", reply_markup=cancel_kb())


@dp.message(AdminAddMail.app_pass)
async def admin_mail_pass(msg: Message, state: FSMContext):
    if msg.text == "❌ Отмена":
        await state.clear()
        await msg.answer("Отменено.", reply_markup=admin_panel())
        return
    data = await state.get_data()
    accounts.add_account(data["owner"], data["email"], msg.text.strip())
    await state.clear()
    await msg.answer("✅ Почта добавлена.", reply_markup=admin_panel())


@dp.message(F.text == "📡 Каналы подписки")
async def admin_channels(msg: Message, state: FSMContext):
    if not is_admin(msg.from_user.id):
        return
    chans = subscriptions.load_channels()
    lines = [f"• {c['title']} — {c['chat_id']}" for c in chans] or ["(пусто)"]
    await state.set_state(AdminAddChannel.title)
    await msg.answer(
        "Текущие каналы:\n" + "\n".join(lines) +
        "\n\nВведи название нового канала (или ❌ Отмена):",
        reply_markup=cancel_kb()
    )


@dp.message(AdminAddChannel.title)
async def admin_ch_title(msg: Message, state: FSMContext):
    if msg.text == "❌ Отмена":
        await state.clear()
        await msg.answer("Отменено.", reply_markup=admin_panel())
        return
    await state.update_data(title=msg.text.strip())
    await state.set_state(AdminAddChannel.link)
    await msg.answer("Ссылка (https://t.me/...):", reply_markup=cancel_kb())


@dp.message(AdminAddChannel.link)
async def admin_ch_link(msg: Message, state: FSMContext):
    if msg.text == "❌ Отмена":
        await state.clear()
        await msg.answer("Отменено.", reply_markup=admin_panel())
        return
    await state.update_data(link=msg.text.strip())
    await state.set_state(AdminAddChannel.chat_id)
    await msg.answer("ID канала (-100...):", reply_markup=cancel_kb())


@dp.message(AdminAddChannel.chat_id)
async def admin_ch_id(msg: Message, state: FSMContext):
    if msg.text == "❌ Отмена":
        await state.clear()
        await msg.answer("Отменено.", reply_markup=admin_panel())
        return
    data = await state.get_data()
    subscriptions.add_channel(data["title"], data["link"], msg.text.strip())
    await state.clear()
    await msg.answer("✅ Канал добавлен.", reply_markup=admin_panel())


@dp.message(F.text == "🔑 Генерировать ключ")
async def admin_gen_start(msg: Message, state: FSMContext):
    if not is_admin(msg.from_user.id):
        return
    await state.set_state(AdminGenKey.unit)
    await msg.answer("Выбери срок:", reply_markup=duration_kb())


@dp.callback_query(F.data.startswith("unit:"))
async def admin_gen_unit(cb: CallbackQuery, state: FSMContext):
    unit = cb.data.split(":", 1)[1]
    await state.update_data(unit=unit)
    if unit == "forever":
        raw = subscriptions.create_key("forever", 1, cb.from_user.id)
        await state.clear()
        await cb.message.edit_text(f"✅ Ключ навсегда:\n`{raw}`", parse_mode="Markdown")
        await cb.answer()
        return
    await state.set_state(AdminGenKey.amount)
    await cb.message.edit_text(f"Срок: {unit}. Сколько единиц? (число)")
    await cb.answer()


@dp.message(AdminGenKey.amount)
async def admin_gen_amount(msg: Message, state: FSMContext):
    if msg.text == "❌ Отмена":
        await state.clear()
        await msg.answer("Отменено.", reply_markup=admin_panel())
        return
    try:
        amount = int(msg.text.strip())
        if amount <= 0:
            raise ValueError
    except ValueError:
        await msg.answer("Положительное число.")
        return
    data = await state.get_data()
    raw = subscriptions.create_key(data["unit"], amount, msg.from_user.id)
    await state.clear()
    await msg.answer(f"✅ Ключ выдан:\n`{raw}`", parse_mode="Markdown",
                     reply_markup=admin_panel())


def _start_broadcast(chat_id: int, account_email: str, subject: str,
                     body: str, recipients: list[str], count: int):
    def worker():
        accs = accounts.get_accounts()
        acc = accs.get(account_email)
        if not acc:
            notify(chat_id, "❌ Почта не найдена.")
            return
        total_sent = 0
        total_failed = 0
        for i in range(count):
            try:
                res = mailer.send_bulk(
                    from_email=acc["email"],
                    app_password=acc["app_password"],
                    recipients=recipients,
                    subject=subject,
                    body_html=templates.render(body),
                )
                total_sent += res["sent"]
                total_failed += res["failed"]
            except Exception as e:
                notify(chat_id, f"❌ Ошибка: {e}")
                return
            if i < count - 1:
                time.sleep(settings.SEND_DELAY)
        notify(chat_id, f"✅ Готово.\nОтправлено: {total_sent}\nОшибок: {total_failed}")
    threading.Thread(target=worker, daemon=True).start()


async def main():
    global MAIN_LOOP
    MAIN_LOOP = asyncio.get_running_loop()
    print("Stamp bot started")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
