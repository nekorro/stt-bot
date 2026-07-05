"""Transcriber backed by faster-whisper (CTranslate2). Model injected for engine-free tests."""
from __future__ import annotations

from collections.abc import Callable, Mapping
from dataclasses import dataclass


@dataclass(frozen=True)
class TranscriptionResult:
    text: str
    language: str
    duration_s: float


class Transcriber:
    def __init__(
        self,
        model,
        task: str = "transcribe",
        language: str | None = None,
        allowed_languages: list[str] | tuple[str, ...] | None = None,
        detect_language: Callable[[str], Mapping[str, float]] | None = None,
        beam_size: int = 1,
        vad_filter: bool = True,
        priority_language: str | None = None,
        priority_margin: float = 0.0,
        initial_prompt: str | None = None,
    ):
        self._model = model
        self._task = task
        self._language = language
        self._allowed_languages = list(allowed_languages) if allowed_languages else None
        self._detect_language = detect_language
        self._beam_size = beam_size
        self._vad_filter = vad_filter
        self._priority_language = priority_language
        self._priority_margin = priority_margin
        self._initial_prompt = initial_prompt

    @classmethod
    def load(
        cls,
        model_name: str,
        device: str,
        compute_type: str = "int8",
        cpu_threads: int = 0,
        task: str = "transcribe",
        language: str | None = None,
        allowed_languages: list[str] | tuple[str, ...] | None = None,
        beam_size: int = 1,
        vad_filter: bool = True,
        priority_language: str | None = None,
        priority_margin: float = 0.0,
        initial_prompt: str | None = None,
        download_root: str | None = None,
    ) -> "Transcriber":
        from faster_whisper import WhisperModel, decode_audio  # lazy: engine-free tests

        model = WhisperModel(
            model_name,
            device=device,
            compute_type=compute_type,
            cpu_threads=cpu_threads,
            download_root=download_root,
        )

        def detect(audio_path: str) -> Mapping[str, float]:
            audio = decode_audio(audio_path)
            _, _, all_probs = model.detect_language(audio)
            return {lang: prob for lang, prob in all_probs}

        return cls(
            model,
            task=task,
            language=language,
            allowed_languages=allowed_languages,
            detect_language=detect,
            beam_size=beam_size,
            vad_filter=vad_filter,
            priority_language=priority_language,
            priority_margin=priority_margin,
            initial_prompt=initial_prompt,
        )

    def _resolve_language(self, audio_path: str) -> str | None:
        if self._language:
            return self._language
        if self._allowed_languages and self._detect_language is not None:
            probs = self._detect_language(audio_path)
            best = max(self._allowed_languages, key=lambda lang: probs.get(lang, 0.0))
            prio = self._priority_language
            if (
                prio
                and prio in self._allowed_languages
                and probs.get(prio, 0.0) >= probs.get(best, 0.0) - self._priority_margin
            ):
                return prio
            return best
        return None

    def transcribe(self, audio_path: str) -> TranscriptionResult:
        language = self._resolve_language(audio_path)
        prompt = (
            self._initial_prompt
            if self._initial_prompt and language == self._priority_language
            else None
        )
        segments, info = self._model.transcribe(
            audio_path,
            language=language,
            task=self._task,
            beam_size=self._beam_size,
            vad_filter=self._vad_filter,
            condition_on_previous_text=False,
            initial_prompt=prompt,
        )
        text = "".join(segment.text for segment in segments).strip()
        return TranscriptionResult(
            text=text,
            language=(getattr(info, "language", "") or ""),
            duration_s=float(getattr(info, "duration", 0.0) or 0.0),
        )

    def warmup(self, audio=None) -> None:
        """Prime CTranslate2 so the first real request isn't slow. Best-effort."""
        try:
            if audio is None:
                import numpy as np  # provided transitively by faster-whisper

                audio = np.zeros(16000, dtype=np.float32)  # 1s of silence @ 16 kHz
            segments, _ = self._model.transcribe(
                audio, beam_size=self._beam_size, vad_filter=False
            )
            for _ in segments:
                pass
        except Exception:  # noqa: BLE001 — warm-up must never break startup
            pass
