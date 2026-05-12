"""
Avatar Arena Omsk VR raffle bot (simple VK LongPoll version).

No callback URL, no ngrok. Just:
1) Set VK_GROUP_TOKEN env variable
2) python main.py
"""

from __future__ import annotations

import datetime as dt
import csv
import json
import os
import re
import secrets
import shutil
import sqlite3
import tempfile
import time
import atexit
import threading
from contextlib import contextmanager
from pathlib import Path
from typing import Iterator

import vk_api
from vk_api.bot_longpoll import VkBotEventType, VkBotLongPoll
from vk_api.utils import get_random_id
try:
    from openpyxl import Workbook
except ImportError:  # pragma: no cover - optional runtime dependency
    Workbook = None

BASE_DIR = Path(__file__).resolve().parent
# On Amvera, persistent storage is mounted at /data.
# Fallback to local folder for local runs/tests.
PERSISTENT_DIR = Path(os.getenv("PERSISTENT_DIR", "/data"))
DB_PATH = (PERSISTENT_DIR / "raffle.db") if PERSISTENT_DIR.exists() else (BASE_DIR / "raffle.db")
LOCK_PATH = BASE_DIR / "bot.lock"
PD_POLICY_URL = os.getenv("PD_POLICY_URL", "https://www.consultant.ru/document/cons_doc_LAW_61801/")
VK_GROUP_TOKEN = os.getenv("VK_GROUP_TOKEN", "")
VK_GROUP_ID = int(os.getenv("VK_GROUP_ID", "0"))
VK_ADMIN_IDS = {int(x) for x in os.getenv("VK_ADMIN_IDS", "").split(",") if x.strip().isdigit()}
RAFFLE_POST_OWNER_ID = int(os.getenv("RAFFLE_POST_OWNER_ID", "0"))
RAFFLE_POST_ID = int(os.getenv("RAFFLE_POST_ID", "0"))
DEFAULT_STAGE_WINNERS_COUNT = int(os.getenv("DEFAULT_STAGE_WINNERS_COUNT", "1"))
REMINDER_INTERVAL_SEC = int(os.getenv("REMINDER_INTERVAL_SEC", "300"))
ADMIN_CONTACT_LINK = os.getenv("ADMIN_CONTACT_LINK", "https://vk.com/id36201837")
CONSENT_TEXT = "Даю согласие на обработку персональных данных в целях участия в розыгрыше Avatar Arena Omsk VR."
USER_MESSAGE_RATE_LIMIT_SEC = float(os.getenv("USER_MESSAGE_RATE_LIMIT_SEC", "0.8"))
RECENT_MSG_KEYS: set[str] = set()
LAST_USER_MESSAGE_TS: dict[int, float] = {}


def ensure_persistent_db_seeded() -> None:
    if DB_PATH.exists():
        return
    seed_db_path = BASE_DIR / "raffle.db"
    if seed_db_path.exists() and seed_db_path != DB_PATH:
        DB_PATH.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(seed_db_path, DB_PATH)
        print(f"[BOOT] Seeded persistent DB at {DB_PATH}")


def process_alive(pid: int) -> bool:
    try:
        os.kill(pid, 0)
    except OSError:
        return False
    return True


def acquire_single_instance_lock() -> None:
    if LOCK_PATH.exists():
        content = LOCK_PATH.read_text(encoding="utf-8").strip()
        if content.isdigit() and process_alive(int(content)):
            raise RuntimeError("Бот уже запущен в другом процессе.")
    LOCK_PATH.write_text(str(os.getpid()), encoding="utf-8")
    atexit.register(release_single_instance_lock)


def release_single_instance_lock() -> None:
    try:
        if LOCK_PATH.exists():
            content = LOCK_PATH.read_text(encoding="utf-8").strip()
            # Delete lock only if it belongs to current process.
            if content == str(os.getpid()):
                LOCK_PATH.unlink()
    except OSError:
        pass


@contextmanager
def db() -> Iterator[sqlite3.Connection]:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    # Better resilience under short lock contention bursts.
    conn.execute("PRAGMA busy_timeout=5000")
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()


def now_iso() -> str:
    return dt.datetime.now(dt.timezone.utc).isoformat()


def log_event(action: str, details: str) -> None:
    print(f"[EVENT] {action} | {details}")


def init_db() -> None:
    with db() as conn:
        conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS users (
                vk_user_id INTEGER PRIMARY KEY,
                first_seen_at TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS user_consents (
                vk_user_id INTEGER PRIMARY KEY,
                accepted_at TEXT NOT NULL,
                consent_text TEXT NOT NULL DEFAULT ''
            );
            CREATE TABLE IF NOT EXISTS pending_tokens (
                vk_user_id INTEGER PRIMARY KEY,
                token TEXT NOT NULL,
                created_at TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS admin_states (
                vk_user_id INTEGER PRIMARY KEY,
                state TEXT NOT NULL,
                data_json TEXT,
                updated_at TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS stages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                stage_no INTEGER NOT NULL UNIQUE,
                status TEXT NOT NULL CHECK(status IN ('planned', 'active', 'closed')),
                starts_at TEXT,
                ends_at TEXT,
                created_at TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS qr_tokens (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                token TEXT NOT NULL UNIQUE,
                issued_for_receipt TEXT,
                issued_at TEXT NOT NULL,
                is_used INTEGER NOT NULL DEFAULT 0,
                used_by_vk_id INTEGER,
                used_at TEXT,
                active_for_next_stage INTEGER NOT NULL DEFAULT 1,
                is_winner INTEGER NOT NULL DEFAULT 0
            );
            CREATE TABLE IF NOT EXISTS activations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                token_id INTEGER NOT NULL,
                vk_user_id INTEGER NOT NULL,
                activated_at TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS draws (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                stage_no INTEGER NOT NULL,
                winners_count INTEGER NOT NULL,
                drawn_at TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS draw_winners (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                draw_id INTEGER NOT NULL,
                token_id INTEGER NOT NULL UNIQUE,
                vk_user_id INTEGER NOT NULL
            );
            CREATE TABLE IF NOT EXISTS user_states (
                vk_user_id INTEGER PRIMARY KEY,
                state TEXT NOT NULL,
                data_json TEXT,
                updated_at TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS participants (
                vk_user_id INTEGER PRIMARY KEY,
                full_name TEXT NOT NULL,
                phone TEXT NOT NULL,
                is_subscriber INTEGER NOT NULL DEFAULT 0,
                like_repost_status TEXT NOT NULL DEFAULT 'unknown',
                participation_status TEXT NOT NULL DEFAULT 'draft',
                participant_number INTEGER UNIQUE,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS participant_checks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                vk_user_id INTEGER NOT NULL,
                check_type TEXT NOT NULL,
                check_result TEXT NOT NULL,
                details TEXT,
                checked_at TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS participant_draws (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                winners_count INTEGER NOT NULL,
                created_at TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS participant_draw_winners (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                draw_id INTEGER NOT NULL,
                vk_user_id INTEGER NOT NULL,
                participant_number INTEGER NOT NULL
            );
            CREATE TABLE IF NOT EXISTS reminders_log (
                reminder_key TEXT PRIMARY KEY,
                created_at TEXT NOT NULL
            );
            """
        )
        migrate_stages_schema(conn)
        for stage_no in (1, 2, 3):
            conn.execute(
                """
                INSERT OR IGNORE INTO stages(stage_no, status, starts_at, ends_at, created_at)
                VALUES(?, 'planned', NULL, NULL, ?)
                """,
                (stage_no, now_iso()),
            )
        migrate_participants_schema(conn)
        migrate_user_consents_schema(conn)


def seed_qr_tokens_if_empty() -> None:
    csv_path = BASE_DIR / "qr_links_for_print.csv"
    if not csv_path.exists():
        return

    with db() as conn:
        row = conn.execute("SELECT COUNT(*) AS c FROM qr_tokens").fetchone()
        current_count = row["c"] if row else 0
        if current_count > 0:
            return

        inserted = 0
        with csv_path.open("r", encoding="utf-8", newline="") as f:
            reader = csv.DictReader(f)
            for i, rec in enumerate(reader, start=1):
                token = (rec.get("token") or "").strip().upper()
                if not token:
                    continue
                receipt = f"RCP-{i:04d}"
                conn.execute(
                    """
                    INSERT OR IGNORE INTO qr_tokens(token, issued_for_receipt, issued_at, active_for_next_stage)
                    VALUES(?, ?, ?, 1)
                    """,
                    (token, receipt, now_iso()),
                )
                inserted += 1

        print(f"[BOOT] Seeded QR tokens from CSV: inserted={inserted}")


def migrate_stages_schema(conn: sqlite3.Connection) -> None:
    columns = {row["name"] for row in conn.execute("PRAGMA table_info(stages)").fetchall()}
    if "starts_at" not in columns:
        conn.execute("ALTER TABLE stages ADD COLUMN starts_at TEXT")
    if "ends_at" not in columns:
        conn.execute("ALTER TABLE stages ADD COLUMN ends_at TEXT")


def migrate_participants_schema(conn: sqlite3.Connection) -> None:
    columns = {row["name"] for row in conn.execute("PRAGMA table_info(participants)").fetchall()}
    if not columns:
        return
    if "like_repost_status" not in columns:
        conn.execute("ALTER TABLE participants ADD COLUMN like_repost_status TEXT NOT NULL DEFAULT 'unknown'")


def migrate_user_consents_schema(conn: sqlite3.Connection) -> None:
    columns = {row["name"] for row in conn.execute("PRAGMA table_info(user_consents)").fetchall()}
    if not columns:
        return
    if "consent_text" not in columns:
        conn.execute("ALTER TABLE user_consents ADD COLUMN consent_text TEXT NOT NULL DEFAULT ''")


def ensure_user(conn: sqlite3.Connection, user_id: int) -> None:
    conn.execute(
        "INSERT OR IGNORE INTO users(vk_user_id, first_seen_at) VALUES(?, ?)",
        (user_id, now_iso()),
    )


def has_consent(conn: sqlite3.Connection, user_id: int) -> bool:
    return bool(conn.execute("SELECT 1 FROM user_consents WHERE vk_user_id=?", (user_id,)).fetchone())


def save_consent(conn: sqlite3.Connection, user_id: int) -> None:
    ensure_user(conn, user_id)
    conn.execute(
        "INSERT OR REPLACE INTO user_consents(vk_user_id, accepted_at, consent_text) VALUES(?, ?, ?)",
        (user_id, now_iso(), CONSENT_TEXT),
    )


def active_stage(conn: sqlite3.Connection) -> sqlite3.Row | None:
    return conn.execute("SELECT * FROM stages WHERE status='active' LIMIT 1").fetchone()


def extract_token(text: str) -> str | None:
    match = re.search(r"(QR-[A-Za-z0-9_\-]+)", text or "")
    return match.group(1) if match else None


def extract_tokens(text: str) -> list[str]:
    found = re.findall(r"(QR-[A-Za-z0-9_\-]+)", text or "", flags=re.I)
    # Keep order and remove duplicates.
    unique: list[str] = []
    seen: set[str] = set()
    for token in found:
        normalized = token.upper()
        if normalized in seen:
            continue
        seen.add(normalized)
        unique.append(normalized)
    return unique


def build_dedup_keys(msg: dict, text: str) -> list[str]:
    keys: list[str] = []
    peer_id = msg.get("peer_id")
    cmid = msg.get("conversation_message_id")
    msg_id = msg.get("id")
    from_id = msg.get("from_id")
    ts = msg.get("date")

    if isinstance(peer_id, int) and isinstance(cmid, int):
        keys.append(f"cmid:{peer_id}:{cmid}")
    if isinstance(peer_id, int) and isinstance(msg_id, int):
        keys.append(f"msgid:{peer_id}:{msg_id}")
    if not keys and isinstance(from_id, int) and isinstance(ts, int):
        # Fallback signature is used only when stable VK IDs are absent.
        normalized = (text or "").strip().lower()
        keys.append(f"sig:{from_id}:{ts}:{hash(normalized)}")
    return keys


def extract_tokens_from_message(msg: dict, text: str) -> list[str]:
    # VK can pass deep-link token in different fields depending on client.
    tokens: list[str] = []
    tokens.extend(extract_tokens(msg.get("start") or ""))
    tokens.extend(extract_tokens(msg.get("ref") or ""))
    raw_payload = msg.get("payload") or ""
    tokens.extend(extract_tokens(raw_payload))
    try:
        payload_obj = json.loads(raw_payload) if isinstance(raw_payload, str) and raw_payload else {}
    except json.JSONDecodeError:
        payload_obj = {}
    if isinstance(payload_obj, dict):
        for field in ("start", "ref", "qr", "token"):
            value = payload_obj.get(field)
            if isinstance(value, str):
                tokens.extend(extract_tokens(value))
    # Keep order and remove duplicates.
    unique: list[str] = []
    seen: set[str] = set()
    for token in tokens:
        normalized = token.upper()
        if normalized in seen:
            continue
        seen.add(normalized)
        unique.append(normalized)
    return unique


def keyboard_consent() -> str:
    return json.dumps(
        {
            "one_time": False,
            "buttons": [
                [
                    {
                        "action": {"type": "text", "label": "Даю согласие", "payload": {"cmd": "accept_pd"}},
                        "color": "positive",
                    },
                    {"action": {"type": "open_link", "label": "Связаться с администратором", "link": ADMIN_CONTACT_LINK}},
                ]
            ],
        },
        ensure_ascii=False,
    )


def keyboard_main(include_admin: bool = False) -> str:
    buttons = [
        [
            {"action": {"type": "text", "label": "Мои шансы"}, "color": "primary"},
            {"action": {"type": "text", "label": "Правила"}, "color": "secondary"},
        ],
        [
            {"action": {"type": "text", "label": "Проверить QR", "payload": {"cmd": "activate_pending"}}, "color": "secondary"},
        ],
        [{"action": {"type": "open_link", "label": "Связаться с администратором", "link": ADMIN_CONTACT_LINK}}],
    ]
    if include_admin:
        buttons.append(
            [{"action": {"type": "text", "label": "Админ-панель", "payload": {"cmd": "admin_open"}}, "color": "secondary"}]
        )
    return json.dumps({"one_time": False, "buttons": buttons}, ensure_ascii=False)


def keyboard_qr_entry() -> str:
    return json.dumps(
        {
            "one_time": False,
            "buttons": [
                [{"action": {"type": "text", "label": "Участвовать в розыгрыше", "payload": {"cmd": "join_raffle"}}, "color": "positive"}],
                [{"action": {"type": "text", "label": "Проверить QR", "payload": {"cmd": "activate_pending"}}, "color": "secondary"}],
                [{"action": {"type": "open_link", "label": "Связаться с администратором", "link": ADMIN_CONTACT_LINK}}],
            ],
        },
        ensure_ascii=False,
    )


def keyboard_phone_entry() -> str:
    return json.dumps(
        {
            "one_time": False,
            "buttons": [
                [{"action": {"type": "open_link", "label": "Связаться с администратором", "link": ADMIN_CONTACT_LINK}}],
            ],
        },
        ensure_ascii=False,
    )


def keyboard_admin_panel() -> str:
    return json.dumps(
        {
            "one_time": False,
            "buttons": [
                [
                    {"action": {"type": "text", "label": "Запустить розыгрыш", "payload": {"cmd": "admin_next_stage"}}, "color": "positive"},
                ],
                [
                    {"action": {"type": "text", "label": "Экспорт Excel", "payload": {"cmd": "admin_export_excel"}}, "color": "secondary"},
                    {"action": {"type": "text", "label": "Участники CSV", "payload": {"cmd": "admin_export_csv"}}, "color": "secondary"},
                ],
                [
                    {"action": {"type": "text", "label": "Статистика", "payload": {"cmd": "admin_summary"}}, "color": "secondary"},
                ],
                [
                    {"action": {"type": "text", "label": "Новый цикл розыгрыша", "payload": {"cmd": "admin_reset_cycle"}}, "color": "negative"},
                ],
                [
                    {"action": {"type": "text", "label": "В меню", "payload": {"cmd": "admin_back"}}, "color": "secondary"},
                ],
            ],
        },
        ensure_ascii=False,
    )


def parse_iso_datetime(value: str) -> dt.datetime | None:
    candidate = (value or "").strip()
    if not candidate:
        return None
    if candidate.endswith("Z"):
        candidate = candidate[:-1] + "+00:00"
    try:
        parsed = dt.datetime.fromisoformat(candidate)
    except ValueError:
        return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=dt.timezone.utc)
    return parsed.astimezone(dt.timezone.utc)


def format_stage(row: sqlite3.Row) -> str:
    starts = row["starts_at"] or "не задано"
    ends = row["ends_at"] or "не задано"
    return f"Этап {row['stage_no']}: {row['status']} | старт: {starts} | стоп: {ends}"


def stages_overview(conn: sqlite3.Connection) -> str:
    rows = conn.execute("SELECT stage_no, status, starts_at, ends_at FROM stages ORDER BY stage_no").fetchall()
    if not rows:
        return "Этапы не настроены."
    return "\n".join(format_stage(row) for row in rows)


def notify_many(vk, user_ids: set[int], text: str) -> tuple[int, int]:
    ok_count = 0
    fail_count = 0
    for uid in sorted(user_ids):
        try:
            vk.messages.send(user_id=uid, message=text, random_id=get_random_id())
            ok_count += 1
        except Exception:
            fail_count += 1
    return ok_count, fail_count


def reminder_sent(conn: sqlite3.Connection, reminder_key: str) -> bool:
    row = conn.execute("SELECT 1 FROM reminders_log WHERE reminder_key=?", (reminder_key,)).fetchone()
    return bool(row)


def mark_reminder_sent(conn: sqlite3.Connection, reminder_key: str) -> None:
    conn.execute(
        "INSERT OR IGNORE INTO reminders_log(reminder_key, created_at) VALUES(?, ?)",
        (reminder_key, now_iso()),
    )


def stage_participant_ids(conn: sqlite3.Connection) -> set[int]:
    rows = conn.execute(
        """
        SELECT DISTINCT used_by_vk_id AS vk_user_id
        FROM qr_tokens
        WHERE is_used=1 AND active_for_next_stage=1 AND used_by_vk_id IS NOT NULL
        """
    ).fetchall()
    return {int(row["vk_user_id"]) for row in rows}


def process_stage_reminders(conn: sqlite3.Connection, vk) -> None:
    stage = active_stage(conn)
    if not stage:
        return
    ends_at = parse_iso_datetime(stage["ends_at"] or "")
    if not ends_at:
        return

    now = dt.datetime.now(dt.timezone.utc)
    today = now.date()
    days_left = (ends_at.date() - today).days
    stage_no = int(stage["stage_no"])
    participants = stage_participant_ids(conn)

    participant_messages = {
        5: f"⏳ До розыгрыша этапа {stage_no} осталось 5 дней!\nПора активировать последние QR-коды и увеличить свои шансы 🚀",
        1: f"🔥 Уже завтра розыгрыш этапа {stage_no}!\nПроверьте — все ли ваши QR-коды активированы?",
        0: f"🎯 Сегодня день розыгрыша этапа {stage_no}!\nСовсем скоро определим победителей 🏆",
    }
    if days_left in participant_messages and participants:
        p_key = f"participants:stage:{stage_no}:d{days_left}"
        if not reminder_sent(conn, p_key):
            ok, fail = notify_many(vk, participants, participant_messages[days_left])
            mark_reminder_sent(conn, p_key)
            log_event("participant_reminder", f"stage={stage_no}; d={days_left}; ok={ok}; fail={fail}")

    if VK_ADMIN_IDS:
        if days_left == 0:
            a_key = f"admins:stage:{stage_no}:today"
            if not reminder_sent(conn, a_key):
                ok, fail = notify_many(
                    vk,
                    set(VK_ADMIN_IDS),
                    f"Напоминание администратору: сегодня розыгрыш этапа {stage_no}. "
                    "Нажмите кнопку «Запустить розыгрыш».",
                )
                mark_reminder_sent(conn, a_key)
                log_event("admin_reminder", f"stage={stage_no}; today; ok={ok}; fail={fail}")
        elif days_left < 0:
            overdue_key = f"admins:stage:{stage_no}:overdue:{today.isoformat()}"
            if not reminder_sent(conn, overdue_key):
                ok, fail = notify_many(
                    vk,
                    set(VK_ADMIN_IDS),
                    f"Этап {stage_no} уже просрочен. Нажмите «Запустить розыгрыш», чтобы завершить этап и перейти дальше.",
                )
                mark_reminder_sent(conn, overdue_key)
                log_event("admin_reminder", f"stage={stage_no}; overdue; ok={ok}; fail={fail}")


def reminders_worker(vk) -> None:
    interval = max(60, REMINDER_INTERVAL_SEC)
    while True:
        try:
            with db() as conn:
                process_stage_reminders(conn, vk)
        except Exception as exc:
            print(f"[WARN] Reminder worker error: {exc}")
        time.sleep(interval)


def create_excel_report(conn: sqlite3.Connection, output_path: Path) -> None:
    if Workbook is None:
        raise RuntimeError("Для экспорта в Excel установите openpyxl: pip install openpyxl")
    wb = Workbook()
    ws_main = wb.active
    ws_main.title = "Summary"
    ws_main.append(["Metric", "Value"])
    users = conn.execute("SELECT COUNT(*) AS c FROM users").fetchone()["c"]
    issued = conn.execute("SELECT COUNT(*) AS c FROM qr_tokens").fetchone()["c"]
    used = conn.execute("SELECT COUNT(*) AS c FROM qr_tokens WHERE is_used=1").fetchone()["c"]
    winners = conn.execute("SELECT COUNT(*) AS c FROM qr_tokens WHERE is_winner=1").fetchone()["c"]
    ws_main.append(["Users", users])
    ws_main.append(["Issued QR", issued])
    ws_main.append(["Activated QR", used])
    ws_main.append(["Winner QR", winners])
    ws_main.append([])
    ws_main.append(["Stages"])
    ws_main.append(["Stage", "Status", "Starts At", "Ends At"])
    for row in conn.execute("SELECT stage_no, status, starts_at, ends_at FROM stages ORDER BY stage_no").fetchall():
        ws_main.append([row["stage_no"], row["status"], row["starts_at"], row["ends_at"]])

    ws_draws = wb.create_sheet("Draws")
    ws_draws.append(["Draw ID", "Stage", "Winners Count", "Drawn At"])
    for row in conn.execute("SELECT id, stage_no, winners_count, drawn_at FROM draws ORDER BY id").fetchall():
        ws_draws.append([row["id"], row["stage_no"], row["winners_count"], row["drawn_at"]])

    ws_winners = wb.create_sheet("Winners")
    ws_winners.append(["Draw ID", "Stage", "Token", "VK User ID"])
    for row in conn.execute(
        """
        SELECT dw.draw_id, d.stage_no, qt.token, dw.vk_user_id
        FROM draw_winners dw
        JOIN draws d ON d.id = dw.draw_id
        JOIN qr_tokens qt ON qt.id = dw.token_id
        ORDER BY dw.draw_id, dw.id
        """
    ).fetchall():
        ws_winners.append([row["draw_id"], row["stage_no"], row["token"], row["vk_user_id"]])

    ws_tokens = wb.create_sheet("Tokens")
    ws_tokens.append(["Token", "Receipt", "Issued At", "Used", "Used By", "Used At", "Active Next Stage", "Winner"])
    for row in conn.execute(
        """
        SELECT token, issued_for_receipt, issued_at, is_used, used_by_vk_id, used_at, active_for_next_stage, is_winner
        FROM qr_tokens
        ORDER BY id
        """
    ).fetchall():
        ws_tokens.append(
            [
                row["token"],
                row["issued_for_receipt"],
                row["issued_at"],
                int(row["is_used"]),
                row["used_by_vk_id"],
                row["used_at"],
                int(row["active_for_next_stage"]),
                int(row["is_winner"]),
            ]
        )

    wb.save(output_path)


def send_document(vk, user_id: int, file_path: Path, title: str, message: str = "Готово: файл сформирован.") -> None:
    upload = vk.docs.getMessagesUploadServer(type="doc", peer_id=user_id)
    with file_path.open("rb") as f:
        import requests

        response = requests.post(upload["upload_url"], files={"file": f}, timeout=30)
    response.raise_for_status()
    file_token = response.json()["file"]
    saved = vk.docs.save(file=file_token, title=title)
    doc = saved["doc"]
    attachment = f"doc{doc['owner_id']}_{doc['id']}"
    vk.messages.send(user_id=user_id, random_id=get_random_id(), message=message, attachment=attachment)


def create_participants_csv(conn: sqlite3.Connection, output_path: Path) -> None:
    rows = conn.execute(
        """
        SELECT
            p.vk_user_id,
            p.full_name,
            p.phone,
            p.participation_status AS status,
            p.participant_number,
            p.created_at,
            COALESCE(COUNT(a.id), 0) AS qr_count,
            COALESCE(COUNT(a.id), 0) AS chances,
            CASE
                WHEN EXISTS(SELECT 1 FROM participant_draw_winners pdw WHERE pdw.vk_user_id = p.vk_user_id)
                     OR EXISTS(SELECT 1 FROM draw_winners dw WHERE dw.vk_user_id = p.vk_user_id)
                THEN 1 ELSE 0
            END AS is_winner
        FROM participants p
        LEFT JOIN activations a ON a.vk_user_id = p.vk_user_id
        GROUP BY p.vk_user_id, p.full_name, p.phone, p.participation_status, p.participant_number, p.created_at
        ORDER BY created_at
        """
    ).fetchall()
    with output_path.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.writer(f, delimiter=";")
        writer.writerow(
            [
                "VK ID",
                "ФИО",
                "Телефон",
                "Статус",
                "Кол-во QR",
                "Шансы",
                "Номер участника",
                "Дата регистрации",
                "Победитель",
            ]
        )
        for row in rows:
            writer.writerow(
                [
                    row["vk_user_id"],
                    row["full_name"],
                    row["phone"],
                    row["status"],
                    row["qr_count"],
                    row["chances"],
                    row["participant_number"],
                    row["created_at"],
                    "да" if int(row["is_winner"]) else "нет",
                ]
            )


def run_participant_draw(conn: sqlite3.Connection, winners_count: int) -> tuple[bool, str, set[int]]:
    if winners_count <= 0:
        return False, "Количество победителей должно быть больше нуля.", set()
    pool = conn.execute(
        """
        SELECT vk_user_id, participant_number
        FROM participants
        WHERE participation_status='registered'
        """
    ).fetchall()
    if not pool:
        return False, "Нет зарегистрированных участников для розыгрыша.", set()
    if winners_count > len(pool):
        return False, "Победителей больше, чем участников в пуле.", set()
    selected = secrets.SystemRandom().sample(pool, winners_count)
    draw_id = conn.execute(
        "INSERT INTO participant_draws(winners_count, created_at) VALUES(?, ?)",
        (winners_count, now_iso()),
    ).lastrowid
    winner_ids: set[int] = set()
    numbers: list[str] = []
    for row in selected:
        conn.execute(
            "INSERT INTO participant_draw_winners(draw_id, vk_user_id, participant_number) VALUES(?, ?, ?)",
            (draw_id, row["vk_user_id"], row["participant_number"] or 0),
        )
        winner_ids.add(int(row["vk_user_id"]))
        numbers.append(str(row["participant_number"] or "-"))
    log_event("participant_draw", f"draw_id={draw_id}; winners={len(winner_ids)}")
    return True, f"Розыгрыш участников выполнен. Победители: {len(winner_ids)}. Номера: {', '.join(numbers)}", winner_ids

def keyboard_activate_pending() -> str:
    return json.dumps(
        {
            "one_time": False,
            "buttons": [
                [
                    {
                        "action": {"type": "text", "label": "Активировать автоматически", "payload": {"cmd": "activate_pending"}},
                        "color": "positive",
                    }
                ],
                [{"action": {"type": "text", "label": "Правила"}, "color": "secondary"}],
            ],
        },
        ensure_ascii=False,
    )


def keyboard_start_from_qr() -> str:
    return json.dumps(
        {
            "one_time": False,
            "buttons": [
                [
                    {
                        "action": {"type": "text", "label": "Старт", "payload": {"cmd": "start_qr_flow"}},
                        "color": "positive",
                    }
                ]
            ],
        },
        ensure_ascii=False,
    )


def send(vk, user_id: int, text: str, keyboard: str | None = None) -> None:
    params = {"user_id": user_id, "message": text, "random_id": get_random_id()}
    if keyboard:
        params["keyboard"] = keyboard
    try:
        vk.messages.send(**params)
    except Exception as exc:
        # Do not tear down LongPoll loop because of a transient send failure.
        print(f"[WARN] Send failed for user {user_id}: {exc}")


def save_pending_token(conn: sqlite3.Connection, user_id: int, token: str) -> None:
    token = (token or "").strip().upper()
    conn.execute(
        """
        INSERT OR REPLACE INTO pending_tokens(vk_user_id, token, created_at)
        VALUES(?, ?, ?)
        """,
        (user_id, token, now_iso()),
    )


def pop_pending_token(conn: sqlite3.Connection, user_id: int) -> str | None:
    row = conn.execute("SELECT token FROM pending_tokens WHERE vk_user_id=?", (user_id,)).fetchone()
    if not row:
        return None
    conn.execute("DELETE FROM pending_tokens WHERE vk_user_id=?", (user_id,))
    return row["token"]


def peek_pending_token(conn: sqlite3.Connection, user_id: int) -> str | None:
    row = conn.execute("SELECT token FROM pending_tokens WHERE vk_user_id=?", (user_id,)).fetchone()
    return row["token"] if row else None


def set_admin_state(conn: sqlite3.Connection, user_id: int, state: str, data: dict | None = None) -> None:
    conn.execute(
        """
        INSERT OR REPLACE INTO admin_states(vk_user_id, state, data_json, updated_at)
        VALUES(?, ?, ?, ?)
        """,
        (user_id, state, json.dumps(data or {}, ensure_ascii=False), now_iso()),
    )


def get_admin_state(conn: sqlite3.Connection, user_id: int) -> tuple[str, dict] | None:
    row = conn.execute("SELECT state, data_json FROM admin_states WHERE vk_user_id=?", (user_id,)).fetchone()
    if not row:
        return None
    try:
        data = json.loads(row["data_json"] or "{}")
    except json.JSONDecodeError:
        data = {}
    return row["state"], data


def clear_admin_state(conn: sqlite3.Connection, user_id: int) -> None:
    conn.execute("DELETE FROM admin_states WHERE vk_user_id=?", (user_id,))


def set_user_state(conn: sqlite3.Connection, user_id: int, state: str, data: dict | None = None) -> None:
    conn.execute(
        """
        INSERT OR REPLACE INTO user_states(vk_user_id, state, data_json, updated_at)
        VALUES(?, ?, ?, ?)
        """,
        (user_id, state, json.dumps(data or {}, ensure_ascii=False), now_iso()),
    )


def get_user_state(conn: sqlite3.Connection, user_id: int) -> tuple[str, dict] | None:
    row = conn.execute("SELECT state, data_json FROM user_states WHERE vk_user_id=?", (user_id,)).fetchone()
    if not row:
        return None
    try:
        data = json.loads(row["data_json"] or "{}")
    except json.JSONDecodeError:
        data = {}
    return row["state"], data


def clear_user_state(conn: sqlite3.Connection, user_id: int) -> None:
    conn.execute("DELETE FROM user_states WHERE vk_user_id=?", (user_id,))


def normalize_phone(raw_phone: str) -> str | None:
    cleaned = re.sub(r"\D+", "", raw_phone or "")
    if len(cleaned) == 11 and cleaned.startswith("8"):
        cleaned = "7" + cleaned[1:]
    if len(cleaned) == 11 and cleaned.startswith("7"):
        return f"+{cleaned}"
    return None


def is_rate_limited(user_id: int, now_ts: float) -> bool:
    prev_ts = LAST_USER_MESSAGE_TS.get(user_id)
    LAST_USER_MESSAGE_TS[user_id] = now_ts
    if prev_ts is None:
        return False
    return (now_ts - prev_ts) < USER_MESSAGE_RATE_LIMIT_SEC


def is_manual_qr_text(text: str) -> bool:
    return bool(re.fullmatch(r"\s*QR-[A-Za-z0-9_\-]+\s*", text or "", flags=re.I))


def is_consent_signal(cmd: str | None, low_text: str) -> bool:
    if cmd == "accept_pd":
        return True
    normalized = (low_text or "").strip()
    if normalized in {"согласен", "даю согласие"}:
        return True
    return bool(re.search(r"даю\s+соглас", normalized, flags=re.I))


def is_phone_used_by_other(conn: sqlite3.Connection, phone: str, user_id: int) -> bool:
    row = conn.execute("SELECT vk_user_id FROM participants WHERE phone=?", (phone,)).fetchone()
    if not row:
        return False
    return int(row["vk_user_id"]) != user_id


def participant_row(conn: sqlite3.Connection, user_id: int) -> sqlite3.Row | None:
    return conn.execute("SELECT * FROM participants WHERE vk_user_id=?", (user_id,)).fetchone()


def participant_registered(conn: sqlite3.Connection, user_id: int) -> bool:
    row = participant_row(conn, user_id)
    return bool(row and row["participation_status"] == "registered")


def next_participant_number(conn: sqlite3.Connection) -> int:
    row = conn.execute("SELECT COALESCE(MAX(participant_number), 0) + 1 AS n FROM participants").fetchone()
    return int(row["n"])


def save_participant_draft(conn: sqlite3.Connection, user_id: int, full_name: str, phone: str) -> None:
    existing = participant_row(conn, user_id)
    created_at = existing["created_at"] if existing else now_iso()
    number = existing["participant_number"] if existing else None
    conn.execute(
        """
        INSERT OR REPLACE INTO participants(
            vk_user_id, full_name, phone, is_subscriber, like_repost_status, participation_status,
            participant_number, created_at, updated_at
        )
        VALUES(
            ?, ?, ?, COALESCE((SELECT is_subscriber FROM participants WHERE vk_user_id=?), 0),
            COALESCE((SELECT like_repost_status FROM participants WHERE vk_user_id=?), 'unknown'),
            COALESCE((SELECT participation_status FROM participants WHERE vk_user_id=?), 'draft'),
            ?, ?, ?
        )
        """,
        (user_id, full_name, phone, user_id, user_id, user_id, number, created_at, now_iso()),
    )


def check_subscription(vk, user_id: int) -> tuple[bool, str]:
    try:
        member = vk.groups.isMember(group_id=VK_GROUP_ID, user_id=user_id)
    except Exception as exc:
        return False, f"vk_error:{exc}"
    return bool(member), "ok" if member else "not_subscribed"


def check_like_repost(vk, user_id: int) -> tuple[str, str]:
    if not RAFFLE_POST_ID:
        return "unknown", "post_not_configured"
    try:
        reposted = vk.wall.isReposted(owner_id=RAFFLE_POST_OWNER_ID or -VK_GROUP_ID, post_id=RAFFLE_POST_ID, user_id=user_id)
        if reposted == 1:
            return "ok", "reposted"
        return "failed", "not_reposted"
    except Exception as exc:
        return "unknown", f"vk_error:{exc}"


def recheck_participant_conditions(conn: sqlite3.Connection, vk, user_id: int) -> tuple[bool, str]:
    row = participant_row(conn, user_id)
    if not row:
        return False, "Сначала пройдите регистрацию."
    is_sub, sub_details = check_subscription(vk, user_id)
    like_status, like_details = check_like_repost(vk, user_id)
    conn.execute(
        "INSERT INTO participant_checks(vk_user_id, check_type, check_result, details, checked_at) VALUES(?, 'subscription', ?, ?, ?)",
        (user_id, "ok" if is_sub else "failed", sub_details, now_iso()),
    )
    conn.execute(
        "INSERT INTO participant_checks(vk_user_id, check_type, check_result, details, checked_at) VALUES(?, 'like_repost', ?, ?, ?)",
        (user_id, like_status, like_details, now_iso()),
    )
    status = "registered" if is_sub else "pending_conditions"
    participant_number = row["participant_number"]
    if status == "registered" and not participant_number:
        participant_number = next_participant_number(conn)
    conn.execute(
        """
        UPDATE participants
        SET is_subscriber=?, like_repost_status=?, participation_status=?, participant_number=COALESCE(participant_number, ?), updated_at=?
        WHERE vk_user_id=?
        """,
        (int(is_sub), like_status, status, participant_number, now_iso(), user_id),
    )
    log_event("conditions_check", f"user={user_id}; sub={int(is_sub)}; repost={like_status}; status={status}")
    if status == "registered":
        log_event("participant_registered", f"user={user_id}; number={participant_number}")
        return True, f"Участие подтверждено. Ваш номер участника: {participant_number}."
    return False, "Пока не выполнены условия: требуется подписка на сообщество. Подпишитесь и нажмите «Проверить условия»."


def fetch_vk_full_name(vk, user_id: int) -> str:
    try:
        users = vk.users.get(user_ids=user_id)
        if users:
            first_name = (users[0].get("first_name") or "").strip()
            last_name = (users[0].get("last_name") or "").strip()
            full_name = f"{first_name} {last_name}".strip()
            if full_name:
                return full_name
    except Exception:
        pass
    return "Имя не указано"

def activate_token(conn: sqlite3.Connection, token: str, user_id: int) -> tuple[bool, str]:
    token = (token or "").strip().upper()
    stage = active_stage(conn)
    if not stage:
        return False, "Сейчас нет активного этапа розыгрыша."
    row = conn.execute("SELECT * FROM qr_tokens WHERE UPPER(token)=?", (token,)).fetchone()
    if not row:
        return False, "QR-код не найден. Проверьте и попробуйте снова."
    if row["is_used"]:
        if int(row["used_by_vk_id"] or 0) == user_id:
            return False, "Этот QR уже был активирован вами ранее. Повторно шанс не начисляется."
        return False, "Этот QR-код уже активирован другим участником."
    if row["active_for_next_stage"] == 0:
        return False, "Этот QR-код больше не участвует в розыгрыше."

    ensure_user(conn, user_id)
    conn.execute(
        "UPDATE qr_tokens SET is_used=1, used_by_vk_id=?, used_at=? WHERE id=?",
        (user_id, now_iso(), row["id"]),
    )
    conn.execute(
        "INSERT INTO activations(token_id, vk_user_id, activated_at) VALUES(?, ?, ?)",
        (row["id"], user_id, now_iso()),
    )
    total = conn.execute(
        "SELECT COUNT(*) AS c FROM activations WHERE vk_user_id=?",
        (user_id,),
    ).fetchone()["c"]
    return (
        True,
        "🎉 Есть контакт!\n"
        "QR-код успешно активирован.\n\n"
        "➕ +1 шанс добавлен к вашему балансу\n"
        f"🎯 Всего шансов: {total}\n\n"
        "Продолжайте — каждый новый код увеличивает вероятность победы! 🍀",
    )


def activate_tokens(conn: sqlite3.Connection, tokens: list[str], user_id: int) -> tuple[int, list[str]]:
    success_count = 0
    messages: list[str] = []
    for token in tokens:
        ok, text = activate_token(conn, token, user_id)
        if ok:
            success_count += 1
            messages.append(f"{token}: успешно")
        else:
            messages.append(f"{token}: {text}")
    return success_count, messages


def run_draw_for_stage(conn: sqlite3.Connection, stage_no: int, winners_count: int) -> tuple[bool, str, set[int], set[int]]:
    if winners_count <= 0:
        return False, "Количество победителей должно быть больше нуля.", set(), set()
    stage = conn.execute("SELECT * FROM stages WHERE stage_no=?", (stage_no,)).fetchone()
    if not stage:
        return False, "Этап не найден.", set(), set()
    if stage["status"] != "active":
        return False, "Розыгрыш можно проводить только для активного этапа.", set(), set()

    candidates = conn.execute(
        """
        SELECT id AS token_id, used_by_vk_id AS vk_user_id
        FROM qr_tokens
        WHERE is_used=1 AND active_for_next_stage=1 AND is_winner=0
        """
    ).fetchall()
    if not candidates:
        return False, "Нет кандидатов для розыгрыша.", set(), set()
    if winners_count > len(candidates):
        return False, "Победителей больше, чем доступных кандидатов.", set(), set()

    selected = secrets.SystemRandom().sample(candidates, winners_count)
    draw_id = conn.execute(
        "INSERT INTO draws(stage_no, winners_count, drawn_at) VALUES(?, ?, ?)",
        (stage_no, winners_count, now_iso()),
    ).lastrowid

    all_user_ids = {int(row["vk_user_id"]) for row in candidates if row["vk_user_id"]}
    winner_user_ids: set[int] = set()
    for s in selected:
        conn.execute(
            "INSERT INTO draw_winners(draw_id, token_id, vk_user_id) VALUES(?, ?, ?)",
            (draw_id, s["token_id"], s["vk_user_id"]),
        )
        conn.execute(
            "UPDATE qr_tokens SET is_winner=1, active_for_next_stage=0 WHERE id=?",
            (s["token_id"],),
        )
        winner_user_ids.add(int(s["vk_user_id"]))
    loser_user_ids = all_user_ids - winner_user_ids
    conn.execute("UPDATE stages SET status='closed' WHERE stage_no=?", (stage_no,))
    return True, f"Розыгрыш этапа {stage_no} завершен. Победителей: {len(winner_user_ids)}.", winner_user_ids, loser_user_ids


def start_stage_with_notifications(conn: sqlite3.Connection, vk, stage_no: int) -> str:
    row = conn.execute("SELECT starts_at, ends_at FROM stages WHERE stage_no=?", (stage_no,)).fetchone()
    if not row:
        return "Этап не найден."
    starts_at = parse_iso_datetime(row["starts_at"] or "")
    ends_at = parse_iso_datetime(row["ends_at"] or "")
    now = dt.datetime.now(dt.timezone.utc)
    if starts_at and now < starts_at:
        return "Слишком рано: текущая дата меньше даты старта этапа."
    if ends_at and now > ends_at:
        return "Этап уже просрочен по дате окончания. Сначала обновите сроки."

    result = handle_admin(conn, f"/stage_activate {stage_no}") or "Ошибка запуска этапа."
    participants = {
        int(row["vk_user_id"])
        for row in conn.execute("SELECT DISTINCT vk_user_id FROM activations WHERE vk_user_id IS NOT NULL").fetchall()
    }
    if participants and result == "Этап активирован.":
        p_ok, p_fail = notify_many(
            vk,
            participants,
            f"Этап {stage_no} розыгрыша Avatar Arena Omsk VR официально стартовал!\n"
            "Вы участвуете, потому что у вас есть активированные купоны.\n"
            "Удачи! 🍀",
        )
        result = f"{result}\nУведомлены участники: {p_ok}, ошибок доставки: {p_fail}"
    return result


def stop_stage(conn: sqlite3.Connection, stage_no: int) -> str:
    return handle_admin(conn, f"/stage_close {stage_no}") or "Ошибка остановки этапа."


def run_stage_draw_with_notifications(conn: sqlite3.Connection, vk, stage_no: int, winners_count: int) -> tuple[bool, str]:
    ok, result, winners_user_ids, losers_user_ids = run_draw_for_stage(conn, stage_no, winners_count)
    if not ok:
        return False, result or "Ошибка розыгрыша."
    winner_text = (
        "🏆 ВЫ ПОБЕДИЛИ!!!\n\n"
        f"Ваш купон стал выигрышным в этапе {stage_no} 🎉\n\n"
        "🔥 Поздравляем! Вы среди лучших!\n"
        "С вами свяжется администратор для получения приза.\n\n"
        "Спасибо за участие 💙"
    )
    loser_text = (
        f"⏳ Этап {stage_no} завершён.\n\n"
        "В этот раз удача прошла мимо, но это ещё не конец!\n"
        "Ваши шансы могут сыграть в следующих этапах 🍀\n\n"
        "Не останавливайтесь — победа может быть совсем рядом!"
    )
    w_ok, w_fail = notify_many(vk, winners_user_ids, winner_text)
    l_ok, l_fail = notify_many(vk, losers_user_ids, loser_text)
    return True, (
        f"{result}\n"
        f"Уведомления отправлены:\n"
        f"- победителям: {w_ok}, ошибок: {w_fail}\n"
        f"- остальным участникам: {l_ok}, ошибок: {l_fail}"
    )


def advance_to_next_stage(conn: sqlite3.Connection, vk, winners_count: int) -> str:
    now = dt.datetime.now(dt.timezone.utc)
    current = active_stage(conn)
    parts: list[str] = []

    if current:
        current_no = int(current["stage_no"])
        draw_ok, draw_result = run_stage_draw_with_notifications(conn, vk, current_no, winners_count)
        if not draw_ok:
            return (
                f"Не удалось завершить этап {current_no}: {draw_result}\n"
                "Переход к следующему этапу отменен."
            )
        parts.append(f"Этап {current_no} завершен.\n{draw_result}")
        next_no = current_no + 1
    else:
        row = conn.execute(
            "SELECT stage_no FROM stages WHERE status='planned' ORDER BY stage_no LIMIT 1"
        ).fetchone()
        if not row:
            return "Нет этапов для запуска: все этапы завершены."
        next_no = int(row["stage_no"])
        parts.append("Активного этапа не было. Запускаю ближайший запланированный этап.")

    if next_no > 3:
        parts.append("Это был последний этап. Все этапы завершены.")
        return "\n\n".join(parts)

    starts_at = now
    ends_at = now + dt.timedelta(days=30)
    conn.execute(
        "UPDATE stages SET starts_at=?, ends_at=?, status='planned' WHERE stage_no=?",
        (starts_at.isoformat(), ends_at.isoformat(), next_no),
    )
    start_result = start_stage_with_notifications(conn, vk, next_no)
    parts.append(
        f"Запуск этапа {next_no}:\n{start_result}\n"
        f"Сроки: {starts_at.isoformat()} — {ends_at.isoformat()}"
    )
    return "\n\n".join(parts)


def reset_raffle_cycle(conn: sqlite3.Connection) -> str:
    conn.execute("UPDATE stages SET status='planned', starts_at=NULL, ends_at=NULL")
    conn.execute("DELETE FROM draws")
    conn.execute("DELETE FROM draw_winners")
    conn.execute("DELETE FROM reminders_log")
    conn.execute("DELETE FROM activations")
    conn.execute("DELETE FROM pending_tokens")
    conn.execute(
        """
        UPDATE qr_tokens
        SET is_used=0, used_by_vk_id=NULL, used_at=NULL, is_winner=0, active_for_next_stage=1
        """
    )
    return "Новый цикл розыгрыша подготовлен: этапы и активации сброшены."


def handle_admin(conn: sqlite3.Connection, text: str) -> str | None:
    parts = text.strip().split()
    if not parts:
        return None
    cmd = parts[0].lower()

    if cmd == "/stage_activate" and len(parts) == 2:
        if not parts[1].isdigit():
            return "Номер этапа должен быть числом."
        stage_no = int(parts[1])
        if active_stage(conn):
            return "Сначала закройте текущий активный этап."
        updated = conn.execute(
            "UPDATE stages SET status='active' WHERE stage_no=? AND status IN ('planned','closed')",
            (stage_no,),
        ).rowcount
        return "Этап активирован." if updated else "Не удалось активировать этап."

    if cmd == "/stage_close" and len(parts) == 2:
        if not parts[1].isdigit():
            return "Номер этапа должен быть числом."
        stage_no = int(parts[1])
        updated = conn.execute(
            "UPDATE stages SET status='closed' WHERE stage_no=? AND status='active'",
            (stage_no,),
        ).rowcount
        return "Этап закрыт." if updated else "Активный этап не найден."

    if cmd == "/draw" and len(parts) == 3:
        if not parts[1].isdigit() or not parts[2].isdigit():
            return "Этап и количество победителей должны быть числами."
        stage_no = int(parts[1])
        winners_count = int(parts[2])
        ok, message, _, _ = run_draw_for_stage(conn, stage_no, winners_count)
        return message if ok else message

    if cmd == "/summary":
        users = conn.execute("SELECT COUNT(*) AS c FROM users").fetchone()["c"]
        issued = conn.execute("SELECT COUNT(*) AS c FROM qr_tokens").fetchone()["c"]
        used = conn.execute("SELECT COUNT(*) AS c FROM qr_tokens WHERE is_used=1").fetchone()["c"]
        winners = conn.execute("SELECT COUNT(*) AS c FROM qr_tokens WHERE is_winner=1").fetchone()["c"]
        participants_all = conn.execute("SELECT COUNT(*) AS c FROM participants").fetchone()["c"]
        participants_registered = conn.execute(
            "SELECT COUNT(*) AS c FROM participants WHERE participation_status='registered'"
        ).fetchone()["c"]
        participant_draws = conn.execute("SELECT COUNT(*) AS c FROM participant_draws").fetchone()["c"]
        return (
            f"Пользователи: {users}\n"
            f"QR выдано: {issued}\n"
            f"Активировано: {used}\n"
            f"Выигравших QR: {winners}\n"
            f"Участников всего: {participants_all}\n"
            f"Участников подтверждено: {participants_registered}\n"
            f"Розыгрышей участников: {participant_draws}"
        )

    return None


def main() -> None:
    if not VK_GROUP_TOKEN:
        raise RuntimeError("Set VK_GROUP_TOKEN env variable before running.")
    if not VK_GROUP_ID:
        raise RuntimeError("Set VK_GROUP_ID env variable before running.")

    acquire_single_instance_lock()
    ensure_persistent_db_seeded()
    init_db()
    seed_qr_tokens_if_empty()
    vk_session = vk_api.VkApi(token=VK_GROUP_TOKEN)
    vk = vk_session.get_api()
    longpoll = VkBotLongPoll(vk_session, VK_GROUP_ID)
    threading.Thread(target=reminders_worker, args=(vk,), daemon=True).start()

    print("VK bot started (LongPoll mode).")
    while True:
        try:
            for event in longpoll.listen():
                if event.type != VkBotEventType.MESSAGE_NEW:
                    continue
                msg = event.obj.message
                if msg.get("out") == 1:
                    continue

                user_id = msg.get("from_id")
                if not isinstance(user_id, int) or user_id <= 0:
                    # Skip non-user/system events to avoid DB/send failures.
                    continue
                text = (msg.get("text") or "").strip()
                dedup_keys = build_dedup_keys(msg, text)
                if dedup_keys and any(key in RECENT_MSG_KEYS for key in dedup_keys):
                    continue
                for key in dedup_keys:
                    RECENT_MSG_KEYS.add(key)
                if len(RECENT_MSG_KEYS) > 15000:
                    RECENT_MSG_KEYS.clear()
                token_hints = extract_tokens_from_message(msg, text)
                payload = {}
                raw_payload = msg.get("payload")
                if isinstance(raw_payload, dict):
                    payload = raw_payload
                elif isinstance(raw_payload, str) and raw_payload:
                    try:
                        payload = json.loads(raw_payload)
                    except (json.JSONDecodeError, TypeError):
                        payload = {}
                if not payload.get("cmd") and not token_hints and is_rate_limited(user_id, time.monotonic()):
                    continue

                with db() as conn:
                    ensure_user(conn, user_id)

                    is_admin = user_id in VK_ADMIN_IDS
                    low = text.lower()
                    cmd = payload.get("cmd")

                    # Gracefully handle stale buttons from older keyboards.
                    legacy_disabled_cmds = {
                        "admin_stage_schedule_start",
                        "admin_stage_start",
                        "admin_stage_stop",
                        "admin_draw_start",
                        "admin_participant_draw_start",
                        "admin_stage_start_1",
                        "admin_stage_start_2",
                        "admin_stage_start_3",
                        "admin_stage_stop_1",
                        "admin_stage_stop_2",
                        "admin_stage_stop_3",
                        "admin_draw_stage_1",
                        "admin_draw_stage_2",
                        "admin_draw_stage_3",
                    }
                    if is_admin and not payload.get("cmd"):
                        text_to_cmd = {
                            "админ-панель": "admin_open",
                            "админ": "admin_open",
                            "запустить розыгрыш": "admin_next_stage",
                            "следующий этап": "admin_next_stage",
                            "новый цикл розыгрыша": "admin_reset_cycle",
                            "экспорт excel": "admin_export_excel",
                            "участники csv": "admin_export_csv",
                            "статистика": "admin_summary",
                            "в меню": "admin_back",
                        }
                        if low in text_to_cmd:
                            payload["cmd"] = text_to_cmd[low]
                            cmd = payload["cmd"]

                    # Admin panel entry and payload actions
                    if is_admin and cmd in legacy_disabled_cmds:
                        send(
                            vk,
                            user_id,
                            "Кнопка из старой версии панели отключена.\n"
                            "Используйте актуальную кнопку «Запустить розыгрыш».",
                            keyboard=keyboard_admin_panel(),
                        )
                        continue
                    if is_admin and cmd == "admin_open":
                        clear_admin_state(conn, user_id)
                        send(
                            vk,
                            user_id,
                            "Панель администратора.\nВыберите действие кнопками ниже.",
                            keyboard=keyboard_admin_panel(),
                        )
                        continue
                    if is_admin and cmd == "admin_back":
                        clear_admin_state(conn, user_id)
                        send(vk, user_id, "Возвращаю в основное меню.", keyboard=keyboard_main(include_admin=is_admin))
                        continue
                    if is_admin and cmd == "admin_next_stage":
                        winners_count = DEFAULT_STAGE_WINNERS_COUNT if DEFAULT_STAGE_WINNERS_COUNT > 0 else 1
                        result = advance_to_next_stage(conn, vk, winners_count)
                        active = active_stage(conn)
                        if result.startswith("Не удалось") or result.startswith("Нет этапов"):
                            admin_text = f"⚠️ {result}"
                        else:
                            active_text = f"Этап {active['stage_no']} активен." if active else "Активного этапа сейчас нет."
                            admin_text = (
                                "✅ Этапы обновлены.\n"
                                f"{active_text}\n"
                                f"Победителей в следующем розыгрыше по умолчанию: {winners_count}."
                            )
                        send(
                            vk,
                            user_id,
                            f"{admin_text}\n\nЕсли нужны детали, нажмите «Статистика».",
                            keyboard=keyboard_admin_panel(),
                        )
                        continue
                    if is_admin and cmd == "admin_summary":
                        result = handle_admin(conn, "/summary")
                        send(vk, user_id, f"{result or 'Ошибка получения статистики.'}\n\n{stages_overview(conn)}", keyboard=keyboard_admin_panel())
                        continue
                    if is_admin and cmd == "admin_reset_cycle":
                        result = reset_raffle_cycle(conn)
                        send(vk, user_id, f"♻️ {result}\n\nНажмите «Запустить розыгрыш», чтобы стартовать этап 1.", keyboard=keyboard_admin_panel())
                        continue
                    if is_admin and cmd == "admin_export_excel":
                        try:
                            with tempfile.NamedTemporaryFile(prefix="raffle_report_", suffix=".xlsx", delete=False) as tmp:
                                report_path = Path(tmp.name)
                            create_excel_report(conn, report_path)
                            send_document(
                                vk,
                                user_id,
                                report_path,
                                f"raffle_report_{dt.datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx",
                                message="Готово: выгрузка Excel.",
                            )
                            try:
                                report_path.unlink(missing_ok=True)
                            except OSError:
                                pass
                        except Exception as exc:
                            send(vk, user_id, f"Не удалось сформировать/отправить Excel: {exc}", keyboard=keyboard_admin_panel())
                        continue
                    if is_admin and cmd == "admin_export_csv":
                        try:
                            with tempfile.NamedTemporaryFile(prefix="participants_", suffix=".csv", delete=False) as tmp:
                                report_path = Path(tmp.name)
                            create_participants_csv(conn, report_path)
                            send_document(
                                vk,
                                user_id,
                                report_path,
                                f"participants_{dt.datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                                message="Готово: выгрузка участников CSV.",
                            )
                            try:
                                report_path.unlink(missing_ok=True)
                            except OSError:
                                pass
                        except Exception as exc:
                            send(vk, user_id, f"Не удалось сформировать/отправить CSV: {exc}", keyboard=keyboard_admin_panel())
                        continue

                    consented = has_consent(conn, user_id)
                    user_state = get_user_state(conn, user_id)
                    if consented and is_consent_signal(cmd, low):
                        if participant_registered(conn, user_id):
                            send(
                                vk,
                                user_id,
                                "Согласие уже получено, регистрация завершена.\n"
                                "Вы уже участвуете в розыгрыше.",
                                keyboard=keyboard_main(include_admin=is_admin),
                            )
                        else:
                            set_user_state(conn, user_id, "await_phone")
                            send(
                                vk,
                                user_id,
                                "✅ Согласие уже зафиксировано.\n"
                                "Отправьте номер телефона в формате +79991234567 📱",
                                keyboard=keyboard_phone_entry(),
                            )
                        continue
                    if user_state:
                        if not consented:
                            clear_user_state(conn, user_id)
                            send(
                                vk,
                                user_id,
                                "Сначала подтвердите согласие на обработку персональных данных.",
                                keyboard=keyboard_consent(),
                            )
                            continue
                        state, data = user_state
                        if state == "await_phone":
                            if low in {"start", "/start", "начать", "привет", "старт"}:
                                clear_user_state(conn, user_id)
                                if consented:
                                    send(
                                        vk,
                                        user_id,
                                        "🚀 Добро пожаловать в мир Avatar Arena Omsk VR!\n"
                                        "Здесь начинается игра, где каждый шанс может стать победой 🏆\n\n"
                                        "Активируйте QR-коды, накапливайте шансы и забирайте призы!\n\n"
                                        "Готовы испытать удачу? Выбирайте действие ниже 👇",
                                        keyboard=keyboard_qr_entry(),
                                    )
                                else:
                                    send(
                                        vk,
                                        user_id,
                                        "🚀 Добро пожаловать в мир Avatar Arena Omsk VR!\n"
                                        "Здесь начинается игра, где каждый шанс может стать победой 🏆\n\n"
                                        "Активируйте QR-коды, накапливайте шансы и забирайте призы!\n\n"
                                        "Готовы испытать удачу? Выбирайте действие ниже 👇",
                                        keyboard=keyboard_qr_entry(),
                                    )
                                continue
                            phone = normalize_phone(text)
                            if not phone:
                                send(
                                    vk,
                                    user_id,
                                    "📱 Похоже, номер введен некорректно.\n"
                                    "Пожалуйста, введите телефон в формате: +79991234567",
                                    keyboard=keyboard_phone_entry(),
                                )
                                continue
                            if is_phone_used_by_other(conn, phone, user_id):
                                send(
                                    vk,
                                    user_id,
                                    "Этот номер уже зарегистрирован другим участником. "
                                    "По правилам 1 телефон = 1 участник.",
                                    keyboard=keyboard_phone_entry(),
                                )
                                continue
                            full_name = fetch_vk_full_name(vk, user_id)
                            save_participant_draft(conn, user_id, full_name, phone)
                            participant = participant_row(conn, user_id)
                            participant_number = participant["participant_number"] if participant else None
                            if not participant_number:
                                participant_number = next_participant_number(conn)
                            conn.execute(
                                """
                                UPDATE participants
                                SET participation_status='registered', is_subscriber=1, participant_number=COALESCE(participant_number, ?), updated_at=?
                                WHERE vk_user_id=?
                                """,
                                (participant_number, now_iso(), user_id),
                            )
                            clear_user_state(conn, user_id)
                            pending = pop_pending_token(conn, user_id)
                            if pending:
                                ok, response_text = activate_token(conn, pending, user_id)
                                if ok:
                                    send(
                                        vk,
                                        user_id,
                                        "🔥 Отлично! Вы в игре!\n"
                                        "Ваш номер сохранён, участие подтверждено.\n\n"
                                        "Код из QR активирован автоматически ✅\n\n"
                                        f"{response_text}",
                                        keyboard=keyboard_main(include_admin=is_admin),
                                    )
                                else:
                                    send(
                                        vk,
                                        user_id,
                                        "🔥 Отлично! Вы в игре!\n"
                                        "Ваш номер сохранён, участие подтверждено.\n\n"
                                        f"{response_text}\n\n"
                                        "Сканируйте новые QR-коды с купонов для автоматического начисления шансов.\n"
                                        "Ручной ввод QR отключен правилами розыгрыша.",
                                        keyboard=keyboard_main(include_admin=is_admin),
                                    )
                            else:
                                send(
                                    vk,
                                    user_id,
                                    "🔥 Отлично! Вы в игре!\n"
                                    "Ваш номер сохранён, участие подтверждено.\n\n"
                                    "Сканируйте новые QR-коды с купонов для автоматического начисления шансов.\n"
                                    "Ручной ввод QR отключен правилами розыгрыша.",
                                    keyboard=keyboard_main(include_admin=is_admin),
                                )
                            continue

                    if cmd == "join_raffle" or low in {"участвовать", "регистрация", "участвовать в розыгрыше"}:
                        send(
                            vk,
                            user_id,
                            "🔐 Для участия в розыгрыше необходимо дать согласие\n"
                            "на обработку персональных данных.\n\n"
                            "Нажимая «Даю согласие», вы принимаете условия по ФЗ-152.\n"
                            f"Политика: {PD_POLICY_URL}",
                            keyboard=keyboard_consent(),
                        )
                        continue

                    if not consented:
                        if token_hints:
                            save_pending_token(conn, user_id, token_hints[0])
                        if is_consent_signal(cmd, low):
                            save_consent(conn, user_id)
                            set_user_state(conn, user_id, "await_phone")
                            send(
                                vk,
                                user_id,
                                "✅ Спасибо! Согласие получено.\n"
                                "Чтобы завершить регистрацию, отправьте номер телефона.\n"
                                "Пример: +79991234567 📱",
                                keyboard=keyboard_phone_entry(),
                            )
                        elif cmd == "join_raffle" or cmd == "start_qr_flow" or text.lower() in {"старт", "start", "/start", "участвовать в розыгрыше"}:
                            send(
                                vk,
                                user_id,
                                "🎁 Вы на шаг ближе к призу в Avatar Arena Omsk VR!\n"
                                "Здесь разыгрываются реальные подарки — и вы можете стать следующим победителем 🏆\n\n"
                                "Чтобы продолжить, подтвердите согласие на обработку данных.\n"
                                "Это необходимо для участия в розыгрыше.\n\n"
                                "Нажимая «Даю согласие», вы принимаете условия по ФЗ-152.\n"
                                f"Политика: {PD_POLICY_URL}",
                                keyboard=keyboard_consent(),
                            )
                        else:
                            # If user came via QR deep-link, start flow immediately.
                            if token_hints:
                                send(
                                    vk,
                                    user_id,
                                    "🎟️ Отлично! Вы перешли по QR-коду.\n"
                                    "Код считан автоматически ✅\n\n"
                                    "Чтобы участвовать в розыгрыше, подтвердите согласие на обработку персональных данных.\n\n"
                                    f"Политика: {PD_POLICY_URL}",
                                    keyboard=keyboard_consent(),
                                )
                            else:
                                send(
                                    vk,
                                    user_id,
                                    "🎟️ Отлично! Вы перешли по QR-коду.\n\n"
                                    "Это ваш шанс попасть в розыгрыш и выиграть приз 🏆\n\n"
                                    "Нажмите кнопку ниже, чтобы начать 👇",
                                    keyboard=keyboard_qr_entry(),
                                )
                        continue

                    # If token arrives while user already consented, activate immediately.
                    if token_hints:
                        if not participant_registered(conn, user_id):
                            save_pending_token(conn, user_id, token_hints[0])
                            set_user_state(conn, user_id, "await_phone")
                            send(
                                vk,
                                user_id,
                                "🎟️ QR-код считан автоматически.\n\n"
                                "Перед активацией нужно завершить регистрацию:\n"
                                "введите номер телефона в формате +79991234567 📱",
                                keyboard=keyboard_phone_entry(),
                            )
                            continue
                        success_count, details = activate_tokens(conn, token_hints, user_id)
                        total_chances = conn.execute(
                            "SELECT COUNT(*) AS c FROM activations WHERE vk_user_id=?",
                            (user_id,),
                        ).fetchone()["c"]
                        if success_count > 0:
                            send(
                                vk,
                                user_id,
                                "🎉 QR-код активирован\n"
                                f"У вас теперь {total_chances} шансов\n\n"
                                f"Успешно активировано: {success_count} из {len(token_hints)}\n"
                                + "\n".join(details[:10])
                                + ("\n... (сокращено)" if len(details) > 10 else ""),
                                keyboard=keyboard_main(include_admin=is_admin),
                            )
                        else:
                            details_text = details[0] if details else "QR-код уже активирован ранее."
                            send(
                                vk,
                                user_id,
                                f"ℹ️ {details_text}\n\n🎯 Ваши шансы: {total_chances}",
                                keyboard=keyboard_main(include_admin=is_admin),
                            )
                        continue

                    if low in {"правила", "rules"}:
                        send(
                            vk,
                            user_id,
                            "📌 Как работает розыгрыш:\n\n"
                            "🎟 1 QR-код = 1 шанс на победу\n"
                            "⏳ Розыгрыш проходит в 3 этапа\n"
                            "🏆 Победители этапа получают приз и выбывают\n\n"
                            "Чем больше у вас кодов — тем выше вероятность выиграть 🚀",
                            keyboard=keyboard_main(include_admin=is_admin),
                        )
                        continue
                    if cmd == "activate_pending":
                        pending = pop_pending_token(conn, user_id)
                        if not pending:
                            send(
                                vk,
                                user_id,
                                "Нет ожидающего QR для активации. Перейдите в бот снова по QR-коду.",
                                keyboard=keyboard_main(include_admin=is_admin),
                            )
                            continue
                        if not participant_registered(conn, user_id):
                            save_pending_token(conn, user_id, pending)
                            set_user_state(conn, user_id, "await_phone")
                            send(
                                vk,
                                user_id,
                                "Перед активацией нужно завершить регистрацию.\n"
                                "Введите номер телефона в формате +79991234567 📱",
                                keyboard=keyboard_phone_entry(),
                            )
                            continue
                        ok, response_text = activate_token(conn, pending, user_id)
                        if ok:
                            send(vk, user_id, f"✅ QR-код активирован автоматически.\n\n{response_text}\nУдачи в розыгрыше! 🍀", keyboard=keyboard_main(include_admin=is_admin))
                        else:
                            send(vk, user_id, f"⚠️ {response_text}", keyboard=keyboard_main(include_admin=is_admin))
                        continue
                    if low in {"мои шансы", "шансы"}:
                        chances = conn.execute(
                            "SELECT COUNT(*) AS c FROM activations WHERE vk_user_id=?",
                            (user_id,),
                        ).fetchone()["c"]
                        send(
                            vk,
                            user_id,
                            f"🎯 Ваш текущий баланс удачи:\n🎟️ {chances} шанс(ов)\n\nЧем больше шансов — тем ближе победа 🏆",
                            keyboard=keyboard_main(include_admin=is_admin),
                        )
                        continue
                    if low in {"start", "/start", "начать", "привет"}:
                        pending = peek_pending_token(conn, user_id)
                        if pending:
                            send(
                                vk,
                                user_id,
                                "🎟️ Обнаружен QR-код для активации.\nНажмите кнопку ниже, и я активирую его автоматически.",
                                keyboard=keyboard_activate_pending(),
                            )
                            continue
                        send(
                            vk,
                            user_id,
                            "🚀 Добро пожаловать в мир Avatar Arena Omsk VR!\n"
                            "Здесь начинается игра, где каждый шанс может стать победой 🏆\n\n"
                            "Активируйте QR-коды, накапливайте шансы и забирайте призы!\n\n"
                            "Готовы испытать удачу? Выбирайте действие ниже 👇",
                            keyboard=keyboard_qr_entry(),
                        )
                        continue
                    if is_manual_qr_text(text):
                        send(
                            vk,
                            user_id,
                            "Ручной ввод QR отключен. Используйте только переход по QR-ссылке вида "
                            "https://vk.me/club<ID>?start=QR-XXXX.",
                            keyboard=keyboard_main(include_admin=is_admin),
                        )
                        continue
                    if is_admin and low in {"админ-панель", "панель", "admin"}:
                        send(vk, user_id, "Панель администратора.\nВыберите действие кнопками ниже.", keyboard=keyboard_admin_panel())
                        continue
                    if not text:
                        # Do not spam on empty service events.
                        continue

                    send(
                        vk,
                        user_id,
                        "🤖 Я не совсем понял вас 😅\n\n"
                        "Давайте попробуем ещё раз — выберите действие ниже 👇",
                        keyboard=keyboard_main(include_admin=is_admin),
                    )
        except Exception as exc:
            print(f"[WARN] LongPoll reconnect after error: {exc}")
            time.sleep(2)


if __name__ == "__main__":
    main()
