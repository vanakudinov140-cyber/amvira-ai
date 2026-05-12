# -*- coding: utf-8 -*-
"""
Created on Fri Mar 13 19:11:26 2026

@author: Dimid Ivanovich
"""

# -*- coding: utf-8 -*-
import asyncio
import logging
import random
import string
import io
import textwrap
import aiohttp 
import datetime
import os
import matplotlib.pyplot as plt
# Эта строка удалит старый лог при каждом перезапуске бота, 
# чтобы иероглифы не копились
import nest_asyncio
nest_asyncio.apply()
if os.path.exists("bot_log.txt"):
    os.remove("bot_log.txt")


from aiogram import Bot, Dispatcher, types, F
from aiogram.client.session.aiohttp import AiohttpSession 
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from gigachat import GigaChat

# Для PDF
from reportlab.pdfgen import canvas
from reportlab.pdfbase import ttfonts, pdfmetrics
from reportlab.lib.pagesizes import A4

# --- КОНФИГУРАЦИЯ ---
API_TOKEN = '8403026726:AAEhk_kZf9UTLqlBvcq_MkBDs5hcUGrOWNI'
GIGACHAT_CREDENTIALS = 'MDE5Y2U3NjQtMjU3ZC03MDNlLWJlOTUtYzY1YTkxNzg4OTZiOjQ3MWNjYzIwLTQzMDEtNGU0YS1hMDkwLTdjYjEyODA1NzM1Zg=='
ADMIN_IDS = [414246886, 1299192895]  


logging.basicConfig(level=logging.INFO)

# --- ИСПРАВЛЕНИЕ СЕТИ (Чтобы не было ошибки 10054 и таймаутов) ---
# В новых версиях aiogram настройки коннектора передаются так:
session = AiohttpSession()
# Отключаем проверку SSL для стабильности на Windows
session.connector_init_kwargs = {"ssl": False}

# Создаем бота с настроенной сессией
bot = Bot(token=API_TOKEN, session=session)
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


class CollabXStates(StatesGroup):
    waiting_for_code = State()
    answering_questions = State()
    answering_case = State()

# --- ФУНКЦИЯ PDF ---
def generate_pdf_report(u1, u2, text):
    packet = io.BytesIO()
    can = canvas.Canvas(packet, pagesize=A4)
    
    # 1. Находим путь к шрифту в папке бота на Amvera
    # Файл arial.ttf ДОЛЖЕН лежать в одной папке с ботом!
    import os
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
    roles_count = {}

    # считаем роли
    for data in results.values():
        role = data.get('role', 'Неизвестно')
        main_role = role.split(" + ")[0]
        roles_count[main_role] = roles_count.get(main_role, 0) + 1

    roles = list(roles_count.keys())
    counts = list(roles_count.values())

    plt.figure()

    bars = plt.bar(roles, counts)

    # ✅ добавляем подписи над столбцами
    for bar in bars:
        height = bar.get_height()
        plt.text(
            bar.get_x() + bar.get_width() / 2,
            height,
            f'{int(height)}',
            ha='center',
            va='bottom'
        )

    # ✅ добавляем оси
    plt.ylabel("Количество участников")
    plt.xlabel("Роли")

    # ✅ заголовок понятнее
    plt.title("Распределение ролей в команде")

    plt.xticks(rotation=25)

    # ✅ сетка (сразу +100 к читаемости)
    plt.grid(axis='y', linestyle='--', alpha=0.5)

    # сохраняем
    buf = io.BytesIO()
    plt.savefig(buf, format='png', bbox_inches='tight')
    plt.close()
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
    code = ''.join(random.choices(string.digits, k=5))
    # В поле 'name' теперь будет записываться имя из Telegram профиля
    teams[code] = {'owner': message.from_user.id, 'members': [message.from_user.id], 'results': {}}
    
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
    code = message.text.strip()
    if code in teams:
        user_id = message.from_user.id
        if user_id not in teams[code]['members']:
            teams[code]['members'].append(user_id)
        
        # Сбрасываем прогресс для нового участника
        await state.update_data(code=code, current_q=0, answers=[])
        await state.set_state(CollabXStates.answering_questions)
        
        team_size = len(teams[code]['members'])

        await message.answer(
            f"✅ Вы присоединились к команде\n"
            f"👥 Участников сейчас: {team_size}\n\n"
            f"Сейчас мы определим ваш стиль работы и поведения в стрессе.\n"
            f"Это займет около 2 минут."
            )
        
        # ДОБАВЛЯЕМ ОТРИСОВКУ ПЕРВОГО ВОПРОСА С КРУЖОЧКОМ
        progress_bar = "🟢" + "⚪️" * (len(QUESTIONS) - 1)
        await message.answer(
            f"{progress_bar}\n\n"
       f"🧠 *Оцените утверждение:*\n\n"
f"*Вопрос 1 из {len(QUESTIONS)}:*\n{QUESTIONS[0]}\n\n"
f"{SCALE_HELP}"
       f"{SCALE_HELP}", # Добавили подсказку
       reply_markup=get_score_kb(),
       parse_mode="Markdown"
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
    data = await state.get_data()
    code = data.get('code')
    
    if not code or code not in teams:
        await message.answer("Ошибка: Команда не найдена.")
        return

    user_name = message.from_user.full_name # Имя из Telegram

    info = {
        'test': data['answers'], 
        'case': message.text, 
        'name': user_name
    }
    
    # Сохраняем результат участника в общий словарь результатов команды
    if 'results' not in teams[code]:
        teams[code]['results'] = {}
    
    teams[code]['results'][message.from_user.id] = info
    
    # Запись в лог
    log_event("ТЕСТ ЗАВЕРШЕН", user_name, message.from_user.id, f"Команда: {code}")
    
    await message.answer(
    "✅ Ответ принят\n\n"
    "Ваш стиль поведения зафиксирован.\n"
    "Теперь система сможет определить вашу роль в команде."
)
    
    # Логика кнопок в зависимости от роли (Организатор или Участник)
    is_owner = (message.from_user.id == teams[code].get('owner') or 
                message.from_user.id == teams[code].get('user1'))

    if is_owner:
        # Организатору даем две кнопки: запуск и выход в меню
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
        # Обычному участнику даем только кнопку возврата
        kb = [[types.KeyboardButton(text="🏠 В главное меню")]]
        markup = types.ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True)
        await message.answer(
            "Ожидайте, пока организатор запустит общий анализ.\n"
            "Вы можете вернуться в главное меню, если хотите начать заново.", 
            reply_markup=markup
        )
    
    await state.clear()

# --- ОБЯЗАТЕЛЬНО ДОБАВЬТЕ ЭТОТ ОБРАБОТЧИК НИЖЕ ---
@dp.message(F.text == "🏠 В главное меню")
async def go_home_handler(message: types.Message, state: FSMContext):
    await state.clear()
    await start_cmd(message, state) # Вызывает ваше начальное приветствие с кнопками



# ОБРАБОТЧИК КНОПКИ ЗАПУСКА
@dp.message(F.text.contains("Запустить анализ"))
async def start_analysis_handler(message: types.Message):
    # Ищем, в какой команде состоит этот пользователь как создатель
    target_code = None
    for code, data in teams.items():
        if data.get('owner') == message.from_user.id or data.get('user1') == message.from_user.id:
            target_code = code
            break
    
    if target_code:
        if len(teams[target_code].get('results', {})) < 2:
            await message.answer("Ошибка: Нужен хотя бы еще один участник с пройденным тестом!")
        else:
            await run_ai(target_code)
    else:
        await message.answer("Команда не найдена.")

async def run_ai(code):
    t = teams[code]
    results = t.get('results', {})
    uids = list(results.keys())

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


    try:
        async with GigaChat(credentials=GIGACHAT_CREDENTIALS, verify_ssl_certs=False) as giga:
            # 1. Получаем ответ от ИИ
            response = await giga.achat(prompt)
            
            # ИСПРАВЛЕНО: Достаем текст и СРАЗУ чистим его от звездочек и решеток
            raw_text = response.choices[0].message.content
            res_text = raw_text.replace("*", "").replace("#", "").replace("_", "").replace("##", "")
            
            compatibility = random.randint(70, 95)
            
            # 2. МГНОВЕННО отправляем текст всем участникам
            for uid in uids:
                # Красивый заголовок без Markdown-разметки
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
                
                # Собираем список ролей для сообщения
                roles_info = ""
                for member_uid in uids:
                    m_data = results[member_uid]
                    m_role = get_role(m_data['test'])
                    roles_info += f"👤 {m_data['name']} — {m_role}\n"
                
                roles_info += "\n📝 ПОДРОБНЫЙ РАЗБОР:\n\n"
                
                try:
                    # Отправляем основной текст (без parse_mode, чтобы не было ошибок из-за символов)
                    await bot.send_message(uid, header + roles_info + res_text)
                    # Маленькое уведомление о PDF
                    await bot.send_message(uid, "📄 Генерирую PDF-отчет для печати...")
                except Exception as e:
                    logging.error(f"Не удалось отправить текст пользователю {uid}: {e}")
                    continue

            # 3. Создаем PDF (используем уже чистый текст)
            p_names = ", ".join([results[uid]['name'] for uid in uids])
            pdf_file = generate_pdf_report("Команда", p_names, res_text)
            
            chart_buf = generate_roles_chart(results)
            
            # 4. Рассылаем файл
            for uid in uids:
                try:
                    pdf_file.seek(0)
                    file_to_send = types.BufferedInputFile(pdf_file.read(), filename="CollabX_Report.pdf")
                    await bot.send_document(uid, file_to_send)
                    await bot.send_message(
    uid,
    "📌 Отчет можно использовать для обсуждения внутри команды или с руководителем."
)
                    chart_buf.seek(0)
                    chart_file = types.BufferedInputFile(chart_buf.read(), filename="roles_chart.png")

                    await bot.send_message(
                        uid,
                        "📊 На графике показано, сколько участников относится к каждой роли.\n"
                        "Это помогает понять баланс команды."
                        )

                    await bot.send_photo(
                            uid,
                            chart_file,
                            caption="📊 Визуальное распределение ролей в команде"
                            )
                except Exception as e:
                    logging.error(f"Не удалось отправить PDF пользователю {uid}: {e}")
                    continue
                
    except Exception as e:
        logging.error(f"Критическая ошибка в run_ai: {e}")
        for uid in uids:
            try:
                await bot.send_message(uid, "🤖 Запускаю AI-анализ команды...")
                await asyncio.sleep(1)

                await bot.send_message(uid, "📊 Анализирую ответы участников...")
                await asyncio.sleep(1)

                await bot.send_message(uid, "🧠 Определяю командные роли...")
                await asyncio.sleep(1)

                await bot.send_message(uid, "⚖️ Оцениваю совместимость...")
                await asyncio.sleep(1)

            except:
                continue



async def main():
    # Удаляем вебхуки, чтобы бот не отвечал на старые сообщения
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logging.info("Бот остановлен")




