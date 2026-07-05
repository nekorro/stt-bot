"""Whisper wrapper. The model object is injected so this is testable without torch."""
from __future__ import annotations

from collections.abc import Callable, Mapping
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
    def __init__(
        self,
        model,
        task: str = "transcribe",
        language: str | None = None,
        allowed_languages: list[str] | tuple[str, ...] | None = None,
        detect_language: Callable[[str], Mapping[str, float]] | None = None,
    ):
        self._model = model
        self._task = task
        self._language = language
        self._allowed_languages = list(allowed_languages) if allowed_languages else None
        self._detect_language = detect_language

    @classmethod
    def load(
        cls,
        model_name: str,
        device: str,
        task: str = "transcribe",
        language: str | None = None,
        allowed_languages: list[str] | tuple[str, ...] | None = None,
        download_root: str | None = None,
    ) -> "Transcriber":
        import whisper  # lazy: keeps torch out of unit tests

        model = whisper.load_model(model_name, device=device, download_root=download_root)

        def detect(audio_path: str) -> Mapping[str, float]:
            audio = whisper.pad_or_trim(whisper.load_audio(audio_path))
            mel = whisper.log_mel_spectrogram(
                audio, n_mels=model.dims.n_mels
            ).to(model.device)
            _, probs = model.detect_language(mel)
            return probs

        return cls(
            model,
            task=task,
            language=language,
            allowed_languages=allowed_languages,
            detect_language=detect,
        )

    def _resolve_language(self, audio_path: str) -> str | None:
        if self._language:
            return self._language
        if self._allowed_languages and self._detect_language is not None:
            probs = self._detect_language(audio_path)
            return max(self._allowed_languages, key=lambda lang: probs.get(lang, 0.0))
        return None

    def transcribe(self, audio_path: str) -> TranscriptionResult:
        language = self._resolve_language(audio_path)
        # fp16=False: we run on CPU, where fp16 is unsupported (and Whisper warns).
        result = self._model.transcribe(
            audio_path, task=self._task, language=language, fp16=False
        )
        return TranscriptionResult(
            text=(result.get("text") or "").strip(),
            language=(result.get("language") or ""),
            duration_s=_duration(result),
        )
