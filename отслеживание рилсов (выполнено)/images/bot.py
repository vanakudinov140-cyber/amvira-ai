# -*- coding: utf-8 -*-

import asyncio
import logging
import os
import sys
from datetime import datetime, date

from aiogram import Bot, Dispatcher, types, F
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters import CommandStart
from aiogram.enums import ParseMode
from aiogram.client.default import DefaultBotProperties
from aiogram.exceptions import (
    TelegramNetworkError,
    TelegramRetryAfter,
    TelegramUnauthorizedError,
)

import aiosqlite
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from openpyxl import Workbook

# ======================
# CONFIG
# ======================

def _normalize_bot_token(raw: str) -> str:
    if not raw:
        return ""
    return (
        raw.strip()
        .strip("\ufeff")
        .replace("\r", "")
        .replace("\n", "")
        .replace(" ", "")
    )


# Токен можно задать переменной окружения BOT_TOKEN (удобнее и безопаснее, чем править файл).
_TOKEN_FALLBACK = "6743374559:AAHFV3kF-wBY1Qk2z19c5JVlsxfJN9v3UiQ"

TOKEN = _normalize_bot_token(os.environ.get("BOT_TOKEN", "")) or _normalize_bot_token(
    _TOKEN_FALLBACK
)
if ":" not in TOKEN or not TOKEN.split(":", 1)[0].isdigit():
    sys.exit(
        "Ошибка: токен бота не задан или выглядит некорректно.\n"
        "Задай переменную окружения BOT_TOKEN или исправь _TOKEN_FALLBACK в bot.py "
        "(без пробелов и переносов строк вокруг токена)."
    )

ADMIN_IDS = [1299192895, 493452217]  # 👈 свои ID

logging.basicConfig(level=logging.INFO)

bot = Bot(
    token=TOKEN,
    default=DefaultBotProperties(parse_mode=ParseMode.HTML)
)

dp = Dispatcher()
scheduler = AsyncIOScheduler()

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
# На Amvera постоянное хранилище обычно смонтировано в /data (см. amvera.yaml).
_data_env = os.environ.get("DATA_DIR", "").strip()
if _data_env:
    DATA_DIR = _data_env
elif os.path.isdir("/data"):
    DATA_DIR = "/data"
else:
    DATA_DIR = BASE_DIR

DB_NAME = os.path.join(DATA_DIR, "bot.db")
WELCOME_IMAGE = os.path.join(BASE_DIR, "images", "welcome.jpg")
SUCCESS_IMAGE = os.path.join(BASE_DIR, "images", "success.jpg")
NO_ENERGY_IMAGE = os.path.join(BASE_DIR, "images", "no_energy.jpg")
HOW_LEVEL_UP_IMAGE = os.path.join(BASE_DIR, "images", "how_level_up.jpg")

# ======================
# SAFE SEND (анти-флуд)
# ======================

async def safe_send(chat_id, text, **kwargs):
    while True:
        try:
            return await bot.send_message(chat_id, text, **kwargs)
        except TelegramRetryAfter as e:
            await asyncio.sleep(e.retry_after)

# ======================
# HELPERS
# ======================

def is_admin(user_id):
    return user_id in ADMIN_IDS

def progress_bar(value, max_value=3):
    """Как в макете заказчика: 🗝️ + 10 позиций (заполненные — 🟣, пустые — ⚪)."""
    value = min(value, max_value)
    filled = int((value / max_value) * 10)
    return "🗝️" + "🟣" * filled + "⚪" * (10 - filled)

def get_level(total):
    if total < 5:
        return "ЛЕНТЯЙКА 💌"
    elif total < 15:
        return "ПОЧТИ В ИГРЕ 🤏🏼"
    elif total < 30:
        return "В ИГРЕ 🦸🏼‍♀️"
    else:
        return "ТЫ В ПРАЙМЕ 🏰🕯️"

def intro_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(
            text="Узнать, чем полезен БОТ ДИСЦИПЛИНЫ📔",
            callback_data="about_discipline_bot"
        )]
    ])

def ready_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(
            text="🏰как повышается мой уровень?",
            callback_data="how_level_up"
        )]
    ])


def confirm_ready_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(
            text="все поняла! готова быть в прайме⭐️⭐️⭐️",
            callback_data="ready_prime"
        )]
    ])

def main_keyboard(user_id=None):
    buttons = [
        [
            InlineKeyboardButton(text="📊 Прогресс", callback_data="stats"),
            InlineKeyboardButton(text="🏆 Рейтинг", callback_data="leaderboard")
        ],
        [
            InlineKeyboardButton(text="я опубликовала пост/reels🦸🏼‍♀️", callback_data="published_content"),
            InlineKeyboardButton(text="😴 Нет ресурса", callback_data="no_energy")
        ]
    ]

    if user_id and is_admin(user_id):
        buttons.append(
            [InlineKeyboardButton(text="🔐 Админка", callback_data="admin_panel")]
        )

    return InlineKeyboardMarkup(inline_keyboard=buttons)

def admin_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="📊 Статистика", callback_data="admin_stats"),
            InlineKeyboardButton(text="📥 Excel", callback_data="admin_export")
        ]
    ])

def is_link(text):
    return "http://" in text or "https://" in text


def image_exists(path):
    return bool(path) and os.path.isfile(path)


async def answer_with_optional_photo(message: types.Message, text: str, image_path: str | None = None, **kwargs):
    if image_exists(image_path):
        await message.answer_photo(
            photo=types.FSInputFile(image_path),
            caption=text,
            **kwargs
        )
        return
    if image_path:
        logging.warning("Картинка не найдена: %s", image_path)
    await message.answer(text, **kwargs)

# ======================
# DATABASE
# ======================

async def init_db():
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute("""
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            total_points INTEGER DEFAULT 0,
            streak INTEGER DEFAULT 0,
            last_date TEXT,
            best_day INTEGER DEFAULT 0,
            challenge_day INTEGER DEFAULT 0
        )
        """)

        await db.execute("""
        CREATE TABLE IF NOT EXISTS submissions (
            user_id INTEGER,
            date TEXT,
            count INTEGER,
            PRIMARY KEY (user_id, date)
        )
        """)
        await db.commit()

# ======================
# CORE LOGIC
# ======================

async def get_today_count(user_id):
    today = str(date.today())
    async with aiosqlite.connect(DB_NAME) as db:
        cur = await db.execute(
            "SELECT count FROM submissions WHERE user_id=? AND date=?",
            (user_id, today)
        )
        row = await cur.fetchone()
        return row[0] if row else 0

async def update_submission(user_id):
    today = str(date.today())

    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute(
            "INSERT OR IGNORE INTO users (user_id) VALUES (?)",
            (user_id,)
        )

        cur = await db.execute(
            "SELECT count FROM submissions WHERE user_id=? AND date=?",
            (user_id, today)
        )
        row = await cur.fetchone()

        if row:
            new_count = row[0] + 1
        else:
            new_count = 1
            await db.execute(
                "INSERT OR IGNORE INTO submissions VALUES (?, ?, ?)",
                (user_id, today, 0)
            )

        await db.execute(
            "UPDATE submissions SET count=? WHERE user_id=? AND date=?",
            (new_count, user_id, today)
        )

        cur = await db.execute(
            "SELECT total_points, streak, last_date, best_day, challenge_day FROM users WHERE user_id=?",
            (user_id,)
        )
        user_row = await cur.fetchone()
        if user_row is None:
            total, streak, last_date, best, challenge = 0, 0, None, 0, 0
        else:
            total, streak, last_date, best, challenge = user_row

        if last_date != today:
            if last_date:
                last = datetime.strptime(last_date, "%Y-%m-%d").date()
                if (date.today() - last).days == 1:
                    streak += 1
                    challenge += 1
                else:
                    streak = 1
                    challenge = 1
            else:
                streak = 1
                challenge = 1

        total += 1
        best = max(best, new_count)

        await db.execute("""
        UPDATE users
        SET total_points=?, streak=?, last_date=?, best_day=?, challenge_day=?
        WHERE user_id=?
        """, (total, streak, today, best, challenge, user_id))

        await db.commit()

        return new_count, total, streak, best, challenge

# ======================
# START
# ======================

@dp.message(CommandStart())
async def start(message: types.Message):
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute(
            "INSERT OR IGNORE INTO users (user_id) VALUES (?)",
            (message.from_user.id,)
        )
        await db.commit()

    await answer_with_optional_photo(
        message,
        """
<b><u>Привет!🏰🩰</u></b>
Это <b>бот дисциплины <u>UGC PRIME</u></b>!
Он будет помогать тебе держать <b>регулярность</b> и доводить до результата через <b>систему</b>!🗝️
Тебе необходимо после публикации <u>поста/reels</u> отправлять ссылку в этот бот👇🏼
<b><u>Важно:</u></b> <u>аккаунт должен быть открытым!</u>📔
""",
        image_path=WELCOME_IMAGE,
        reply_markup=intro_keyboard()
    )

@dp.callback_query(F.data == "about_discipline_bot")
async def about_discipline_bot(callback: types.CallbackQuery):
    await callback.answer()
    await callback.message.answer("""
⭐️<b><u>БОТ ДИСЦИПЛИНЫ — ТВОЙ ДРУГ НА 2 МЕСЯЦА!</u></b>
<b>Теперь он будет:</b>
🗝️отслеживать твои reels и посты
🗝️фиксировать твой прогресс
🗝️подсказывать, на каком уровне регулярности ты находишься сейчас:
1. <b>ЛЕНТЯЙКА💌</b>
2. <b>ПОЧТИ В ИГРЕ🤏🏼</b>
3. <b>В ИГРЕ🦸🏼‍♀️</b>
4. <b>ТЫ В ПРАЙМЕ🏰🕯️</b>
🗝️считает количество опубликованного контента в день и за неделю — подводит итоги недели
🗝️отправляет напоминание о том, что необходимо опубликовать reels/пост
<b><u>Обязательно:</u></b> поставь <b>уведомление</b> на этот бот — это твой <b><u>личный трекер</u></b>⭐️⭐️⭐️
""", reply_markup=ready_keyboard())

@dp.callback_query(F.data == "how_level_up")
async def how_level_up(callback: types.CallbackQuery):
    await callback.answer()
    await answer_with_optional_photo(
        callback.message,
        """
Для повышения твоего уровня в игре, тебе необходимо <b><u>РЕГУЛЯРНО</u></b> публиковать контент (reels и посты) и отправлять это в <b><u>БОТ ДИСЦИПЛИНЫ</u></b>🏰

Во вкладке:
📶<b>Твой прогресс</b> — ты будешь видеть сколько единиц контента ты опубликовала и собирать <b>КЛЮЧИКИ</b>🗝️

🌟<b>Дней подряд</b>: показывает сколько дней подряд ты публикуешь контент

<b>ВАЖНО</b>: для того, чтобы быть в ПРАЙМЕ💅🏼 необходимо публиковать 2 единицы контента в день (reels, посты) и собирать ключики!

Помни — регулярность, это важно и не забывай присылать ссылки на свои reels и посты!!
""",
        image_path=HOW_LEVEL_UP_IMAGE,
        reply_markup=confirm_ready_keyboard()
    )

@dp.callback_query(F.data == "ready_prime")
async def ready_prime(callback: types.CallbackQuery):
    await callback.answer()
    await callback.message.answer(
        "<b><u>Ты в системе!</u></b> Нажимай кнопку ниже после публикации 👇🏼",
        reply_markup=main_keyboard(callback.from_user.id)
    )

# ======================
# MESSAGE (ссылка)
# ======================

@dp.message(F.text)
async def handle(message: types.Message):
    name = message.from_user.first_name

    if not is_link(message.text):
        await message.answer(f"🧐 {name}, пришли ссылку на видео 💌")
        return

    count, total, streak, best, challenge = await update_submission(message.from_user.id)

    await answer_with_optional_photo(
        message,
        "<b><u>Ты умничка!!🤍</u></b>",
        image_path=SUCCESS_IMAGE
    )

    await asyncio.sleep(0.3)

    await message.answer(
        f"🗝️ Ключи: <b>{total}</b>",
        reply_markup=main_keyboard(message.from_user.id)
    )

# ======================
# STATS
# ======================

@dp.callback_query(F.data == "stats")
async def stats(callback: types.CallbackQuery):
    await callback.answer()
    name = callback.from_user.first_name

    async with aiosqlite.connect(DB_NAME) as db:
        cur = await db.execute(
            "SELECT total_points, streak, best_day, challenge_day FROM users WHERE user_id=?",
            (callback.from_user.id,)
        )
        total, streak, best, challenge = await cur.fetchone()
        cur = await db.execute(
            """
            SELECT COALESCE(SUM(count), 0)
            FROM submissions
            WHERE user_id=? AND date >= date('now', '-6 day')
            """,
            (callback.from_user.id,)
        )
        week_total = (await cur.fetchone())[0]

    today = await get_today_count(callback.from_user.id)

    text = f"""
📊 <b><u>{name}, твой день</u></b>

<b>Сегодня:</b> {today}/3
{progress_bar(today)}

🔥 <b>Дней подряд:</b> {streak}
🏆 <b>Лучший день:</b> {best}
🏰 <b>Уровень: {get_level(total)}</b>
🗝️ <b>Ключи:</b> {total}
📅 <b>За 7 дней:</b> {week_total}

Ты уже в системе
<b><u>Не выпадай</u></b> 🤍
"""

    await safe_send(callback.from_user.id, text, reply_markup=main_keyboard(callback.from_user.id))

# ======================
# LEADERBOARD
# ======================

@dp.callback_query(F.data == "leaderboard")
async def leaderboard(callback: types.CallbackQuery):
    await callback.answer()
    async with aiosqlite.connect(DB_NAME) as db:
        cur = await db.execute("""
        SELECT user_id, SUM(count)
        FROM submissions
        GROUP BY user_id
        ORDER BY SUM(count) DESC
        LIMIT 5
        """)
        rows = await cur.fetchall()

    text = (
        "🏆 <b>Топ участниц</b>\n"
        "<u>рейтинг: клубнички на ключики</u> 🗝️\n\n"
    )
    medals = ["🥇", "🥈", "🥉", "4️⃣", "5️⃣"]

    for i, (uid, total) in enumerate(rows):
        try:
            user = await bot.get_chat(uid)
            name = user.first_name
        except:
            name = "Участница"

        text += f"{medals[i]} <b>{name}</b> — {total} 🗝️\n"

    text += "\n🔥 Продолжай — ты тоже можешь быть здесь"

    await safe_send(callback.from_user.id, text)

# ======================
# CALLBACKS
# ======================

@dp.callback_query(F.data == "published_content")
async def published_content(callback: types.CallbackQuery):
    await callback.answer()
    await callback.message.answer("⭐️ <b><u>Отлично, присылай ссылку</u></b>")

@dp.callback_query(F.data == "no_energy")
async def no_energy(callback: types.CallbackQuery):
    await callback.answer()
    name = callback.from_user.first_name
    await answer_with_optional_photo(
        callback.message,
        f"""
<b>🤍 {name}, я понимаю</b>

Но давай <b>честно</b>

Иногда это просто <u>откладывание</u>

Сделай минимум:
— <b>коротко</b>
— <b>просто</b>
— <b>без идеала</b>

<b><u>И ты уже выиграла сегодня</u></b>
""",
        image_path=NO_ENERGY_IMAGE
    )

# ======================
# ADMIN
# ======================

@dp.callback_query(F.data == "admin_panel")
async def admin_panel(callback: types.CallbackQuery):
    await callback.answer()
    if not is_admin(callback.from_user.id):
        return

    await callback.message.answer("🔐 Админ-панель", reply_markup=admin_keyboard())

@dp.callback_query(F.data == "admin_stats")
async def admin_stats(callback: types.CallbackQuery):
    await callback.answer()
    async with aiosqlite.connect(DB_NAME) as db:
        cur = await db.execute("SELECT COUNT(*) FROM users")
        users = (await cur.fetchone())[0]

    await callback.message.answer(f"👥 Пользователей: {users}")

@dp.callback_query(F.data == "admin_export")
async def export(callback: types.CallbackQuery):
    await callback.answer()
    wb = Workbook()
    ws = wb.active
    ws.title = "Статистика"

    # Заголовки (красиво)
    headers = [
        "User ID",
        "Имя",
        "Очки",
        "Дни подряд",
        "Лучший день",
        "Челлендж (день)",
        "Уровень"
    ]
    ws.append(headers)

    async with aiosqlite.connect(DB_NAME) as db:
        cur = await db.execute("""
        SELECT user_id, total_points, streak, best_day, challenge_day
        FROM users
        """)
        rows = await cur.fetchall()

    for user_id, points, streak, best, challenge in rows:
        try:
            user = await bot.get_chat(user_id)
            name = user.first_name
        except:
            name = "Неизвестно"

        # уровень
        if points < 5:
            level = "Новичок"
        elif points < 15:
            level = "В потоке"
        else:
            level = "В ПРАЙМЕ"

        ws.append([
            user_id,
            name,
            points,
            streak,
            best,
            f"{challenge}/7",
            level
        ])

        await asyncio.sleep(0.05)  # анти-флуд

    # Немного “красоты” — ширина колонок
    ws.column_dimensions["A"].width = 15
    ws.column_dimensions["B"].width = 20
    ws.column_dimensions["C"].width = 10
    ws.column_dimensions["D"].width = 15
    ws.column_dimensions["E"].width = 15
    ws.column_dimensions["F"].width = 18
    ws.column_dimensions["G"].width = 15

    file = os.path.join(DATA_DIR, "ugc_prime_stats.xlsx")
    wb.save(file)

    await callback.message.answer_document(types.FSInputFile(file))
# ======================
# REMINDER
# ======================

async def reminder():
    async with aiosqlite.connect(DB_NAME) as db:
        cur = await db.execute("SELECT user_id FROM users")
        users = await cur.fetchall()

    for (uid,) in users:
        count = await get_today_count(uid)

        if count == 0:
            try:
                user = await bot.get_chat(uid)
                name = user.first_name
            except:
                name = "ты"

            await safe_send(
                uid,
                f"""
⏰ <b>{name}, я рядом</b>

Ты сегодня ещё не выложила контент

Не жди идеального момента

Сделай один шаг 🤍
""",
                reply_markup=main_keyboard(uid)
            )

            await asyncio.sleep(0.2)

# ======================
# MAIN
# ======================

async def main():
    await init_db()

    try:
        me = await bot.get_me()
        logging.info("Авторизация OK: @%s", me.username)
    except TelegramUnauthorizedError:
        logging.error(
            "Telegram отклонил токен (401). Скопируй новый токен из BotFather без пробелов, "
            "или задай переменную окружения BOT_TOKEN и перезапусти скрипт."
        )
        sys.exit(1)
    except TelegramNetworkError as e:
        logging.error("Нет сети до api.telegram.org: %s", e)
        sys.exit(1)

    scheduler.add_job(reminder, "cron", hour=16)
    scheduler.add_job(reminder, "cron", hour=20)

    scheduler.start()

    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())