import pytest
from stt_bot.config import load_config, Config, ConfigError


def test_minimal_env_uses_defaults():
    cfg = load_config({"TELEGRAM_BOT_TOKEN": "abc"})
    assert isinstance(cfg, Config)
    assert cfg.telegram_bot_token == "abc"
    assert cfg.whisper_model == "base"
    assert cfg.whisper_task == "transcribe"
    assert cfg.whisper_device == "cpu"
    assert cfg.whisper_language is None
    assert cfg.allowed_chat_ids is None
    assert cfg.max_audio_duration_s == 600
    assert cfg.max_file_mb == 50
    assert cfg.max_concurrent_transcriptions == 1
    assert cfg.metrics_port == 9100
    assert cfg.log_level == "INFO"


def test_missing_token_raises():
    with pytest.raises(ConfigError):
        load_config({})


def test_invalid_task_raises():
    with pytest.raises(ConfigError):
        load_config({"TELEGRAM_BOT_TOKEN": "x", "WHISPER_TASK": "sing"})


def test_allowed_chat_ids_parsed():
    cfg = load_config({"TELEGRAM_BOT_TOKEN": "x", "ALLOWED_CHAT_IDS": "10, -20 ,30"})
    assert cfg.allowed_chat_ids == frozenset({10, -20, 30})


def test_invalid_int_raises():
    with pytest.raises(ConfigError):
        load_config({"TELEGRAM_BOT_TOKEN": "x", "METRICS_PORT": "notanint"})
