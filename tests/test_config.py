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
    assert cfg.whisper_allowed_languages == ("en", "ru")


def test_allowed_languages_parsed_and_lowercased():
    cfg = load_config(
        {"TELEGRAM_BOT_TOKEN": "x", "WHISPER_ALLOWED_LANGUAGES": "EN, De ,fr"}
    )
    assert cfg.whisper_allowed_languages == ("en", "de", "fr")


def test_empty_allowed_languages_means_no_restriction():
    cfg = load_config(
        {"TELEGRAM_BOT_TOKEN": "x", "WHISPER_ALLOWED_LANGUAGES": ""}
    )
    assert cfg.whisper_allowed_languages is None


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


def test_speed_defaults():
    cfg = load_config({"TELEGRAM_BOT_TOKEN": "x"})
    assert cfg.whisper_compute_type == "int8"
    assert cfg.whisper_beam_size == 1
    assert cfg.whisper_vad is True
    assert cfg.whisper_cpu_threads == 0


def test_speed_overrides_parsed():
    cfg = load_config({
        "TELEGRAM_BOT_TOKEN": "x",
        "WHISPER_COMPUTE_TYPE": "float32",
        "WHISPER_BEAM_SIZE": "5",
        "WHISPER_VAD": "false",
        "WHISPER_CPU_THREADS": "2",
    })
    assert cfg.whisper_compute_type == "float32"
    assert cfg.whisper_beam_size == 5
    assert cfg.whisper_vad is False
    assert cfg.whisper_cpu_threads == 2


def test_invalid_beam_size_raises():
    with pytest.raises(ConfigError):
        load_config({"TELEGRAM_BOT_TOKEN": "x", "WHISPER_BEAM_SIZE": "0"})


def test_invalid_vad_raises():
    with pytest.raises(ConfigError):
        load_config({"TELEGRAM_BOT_TOKEN": "x", "WHISPER_VAD": "maybe"})


def test_language_priority_and_prompt_defaults():
    cfg = load_config({"TELEGRAM_BOT_TOKEN": "x"})
    assert cfg.whisper_priority_language == "ru"
    assert cfg.whisper_priority_margin == 0.2
    assert cfg.whisper_initial_prompt  # non-empty Russian default
    assert "хуй" in cfg.whisper_initial_prompt


def test_priority_and_prompt_overrides():
    cfg = load_config({
        "TELEGRAM_BOT_TOKEN": "x",
        "WHISPER_LANGUAGE_PRIORITY": "EN",
        "WHISPER_PRIORITY_MARGIN": "0.5",
        "WHISPER_INITIAL_PROMPT": "hi there",
    })
    assert cfg.whisper_priority_language == "en"
    assert cfg.whisper_priority_margin == 0.5
    assert cfg.whisper_initial_prompt == "hi there"


def test_empty_priority_and_prompt_become_none():
    cfg = load_config({
        "TELEGRAM_BOT_TOKEN": "x",
        "WHISPER_LANGUAGE_PRIORITY": "",
        "WHISPER_INITIAL_PROMPT": "",
    })
    assert cfg.whisper_priority_language is None
    assert cfg.whisper_initial_prompt is None


def test_invalid_margin_raises():
    with pytest.raises(ConfigError):
        load_config({"TELEGRAM_BOT_TOKEN": "x", "WHISPER_PRIORITY_MARGIN": "1.5"})
    with pytest.raises(ConfigError):
        load_config({"TELEGRAM_BOT_TOKEN": "x", "WHISPER_PRIORITY_MARGIN": "abc"})
