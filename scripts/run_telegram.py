"""Run the Jarvis Telegram bot (long-polling).

    python scripts/run_telegram.py

Needs TELEGRAM_BOT_TOKEN in .env. With no token it prints instructions and exits (no network).
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from core.console import enable_utf8_console
from core.logging_setup import setup_logging
from integrations.telegram_bot import JarvisTelegramBot


def main() -> int:
    enable_utf8_console()
    setup_logging("info")
    bot = JarvisTelegramBot()
    if not bot.configured:
        print("TELEGRAM_BOT_TOKEN is not set in .env.")
        print("1) Open Telegram, message @BotFather, /newbot, copy the token.")
        print("2) Paste it into .env as TELEGRAM_BOT_TOKEN=...")
        print("3) (Optional) set TELEGRAM_CHAT_ID to restrict control to you.")
        print("4) Run this again.")
        return 1
    bot.run_polling()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
