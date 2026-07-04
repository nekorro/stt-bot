"""Entrypoint: config → model → monitoring → polling."""
from __future__ import annotations

import logging

from telegram import Update

from .bot import build_application
from .config import load_config
from .handlers import AudioHandler
from .health import set_ready, start_monitoring_server
from .logconfig import setup_logging
from .transcriber import Transcriber

log = logging.getLogger(__name__)


def main() -> None:
    config = load_config()
    setup_logging(config.log_level)
    log.info("loading whisper model=%s device=%s", config.whisper_model, config.whisper_device)

    start_monitoring_server(config.metrics_port)

    transcriber = Transcriber.load(
        config.whisper_model,
        config.whisper_device,
        task=config.whisper_task,
        language=config.whisper_language,
        download_root=config.whisper_download_root,
    )
    set_ready(True)
    log.info("model loaded; starting polling")

    handler = AudioHandler(transcriber, config)
    app = build_application(config, handler)
    app.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
