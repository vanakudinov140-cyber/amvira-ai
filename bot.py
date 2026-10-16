# -*- coding: utf-8 -*-

import asyncio
import logging
import os
import re
import sys
from datetime import datetime, date
from urllib.parse import urlsplit, urlunsplit
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
_TOKEN_FALLBACK = ""

TOKEN = _normalize_bot_token(os.environ.get("BOT_TOKEN", "")) or _normalize_bot_token(
    _TOKEN_FALLBACK
)
if ":" not in TOKEN or not TOKEN.split(":", 1)[0].isdigit():
    sys.exit(
        "Ошибка: токен бота не задан или выглядит некорректно.\n"
        "Задай переменную окружения BOT_TOKEN в настройках проекта Amvera "
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
NO_ENERGY_IMAGES = [
    os.path.join(BASE_DIR, "images", f"no_energy_{i}.png")
    for i in range(1, 4)
]


def no_energy_image_for_day(day=None):
    # Единая картинка в течение московского дня; последовательность 1 → 2 → 3.
    day = day or datetime.now(MSK).date()
    return NO_ENERGY_IMAGES[(day - date(2026, 10, 11)).days % 3]


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
        return "НА БЕРЕГУ 🐚"
    elif total == 1:
        return "В ПОТОКЕ 🌊"
    else:
        return "ТЫ В ГЛУБИНЕ 🧜🏼‍♀️"


def intro_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(
            text='Узнать, чем полезен бот дисциплины 🐚',
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
            text="Всё поняла! Готова погружаться 🌊",
            callback_data="ready_prime"
        )]
    ])


def main_keyboard(user_id=None):
    buttons = [
        [
            InlineKeyboardButton(text="📊 Твой прогресс", callback_data="stats"),
            InlineKeyboardButton(text="🔱 Твой рейтинг", callback_data="leaderboard")
        ],
        [
            InlineKeyboardButton(text="🧜🏼‍♀️ Я опубликовала контент", callback_data="published_content"),
            InlineKeyboardButton(text="🥺 Нет ресурса на контент", callback_data="no_energy")
        ]
    ]

    if user_id and is_admin(user_id):
        buttons.append(
            [InlineKeyboardButton(text="🔒 Админка", callback_data="admin_panel")]
        )

    return InlineKeyboardMarkup(inline_keyboard=buttons)


def admin_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="📊 Статистика", callback_data="admin_stats"),
            InlineKeyboardButton(text="📥 Excel", callback_data="admin_export")
        ],
        [
            InlineKeyboardButton(text="🧪 Тест напоминаний (только мне)", callback_data="admin_debug_reminder")
        ]
    ])


_URL_RE = re.compile(r"https?://[^\s<>()]+", re.IGNORECASE)


def extract_url(text):
    match = _URL_RE.search(text or "")
    if not match:
        return None
    return match.group(0).rstrip(".,!?;:)]}\"'")


def normalize_url(url):
    """Нормализует ссылку для защиты от повторного зачёта одной публикации."""
    try:
        parts = urlsplit((url or "").strip())
    except ValueError:
        return (url or "").strip()

    scheme = parts.scheme.lower()
    netloc = parts.netloc.lower()
    if netloc.startswith("www."):
        netloc = netloc[4:]

    path = parts.path.rstrip("/") or "/"
    query = parts.query

    # У Instagram параметры вида ?igsh=... / ?hl=... не меняют саму публикацию.
    if netloc == "instagram.com" or netloc.endswith(".instagram.com"):
        netloc = "instagram.com"
        query = ""

    return urlunsplit((scheme, netloc, path, query, ""))


def is_link(text):
    return extract_url(text) is not None


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

        await db.execute("""
        CREATE TABLE IF NOT EXISTS submitted_links (
            user_id INTEGER NOT NULL,
            url TEXT NOT NULL,
            first_seen_date TEXT NOT NULL,
            PRIMARY KEY (user_id, url)
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


async def update_submission(user_id, normalized_url):
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
        current_count = row[0] if row else 0

        cur = await db.execute(
            "SELECT total_points, streak, last_date, best_day, challenge_day FROM users WHERE user_id=?",
            (user_id,)
        )
        user_row = await cur.fetchone()
        if user_row is None:
            total, streak, last_date, best, challenge = 0, 0, None, 0, 0
        else:
            total, streak, last_date, best, challenge = user_row

        # После дневного лимита новые ссылки не засчитываются и не помечаются использованными.
        if current_count >= 2:
            return current_count, total, streak, best, challenge, "limit"

        cur = await db.execute(
            "SELECT 1 FROM submitted_links WHERE user_id=? AND url=?",
            (user_id, normalized_url)
        )
        if await cur.fetchone():
            return current_count, total, streak, best, challenge, "duplicate"

        new_count = current_count + 1
        if row:
            await db.execute(
                "UPDATE submissions SET count=? WHERE user_id=? AND date=?",
                (new_count, user_id, today)
            )
        else:
            await db.execute(
                "INSERT INTO submissions (user_id, date, count) VALUES (?, ?, ?)",
                (user_id, today, new_count)
            )

        # Ссылка считается использованной только если публикация реально была засчитана.
        await db.execute(
            "INSERT INTO submitted_links (user_id, url, first_seen_date) VALUES (?, ?, ?)",
            (user_id, normalized_url, today)
        )

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

        # Общий итог всегда равен сумме реально засчитанных дневных публикаций.
        cur = await db.execute(
            "SELECT COALESCE(SUM(count), 0) FROM submissions WHERE user_id=?",
            (user_id,)
        )
        total = (await cur.fetchone())[0]
        best = max(best, new_count)

        await db.execute("""
        UPDATE users
        SET total_points=?, streak=?, last_date=?, best_day=?, challenge_day=?
        WHERE user_id=?
        """, (total, streak, today, best, challenge, user_id))

        await db.commit()

        return new_count, total, streak, best, challenge, "counted"

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
        'Привет, girl!🧜🏼\u200d♀️🌊\n\nЭто твой БОТ ДИСЦИПЛИНЫ H2O!\n\nНа ближайшие 3 недели он станет твоим помощником в регулярности и поможет не выпадать из создания контента🩵\n\nВсё просто: после публикации каждого reels или поста отправляй сюда ссылку, а бот будет фиксировать твой прогресс и начислять жемчужины!🦪\n\n<b>Важно:</b> твой аккаунт должен быть открытым.',
        image_path=WELCOME_IMAGE,
        reply_markup=intro_keyboard()
    )


@dp.callback_query(F.data == "about_discipline_bot")
async def about_discipline_bot(callback: types.CallbackQuery):
    await callback.answer()
    await callback.message.answer('🌊 <b>БОТ ДИСЦИПЛИНЫ — ТВОЙ ДРУГ НА 3 НЕДЕЛИ ПОГРУЖЕНИЯ!</b>\n\nЧто он умеет?\n\n🫧Отслеживает твои reels и посты.\n\n🫧Фиксирует прогресс и начисляет жемчужины за опубликованный контент.\n\n🫧 Показывает, на каком уровне регулярности ты сейчас находишься:\n\n1. 🐚 НА БЕРЕГУ\n2. 🌊 В ПОТОКЕ\n3. 🧜🏼\u200d♀️ ТЫ В ГЛУБИНЕ\n\n🫧 Считает количество публикаций за день и неделю, подводит итоги.\n\n🫧 Напоминает, когда пора опубликовать новый контент.\n\n<b>Обязательно включи уведомления!</b> 🩵\n\nПусть этот бот станет твоим маленьким ежедневным ритуалом на пути к результату!', reply_markup=ready_keyboard())


@dp.callback_query(F.data == "how_level_up")
async def how_level_up(callback: types.CallbackQuery):
    await callback.answer()
    await answer_with_optional_photo(
        callback.message,
        """
Для повышения твоего уровня в игре, тебе необходимо <b><u>РЕГУЛЯРНО</u></b> публиковать контент (reels и посты) и отправлять это в <b><u>БОТ ДИСЦИПЛИНЫ</u></b>🏰

Во вкладке:
📶<b>Твой прогресс</b> — ты будешь видеть сколько единиц контента ты опубликовала и собирать <b>ЖЕМЧУЖИНЫ</b>🦪

🌟<b>Дней подряд</b>: показывает сколько дней подряд ты публикуешь контент

<b>ВАЖНО</b>: для того, чтобы быть в ПРАЙМЕ💅🏼необходимо публиковать 2 единицы контента в день (reels, посты) и собирать жемчужины!

Помни — регулярность, это важно и не забывай присылать ссылки на свои reels и посты!!
""",
        image_path=HOW_LEVEL_UP_IMAGE,
        reply_markup=confirm_ready_keyboard()
    )


@dp.callback_query(F.data == "ready_prime")
async def ready_prime(callback: types.CallbackQuery):
    await callback.answer()
    remaining = 2 - await get_today_count(callback.from_user.id)
    await callback.message.answer(
        f'<b>H2O — ЧЕЛЛЕНДЖ 🌊</b>\n\nGirl, время создавать контент!\n\nПомни: если хочешь научиться — начни, а не сравнивай себя с другими🩵\n\n🦪 На сегодня осталось: {remaining}/2',
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

    raw_url = extract_url(message.text)
    if not raw_url:
        await message.answer(f"🧐 {name}, пришли ссылку на видео 💌")
        return

    normalized_url = normalize_url(raw_url)
    count, total, streak, best, challenge, status = await update_submission(
        message.from_user.id,
        normalized_url
    )

    if status == "duplicate":
        await message.answer(
            "Эта ссылка уже была засчитана раньше 🦪\n\n"
            "Пришли ссылку на другую публикацию — повторно жемчужина за тот же контент не начисляется.",
            reply_markup=main_keyboard(message.from_user.id)
        )
        return

    if status == "limit":
        await message.answer(
            "На сегодня уже засчитано <b>2/2</b> публикации 🌊\n"
            "Новые жемчужины начнут начисляться с нового дня.",
            reply_markup=main_keyboard(message.from_user.id)
        )
        return

    await answer_with_optional_photo(
        message,
        'Ты умничка!!🩵\n\nЕщё одна публикация в копилку твоей регулярности!',
        image_path=SUCCESS_IMAGE
    )

    await asyncio.sleep(0.3)

    await message.answer(
        f"🦪Жемчужины: {total}\n\n🫧Сегодня: {count}/2\n\n"
        "Продолжай в том же духе, ты уже на шаг ближе к своей цели!",
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

    text = f"""📊<b>{name}, твой прогресс в H2O!</b>

🫧 Сегодня: {today}/2

🦪{progress_bar(today)}

🩵 Дней подряд: {streak}

🏆 Лучший день: {best}

🌊 Уровень: {get_level(today)}

🦪 Жемчужины: {total}

📅 За 7 дней: {week_total}

Girl, помни: регулярность — это не про идеальный контент каждый день, а про привычку продолжать!

Не выпадай из потока🩵"""

    await safe_send(callback.from_user.id, text, reply_markup=main_keyboard(callback.from_user.id))

# ======================
# LEADERBOARD
# ======================

@dp.callback_query(F.data == "leaderboard")
async def leaderboard(callback: types.CallbackQuery):
    await callback.answer()
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

    text = "🔱 <b>ТОП-5 САМЫХ АКТИВНЫХ GIRLS H2O!</b>\n\nНаши жемчужные лидеры за всё время!🦪\n\n"

    for i, (_uid, name, total) in enumerate(rows, start=1):
        place = {1: "🥇", 2: "🥈", 3: "🥉"}.get(i, f"{i}.")
        text += f"{place} {name} — {total} 🦪\n\n"

    if not rows:
        text += "Пока нет зафиксированных публикаций.\n\n"

    text += "Girls, горжусь вашей регулярностью!🌊\n\nА если тебя пока нет в рейтинге — всё впереди. Продолжай создавать контент, собирать жемчужины и погружаться глубже🩵"

    await safe_send(callback.from_user.id, text)

# ======================
# CALLBACKS
# ======================

@dp.callback_query(F.data == "published_content")
async def published_content(callback: types.CallbackQuery):
    await callback.answer()
    await callback.message.answer('Урааа!🌊\n\nПрисылай ссылку на свой reels или пост, будем пополнять твою коллекцию жемчужин🦪')


@dp.callback_query(F.data == "no_energy")
async def no_energy(callback: types.CallbackQuery):
    await callback.answer()
    await answer_with_optional_photo(
        callback.message,
        """Girl, понимаю тебя🩵

Не каждый день у нас есть вдохновение, энергия и желание создавать контент.

Но помни: <b>дисциплина приведёт тебя туда, куда мотивация никогда не приведёт.</b>

Не обязательно сегодня создавать шедевр!

Попробуй сделать минимум:

🫧Сними короткий reels

🫧Поделись одной мыслью

🫧Опубликуй то, что давно лежит в черновиках

Не обесценивай маленькие шаги, ведь именно из них складывается большой результат🌊

А если тебе действительно нужен отдых — разреши себе восстановиться и возвращайся в свой ритм🩵""",
        image_path=no_energy_image_for_day()
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
    if not is_admin(callback.from_user.id):
        return

    async with aiosqlite.connect(DB_NAME) as db:
        cur = await db.execute("SELECT COUNT(*) FROM users")
        users = (await cur.fetchone())[0]

    await callback.message.answer(f"👥 Пользователей: {users}")


@dp.callback_query(F.data == "admin_export")
async def export(callback: types.CallbackQuery):
    await callback.answer()
    if not is_admin(callback.from_user.id):
        return

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

    today_str = moscow_today_str()
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
            f"{challenge}/21",
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


async def send_debug_reminder_preview(target, admin_id):
    """Безопасный предпросмотр: отправляет оба варианта напоминания только админу."""
    count = await get_today_count(admin_id)
    remaining = max(0, 2 - count)

    await target.answer(
        "🧪 Запускаю безопасный тест напоминаний.\n"
        "Оба тестовых сообщения будут отправлены только вам — участницы ничего не получат."
    )

    for label, image_path in (
        ("16:00", REMINDER_16_IMAGE),
        ("20:00", REMINDER_20_IMAGE),
    ):
        text = (
            f"🧪 <b>ТЕСТ НАПОМИНАНИЯ {label}</b>\n"
            "<i>Это сообщение видит только администратор.</i>\n\n"
            "<b>H2O — ЧЕЛЛЕНДЖ 🌊</b>\n\n"
            "Girl, время создавать контент!\n\n"
            "Помни: если хочешь научиться — начни, а не сравнивай себя с другими🩵\n\n"
            f"🦪 На сегодня осталось: {remaining}/2"
        )

        if image_exists(image_path):
            await safe_send_photo(
                admin_id,
                image_path,
                text,
                reply_markup=main_keyboard(admin_id)
            )
        else:
            await safe_send(
                admin_id,
                text,
                reply_markup=main_keyboard(admin_id)
            )

    await target.answer(
        "✅ Проверка завершена. Два тестовых напоминания отправлены только вам. "
        "Массовая рассылка не запускалась."
    )


@dp.callback_query(F.data == "admin_debug_reminder")
async def admin_debug_reminder(callback: types.CallbackQuery):
    await callback.answer()
    if not is_admin(callback.from_user.id):
        return
    await send_debug_reminder_preview(callback.message, callback.from_user.id)


@dp.message(Command("debug_reminder"))
async def debug_reminder(message: types.Message):
    if not is_admin(message.from_user.id):
        await message.answer("⛔ Команда доступна только администратору.")
        return

    await send_debug_reminder_preview(message, message.from_user.id)

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
            text = f'<b>H2O — ЧЕЛЛЕНДЖ 🌊</b>\n\nGirl, время создавать контент!\n\nПомни: если хочешь научиться — начни, а не сравнивай себя с другими🩵\n\n🦪 На сегодня осталось: {remaining}/2'

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
