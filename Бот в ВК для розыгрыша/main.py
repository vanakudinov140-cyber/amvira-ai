"""
VK raffle bot backend (MVP) for Avatar Arena Omsk VR.

Implements final agreed mechanics:
- 3 stages x 30 days
- 1 QR token = 1 chance
- winning tokens are excluded from next stages
- non-winning tokens continue participating
- draw is launched inside this system (no third-party raffle services)

Run:
    python main.py
Then open:
    http://127.0.0.1:8000/docs

Dependencies:
    pip install fastapi uvicorn
"""

from __future__ import annotations

import datetime as dt
import json
import os
import re
import secrets
import sqlite3
import urllib.parse
import urllib.request
from contextlib import contextmanager
from pathlib import Path
from typing import Any, Iterator

from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel, Field

BASE_DIR = Path(__file__).resolve().parent
DB_PATH = BASE_DIR / "raffle.db"
GROUP_DOMAIN = "avatararenaomskvr"
VK_API_VERSION = "5.199"
VK_GROUP_TOKEN = os.getenv("VK_GROUP_TOKEN", "")
VK_CONFIRMATION_TOKEN = os.getenv("VK_CONFIRMATION_TOKEN", "")
VK_ADMIN_IDS = {int(x) for x in os.getenv("VK_ADMIN_IDS", "").split(",") if x.strip().isdigit()}
PD_POLICY_URL = os.getenv("PD_POLICY_URL", "https://www.consultant.ru/document/cons_doc_LAW_61801/")

app = FastAPI(title="Avatar Arena QR Raffle API", version="1.0.0")


@contextmanager
def db() -> Iterator[sqlite3.Connection]:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()


def utcnow_iso() -> str:
    return dt.datetime.now(dt.timezone.utc).isoformat()


def to_date(value: str) -> dt.date:
    try:
        return dt.date.fromisoformat(value)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail="Date format must be YYYY-MM-DD.") from exc


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
                FOREIGN KEY(vk_user_id) REFERENCES users(vk_user_id)
            );

            CREATE TABLE IF NOT EXISTS stages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                stage_no INTEGER NOT NULL UNIQUE,
                start_date TEXT NOT NULL,
                end_date TEXT NOT NULL,
                status TEXT NOT NULL CHECK(status IN ('planned', 'active', 'closed')),
                created_at TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS qr_tokens (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                token TEXT NOT NULL UNIQUE,
                vk_deeplink TEXT NOT NULL,
                issued_for_receipt TEXT,
                issued_at TEXT NOT NULL,
                expires_at TEXT,
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
                activated_at TEXT NOT NULL,
                FOREIGN KEY(token_id) REFERENCES qr_tokens(id)
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
                vk_user_id INTEGER NOT NULL,
                FOREIGN KEY(draw_id) REFERENCES draws(id),
                FOREIGN KEY(token_id) REFERENCES qr_tokens(id)
            );
            """
        )


class StageCreateIn(BaseModel):
    stage_no: int = Field(ge=1, le=3)
    start_date: str
    end_date: str


class IssueTokensIn(BaseModel):
    amount_rub: int = Field(ge=0)
    receipt_id: str = Field(min_length=1, max_length=64)
    expires_at: str | None = None


class DrawIn(BaseModel):
    winners_count: int = Field(ge=1)


def ensure_user(conn: sqlite3.Connection, vk_user_id: int) -> None:
    conn.execute(
        """
        INSERT OR IGNORE INTO users(vk_user_id, first_seen_at)
        VALUES(?, ?)
        """,
        (vk_user_id, utcnow_iso()),
    )


def active_stage(conn: sqlite3.Connection) -> sqlite3.Row | None:
    return conn.execute("SELECT * FROM stages WHERE status='active' LIMIT 1").fetchone()


def build_token_link(token: str) -> str:
    return f"https://vk.me/{GROUP_DOMAIN}?ref={token}"


def vk_api(method: str, params: dict[str, Any]) -> dict[str, Any]:
    if not VK_GROUP_TOKEN:
        raise RuntimeError("VK_GROUP_TOKEN is not set.")
    payload = {"access_token": VK_GROUP_TOKEN, "v": VK_API_VERSION, **params}
    data = urllib.parse.urlencode(payload).encode("utf-8")
    req = urllib.request.Request(
        f"https://api.vk.com/method/{method}",
        data=data,
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    with urllib.request.urlopen(req, timeout=10) as resp:
        raw = resp.read().decode("utf-8")
    import json

    result = json.loads(raw)
    if "error" in result:
        raise RuntimeError(f"VK API error: {result['error']}")
    return result["response"]


def keyboard_main_menu() -> str:
    return json.dumps(
        {
            "one_time": False,
            "buttons": [
                [
                    {
                        "action": {"type": "text", "label": "Активировать QR", "payload": {"cmd": "activate_hint"}},
                        "color": "positive",
                    },
                    {
                        "action": {"type": "text", "label": "Мои шансы", "payload": {"cmd": "my_chances"}},
                        "color": "primary",
                    },
                ],
                [
                    {
                        "action": {"type": "text", "label": "Правила", "payload": {"cmd": "rules"}},
                        "color": "secondary",
                    }
                ],
            ],
        },
        ensure_ascii=False,
    )


def keyboard_consent() -> str:
    return json.dumps(
        {
            "one_time": False,
            "buttons": [
                [
                    {
                        "action": {"type": "text", "label": "Согласен", "payload": {"cmd": "accept_pd"}},
                        "color": "positive",
                    },
                    {
                        "action": {"type": "open_link", "label": "Политика", "link": PD_POLICY_URL},
                    },
                ]
            ],
        },
        ensure_ascii=False,
    )


def vk_send_message(user_id: int, text: str, keyboard: str | None = None) -> None:
    params: dict[str, Any] = {
        "user_id": user_id,
        "random_id": secrets.randbelow(2_000_000_000),
        "message": text,
    }
    if keyboard:
        params["keyboard"] = keyboard
    vk_api(
        "messages.send",
        params,
    )


def activate_token_core(token: str, vk_user_id: int) -> dict[str, Any]:
    with db() as conn:
        stage = active_stage(conn)
        if not stage:
            raise HTTPException(status_code=400, detail="No active stage right now.")

        row = conn.execute("SELECT * FROM qr_tokens WHERE token=?", (token,)).fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Token not found.")
        if row["is_used"]:
            raise HTTPException(status_code=409, detail="Token already activated.")
        if row["expires_at"] and dt.date.today() > to_date(row["expires_at"]):
            raise HTTPException(status_code=410, detail="Token expired.")
        if row["active_for_next_stage"] == 0:
            raise HTTPException(status_code=409, detail="Token is not active for current stage.")

        ensure_user(conn, vk_user_id)
        now = utcnow_iso()
        conn.execute(
            """
            UPDATE qr_tokens
            SET is_used=1, used_by_vk_id=?, used_at=?
            WHERE id=?
            """,
            (vk_user_id, now, row["id"]),
        )
        conn.execute(
            """
            INSERT INTO activations(token_id, vk_user_id, activated_at)
            VALUES(?, ?, ?)
            """,
            (row["id"], vk_user_id, now),
        )

        total_chances = conn.execute(
            "SELECT COUNT(*) AS c FROM activations WHERE vk_user_id=?",
            (vk_user_id,),
        ).fetchone()["c"]

    return {
        "ok": True,
        "message": f"QR activated. Total chances: {total_chances}",
        "vk_user_id": vk_user_id,
        "total_chances": total_chances,
        "stage": stage["stage_no"],
    }


def extract_token_from_text(text: str) -> str | None:
    match = re.search(r"(QR-[A-Za-z0-9_\-]+)", text or "")
    return match.group(1) if match else None


def has_consent(conn: sqlite3.Connection, vk_user_id: int) -> bool:
    row = conn.execute("SELECT 1 FROM user_consents WHERE vk_user_id=?", (vk_user_id,)).fetchone()
    return bool(row)


def save_consent(conn: sqlite3.Connection, vk_user_id: int) -> None:
    ensure_user(conn, vk_user_id)
    conn.execute(
        """
        INSERT OR REPLACE INTO user_consents(vk_user_id, accepted_at)
        VALUES(?, ?)
        """,
        (vk_user_id, utcnow_iso()),
    )


@app.on_event("startup")
def startup() -> None:
    init_db()


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/admin/stages")
def create_stage(payload: StageCreateIn) -> dict[str, Any]:
    start = to_date(payload.start_date)
    end = to_date(payload.end_date)
    if end < start:
        raise HTTPException(status_code=400, detail="end_date must be after start_date.")
    with db() as conn:
        try:
            conn.execute(
                """
                INSERT INTO stages(stage_no, start_date, end_date, status, created_at)
                VALUES(?, ?, ?, 'planned', ?)
                """,
                (payload.stage_no, payload.start_date, payload.end_date, utcnow_iso()),
            )
        except sqlite3.IntegrityError as exc:
            raise HTTPException(status_code=409, detail="Stage number already exists.") from exc
    return {"ok": True}


@app.post("/admin/stages/{stage_no}/activate")
def activate_stage(stage_no: int) -> dict[str, Any]:
    with db() as conn:
        current = active_stage(conn)
        if current:
            raise HTTPException(status_code=400, detail="Another stage is already active.")
        updated = conn.execute(
            "UPDATE stages SET status='active' WHERE stage_no=? AND status IN ('planned', 'closed')",
            (stage_no,),
        ).rowcount
        if not updated:
            raise HTTPException(status_code=404, detail="Stage not found.")
    return {"ok": True, "active_stage": stage_no}


@app.post("/admin/stages/{stage_no}/close")
def close_stage(stage_no: int) -> dict[str, Any]:
    with db() as conn:
        updated = conn.execute(
            "UPDATE stages SET status='closed' WHERE stage_no=? AND status='active'",
            (stage_no,),
        ).rowcount
        if not updated:
            raise HTTPException(status_code=404, detail="Active stage not found.")
    return {"ok": True}


@app.post("/admin/issue-tokens")
def issue_tokens(payload: IssueTokensIn) -> dict[str, Any]:
    chances = payload.amount_rub // 1200
    if chances <= 0:
        return {"ok": True, "issued": 0, "message": "No chances for this amount."}

    exp_iso = None
    if payload.expires_at:
        exp_iso = to_date(payload.expires_at).isoformat()

    issued_items: list[dict[str, str]] = []
    with db() as conn:
        for _ in range(chances):
            token = f"QR-{secrets.token_urlsafe(8)}"
            link = build_token_link(token)
            conn.execute(
                """
                INSERT INTO qr_tokens(token, vk_deeplink, issued_for_receipt, issued_at, expires_at)
                VALUES(?, ?, ?, ?, ?)
                """,
                (token, link, payload.receipt_id, utcnow_iso(), exp_iso),
            )
            issued_items.append({"token": token, "link": link})
    return {"ok": True, "issued": chances, "items": issued_items}


@app.get("/activate/{token}")
def activate_token(token: str, vk_user_id: int = Query(..., ge=1)) -> dict[str, Any]:
    return activate_token_core(token, vk_user_id)


@app.post("/admin/stages/{stage_no}/draw")
def run_draw(stage_no: int, payload: DrawIn) -> dict[str, Any]:
    with db() as conn:
        stage = conn.execute("SELECT * FROM stages WHERE stage_no=?", (stage_no,)).fetchone()
        if not stage:
            raise HTTPException(status_code=404, detail="Stage not found.")

        candidates = conn.execute(
            """
            SELECT t.id AS token_id, t.used_by_vk_id AS vk_user_id
            FROM qr_tokens t
            WHERE t.is_used=1
              AND t.active_for_next_stage=1
              AND t.is_winner=0
            """
        ).fetchall()
        if not candidates:
            raise HTTPException(status_code=400, detail="No candidates for draw.")
        if payload.winners_count > len(candidates):
            raise HTTPException(status_code=400, detail="Winners count is bigger than candidate count.")

        selected = secrets.SystemRandom().sample(candidates, payload.winners_count)
        now = utcnow_iso()
        draw_id = conn.execute(
            """
            INSERT INTO draws(stage_no, winners_count, drawn_at)
            VALUES(?, ?, ?)
            """,
            (stage_no, payload.winners_count, now),
        ).lastrowid

        winners_out = []
        for item in selected:
            conn.execute(
                """
                INSERT INTO draw_winners(draw_id, token_id, vk_user_id)
                VALUES(?, ?, ?)
                """,
                (draw_id, item["token_id"], item["vk_user_id"]),
            )
            conn.execute(
                """
                UPDATE qr_tokens
                SET is_winner=1, active_for_next_stage=0
                WHERE id=?
                """,
                (item["token_id"],),
            )
            winners_out.append({"token_id": item["token_id"], "vk_user_id": item["vk_user_id"]})

    return {"ok": True, "stage": stage_no, "draw_id": draw_id, "winners": winners_out}


@app.get("/admin/users/{vk_user_id}")
def user_stats(vk_user_id: int) -> dict[str, Any]:
    with db() as conn:
        user = conn.execute("SELECT * FROM users WHERE vk_user_id=?", (vk_user_id,)).fetchone()
        if not user:
            raise HTTPException(status_code=404, detail="User not found.")
        chances = conn.execute(
            "SELECT COUNT(*) AS c FROM activations WHERE vk_user_id=?",
            (vk_user_id,),
        ).fetchone()["c"]
    return {"vk_user_id": vk_user_id, "total_chances": chances}


@app.get("/admin/summary")
def summary() -> dict[str, Any]:
    with db() as conn:
        users = conn.execute("SELECT COUNT(*) AS c FROM users").fetchone()["c"]
        issued = conn.execute("SELECT COUNT(*) AS c FROM qr_tokens").fetchone()["c"]
        activated = conn.execute("SELECT COUNT(*) AS c FROM qr_tokens WHERE is_used=1").fetchone()["c"]
        winners = conn.execute("SELECT COUNT(*) AS c FROM qr_tokens WHERE is_winner=1").fetchone()["c"]
    return {
        "users": users,
        "issued_tokens": issued,
        "activated_tokens": activated,
        "winner_tokens": winners,
    }


@app.post("/vk/callback")
def vk_callback(event: dict[str, Any]) -> str:
    event_type = event.get("type")
    if event_type == "confirmation":
        if not VK_CONFIRMATION_TOKEN:
            raise HTTPException(status_code=500, detail="VK_CONFIRMATION_TOKEN is not set.")
        return VK_CONFIRMATION_TOKEN

    if event_type != "message_new":
        return "ok"

    obj = event.get("object", {})
    message = obj.get("message", {})
    user_id = int(message.get("from_id", 0))
    text = (message.get("text", "") or "").strip()
    payload_raw = message.get("payload")
    payload_cmd = ""
    if payload_raw:
        try:
            payload_cmd = (json.loads(payload_raw) or {}).get("cmd", "")
        except json.JSONDecodeError:
            payload_cmd = ""

    token_from_ref = message.get("ref")
    token = token_from_ref or extract_token_from_text(text)

    if not user_id:
        return "ok"

    with db() as conn:
        user_has_consent = has_consent(conn, user_id)

    if not user_has_consent and payload_cmd == "accept_pd":
        with db() as conn:
            save_consent(conn, user_id)
        vk_send_message(
            user_id,
            "Отлично, согласие получено.\n"
            "Добро пожаловать в розыгрыш Avatar Arena Omsk VR!\n"
            "Сканируйте QR-коды и получайте шансы на приз.",
            keyboard=keyboard_main_menu(),
        )
        return "ok"

    if not user_has_consent:
        vk_send_message(
            user_id,
            "Перед участием нужно подтвердить согласие на обработку персональных данных.\n\n"
            "Нажимая «Согласен», вы подтверждаете согласие на обработку персональных данных "
            "в целях проведения розыгрыша в соответствии с ФЗ-152 (ст. 9).\n"
            f"Политика: {PD_POLICY_URL}",
            keyboard=keyboard_consent(),
        )
        return "ok"

    if payload_cmd == "rules" or text.lower() in {"правила", "rules"}:
        vk_send_message(
            user_id,
            "Правила розыгрыша:\n"
            "1) 1 QR-код = 1 шанс.\n"
            "2) Розыгрыш идет в 3 этапа по 30 дней.\n"
            "3) Выигравшие коды выбывают, остальные переходят в следующий этап.",
            keyboard=keyboard_main_menu(),
        )
        return "ok"

    if payload_cmd == "my_chances" or text.lower() in {"мои шансы", "шансы"}:
        with db() as conn:
            ensure_user(conn, user_id)
            chances = conn.execute(
                "SELECT COUNT(*) AS c FROM activations WHERE vk_user_id=?",
                (user_id,),
            ).fetchone()["c"]
        vk_send_message(
            user_id,
            f"Сейчас у вас {chances} шанс(ов) на розыгрыш.",
            keyboard=keyboard_main_menu(),
        )
        return "ok"

    if payload_cmd == "activate_hint":
        vk_send_message(
            user_id,
            "Отлично! Отправьте QR-код (или текст токена в формате QR-XXXX), "
            "и я сразу начислю шанс.",
            keyboard=keyboard_main_menu(),
        )
        return "ok"

    if not token:
        vk_send_message(
            user_id,
            "Добро пожаловать в розыгрыш Avatar Arena Omsk VR!\n"
            "Нажмите «Активировать QR» или отправьте QR-токен в чат.",
            keyboard=keyboard_main_menu(),
        )
        return "ok"

    try:
        result = activate_token_core(token, user_id)
        vk_send_message(
            user_id,
            "QR успешно активирован.\n"
            f"Начислен 1 шанс. Всего шансов: {result['total_chances']}.",
            keyboard=keyboard_main_menu(),
        )
    except HTTPException as exc:
        detail = str(exc.detail)
        if "already activated" in detail:
            vk_send_message(user_id, "Этот QR-код уже был использован.", keyboard=keyboard_main_menu())
        elif "expired" in detail:
            vk_send_message(user_id, "Срок действия этого QR-кода истек.", keyboard=keyboard_main_menu())
        elif "not found" in detail:
            vk_send_message(user_id, "QR-код не найден. Проверьте и попробуйте снова.", keyboard=keyboard_main_menu())
        elif "No active stage" in detail:
            vk_send_message(user_id, "Сейчас нет активного этапа розыгрыша.", keyboard=keyboard_main_menu())
        else:
            vk_send_message(user_id, "Не удалось активировать QR-код. Попробуйте позже.", keyboard=keyboard_main_menu())
    return "ok"


@app.post("/admin/vk/test-message")
def admin_vk_test_message(user_id: int = Query(..., ge=1), text: str = Query(..., min_length=1)) -> dict[str, Any]:
    if VK_ADMIN_IDS and user_id not in VK_ADMIN_IDS:
        raise HTTPException(status_code=403, detail="User is not in VK_ADMIN_IDS.")
    try:
        vk_send_message(user_id, text)
    except RuntimeError as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc
    return {"ok": True}


def main() -> None:
    import uvicorn

    print("Starting Avatar Arena raffle backend...")
    uvicorn.run(app, host="127.0.0.1", port=8000)


if __name__ == "__main__":
    main()
