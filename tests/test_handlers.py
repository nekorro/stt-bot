from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock

import pytest

from uebot.config import load_config
from uebot.handlers import AudioHandler
from uebot.transcriber import TranscriptionResult


def make_update(chat_id=1, message_id=99, voice=None, audio=None):
    msg = SimpleNamespace(
        message_id=message_id,
        chat_id=chat_id,
        voice=voice,
        audio=audio,
        reply_text=AsyncMock(),
    )
    return SimpleNamespace(effective_message=msg, effective_chat=SimpleNamespace(id=chat_id))


def make_context(tmp_path):
    async def fake_download(custom_path=None):
        with open(custom_path, "wb") as fh:
            fh.write(b"fakeaudio")

    tg_file = SimpleNamespace(download_to_drive=fake_download)
    bot = SimpleNamespace(get_file=AsyncMock(return_value=tg_file))
    return SimpleNamespace(bot=bot)


def media(duration=5, file_size=1000):
    return SimpleNamespace(file_id="fid", duration=duration, file_size=file_size)


@pytest.fixture
def cfg():
    return load_config({"TELEGRAM_BOT_TOKEN": "x"})


async def test_happy_path_replies_with_transcript(cfg, tmp_path):
    transcriber = MagicMock()
    transcriber.transcribe.return_value = TranscriptionResult("hello there", "en", 5.0)
    handler = AudioHandler(transcriber, cfg)
    update = make_update(voice=media())
    await handler.handle(update, make_context(tmp_path))
    update.effective_message.reply_text.assert_awaited()
    sent = update.effective_message.reply_text.await_args_list[0]
    assert sent.args[0] == "hello there"
    assert sent.kwargs["reply_to_message_id"] == 99


async def test_empty_transcript_message(cfg, tmp_path):
    transcriber = MagicMock()
    transcriber.transcribe.return_value = TranscriptionResult("", "en", 1.0)
    handler = AudioHandler(transcriber, cfg)
    update = make_update(voice=media())
    await handler.handle(update, make_context(tmp_path))
    sent = update.effective_message.reply_text.await_args_list[0]
    assert "no speech" in sent.args[0].lower()


async def test_allowlist_blocks(tmp_path):
    cfg = load_config({"TELEGRAM_BOT_TOKEN": "x", "ALLOWED_CHAT_IDS": "42"})
    transcriber = MagicMock()
    handler = AudioHandler(transcriber, cfg)
    update = make_update(chat_id=7, voice=media())
    await handler.handle(update, make_context(tmp_path))
    transcriber.transcribe.assert_not_called()
    update.effective_message.reply_text.assert_not_awaited()


async def test_duration_guard(tmp_path):
    cfg = load_config({"TELEGRAM_BOT_TOKEN": "x", "MAX_AUDIO_DURATION_S": "10"})
    transcriber = MagicMock()
    handler = AudioHandler(transcriber, cfg)
    update = make_update(voice=media(duration=999))
    await handler.handle(update, make_context(tmp_path))
    transcriber.transcribe.assert_not_called()
    sent = update.effective_message.reply_text.await_args_list[0]
    assert "too long" in sent.args[0].lower()


async def test_transcription_failure_replies_error(cfg, tmp_path):
    transcriber = MagicMock()
    transcriber.transcribe.side_effect = RuntimeError("boom")
    handler = AudioHandler(transcriber, cfg)
    update = make_update(voice=media())
    await handler.handle(update, make_context(tmp_path))
    sent = update.effective_message.reply_text.await_args_list[0]
    assert "couldn't transcribe" in sent.args[0].lower()


async def test_size_guard(tmp_path):
    cfg = load_config({"TELEGRAM_BOT_TOKEN": "x", "MAX_FILE_MB": "1"})
    transcriber = MagicMock()
    handler = AudioHandler(transcriber, cfg)
    update = make_update(voice=media(file_size=5 * 1024 * 1024))
    await handler.handle(update, make_context(tmp_path))
    transcriber.transcribe.assert_not_called()
    sent = update.effective_message.reply_text.await_args_list[0]
    assert "too large" in sent.args[0].lower()


async def test_temp_file_removed_after_success(cfg, tmp_path):
    import os
    transcriber = MagicMock()
    transcriber.transcribe.return_value = TranscriptionResult("hi", "en", 1.0)
    handler = AudioHandler(transcriber, cfg)
    captured = {}

    async def fake_download(custom_path=None):
        captured["path"] = custom_path
        with open(custom_path, "wb") as fh:
            fh.write(b"x")

    from types import SimpleNamespace
    tg_file = SimpleNamespace(download_to_drive=fake_download)
    context = SimpleNamespace(bot=SimpleNamespace(get_file=AsyncMock(return_value=tg_file)))
    update = make_update(voice=media())
    await handler.handle(update, context)
    assert not os.path.exists(captured["path"])


async def test_send_failure_after_success_does_not_send_error_reply(cfg, tmp_path):
    transcriber = MagicMock()
    transcriber.transcribe.return_value = TranscriptionResult("x" * 5000, "en", 5.0)
    handler = AudioHandler(transcriber, cfg)
    update = make_update(voice=media())
    update.effective_message.reply_text = AsyncMock(side_effect=[None, RuntimeError("send failed")])
    with pytest.raises(RuntimeError):
        await handler.handle(update, make_context(tmp_path))
    calls = update.effective_message.reply_text.await_args_list
    assert all(
        "couldn't transcribe" not in (c.args[0].lower() if c.args else "")
        for c in calls
    )
