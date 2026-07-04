"""Assemble the python-telegram-bot Application."""
from __future__ import annotations

from telegram.ext import Application, CommandHandler, MessageHandler, filters

from .config import Config
from .handlers import AudioHandler


def build_application(config: Config, handler: AudioHandler) -> Application:
    app = Application.builder().token(config.telegram_bot_token).build()
    app.add_handler(CommandHandler("start", handler.start_command))
    app.add_handler(MessageHandler(filters.VOICE | filters.AUDIO, handler.handle))
    return app
