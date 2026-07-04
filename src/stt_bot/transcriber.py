"""Whisper wrapper. The model object is injected so this is testable without torch."""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class TranscriptionResult:
    text: str
    language: str
    duration_s: float


def _duration(result: dict) -> float:
    segments = result.get("segments") or []
    if not segments:
        return 0.0
    return float(segments[-1].get("end", 0.0) or 0.0)


class Transcriber:
    def __init__(self, model, task: str = "transcribe", language: str | None = None):
        self._model = model
        self._task = task
        self._language = language

    @classmethod
    def load(
        cls,
        model_name: str,
        device: str,
        task: str = "transcribe",
        language: str | None = None,
        download_root: str | None = None,
    ) -> "Transcriber":
        import whisper  # lazy: keeps torch out of unit tests

        model = whisper.load_model(model_name, device=device, download_root=download_root)
        return cls(model, task=task, language=language)

    def transcribe(self, audio_path: str) -> TranscriptionResult:
        result = self._model.transcribe(
            audio_path, task=self._task, language=self._language
        )
        return TranscriptionResult(
            text=(result.get("text") or "").strip(),
            language=(result.get("language") or ""),
            duration_s=_duration(result),
        )
