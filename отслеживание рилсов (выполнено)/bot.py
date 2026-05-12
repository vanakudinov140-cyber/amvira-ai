# -*- coding: utf-8 -*-

import asyncio
import logging
import os
import sys
from datetime import datetime, date
from zoneinfo import ZoneInfo

from aiogram import Bot, Dispatcher, types, F
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters import Command, CommandStart
from aiogram.enums import ParseMode
from aiogram.client.default import DefaultBotProperties
from aiogram.exceptions import (
    TelegramBadRequest,
    TelegramForbiddenError,
    TelegramNetworkError,
    TelegramRetryAfter,
    TelegramUnauthorizedError,
)

import aiosqlite
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
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
_TOKEN_FALLBACK = "8712874861:AAGwJvhASgN9pkVZeXxLRzW2WbwTuAO3WWs"

TOKEN = _normalize_bot_token(os.environ.get("BOT_TOKEN", "")) or _normalize_bot_token(
    _TOKEN_FALLBACK
)
if ":" not in TOKEN or not TOKEN.split(":", 1)[0].isdigit():
    sys.exit(
        "Ошибка: токен бота не задан или выглядит некорректно.\n"
        "Задай переменную окружения BOT_TOKEN или исправь _TOKEN_FALLBACK в bot.py "
        "(без пробелов и переносов строк вокруг токена)."
    )

ADMIN_IDS = [1299192895, 493452217, 929467677]  # 👈 свои ID

logging.basicConfig(level=logging.INFO)

bot = Bot(
    token=TOKEN,
    default=DefaultBotProperties(parse_mode=ParseMode.HTML)
)

dp = Dispatcher()
scheduler = AsyncIOScheduler(timezone=ZoneInfo("Europe/Moscow"))
MSK = ZoneInfo("Europe/Moscow")


def moscow_today_str() -> str:
    return datetime.now(MSK).date().isoformat()

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
REMINDER_16_IMAGE = os.path.join(BASE_DIR, "images", "reminder_16.jpg")
REMINDER_20_IMAGE = os.path.join(BASE_DIR, "images", "reminder_20.jpg")

def _pick_existing_path(candidates: list[str]) -> str | None:
    return next((p for p in candidates if p and os.path.isfile(p)), None)


_image_base_dirs = [
    BASE_DIR,
    os.getcwd(),
    os.path.dirname(BASE_DIR),
    "/app",
]
_how_level_up_names = [
    "how_level_up_v2.jpg",
    "how_level_up_v2.jpeg",
    "how_level_up_v2.png",
    "how_level_up.jpg",
    "how_level_up.jpeg",
    "how_level_up.png",
    "IMG_6013.jpg",
    "IMG_6013.jpeg",
    "IMG_6013.png",
]
_how_level_up_candidates = []
for _base in _image_base_dirs:
    _images_dir = os.path.join(_base, "images")
    for _name in _how_level_up_names:
        _how_level_up_candidates.append(os.path.join(_images_dir, _name))

HOW_LEVEL_UP_IMAGE = _pick_existing_path(_how_level_up_candidates) or _pick_existing_path([WELCOME_IMAGE])
logging.info(
    "Image paths: BASE_DIR=%s, CWD=%s, HOW_LEVEL_UP_IMAGE=%s, EXISTS=%s",
    BASE_DIR,
    os.getcwd(),
    HOW_LEVEL_UP_IMAGE,
    os.path.isfile(HOW_LEVEL_UP_IMAGE) if HOW_LEVEL_UP_IMAGE else False,
)

# ======================
# SAFE SEND (анти-флуд)
# ======================

async def safe_send(chat_id, text, **kwargs):
    while True:
        try:
            return await bot.send_message(chat_id, text, **kwargs)
        except TelegramRetryAfter as e:
            await asyncio.sleep(e.retry_after)
        except (TelegramForbiddenError, TelegramUnauthorizedError) as e:
            logging.info("Skip send_message to user %s: %s", chat_id, e)
            return None
        except TelegramBadRequest as e:
            logging.warning("Bad request for send_message to %s: %s", chat_id, e)
            return None
        except TelegramNetworkError as e:
            logging.warning("Network error in send_message to %s: %s", chat_id, e)
            await asyncio.sleep(1)


async def safe_send_photo(chat_id, photo_path, caption, **kwargs):
    while True:
        try:
            return await bot.send_photo(
                chat_id=chat_id,
                photo=types.FSInputFile(photo_path),
                caption=caption,
                **kwargs
            )
        except TelegramRetryAfter as e:
            await asyncio.sleep(e.retry_after)
        except (TelegramForbiddenError, TelegramUnauthorizedError) as e:
            logging.info("Skip send_photo to user %s: %s", chat_id, e)
            return None
        except TelegramBadRequest as e:
            logging.warning("Bad request for send_photo to %s: %s", chat_id, e)
            return None
        except TelegramNetworkError as e:
            logging.warning("Network error in send_photo to %s: %s", chat_id, e)
            await asyncio.sleep(1)

# ======================
# HELPERS
# ======================

def is_admin(user_id):
    return user_id in ADMIN_IDS

def progress_bar(value, max_value=2):
    """Дневной индикатор: красные кружки меняются на белые."""
    value = max(0, min(int(value), max_value))
    return "⚪" * value + "🔴" * (max_value - value)

def get_level(total):
    if total <= 0:
        return "ЛЕНТЯЙКА 💌"
    elif total == 1:
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
            InlineKeyboardButton(text="📶Твой прогресс", callback_data="stats"),
            InlineKeyboardButton(text="🔱Твой рейтинг", callback_data="leaderboard")
        ],
        [
            InlineKeyboardButton(text="🏰Я опубликовала контент", callback_data="published_content"),
            InlineKeyboardButton(text="🥺Нет ресурса на контент", callback_data="no_energy")
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
        ],
        [
            InlineKeyboardButton(text="🧪 Проверка напоминаний", callback_data="admin_debug_reminder")
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


async def safe_callback_answer(callback: types.CallbackQuery):
    try:
        await callback.answer()
    except TelegramBadRequest as e:
        # Нажатие по слишком старой inline-кнопке: игнорируем без traceback.
        logging.info("Skip stale callback answer: %s", e)

# ======================
# DATABASE
# ======================

async def init_db():
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute("""
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            first_name TEXT,
            total_points INTEGER DEFAULT 0,
            streak INTEGER DEFAULT 0,
            last_date TEXT,
            best_day INTEGER DEFAULT 0,
            challenge_day INTEGER DEFAULT 0
        )
        """)
        try:
            await db.execute("ALTER TABLE users ADD COLUMN first_name TEXT")
        except Exception:
            pass

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
    today = moscow_today_str()
    async with aiosqlite.connect(DB_NAME) as db:
        cur = await db.execute(
            "SELECT count FROM submissions WHERE user_id=? AND date=?",
            (user_id, today)
        )
        row = await cur.fetchone()
        return row[0] if row else 0

async def update_submission(user_id):
    today = moscow_today_str()

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
            # В день засчитываем максимум 2 публикации.
            new_count = min(row[0] + 1, 2)
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
                if (datetime.now(MSK).date() - last).days == 1:
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
            "INSERT OR IGNORE INTO users (user_id, first_name) VALUES (?, ?)",
            (message.from_user.id, message.from_user.first_name)
        )
        await db.execute(
            "UPDATE users SET first_name=? WHERE user_id=?",
            (message.from_user.first_name, message.from_user.id)
        )
        await db.commit()

    await answer_with_optional_photo(
        message,
        """
Привет!🏰🩰
Это бот дисциплины <b>UGC PRIME</b>!

<i>Он будет помогать тебе держать регулярность и доводить до результата через систему!🗝️</i>

<b>ТВОЯ ЗАДАЧА:</b> <u>после публикации поста/reels отправлять ссылку на опубликованный контент в этот бот!</u>

Важно: аккаунт должен быть <b>открытым!</b>
📔 чтобы бот мог фиксировать твои публикации!
""",
        image_path=WELCOME_IMAGE,
        reply_markup=intro_keyboard()
    )

@dp.callback_query(F.data == "about_discipline_bot")
async def about_discipline_bot(callback: types.CallbackQuery):
    await safe_callback_answer(callback)
    await callback.message.answer("""
⭐️<b>БОТ ДИСЦИПЛИНЫ — ТВОЙ ДРУГ НА 2 МЕСЯЦА!</b>
<u>Теперь он автоматически:</u>

🗝️отслеживает твои reels и посты
🗝️фиксирует твой прогресс
🗝️подсказывает, на каком уровне регулярности ты находишься сейчас:

1. <b>ЛЕНТЯЙКА💌</b>
2. <b>В ИГРЕ🦸🏼‍♀️</b>
3. <b>ТЫ В ПРАЙМЕ🏰🕯️</b>

🗝️считает количество опубликованного контента в день и за неделю — подводит итоги недели
🗝️отправляет напоминание о том, что сейчас необходимо опубликовать reels/пост
🗝️определяет ТОП-5 регулярных учениц за всё время

<b><u>Обязательно</u></b>: поставь уведомление на этот бот — это твой личный трекер⭐️⭐️⭐
""", reply_markup=ready_keyboard())

@dp.callback_query(F.data == "how_level_up")
async def how_level_up(callback: types.CallbackQuery):
    await safe_callback_answer(callback)
    await answer_with_optional_photo(
        callback.message,
        """
Для повышения твоего уровня в игре, тебе необходимо <b><u>РЕГУЛЯРНО</u></b> публиковать контент (reels и посты) и отправлять это в <b><u>БОТ ДИСЦИПЛИНЫ</u></b>🏰

Во вкладке:
📶<b>Твой прогресс</b> — ты будешь видеть сколько единиц контента ты опубликовала и собирать <b>КЛЮЧИКИ</b>🗝️

🌟<b>Дней подряд</b>: показывает сколько дней подряд ты публикуешь контент

<b>ВАЖНО</b>: для того, чтобы быть в ПРАЙМЕ💅🏼необходимо публиковать 2 единицы контента в день (reels, посты) и собирать ключики!

Помни — регулярность, это важно и не забывай присылать ссылки на свои reels и посты!!
""",
        image_path=HOW_LEVEL_UP_IMAGE,
        reply_markup=confirm_ready_keyboard()
    )


@dp.callback_query(F.data == "ready_prime")
async def ready_prime(callback: types.CallbackQuery):
    await safe_callback_answer(callback)
    await callback.message.answer(
        """<b>Пункты нашего меню🏰:</b>

📶Твой прогресс  — поможет тебе отслеживать твою активность и уровень твоей дисциплины

🔱Твой рейтинг — покажет на каком месте рейтинга топ-5 дисциплины находишься среди всех учениц на обучении за все время

🏰Я опубликовала контент — используй эту кнопку, для того чтобы зафиксировать свою публикацию

🥹Нет ресурса на контент  — отмечай, когда у тебя нет ресурса и получай мотивашку""",
        reply_markup=main_keyboard(callback.from_user.id)
    )

# ======================
# MESSAGE (ссылка)
# ======================

@dp.message(F.text & ~F.text.startswith("/"))
async def handle(message: types.Message):
    name = message.from_user.first_name

    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute(
            "INSERT OR IGNORE INTO users (user_id, first_name) VALUES (?, ?)",
            (message.from_user.id, name)
        )
        await db.execute(
            "UPDATE users SET first_name=? WHERE user_id=?",
            (name, message.from_user.id)
        )
        await db.commit()

    if not is_link(message.text):
        await message.answer(f"🧐 {name}, пришли ссылку на видео 💌")
        return

    before_count = await get_today_count(message.from_user.id)
    count, total, streak, best, challenge = await update_submission(message.from_user.id)
    counted_now = count > before_count

    await answer_with_optional_photo(
        message,
        "<u>Ты умничка!!🤍</u>",
        image_path=SUCCESS_IMAGE
    )

    await asyncio.sleep(0.3)

    if counted_now:
        await message.answer(
            f"🗝️ Ключи: <b>{total}</b>\nСегодня: <b>{count}/2</b>",
            reply_markup=main_keyboard(message.from_user.id)
        )
    else:
        await message.answer(
            "На сегодня уже засчитано <b>2/2</b> публикации 🏰\n"
            "Новые ключики начнут начисляться с нового дня.",
            reply_markup=main_keyboard(message.from_user.id)
        )

# ======================
# STATS
# ======================

@dp.callback_query(F.data == "stats")
async def stats(callback: types.CallbackQuery):
    await safe_callback_answer(callback)
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
📶<b><u>{name}, твой день:</u></b>

<b>Сегодня:</b> {today}/2
🗝️:  {progress_bar(today)}
🗝️Ключи: <b>{total}</b>

🏰<b>Уровень:</b> {get_level(today)}
📓<b>Всего публикаций за 7 дней:</b> {week_total}
🌟<b>Дней подряд:</b> {streak}

Ты уже в игре, но <b><u>не выпадай</u></b>🤍
"""

    await safe_send(callback.from_user.id, text, reply_markup=main_keyboard(callback.from_user.id))

# ======================
# LEADERBOARD
# ======================

@dp.callback_query(F.data == "leaderboard")
async def leaderboard(callback: types.CallbackQuery):
    await safe_callback_answer(callback)
    async with aiosqlite.connect(DB_NAME) as db:
        cur = await db.execute("""
        SELECT
            s.user_id,
            COALESCE(NULLIF(TRIM(u.first_name), ''), 'Участница') AS display_name,
            SUM(s.count) AS total_count
        FROM submissions s
        LEFT JOIN users u ON u.user_id = s.user_id
        GROUP BY s.user_id, display_name
        ORDER BY total_count DESC
        LIMIT 5
        """)
        rows = await cur.fetchall()

    text = "🔱<b>Топ-5 ПРАЙМОВЫХ результатов за всё время!</b>\n\n"

    for i, (_uid, name, total) in enumerate(rows, start=1):
        text += f"{i} место: <b>{name}</b> — {total}\n"

    if not rows:
        text += "Пока нет зафиксированных публикаций.\n"

    text += "\n<u>Поздравляем учениц!🗝️⭐️</u>\nПродолжай — ты тоже можешь быть здесь!"

    await safe_send(callback.from_user.id, text)

# ======================
# CALLBACKS
# ======================

@dp.callback_query(F.data == "published_content")
async def published_content(callback: types.CallbackQuery):
    await safe_callback_answer(callback)
    await callback.message.answer("Отлично, присылай ссылку⭐️")

@dp.callback_query(F.data == "no_energy")
async def no_energy(callback: types.CallbackQuery):
    await safe_callback_answer(callback)
    name = callback.from_user.first_name
    await answer_with_optional_photo(
        callback.message,
        f"""
<b>{name}, я рядом 🤍</b>

И правда понимаю тебя
Но иногда мы просто прячемся в «потом»

<b>Давай сегодня бережно к себе:</b>
— совсем немного
— без усложнений
— без идеальной картинки

Этого уже хватит!
<u>Ты уже молодец ✨</u>
""",
        image_path=NO_ENERGY_IMAGE
    )

# ======================
# ADMIN
# ======================

@dp.callback_query(F.data == "admin_panel")
async def admin_panel(callback: types.CallbackQuery):
    await safe_callback_answer(callback)
    if not is_admin(callback.from_user.id):
        return

    await callback.message.answer("🔐 Админ-панель", reply_markup=admin_keyboard())

@dp.callback_query(F.data == "admin_stats")
async def admin_stats(callback: types.CallbackQuery):
    await safe_callback_answer(callback)
    async with aiosqlite.connect(DB_NAME) as db:
        cur = await db.execute("SELECT COUNT(*) FROM users")
        users = (await cur.fetchone())[0]

    await callback.message.answer(f"👥 Пользователей: {users}")

@dp.callback_query(F.data == "admin_export")
async def export(callback: types.CallbackQuery):
    await safe_callback_answer(callback)
    wb = Workbook()
    ws = wb.active
    ws.title = "Статистика"

    headers = [
        "User ID",
        "Имя",
        "Сегодня (шт)",
        "За 7 дней (шт)",
        "Всего публикаций",
        "Дни подряд",
        "Лучший день",
        "Челлендж (день)",
        "Последняя активность",
        "Уровень сегодня"
    ]
    ws.append(headers)

    today_str = str(date.today())
    async with aiosqlite.connect(DB_NAME) as db:
        cur = await db.execute("""
        SELECT
            u.user_id,
            COALESCE(NULLIF(TRIM(u.first_name), ''), 'Неизвестно') AS name,
            COALESCE(u.total_points, 0) AS total_points,
            COALESCE(u.streak, 0) AS streak,
            COALESCE(u.best_day, 0) AS best_day,
            COALESCE(u.challenge_day, 0) AS challenge_day,
            COALESCE(u.last_date, '') AS last_date,
            COALESCE(SUM(CASE WHEN s.date = ? THEN s.count ELSE 0 END), 0) AS today_count,
            COALESCE(SUM(CASE WHEN s.date >= date('now', '-6 day') THEN s.count ELSE 0 END), 0) AS week_total
        FROM users u
        LEFT JOIN submissions s ON s.user_id = u.user_id
        GROUP BY
            u.user_id, name, total_points, streak, best_day, challenge_day, last_date
        ORDER BY total_points DESC, streak DESC
        """, (today_str,))
        rows = await cur.fetchall()

    for (
        user_id,
        name,
        total_points,
        streak,
        best,
        challenge,
        last_date,
        today_count,
        week_total
    ) in rows:
        level = get_level(today_count)

        ws.append([
            user_id,
            name,
            today_count,
            week_total,
            total_points,
            streak,
            best,
            f"{challenge}/7",
            last_date or "-",
            level
        ])

        await asyncio.sleep(0.05)  # анти-флуд

    ws.column_dimensions["A"].width = 15
    ws.column_dimensions["B"].width = 24
    ws.column_dimensions["C"].width = 14
    ws.column_dimensions["D"].width = 16
    ws.column_dimensions["E"].width = 18
    ws.column_dimensions["F"].width = 14
    ws.column_dimensions["G"].width = 14
    ws.column_dimensions["H"].width = 16
    ws.column_dimensions["I"].width = 18
    ws.column_dimensions["J"].width = 20

    file = os.path.join(DATA_DIR, "ugc_prime_stats.xlsx")
    wb.save(file)

    await callback.message.answer_document(types.FSInputFile(file))


async def send_debug_reminder_report(target):
    await target.answer("Запускаю ручную проверку напоминаний (16:00 и 20:00)...")
    stats_16 = await run_reminder(REMINDER_16_IMAGE, "reminder_16")
    stats_20 = await run_reminder(REMINDER_20_IMAGE, "reminder_20")

    report = (
        "🧪 <b>debug_reminder</b>\n\n"
        f"📌 День: {moscow_today_str()}\n\n"
        f"<b>reminder_16</b>\n"
        f"• пользователей в БД: {stats_16['total_users']}\n"
        f"• подходящих (count < 2): {stats_16['eligible_users']}\n"
        f"• отправлено: {stats_16['sent']}\n"
        f"• пропущено (уже 2/2): {stats_16['already_done']}\n"
        f"• не отправлено (block/bad request): {stats_16['not_sent']}\n"
        f"• ошибок: {stats_16['errors']}\n\n"
        f"<b>reminder_20</b>\n"
        f"• пользователей в БД: {stats_20['total_users']}\n"
        f"• подходящих (count < 2): {stats_20['eligible_users']}\n"
        f"• отправлено: {stats_20['sent']}\n"
        f"• пропущено (уже 2/2): {stats_20['already_done']}\n"
        f"• не отправлено (block/bad request): {stats_20['not_sent']}\n"
        f"• ошибок: {stats_20['errors']}"
    )
    await target.answer(report)


@dp.callback_query(F.data == "admin_debug_reminder")
async def admin_debug_reminder(callback: types.CallbackQuery):
    await safe_callback_answer(callback)
    if not is_admin(callback.from_user.id):
        return
    await send_debug_reminder_report(callback.message)


@dp.message(Command("debug_reminder"))
async def debug_reminder(message: types.Message):
    if not is_admin(message.from_user.id):
        await message.answer("⛔ Команда доступна только администратору.")
        return

    await send_debug_reminder_report(message)

# ======================
# REMINDER
# ======================

async def run_reminder(image_path: str, label: str):
    async with aiosqlite.connect(DB_NAME) as db:
        cur = await db.execute("SELECT user_id FROM users")
        users = await cur.fetchall()

    stats = {
        "total_users": len(users),
        "eligible_users": 0,
        "sent": 0,
        "already_done": 0,
        "not_sent": 0,
        "errors": 0,
    }

    logging.info("%s: старт, пользователей в БД=%s, день=%s", label, len(users), moscow_today_str())

    for (uid,) in users:
        try:
            count = await get_today_count(uid)
            if count >= 2:
                stats["already_done"] += 1
                continue

            stats["eligible_users"] += 1
            remaining = 2 - count
            text = f"время выложить контент!!🌟\nНа сегодня осталось: {remaining}/2"

            if image_exists(image_path):
                result = await safe_send_photo(
                    uid,
                    image_path,
                    text,
                    reply_markup=main_keyboard(uid)
                )
            else:
                result = await safe_send(
                    uid,
                    text,
                    reply_markup=main_keyboard(uid)
                )

            if result is None:
                stats["not_sent"] += 1
            else:
                stats["sent"] += 1

            await asyncio.sleep(0.2)
        except Exception as e:
            stats["errors"] += 1
            logging.exception("Ошибка в %s для user_id=%s: %s", label, uid, e)

    logging.info("%s: завершено, stats=%s", label, stats)
    return stats


async def reminder_16():
    await run_reminder(REMINDER_16_IMAGE, "reminder_16")


async def reminder_20():
    await run_reminder(REMINDER_20_IMAGE, "reminder_20")

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

    # Явный часовой пояс + запас на задержку цикла событий.
    trigger_16 = CronTrigger(hour=16, minute=0, timezone=MSK)
    trigger_20 = CronTrigger(hour=20, minute=0, timezone=MSK)
    scheduler.add_job(
        reminder_16,
        trigger_16,
        id="reminder_16",
        replace_existing=True,
        misfire_grace_time=3600,
    )
    scheduler.add_job(
        reminder_20,
        trigger_20,
        id="reminder_20",
        replace_existing=True,
        misfire_grace_time=3600,
    )

    scheduler.start()
    for job in scheduler.get_jobs():
        logging.info(
            "Запланировано: id=%s next_run=%s",
            job.id,
            getattr(job, "next_run_time", None),
        )

    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())