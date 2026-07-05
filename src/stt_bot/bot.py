"""Assemble the python-telegram-bot Application."""
from __future__ import annotations

import logging

from telegram.ext import Application, CommandHandler, MessageHandler, filters

from .config import Config
from .handlers import VoiceHandler

log = logging.getLogger(__name__)


async def _log_update_error(update, context):
    log.error("error handling update", exc_info=context.error)


def build_application(config: Config, handler: VoiceHandler) -> Application:
    app = Application.builder().token(config.telegram_bot_token).build()
    app.add_handler(CommandHandler("start", handler.start_command))
    app.add_handler(MessageHandler(filters.VOICE, handler.handle))
    app.add_error_handler(_log_update_error)
    return app
