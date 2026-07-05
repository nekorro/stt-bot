from stt_bot.transcriber import Transcriber, TranscriptionResult


class FakeModel:
    def __init__(self, result):
        self._result = result
        self.calls = []

    def transcribe(self, path, task=None, language=None, fp16=None):
        self.calls.append(
            {"path": path, "task": task, "language": language, "fp16": fp16}
        )
        return self._result


def test_maps_whisper_result():
    model = FakeModel({
        "text": "  hello world  ",
        "language": "en",
        "segments": [{"end": 3.5}],
    })
    t = Transcriber(model, task="transcribe", language=None)
    result = t.transcribe("/tmp/a.ogg")
    assert isinstance(result, TranscriptionResult)
    assert result.text == "hello world"
    assert result.language == "en"
    assert result.duration_s == 3.5
    assert model.calls[0] == {
        "path": "/tmp/a.ogg", "task": "transcribe", "language": None, "fp16": False
    }


def test_empty_text_and_no_segments():
    model = FakeModel({"text": "", "language": "ru"})
    t = Transcriber(model)
    result = t.transcribe("/tmp/b.ogg")
    assert result.text == ""
    assert result.language == "ru"
    assert result.duration_s == 0.0


def test_passes_task_and_language_through():
    model = FakeModel({"text": "hi", "language": "en", "segments": []})
    t = Transcriber(model, task="translate", language="de")
    t.transcribe("/tmp/c.ogg")
    assert model.calls[0]["task"] == "translate"
    assert model.calls[0]["language"] == "de"


def test_disables_fp16_for_cpu():
    # Whisper warns "FP16 is not supported on CPU" unless fp16=False is passed.
    model = FakeModel({"text": "hi", "language": "en", "segments": []})
    t = Transcriber(model)
    t.transcribe("/tmp/a.ogg")
    assert model.calls[0]["fp16"] is False


def test_no_allowed_languages_leaves_detection_to_whisper():
    model = FakeModel({"text": "hi", "language": "en", "segments": []})
    t = Transcriber(model)
    t.transcribe("/tmp/a.ogg")
    assert model.calls[0]["language"] is None


def test_restricts_detected_language_to_allowed_set():
    # Detector thinks French is most likely, but only en/ru are allowed;
    # ru outranks en among the allowed set, so ru is forced.
    model = FakeModel({"text": "привет", "language": "ru", "segments": []})
    detect = lambda path: {"fr": 0.90, "ru": 0.60, "en": 0.20}
    t = Transcriber(model, allowed_languages=["en", "ru"], detect_language=detect)
    t.transcribe("/tmp/a.ogg")
    assert model.calls[0]["language"] == "ru"


def test_picks_english_when_more_probable_among_allowed():
    model = FakeModel({"text": "hello", "language": "en", "segments": []})
    detect = lambda path: {"en": 0.80, "ru": 0.10}
    t = Transcriber(model, allowed_languages=["en", "ru"], detect_language=detect)
    t.transcribe("/tmp/a.ogg")
    assert model.calls[0]["language"] == "en"


def test_forced_language_overrides_allowed_detection():
    model = FakeModel({"text": "hi", "language": "en", "segments": []})
    called = {"detect": False}

    def detect(path):
        called["detect"] = True
        return {"en": 0.1, "ru": 0.9}

    t = Transcriber(
        model, language="en", allowed_languages=["en", "ru"], detect_language=detect
    )
    t.transcribe("/tmp/a.ogg")
    assert model.calls[0]["language"] == "en"
    assert called["detect"] is False  # a forced language skips detection entirely
