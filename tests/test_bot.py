from unittest.mock import MagicMock

from uebot.bot import build_application
from uebot.config import load_config
from uebot.logconfig import setup_logging


def test_setup_logging_runs():
    setup_logging("DEBUG")  # must not raise


def test_build_application_registers_handlers():
    cfg = load_config({"TELEGRAM_BOT_TOKEN": "123:abc"})
    handler = MagicMock()
    app = build_application(cfg, handler)
    # At least one handler group with two handlers (/start + media).
    total = sum(len(hs) for hs in app.handlers.values())
    assert total >= 2
