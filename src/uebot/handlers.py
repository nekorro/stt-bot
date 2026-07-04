"""Telegram handlers: download → transcribe → reply."""
from __future__ import annotations

import asyncio
import logging
import os
import tempfile

from .config import Config
from .metrics import (
    AUDIO_DURATION,
    MESSAGES_RECEIVED,
    TRANSCRIPTION_DURATION,
    TRANSCRIPTIONS,
)
from .textsplit import split_message
from .transcriber import Transcriber

log = logging.getLogger(__name__)

_START_TEXT = (
    "Hi! Send or forward me a voice message or an audio file and I'll reply "
    "with a text transcription."
)


class AudioHandler:
    def __init__(self, transcriber: Transcriber, config: Config):
        self._transcriber = transcriber
        self._config = config
        self._sem = asyncio.Semaphore(config.max_concurrent_transcriptions)

    async def start_command(self, update, context) -> None:
        await update.effective_message.reply_text(_START_TEXT)

    def _chat_allowed(self, chat_id: int) -> bool:
        allowed = self._config.allowed_chat_ids
        return allowed is None or chat_id in allowed

    async def handle(self, update, context) -> None:
        msg = update.effective_message
        media = msg.voice or msg.audio
        if media is None:
            return
        kind = "voice" if msg.voice else "audio"
        chat_id = update.effective_chat.id

        if not self._chat_allowed(chat_id):
            log.debug("ignoring message from disallowed chat %s", chat_id)
            return

        MESSAGES_RECEIVED.labels(type=kind).inc()

        duration = getattr(media, "duration", 0) or 0
        if duration:
            AUDIO_DURATION.observe(duration)
        if duration > self._config.max_audio_duration_s:
            TRANSCRIPTIONS.labels(status="rejected").inc()
            await msg.reply_text(
                f"That audio is too long (>{self._config.max_audio_duration_s}s).",
                reply_to_message_id=msg.message_id,
            )
            return

        size = getattr(media, "file_size", 0) or 0
        if size > self._config.max_file_mb * 1024 * 1024:
            TRANSCRIPTIONS.labels(status="rejected").inc()
            await msg.reply_text(
                f"That file is too large (>{self._config.max_file_mb} MB).",
                reply_to_message_id=msg.message_id,
            )
            return

        tmp = tempfile.NamedTemporaryFile(suffix=".audio", delete=False)
        path = tmp.name
        tmp.close()
        try:
            tg_file = await context.bot.get_file(media.file_id)
            await tg_file.download_to_drive(custom_path=path)

            async with self._sem:
                with TRANSCRIPTION_DURATION.time():
                    result = await asyncio.to_thread(self._transcriber.transcribe, path)

            if not result.text:
                TRANSCRIPTIONS.labels(status="empty").inc()
                await msg.reply_text(
                    "(no speech detected)", reply_to_message_id=msg.message_id
                )
                return

            TRANSCRIPTIONS.labels(status="success").inc()
            log.info(
                "transcribed chat=%s msg=%s kind=%s lang=%s audio_s=%.1f chars=%d",
                chat_id, msg.message_id, kind, result.language, duration, len(result.text),
            )
            for chunk in split_message(result.text):
                await msg.reply_text(chunk, reply_to_message_id=msg.message_id)
        except Exception:  # noqa: BLE001 — report to user, keep bot alive
            TRANSCRIPTIONS.labels(status="failure").inc()
            log.exception("transcription failed chat=%s msg=%s", chat_id, msg.message_id)
            await msg.reply_text(
                "⚠️ Couldn't transcribe this one.", reply_to_message_id=msg.message_id
            )
        finally:
            try:
                os.unlink(path)
            except OSError:
                pass
