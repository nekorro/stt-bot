"""Prometheus metrics for stt_bot."""
from __future__ import annotations

from prometheus_client import Counter, Gauge, Histogram

from . import __version__

MESSAGES_RECEIVED = Counter(
    "stt_bot_messages_received_total",
    "Voice messages received",
    ["type"],
)
TRANSCRIPTIONS = Counter(
    "stt_bot_transcriptions_total",
    "Transcription outcomes",
    ["status"],  # success | failure | rejected | empty
)
TRANSCRIPTION_DURATION = Histogram(
    "stt_bot_transcription_duration_seconds",
    "Wall-clock time spent transcribing",
    buckets=(1, 5, 15, 30, 60, 120, 300, 600),
)
AUDIO_DURATION = Histogram(
    "stt_bot_audio_duration_seconds",
    "Duration of received audio",
    buckets=(5, 15, 30, 60, 120, 300, 600, 1200),
)
BUILD_INFO = Gauge(
    "stt_bot_build_info",
    "Build info",
    ["version"],
)
BUILD_INFO.labels(version=__version__).set(1)
