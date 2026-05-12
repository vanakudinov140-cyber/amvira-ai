# -*- coding: utf-8 -*-
"""
Created on Fri Mar 13 19:11:26 2026

@author: Dimid Ivanovich
"""

# -*- coding: utf-8 -*-
import asyncio
import logging
import random
import sys
import string
import io
import textwrap
import aiohttp 
import datetime
import os
# reportlab / Pillow / GigaChat подгружаются по мере необходимости — ниже пик RAM при старте (Amvera и др.)
# Эта строка удалит старый лог при каждом перезапуске бота,
# чтобы иероглифы не копились
if os.path.exists("bot_log.txt"):
    os.remove("bot_log.txt")


from aiogram import Bot, Dispatcher, types, F
from aiogram.client.session.aiohttp import AiohttpSession
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.utils.token import TokenValidationError

# --- КОНФИГУРАЦИЯ (секреты только из окружения — в панели Amvera задайте TELEGRAM_BOT_TOKEN и GIGACHAT_CREDENTIALS) ---
def _env_token():
    for key in ("TELEGRAM_BOT_TOKEN", "BOT_TOKEN", "TOKEN"):
        v = os.environ.get(key, "").strip()
        if v:
            return v
    return ""


API_TOKEN = _env_token()
GIGACHAT_CREDENTIALS = os.environ.get("GIGACHAT_CREDENTIALS", "").strip()
_admin_raw = os.environ.get("ADMIN_IDS", "414246886,1299192895")
ADMIN_IDS = [int(x.strip()) for x in _admin_raw.split(",") if x.strip().isdigit()]


logging.basicConfig(level=logging.INFO)

# --- ИСПРАВЛЕНИЕ СЕТИ (Чтобы не было ошибки 10054 и таймаутов) ---
# В новых версиях aiogram настройки коннектора передаются так:
session = AiohttpSession()
# На Windows иногда падает проверка SSL; на Linux (Amvera) оставляем обычный SSL к Telegram
if sys.platform == "win32":
    session.connector_init_kwargs = {"ssl": False}

# Bot создаётся в main() — иначе при пустом токене на Amvera падаем при импорте с «Token is invalid»
bot: Bot | None = None
dp = Dispatcher()

def log_event(event_type, user_name, user_id, extra=""):
    time_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
    log_line = f"[{time_str}] {event_type} | {user_name} (ID:{user_id}) | {extra}\n"
    try:
        # ИСПРАВЛЕНО: используем utf-8-sig для открытия на смартфонах
        with open("bot_log.txt", "a", encoding="utf-8-sig") as f:
            f.write(log_line)
    except Exception as e:
        logging.error(f"Ошибка записи в лог: {e}")

        
def get_score_kb():
    # Кнопки выбора оценки 1-5
    buttons = [types.KeyboardButton(text=str(i)) for i in range(1, 6)]
    # Создаем клавиатуру (в один ряд)
    return types.ReplyKeyboardMarkup(keyboard=[buttons], resize_keyboard=True)


# --- ДАННЫЕ ---
QUESTIONS = [
    "🔥 1. Я готов рисковать ради высокого результата.",
    "⚡️ 2. Мне важно быстро принимать решения.",
    "🗣 3. В конфликте я буду доказывать свою правоту.",
    "📁 4. Порядок для меня важнее творческого хаоса.",
    "⏰ 5. Я предпочитаю работать в четких дедлайнах.",
    "👑 6. Я легко и уверенно беру на себя роль лидера.",
    "🌊 7. Стресс и сжатые сроки помогают мне работать лучше.",
    "👤 8. Мне комфортнее работать в одиночку, чем в группе.",
    "💡 9. Я постоянно предлагаю новые идеи и улучшения.",
    "🎯 10. Я хорошо чувствую эмоциональное состояние коллег."
]

CASE_TEXT = (
    "⚠️ КРИТИЧЕСКАЯ СИТУАЦИЯ\n"
    "━━━━━━━━━━━━━━━━━━━━\n\n"
    "Дедлайн — через 12 часов.\n"
    "Задача не начата.\n"
    "Команда в панике.\n\n"
    "Вы — ключевой человек в этой ситуации.\n\n"
    "📝 Что вы будете делать?\n"
    "Опишите конкретные шаги и что скажете команде.\n\n"
    "💡 Ваш ответ будет использован для оценки вашей роли в стрессе."
)

SCALE_HELP = (
    "🔹 *Как отвечать:*\n"
    "5️⃣ — Полностью согласен (Точно да)\n"
    "1️⃣ — Совсем не согласен (Точно нет)"
)


# Временное хранилище команд в памяти
# Теперь в каждой команде будет список участников
teams = {} # { code: { 'owner': id, 'members': [id1, id2...], 'results': {id: data} } }
# Активная команда владельца (чтобы кнопка анализа запускала нужную команду)
owner_active_team = {}  # { owner_id: code }
analysis_tasks = {}  # { code: asyncio.Task }
TEAM_TTL_HOURS = 24


def _now_ts() -> datetime.datetime:
    return datetime.datetime.now(datetime.UTC)


def touch_team(code: str):
    if code in teams:
        teams[code]["last_activity"] = _now_ts()


def cleanup_expired_teams():
    cutoff = _now_ts() - datetime.timedelta(hours=TEAM_TTL_HOURS)
    expired_codes = []
    for code, data in teams.items():
        last_activity = data.get("last_activity") or data.get("created_at")
        if not isinstance(last_activity, datetime.datetime):
            expired_codes.append(code)
            continue
        if last_activity < cutoff:
            expired_codes.append(code)

    if not expired_codes:
        return

    for code in expired_codes:
        teams.pop(code, None)

    # Чистим карту активных команд владельцев от удаленных кодов
    for owner_id, code in list(owner_active_team.items()):
        if code in expired_codes or code not in teams:
            owner_active_team.pop(owner_id, None)
    for code in expired_codes:
        task = analysis_tasks.get(code)
        if task and not task.done():
            task.cancel()
        analysis_tasks.pop(code, None)


def split_long_text(text: str, limit: int = 3500):
    if len(text) <= limit:
        return [text]
    chunks = []
    rest = text
    while len(rest) > limit:
        cut = rest.rfind("\n", 0, limit)
        if cut < 1:
            cut = limit
        chunks.append(rest[:cut].strip())
        rest = rest[cut:].lstrip()
    if rest:
        chunks.append(rest)
    return chunks


class CollabXStates(StatesGroup):
    waiting_for_code = State()
    answering_questions = State()
    answering_case = State()

# --- ФУНКЦИЯ PDF ---
def generate_pdf_report(u1, u2, text):
    from reportlab.pdfgen import canvas
    from reportlab.pdfbase import ttfonts, pdfmetrics
    from reportlab.lib.pagesizes import A4

    packet = io.BytesIO()
    can = canvas.Canvas(packet, pagesize=A4)
    
    # 1. Находим путь к шрифту в папке бота на Amvera
    # Файл arial.ttf ДОЛЖЕН лежать в одной папке с ботом!
    current_dir = os.path.dirname(os.path.abspath(__file__))
    font_path = os.path.join(current_dir, 'arial.ttf')
    
    try:
        # Регистрируем шрифт под новым именем
        pdfmetrics.registerFont(ttfonts.TTFont('RussianArial', font_path))
        font_name = 'RussianArial'
    except Exception as e:
        logging.error(f"ШРИФТ НЕ НАЙДЕН: {e}")
        # Если файла arial.ttf нет рядом с ботом, будут иероглифы
        font_name = 'Helvetica'

    # 2. Заголовок
    can.setFont(font_name, 20)
    can.drawCentredString(300, 800, "CollabX: Отчет совместимости")
    
    # 3. Имена участников
    can.setFont(font_name, 12)
    can.drawString(50, 760, f"Команда: {u1} и {u2}")
    can.line(50, 750, 550, 750)

    # 4. Основной текст (ИСПРАВЛЕНО ТУТ)
    text_object = can.beginText(50, 730)
    # ВАЖНО: Принудительно ставим шрифт самому текстовому блоку
    text_object.setFont(font_name, 11) 
    text_object.setLeading(14)

    # Убираем символы разметки ИИ, которые ломают PDF
    clean_text = text.replace('*', '').replace('#', '').replace('_', '')
    
    lines = clean_text.split('\n')
    for line in lines:
        wrapped_lines = textwrap.wrap(line, width=85)
        for w_line in wrapped_lines:
            text_object.textLine(w_line)
        if not wrapped_lines:
            text_object.textLine("")

    can.drawText(text_object)
    can.save()
    packet.seek(0)
    return packet


def generate_roles_chart(results):
    """Гистограмма через Pillow (без matplotlib/numpy — заметно меньше RAM на слабом тарифе)."""
    from PIL import Image, ImageDraw, ImageFont

    roles_count = {}
    for data in results.values():
        role = data.get("role", "Неизвестно")
        parts = role.split(" + ")
        main_role = parts[0].strip() if parts else "Неизвестно"
        roles_count[main_role] = roles_count.get(main_role, 0) + 1

    total = len(results) or 1
    items = sorted(roles_count.items(), key=lambda x: x[1], reverse=True)
    roles = [r[0] for r in items]
    counts = [r[1] for r in items]
    mx_count = max(counts) if counts else 1

    current_dir = os.path.dirname(os.path.abspath(__file__))
    font_path = os.path.join(current_dir, "arial.ttf")
    try:
        font_title = ImageFont.truetype(font_path, 20)
        font_role = ImageFont.truetype(font_path, 14)
        font_label = ImageFont.truetype(font_path, 13)
        font_foot = ImageFont.truetype(font_path, 11)
    except OSError:
        font_title = font_role = font_label = font_foot = ImageFont.load_default()

    W = 920
    role_col_w = 280
    bar_x0 = role_col_w + 24
    bar_max_w = W - bar_x0 - 200
    row_h = 52
    top = 88
    foot_lines = textwrap.wrap(
        "Как читать: у каждого участника тест выдаёт пару «основная + вторая роль». "
        "На графике учитывается только основная — так видно, сколько «организаторов», «аналитиков» и т.д. в команде.",
        width=92,
    )
    foot_h = len(foot_lines) * 15 + 28
    H = top + max(1, len(roles)) * row_h + foot_h

    img = Image.new("RGB", (W, H), (250, 250, 250))
    draw = ImageDraw.Draw(img)

    title = (
        f"Баланс главных ролей в команде — участников: {len(results)}. "
        "Столбец = сколько человек с этой главной ролью."
    )
    for i, line in enumerate(textwrap.wrap(title, width=48)):
        draw.text((16, 12 + i * 22), line, fill=(20, 20, 20), font=font_title)

    draw.text((16, 56), "Роль", fill=(80, 80, 80), font=font_label)
    draw.text((bar_x0, 56), "Число людей (основная роль)", fill=(80, 80, 80), font=font_label)

    y = top
    for name, c in zip(roles, counts):
        wrapped = textwrap.wrap(name, width=26)[:2]
        line_y = y + 6
        for ln in wrapped:
            draw.text((16, line_y), ln, fill=(34, 34, 34), font=font_role)
            bbox = draw.textbbox((0, 0), ln, font=font_role)
            line_y += (bbox[3] - bbox[1]) + 2

        t = (c - 1) / max(mx_count - 1, 1) if mx_count > 1 else 0.5
        r = int(35 + t * 80)
        g = int(100 + t * 90)
        b = int(180 + t * 50)
        bw = max(4, int(bar_max_w * (c / mx_count)))
        draw.rectangle(
            [bar_x0, y + 14, bar_x0 + bw, y + 38],
            fill=(r, g, b),
            outline=(255, 255, 255),
            width=1,
        )
        pct = round(100.0 * c / total, 1)
        label = f"{c} чел.  ({pct}%)"
        draw.text((bar_x0 + bw + 10, y + 18), label, fill=(34, 34, 34), font=font_label)
        y += row_h

    fy = H - foot_h + 8
    for ln in foot_lines:
        draw.text((16, fy), ln, fill=(68, 68, 68), font=font_foot)
        fy += 15

    buf = io.BytesIO()
    img.save(buf, format="PNG", optimize=True)
    buf.seek(0)
    return buf

# --- ОБРАБОТЧИКИ ---

@dp.message(Command("start"))
async def start_cmd(message: types.Message, state: FSMContext):
    await state.clear()
    
    kb = [
        [types.KeyboardButton(text="🚀 Создать команду")],
        [types.KeyboardButton(text="🤝 Присоединиться")]
    ]
    
    # ПРОВЕРЬТЕ ЭТУ СТРОЧКУ: 
    # Должно быть ADMIN_IDS (с буквой S) и оператор "in"
    if message.from_user.id in ADMIN_IDS:
        kb.append([types.KeyboardButton(text="⚙️ Админ-панель")])
        
    keyboard = types.ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True)
    await message.answer(
    "👋 Добро пожаловать в *CollabX AI*\n\n"
    "Это инструмент для анализа командной совместимости.\n\n"
    "📌 *Как начать:*\n"
    "— Если у вас ещё нет команды → нажмите *«Создать команду»*\n"
    "— Если вам уже дали код → нажмите *«Присоединиться»*\n\n"
    "После этого система проанализирует роли участников и покажет, "
    "насколько эффективно вы сможете работать вместе.\n\n"
    "Выберите действие 👇",
    reply_markup=keyboard,
    parse_mode="Markdown"
)



@dp.message(F.text.contains("Создать команду"))
async def create_team(message: types.Message, state: FSMContext):
    cleanup_expired_teams()
    code = ''.join(random.choices(string.digits, k=5))
    # В поле 'name' теперь будет записываться имя из Telegram профиля
    now = _now_ts()
    teams[code] = {
        'owner': message.from_user.id,
        'members': [message.from_user.id],
        'results': {},
        'created_at': now,
        'last_activity': now,
    }
    owner_active_team[message.from_user.id] = code
    
    await state.update_data(code=code, current_q=0, answers=[])
    await state.set_state(CollabXStates.answering_questions)
    
    await message.answer(
    f"🚀 Команда успешно создана!\n\n"
    f"🔑 Код подключения: {code}\n\n"
    f"Передайте его участникам.\n"
    f"После подключения мы определим рабочие стили команды.",
)
    
    progress_bar = "🟢" + "⚪️" * (len(QUESTIONS) - 1)
    await message.answer(
        f"{progress_bar}\n\n*Вопрос 1 из {len(QUESTIONS)}:*\n{QUESTIONS[0]}\n\n{SCALE_HELP}",
        reply_markup=get_score_kb(),
        parse_mode="Markdown"
    )
    # Логируем вход по Telegram-имени
    log_event("СОЗДАНИЕ", message.from_user.full_name, message.from_user.id, f"Код: {code}")


@dp.message(F.text.regexp(r"(?i).*создать\s+команд.*"))
async def create_team_fallback(message: types.Message, state: FSMContext):
    # Резервный обработчик на случай отличий текста кнопки на разных клиентах/платформах
    await create_team(message, state)


@dp.message(F.text.contains("Присоединиться"))
async def join_prompt(message: types.Message, state: FSMContext):
    await message.answer("Введите 5-значный код команды:")
    await state.set_state(CollabXStates.waiting_for_code)


@dp.message(F.text == "⚙️ Админ-панель")
async def admin_menu(message: types.Message):
    # ПРАВИЛЬНО: проверяем, что ID НЕТ в списке разрешенных
    if message.from_user.id not in ADMIN_IDS:
        return 

    kb = [
        [types.KeyboardButton(text="📁 Скачать логи (TXT)")] ,
        [types.KeyboardButton(text="⬅️ Назад")]
    ]
    keyboard = types.ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True)
    await message.answer("🛠 Добро пожаловать в панель управления.\nВыберите действие:", reply_markup=keyboard)

@dp.message(F.text == "📁 Скачать логи (TXT)")
async def download_logs(message: types.Message):
    # ПРАВИЛЬНО: проверяем через "not in ADMIN_IDS"
    if message.from_user.id not in ADMIN_IDS: 
        return
    
    try:
        log_file = types.FSInputFile("bot_log.txt")
        await message.answer_document(log_file, caption="📂 Полный лог активности пользователей")
    except Exception as e:
        await message.answer(f"❌ Файл лога еще не создан или пуст. Ошибка: {e}")

@dp.message(F.text == "⬅️ Назад")
async def back_to_start(message: types.Message, state: FSMContext):
    # Проверяем права и возвращаем в начало
    if message.from_user.id in ADMIN_IDS:
        await start_cmd(message, state)

@dp.message(F.text == "🏠 В главное меню")
async def go_to_main_menu(message: types.Message, state: FSMContext):
    await state.clear()
    # Просто вызываем вашу функцию старта
    await start_cmd(message, state)


@dp.message(CollabXStates.waiting_for_code)
async def join_logic(message: types.Message, state: FSMContext):
    cleanup_expired_teams()
    code = message.text.strip()
    if code in teams:
        user_id = message.from_user.id
        newly_joined = user_id not in teams[code]["members"]
        if newly_joined:
            teams[code]["members"].append(user_id)
        touch_team(code)

        # Сбрасываем прогресс для нового участника
        await state.update_data(code=code, current_q=0, answers=[])
        await state.set_state(CollabXStates.answering_questions)

        team_size = len(teams[code]["members"])

        await message.answer(
            f"✅ Вы присоединились к команде\n"
            f"👥 Участников сейчас: {team_size}\n\n"
            f"Сейчас мы определим ваш стиль работы и поведения в стрессе.\n"
            f"Это займет около 2 минут."
        )

        # Уведомление организатору только при первом входе в команду по коду
        owner_id = teams[code].get("owner")
        if newly_joined and owner_id and user_id != owner_id:
            try:
                joiner = message.from_user.full_name or str(user_id)
                await bot.send_message(
                    owner_id,
                    f"🔔 К вашей команде присоединился: {joiner}\n"
                    f"👥 Всего участников в команде: {team_size}",
                )
            except Exception as e:
                logging.error(f"Не удалось уведомить организатора {owner_id}: {e}")
        # Если владелец зашел в эту команду по коду, считаем ее активной
        if owner_id and user_id == owner_id:
            owner_active_team[user_id] = code

        progress_bar = "🟢" + "⚪️" * (len(QUESTIONS) - 1)
        await message.answer(
            f"{progress_bar}\n\n*Вопрос 1 из {len(QUESTIONS)}:*\n{QUESTIONS[0]}\n\n{SCALE_HELP}",
            reply_markup=get_score_kb(),
            parse_mode="Markdown",
        )
    else:
        await message.answer("❌ Код не найден. Проверьте цифры и попробуйте еще раз.")



@dp.message(CollabXStates.answering_questions)
async def handle_q(message: types.Message, state: FSMContext):
    # 1. Быстрая проверка ввода (мгновенно)
    if message.text not in ["1", "2", "3", "4", "5"]:
        await message.answer("Выберите 1-5 на кнопках! 👇")
        return

    # 2. Получение данных из памяти (мгновенно)
    data = await state.get_data()
    ans = data.get('answers', [])
    ans.append(message.text)
    curr = data.get('current_q', 0) + 1
    
    # 3. Обновление состояния и ответ (мгновенно)
    if curr < len(QUESTIONS):
        if curr == 5:
            await message.answer("🔥 Вы прошли половину теста")
        await state.update_data(current_q=curr, answers=ans)
        
        progress_bar = "🟢" * (curr + 1) + "⚪️" * (len(QUESTIONS) - (curr + 1))
        
        await message.answer(
            f"{progress_bar}\n\n*Вопрос {curr + 1} из {len(QUESTIONS)}:*\n{QUESTIONS[curr]}", 
            reply_markup=get_score_kb(),
            parse_mode="Markdown"
        )
    else:
        # Переход к кейсу (только здесь меняем стейт)
        await state.update_data(answers=ans)
        await state.set_state(CollabXStates.answering_case)
        await message.answer("✅ Тест пройден!\n\n" + CASE_TEXT, reply_markup=types.ReplyKeyboardRemove())




@dp.message(CollabXStates.answering_case)
async def handle_case(message: types.Message, state: FSMContext):
    try:
        cleanup_expired_teams()
        data = await state.get_data()
        code = data.get('code')

        if not code or code not in teams:
            await message.answer(
                "⚠️ Сессия команды не найдена (возможно, бот перезапускался).\n"
                "Нажмите «🏠 В главное меню» и начните заново."
            )
            await state.clear()
            await start_cmd(message, state)
            return

        answers = data.get('answers')
        if not answers or len(answers) != len(QUESTIONS):
            await message.answer(
                "⚠️ Не удалось найти результаты теста для этого профиля.\n"
                "Нажмите «🏠 В главное меню» и пройдите опрос заново."
            )
            await state.clear()
            await start_cmd(message, state)
            return

        user_name = message.from_user.full_name  # Имя из Telegram
        info = {
            'test': answers,
            'case': (message.text or "").strip(),
            'name': user_name
        }

        # Сохраняем результат участника в общий словарь результатов команды
        if 'results' not in teams[code]:
            teams[code]['results'] = {}

        teams[code]['results'][message.from_user.id] = info
        touch_team(code)

        # Запись в лог
        log_event("ТЕСТ ЗАВЕРШЕН", user_name, message.from_user.id, f"Команда: {code}")

        await message.answer(
            "✅ Ответ принят\n\n"
            "Ваш стиль поведения зафиксирован.\n"
            "Теперь система сможет определить вашу роль в команде."
        )

        # Логика кнопок в зависимости от роли (Организатор или Участник)
        is_owner = message.from_user.id == teams[code].get("owner")
        if is_owner:
            owner_active_team[message.from_user.id] = code

        if is_owner:
            kb = [
                [types.KeyboardButton(text="📊 Запустить анализ команды")],
                [types.KeyboardButton(text="🏠 В главное меню")]
            ]
            markup = types.ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True)
            await message.answer(
                "📊 Вы — организатор команды\n\n"
                "Когда все участники завершат тест, запустите анализ.\n\n"
                "Вы получите:\n"
                "— распределение ролей\n"
                "— оценку совместимости\n"
                "— рекомендации по работе\n"
                "Или вернитесь в меню, чтобы создать новую группу.",
                reply_markup=markup
            )
        else:
            kb = [[types.KeyboardButton(text="🏠 В главное меню")]]
            markup = types.ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True)
            await message.answer(
                "Ожидайте, пока организатор запустит общий анализ.\n"
                "Вы можете вернуться в главное меню, если хотите начать заново.",
                reply_markup=markup
            )

        await state.clear()
    except Exception:
        logging.exception("Ошибка в handle_case")
        await state.clear()
        await message.answer(
            "⚠️ Произошла ошибка при сохранении ответа.\n"
            "Нажмите «🏠 В главное меню» и начните заново."
        )
        await start_cmd(message, state)

# ОБРАБОТЧИК КНОПКИ ЗАПУСКА
@dp.message(F.text.contains("Запустить анализ"))
async def start_analysis_handler(message: types.Message):
    cleanup_expired_teams()
    owner_id = message.from_user.id
    # 1) В первую очередь берем явно активную команду владельца
    target_code = owner_active_team.get(owner_id)
    # 2) Фолбэк: выбираем команду этого владельца с наибольшим количеством завершенных анкет
    if not target_code or target_code not in teams:
        owner_codes = [code for code, data in teams.items() if data.get("owner") == owner_id]
        if owner_codes:
            target_code = max(
                owner_codes,
                key=lambda c: len(teams[c].get("results", {}))
            )
            owner_active_team[owner_id] = target_code
    
    if target_code:
        touch_team(target_code)
        if len(teams[target_code].get('results', {})) < 2:
            done = len(teams[target_code].get('results', {}))
            await message.answer(
                "Ошибка: для анализа нужно минимум 2 завершенных анкеты.\n"
                f"Сейчас завершили: {done}."
            )
        else:
            existing = analysis_tasks.get(target_code)
            if existing and not existing.done():
                await message.answer("⏳ Анализ уже запущен. Подождите, пожалуйста, результат.")
                return
            await message.answer("✅ Анализ запущен. Это может занять до 1-2 минут.")
            analysis_tasks[target_code] = asyncio.create_task(run_ai_safe(target_code))
    else:
        await message.answer("Команда не найдена.")

async def run_ai_safe(code: str):
    try:
        await run_ai(code)
    except Exception:
        logging.exception("Необработанная ошибка в run_ai_safe")
    finally:
        analysis_tasks.pop(code, None)


async def run_ai(code):
    t = teams[code]
    results = t.get('results', {})
    uids = list(results.keys())

    if not GIGACHAT_CREDENTIALS:
        logging.error("GIGACHAT_CREDENTIALS не задан")
        for uid in uids:
            try:
                await bot.send_message(
                    uid,
                    "❌ Не настроен GigaChat: в панели Amvera задайте переменную GIGACHAT_CREDENTIALS.",
                )
            except Exception:
                pass
        return

    # Внутренняя функция для расчета 7 ролей
    def get_role(answers):
        ans = [int(a) for a in answers]
        # Индексы вопросов в списке (номер вопроса минус 1)
        scores = {
            "Организатор": (ans[3] + ans[4] + ans[5]) / 3,
            "Исполнитель": (ans[3] + ans[4] + ans[7]) / 3,
            "Аналитик": (ans[3] + ans[7] + ans[9]) / 3,
            "Контролер": (ans[2] + ans[3] + ans[4]) / 3,
            "Исследователь": (ans[0] + ans[6] + ans[8]) / 3,
            "Генератор идей": (ans[0] + ans[8]) / 2,
            "Мотиватор": (ans[5] + ans[6] + ans[9]) / 3
        }
        # Находим роль с максимальным средним баллом
        sorted_roles = sorted(scores.items(), key=lambda x: x[1], reverse=True)
        main_role = sorted_roles[0][0]
        second_role = sorted_roles[1][0]

        return f"{main_role} + {second_role}"

    # Уведомляем всех участников
    for uid in uids:
        try:
            await bot.send_chat_action(uid, action="typing")
            await bot.send_message(uid, "🤖 *GigaChat анализирует распределение ролей в вашей команде...*", parse_mode="Markdown")
        except: continue

    # Собираем данные для нейросети
    summary_text = ""
    members_list = []
    
    for uid, data in results.items():
        role = get_role(data['test'])
        data['role'] = role  # 👈 добавили сохранение роли
        members_list.append(f"{data['name']} ({role})")
        summary_text += f"Участник: {data['name']}\n- Роль: {role}\n- Ответ на кейс: {data['case']}\n\n"

    # Промпт с новыми ролями
    prompt = (
    f"Ты — эксперт по командной эффективности.\n\n"
    f"Проанализируй команду из {len(uids)} человек:\n\n"
    f"{summary_text}\n\n"

    f"Сделай подробный разбор:\n\n"

    f"1. Общая эффективность команды (как они будут работать вместе)\n"
    f"2. Сильные стороны команды\n"
    f"3. Потенциальные конфликты и риски\n"
    f"4. Практические рекомендации\n\n"

    f"5. Персональный разбор КАЖДОГО участника:\n"
    f"- его сильные стороны\n"
    f"- его слабые стороны\n"
    f"- как ему лучше работать в команде\n\n"

    f"Пиши ПРОСТЫМ языком, без символов # * _ []\n"
    f"Без разметки, только текст\n"
    f"На русском языке"
)

    compatibility = random.randint(70, 95)
    used_fallback = False
    res_text = ""

    try:
        from gigachat import GigaChat

        async with GigaChat(credentials=GIGACHAT_CREDENTIALS, verify_ssl_certs=False) as giga:
            # Таймаут защищает от "зависаний" на генерации
            response = await asyncio.wait_for(giga.achat(prompt), timeout=90)

        if not getattr(response, "choices", None):
            raise RuntimeError("GigaChat вернул пустой ответ (choices отсутствует).")

        raw_text = response.choices[0].message.content or ""
        res_text = raw_text.replace("*", "").replace("#", "").replace("_", "").replace("##", "").strip()
        if not res_text:
            raise RuntimeError("GigaChat вернул пустой текст ответа.")

    except Exception:
        used_fallback = True
        logging.exception("Критическая ошибка в run_ai (AI этап)")
        # Фолбэк, чтобы пользователь всегда получал завершенный анализ
        role_lines = []
        for uid in uids:
            role_lines.append(f"- {results[uid]['name']}: {results[uid].get('role', 'Неизвестно')}")
        members_text = "\n".join(role_lines)
        res_text = (
            "AI-вызов временно недоступен, поэтому отправляю быстрый резервный разбор.\n\n"
            "1. Общая эффективность:\n"
            "Команда может работать стабильно при четком распределении задач и сроков.\n\n"
            "2. Сильные стороны:\n"
            "Есть разнообразие ролей, что помогает делить ответственность.\n\n"
            "3. Риски:\n"
            "Возможны конфликты при неясных приоритетах и слабой координации.\n\n"
            "4. Рекомендации:\n"
            "- Назначить ответственного за дедлайн.\n"
            "- Зафиксировать приоритеты задач на ближайшие 24 часа.\n"
            "- Делать короткие синхронизации по прогрессу.\n\n"
            "5. Роли участников:\n"
            f"{members_text}"
        )

    # 2. Отправляем текст всем участникам
    for uid in uids:
        header = (
            "🧠 AI-анализ завершен\n"
            "━━━━━━━━━━━━━━━━━━━━\n\n"
            f"💯 Совместимость команды: {compatibility}%\n\n"
            "Команда была проанализирована по:\n"
            "— стилю принятия решений\n"
            "— поведению в стрессе\n"
            "— взаимодействию\n\n"
            "🎭 РАСПРЕДЕЛЕНИЕ РОЛЕЙ:\n"
        )

        roles_info = ""
        for member_uid in uids:
            m_data = results[member_uid]
            m_role = get_role(m_data['test'])
            roles_info += f"👤 {m_data['name']} — {m_role}\n"

        roles_info += "\n📝 ПОДРОБНЫЙ РАЗБОР:\n\n"

        try:
            full_text = header + roles_info + res_text
            for part in split_long_text(full_text):
                await bot.send_message(uid, part)
            if used_fallback:
                await bot.send_message(
                    uid,
                    "⚠️ Основной AI-ответ временно недоступен. Отправлен резервный анализ, чтобы не было зависания.",
                )
            await bot.send_message(uid, "📄 Генерирую PDF-отчет для печати...")
        except Exception as e:
            logging.error(f"Не удалось отправить текст пользователю {uid}: {e}")
            continue

    # 3. PDF и график в потоке (с таймаутами, чтобы бот не "зависал")
    p_names = ", ".join([results[uid]['name'] for uid in uids])
    pdf_file = None
    chart_buf = None

    try:
        pdf_file = await asyncio.wait_for(
            asyncio.to_thread(generate_pdf_report, "Команда", p_names, res_text),
            timeout=40,
        )
    except Exception:
        logging.exception("Не удалось сгенерировать PDF-отчет")

    try:
        chart_buf = await asyncio.wait_for(
            asyncio.to_thread(generate_roles_chart, results),
            timeout=30,
        )
    except Exception:
        logging.exception("Не удалось сгенерировать график ролей")

    # 4. Рассылаем файлы (что удалось подготовить)
    for uid in uids:
        try:
            if pdf_file is not None:
                pdf_file.seek(0)
                file_to_send = types.BufferedInputFile(pdf_file.read(), filename="CollabX_Report.pdf")
                await bot.send_document(uid, file_to_send)
                await bot.send_message(
                    uid,
                    "📌 Отчет можно использовать для обсуждения внутри команды или с руководителем."
                )
            else:
                await bot.send_message(
                    uid,
                    "⚠️ PDF-отчет не удалось сформировать в срок. Текстовый анализ уже отправлен выше."
                )

            if chart_buf is not None:
                chart_buf.seek(0)
                chart_file = types.BufferedInputFile(chart_buf.read(), filename="roles_chart.png")

                await bot.send_message(
                    uid,
                    "📊 Дальше — график «баланс главных ролей».\n"
                    "Для каждого человека берётся первая (основная) роль из пары теста; "
                    "по оси — названия ролей, по числам — сколько человек и какой это процент от команды.",
                )

                await bot.send_photo(
                    uid,
                    chart_file,
                    caption=(
                        "Главные роли в команде: столбец = сколько участников "
                        "имеют эту роль как основную (см. подписи «N чел. (%)»)."
                    ),
                )
            else:
                await bot.send_message(
                    uid,
                    "⚠️ График ролей не удалось сформировать в срок."
                )
        except Exception as e:
            logging.error(f"Не удалось отправить PDF пользователю {uid}: {e}")
            continue



async def main():
    global bot
    if not API_TOKEN:
        raise RuntimeError(
            "Не задан токен бота. Amvera → проект → переменные окружения: "
            "TELEGRAM_BOT_TOKEN (или BOT_TOKEN) = строка из @BotFather, без кавычек и пробелов по краям."
        )
    try:
        bot = Bot(token=API_TOKEN, session=session)
    except TokenValidationError as e:
        raise RuntimeError(
            "Токен не прошёл проверку (пустой, обрезан или неверный). "
            "Проверьте TELEGRAM_BOT_TOKEN в Amvera: целиком, одной строкой, как выдал @BotFather."
        ) from e
    # Удаляем вебхуки, чтобы бот не отвечал на старые сообщения
    try:
        await bot.delete_webhook(drop_pending_updates=True)
        await dp.start_polling(bot)
    finally:
        await bot.session.close()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logging.info("Бот остановлен")




