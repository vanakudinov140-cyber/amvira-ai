# -*- coding: utf-8 -*-
"""
Генерация QR-кодов для выпускного альбома из data.xlsx (колонки Name, Link).

Установка зависимостей (в терминале, из папки со скриптом или любой):
    pip install pandas qrcode[pil] Pillow requests openpyxl

    openpyxl нужен для чтения .xlsx через pandas.

Перед запуском:
    1. Положите рядом со скриптом файл data.xlsx.
    2. Папка output создаётся автоматически; готовые PNG сохраняются туда.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path
from urllib.parse import urlparse

import pandas as pd
import qrcode
import requests
from PIL import Image, ImageDraw, ImageFont

# --- Константы ---
SCRIPT_DIR = Path(__file__).resolve().parent
EXCEL_PATH = SCRIPT_DIR / "data.xlsx"
OUTPUT_DIR = SCRIPT_DIR / "output"
QR_SIZE = 500  # пикселей (квадрат)
LABEL_PADDING = 16  # отступ подписи от QR
LABEL_MIN_HEIGHT = 56  # минимальная высота поля под текст
HEAD_TIMEOUT = 15  # секунд
YANDEX_DOMAINS = ("disk.yandex.ru", "yadisk.cc")


def _find_font(size: int) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    """Arial на Windows или стандартный шрифт Pillow, если файл не найден."""
    candidates = [
        Path(r"C:\Windows\Fonts\arial.ttf"),
        Path(r"C:\Windows\Fonts\arialbd.ttf"),
        Path("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"),
        Path("/System/Library/Fonts/Supplemental/Arial.ttf"),
    ]
    for p in candidates:
        if p.is_file():
            try:
                return ImageFont.truetype(str(p), size=size)
            except OSError:
                continue
    return ImageFont.load_default()


def _sanitize_filename(name: str) -> str:
    """Имя файла без недопустимых символов Windows; пробелы -> подчёркивание."""
    s = name.strip()
    s = re.sub(r'[<>:"/\\|?*]', "_", s)
    s = re.sub(r"\s+", "_", s)
    s = s.strip("._") or "unnamed"
    return s


def _is_yandex_disk_url(url: str) -> bool:
    """Проверка, что в ссылке есть домен Яндекс.Диска."""
    try:
        host = (urlparse(url).hostname or "").lower()
    except ValueError:
        return False
    return any(host == d or host.endswith("." + d) for d in YANDEX_DOMAINS)


def _check_links_unique(links: pd.Series) -> bool:
    """True если все ссылки уникальны (без пустых дубликатов считаем по нормализованной строке)."""
    normalized = links.astype(str).str.strip()
    # Пустые повторы не блокируем проверку уникальности «настоящих» ссылок.
    non_empty = normalized[normalized.ne("") & normalized.ne("nan")]
    dup_non_empty = non_empty[non_empty.duplicated(keep=False)]
    if len(dup_non_empty) > 0:
        print("\n[ОШИБКА] Обнаружены дубликаты в колонке Link. Работа остановлена.")
        print("Повторяющиеся значения:")
        for val in dup_non_empty.unique():
            rows = normalized[normalized == val].index.tolist()
            print(f"  {val!r} — строки (0-based index в Excel+1): {[i + 2 for i in rows]}")
        return False
    return True


def _head_ok(url: str) -> tuple[bool, int | None, str | None]:
    """
    HEAD-запрос: успех только при финальном статусе 200.
    Возвращает (успех, код_статуса, сообщение_об_ошибке).
    """
    try:
        r = requests.head(
            url,
            timeout=HEAD_TIMEOUT,
            allow_redirects=True,
            headers={"User-Agent": "QRAlbumGenerator/1.0"},
        )
        if r.status_code == 200:
            return True, 200, None
        return False, r.status_code, f"HTTP {r.status_code}"
    except requests.RequestException as e:
        return False, None, str(e)


def _make_qr_image(data: str, size: int) -> Image.Image:
    """QR-код как изображение size x size (чёрно-белое)."""
    qr = qrcode.QRCode(
        version=None,
        error_correction=qrcode.constants.ERROR_CORRECT_M,
        box_size=10,
        border=2,
    )
    qr.add_data(data)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white").convert("RGB")
    return img.resize((size, size), Image.Resampling.LANCZOS)


def _compose_with_label(qr_img: Image.Image, caption: str) -> Image.Image:
    """QR сверху, снизу белое поле с подписью (имя)."""
    w, h = qr_img.size
    font = _find_font(22)
    measure = ImageDraw.Draw(Image.new("RGB", (max(w, 400), 120), "white"))
    bbox = measure.textbbox((0, 0), caption, font=font)
    text_h = bbox[3] - bbox[1]
    label_h = max(LABEL_MIN_HEIGHT, text_h + LABEL_PADDING * 2)
    out = Image.new("RGB", (w, h + label_h), "white")
    out.paste(qr_img, (0, 0))
    draw = ImageDraw.Draw(out)
    tw = bbox[2] - bbox[0]
    tx = (w - tw) / 2
    ty = h + (label_h - text_h) / 2 - bbox[1]
    draw.text((tx, ty), caption, fill="black", font=font)
    return out


def main() -> int:
    if not EXCEL_PATH.is_file():
        print(f"[ОШИБКА] Не найден файл: {EXCEL_PATH}")
        return 1

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    df = pd.read_excel(EXCEL_PATH, engine="openpyxl")
    # Нормализация имён колонок (без учёта регистра, лишние пробелы)
    df.columns = [str(c).strip() for c in df.columns]
    col_map = {c.lower(): c for c in df.columns}
    name_col = col_map.get("name")
    link_col = col_map.get("link")
    if not name_col or not link_col:
        print("[ОШИБКА] В Excel должны быть колонки Name и Link.")
        return 1

    links = df[link_col].fillna("").astype(str).str.strip()
    names = df[name_col].fillna("").astype(str).str.strip()

    if not _check_links_unique(links):
        return 1

    used_filenames: dict[str, int] = {}
    ok = 0
    broken = 0

    print("Начало обработки строк...\n")

    for idx, (name, link) in enumerate(zip(names, links), start=2):
        # idx = номер строки в Excel (строка 1 — заголовок)
        if not name:
            print(f"[строка {idx}] Пропуск: пустое имя (Name).")
            broken += 1
            continue
        if not link or link.lower() == "nan":
            print(f"[строка {idx}] Пропуск: пустая ссылка (Link) для «{name}».")
            broken += 1
            continue

        if not _is_yandex_disk_url(link):
            print(
                f"[строка {idx}] ПРЕДУПРЕЖДЕНИЕ: ссылка для «{name}» не похожа на Яндекс.Диск "
                f"(ожидаются домены {YANDEX_DOMAINS})."
            )

        ok_head, code, err = _head_ok(link)
        if not ok_head:
            broken += 1
            detail = err if err else (f"код {code}" if code is not None else "неизвестно")
            print(f"[строка {idx}] Ошибка проверки ссылки для «{name}»: {detail}. Пропуск.")
            continue

        qr_img = _make_qr_image(link, QR_SIZE)
        final_img = _compose_with_label(qr_img, name)

        base = _sanitize_filename(name)
        n = used_filenames.get(base, 0)
        used_filenames[base] = n + 1
        fname = f"{base}.png" if n == 0 else f"{base}_{n + 1}.png"
        out_path = OUTPUT_DIR / fname
        final_img.save(out_path, format="PNG")
        ok += 1
        print(f"[строка {idx}] Сохранено: {out_path.name}")

    print("\n" + "=" * 50)
    print("ИТОГ:")
    print(f"  Успешно создано QR-кодов: {ok}")
    print(f"  Пропущено (битая ссылка / пустые поля): {broken}")
    print(f"  Папка вывода: {OUTPUT_DIR}")
    print("=" * 50)
    return 0


if __name__ == "__main__":
    sys.exit(main())
