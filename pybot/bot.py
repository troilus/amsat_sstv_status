# -*- coding: utf-8 -*-
"""Bot entry point: sets up the python-telegram-bot Application and handlers."""

import json
import logging
import os
import sys

from telegram import BotCommand
from telegram.ext import Application, CallbackQueryHandler, CommandHandler, MessageHandler, filters

from state import Store
from wizard import cmd_cancel, cmd_help, cmd_language, cmd_report, cmd_start, on_callback, on_message

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
log = logging.getLogger("bot")

if getattr(sys, "frozen", False):
    HERE = os.path.dirname(os.path.abspath(sys.executable))
else:
    HERE = os.path.dirname(os.path.abspath(__file__))


def load_config():
    path = os.environ.get("BOT_CONFIG", os.path.join(HERE, "config.json"))
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


async def post_init(app):
    await app.bot.set_my_commands(
        [
            BotCommand("/report", "Report satellite status"),
            BotCommand("/language", "Change language"),
            BotCommand("/cancel", "Cancel current report"),
            BotCommand("/help", "Show help"),
        ]
    )


def main():
    config = load_config()
    token = config.get("telegram_token") or os.environ.get("TELEGRAM_BOT_TOKEN", "")
    if not token or token == "YOUR_TOKEN_HERE":
        log.error("Set telegram_token in config.json (or TELEGRAM_BOT_TOKEN env var) first.")
        sys.exit(1)

    store = Store(config.get("state_file", os.path.join(HERE, "state.json")))
    app = Application.builder().token(token).concurrent_updates(False).post_init(post_init).build()
    app.bot_data["store"] = store
    app.bot_data["api_base"] = config.get("amsat_api_base", "https://www.amsat.org/status/api/v1")
    app.bot_data["catalog_ttl"] = config.get("catalog_ttl", 86400)

    app.add_handler(CommandHandler("start", cmd_start))
    app.add_handler(CommandHandler("help", cmd_help))
    app.add_handler(CommandHandler("language", cmd_language))
    app.add_handler(CommandHandler("cancel", cmd_cancel))
    app.add_handler(CommandHandler("report", cmd_report))
    app.add_handler(CallbackQueryHandler(on_callback))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, on_message))

    log.info("Polling for updates…")
    app.run_polling(allowed_updates=("message", "callback_query"))


if __name__ == "__main__":
    main()