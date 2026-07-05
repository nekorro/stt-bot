"""Environment-driven configuration, validated and fail-fast."""
from __future__ import annotations

import os
from collections.abc import Mapping
from dataclasses import dataclass

_VALID_TASKS = {"transcribe", "translate"}


class ConfigError(Exception):
    """Raised when configuration is missing or invalid."""


@dataclass(frozen=True)
class Config:
    telegram_bot_token: str
    whisper_model: str
    whisper_task: str
    whisper_device: str
    whisper_language: str | None
    whisper_allowed_languages: tuple[str, ...] | None
    whisper_compute_type: str
    whisper_beam_size: int
    whisper_vad: bool
    whisper_cpu_threads: int
    whisper_download_root: str | None
    allowed_chat_ids: frozenset[int] | None
    max_audio_duration_s: int
    max_file_mb: int
    max_concurrent_transcriptions: int
    metrics_port: int
    log_level: str


def _req(env: Mapping[str, str], key: str) -> str:
    value = env.get(key, "").strip()
    if not value:
        raise ConfigError(f"{key} is required")
    return value


def _int(env: Mapping[str, str], key: str, default: int) -> int:
    raw = env.get(key)
    if raw is None or raw.strip() == "":
        return default
    try:
        return int(raw)
    except ValueError as exc:
        raise ConfigError(f"{key} must be an integer, got {raw!r}") from exc


def _bool(env: Mapping[str, str], key: str, default: bool) -> bool:
    raw = env.get(key)
    if raw is None or raw.strip() == "":
        return default
    value = raw.strip().lower()
    if value in {"1", "true", "yes", "on"}:
        return True
    if value in {"0", "false", "no", "off"}:
        return False
    raise ConfigError(f"{key} must be a boolean, got {raw!r}")


def _languages(raw: str | None) -> tuple[str, ...] | None:
    # Unset → default to Russian + English. Explicit empty string → no restriction.
    if raw is None:
        raw = "en,ru"
    langs = tuple(part.strip().lower() for part in raw.split(",") if part.strip())
    return langs or None


def _chat_ids(raw: str | None) -> frozenset[int] | None:
    if raw is None or raw.strip() == "":
        return None
    try:
        return frozenset(int(part) for part in raw.split(",") if part.strip())
    except ValueError as exc:
        raise ConfigError(f"ALLOWED_CHAT_IDS must be comma-separated ints, got {raw!r}") from exc


def load_config(env: Mapping[str, str] = os.environ) -> Config:
    task = env.get("WHISPER_TASK", "transcribe").strip()
    if task not in _VALID_TASKS:
        raise ConfigError(f"WHISPER_TASK must be one of {sorted(_VALID_TASKS)}, got {task!r}")

    language = env.get("WHISPER_LANGUAGE", "").strip() or None
    download_root = env.get("WHISPER_DOWNLOAD_ROOT", "").strip() or None

    beam_size = _int(env, "WHISPER_BEAM_SIZE", 1)
    if beam_size < 1:
        raise ConfigError(f"WHISPER_BEAM_SIZE must be >= 1, got {beam_size}")
    cpu_threads = _int(env, "WHISPER_CPU_THREADS", 0)
    if cpu_threads < 0:
        raise ConfigError(f"WHISPER_CPU_THREADS must be >= 0, got {cpu_threads}")

    return Config(
        telegram_bot_token=_req(env, "TELEGRAM_BOT_TOKEN"),
        whisper_model=env.get("WHISPER_MODEL", "base").strip() or "base",
        whisper_task=task,
        whisper_device=env.get("WHISPER_DEVICE", "cpu").strip() or "cpu",
        whisper_language=language,
        whisper_allowed_languages=_languages(env.get("WHISPER_ALLOWED_LANGUAGES")),
        whisper_compute_type=env.get("WHISPER_COMPUTE_TYPE", "int8").strip() or "int8",
        whisper_beam_size=beam_size,
        whisper_vad=_bool(env, "WHISPER_VAD", True),
        whisper_cpu_threads=cpu_threads,
        whisper_download_root=download_root,
        allowed_chat_ids=_chat_ids(env.get("ALLOWED_CHAT_IDS")),
        max_audio_duration_s=_int(env, "MAX_AUDIO_DURATION_S", 600),
        max_file_mb=_int(env, "MAX_FILE_MB", 50),
        max_concurrent_transcriptions=_int(env, "MAX_CONCURRENT_TRANSCRIPTIONS", 1),
        metrics_port=_int(env, "METRICS_PORT", 9100),
        log_level=env.get("LOG_LEVEL", "INFO").strip() or "INFO",
    )
