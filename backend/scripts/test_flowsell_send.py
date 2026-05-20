#!/usr/bin/env python3
"""
Минимальный test send в FlowSell WhatsApp API.

Использование (из каталога backend/):
  set FLOWSELL_INSTANCE_ID=...
  set FLOWSELL_API_KEY=...
  set TEST_MODE=false
  python scripts/test_flowsell_send.py --phone 79001234567 --message "Test from retention"

Или curl (см. deploy/FLOWSELL_INTEGRATION.md).
"""

from __future__ import annotations

import argparse
import asyncio
import os
import sys

# backend/ в PYTHONPATH
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.config import get_settings
from app.integrations.flowsell.client import FlowsellClient


async def main() -> int:
    parser = argparse.ArgumentParser(description="FlowSell test send")
    parser.add_argument("--phone", required=True, help="79001234567")
    parser.add_argument("--message", required=True, help="Текст сообщения")
    parser.add_argument("--channel", default="sms", help="sms или telegram (label)")
    args = parser.parse_args()

    settings = get_settings()
    if not settings.flowsell_configured:
        print("ERROR: задайте FLOWSELL_INSTANCE_ID и FLOWSELL_API_KEY", file=sys.stderr)
        return 1
    if settings.TEST_MODE:
        print("WARNING: TEST_MODE=true — для реального FlowSell установите TEST_MODE=false", file=sys.stderr)

    async with FlowsellClient(settings) as client:
        result = await client.send_message(args.phone, args.message, args.channel)

    print(f"ok={result.ok} detail={result.detail} id_message={result.id_message}")
    return 0 if result.ok else 2


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
