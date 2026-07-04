from unittest.mock import MagicMock

from stt_bot.bot import build_application
from stt_bot.config import load_config
from stt_bot.logconfig import setup_logging


def test_setup_logging_runs():
    setup_logging("DEBUG")  # must not raise


def test_build_application_registers_handlers():
    cfg = load_config({"TELEGRAM_BOT_TOKEN": "123:abc"})
    handler = MagicMock()
    app = build_application(cfg, handler)
    # At least one handler group with two handlers (/start + media).
    total = sum(len(hs) for hs in app.handlers.values())
    assert total >= 2


def test_build_application_registers_error_handler():
    cfg = load_config({"TELEGRAM_BOT_TOKEN": "123:abc"})
    handler = MagicMock()
    app = build_application(cfg, handler)
    assert app.error_handlers  # at least one error handler registered
