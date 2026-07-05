from stt_bot.transcriber import Transcriber, TranscriptionResult


class FakeSegment:
    def __init__(self, text):
        self.text = text


class FakeInfo:
    def __init__(self, language="en", duration=0.0):
        self.language = language
        self.duration = duration


class FakeModel:
    def __init__(self, segments=(), info=None):
        self._segments = list(segments)
        self._info = info or FakeInfo()
        self.calls = []

    def transcribe(self, audio, **kwargs):
        self.calls.append({"audio": audio, **kwargs})
        return iter(self._segments), self._info


def test_assembles_text_from_segments():
    model = FakeModel(
        segments=[FakeSegment(" hello"), FakeSegment(" world ")],
        info=FakeInfo(language="en", duration=3.5),
    )
    t = Transcriber(model, task="transcribe")
    result = t.transcribe("/tmp/a.ogg")
    assert isinstance(result, TranscriptionResult)
    assert result.text == "hello world"
    assert result.language == "en"
    assert result.duration_s == 3.5


def test_passes_decoding_options():
    model = FakeModel(info=FakeInfo("ru", 1.0))
    t = Transcriber(model, task="translate", language="ru", beam_size=1, vad_filter=True)
    t.transcribe("/tmp/a.ogg")
    call = model.calls[0]
    assert call["audio"] == "/tmp/a.ogg"
    assert call["task"] == "translate"
    assert call["language"] == "ru"
    assert call["beam_size"] == 1
    assert call["vad_filter"] is True
    assert call["condition_on_previous_text"] is False


def test_no_allowed_languages_leaves_detection_to_engine():
    model = FakeModel(info=FakeInfo("en", 1.0))
    t = Transcriber(model)
    t.transcribe("/tmp/a.ogg")
    assert model.calls[0]["language"] is None


def test_restricts_detected_language_to_allowed_set():
    model = FakeModel(info=FakeInfo("ru", 1.0))
    detect = lambda path: {"fr": 0.90, "ru": 0.60, "en": 0.20}
    t = Transcriber(model, allowed_languages=["en", "ru"], detect_language=detect)
    t.transcribe("/tmp/a.ogg")
    assert model.calls[0]["language"] == "ru"


def test_picks_english_when_more_probable_among_allowed():
    model = FakeModel(info=FakeInfo("en", 1.0))
    detect = lambda path: {"en": 0.80, "ru": 0.10}
    t = Transcriber(model, allowed_languages=["en", "ru"], detect_language=detect)
    t.transcribe("/tmp/a.ogg")
    assert model.calls[0]["language"] == "en"


def test_forced_language_overrides_allowed_detection():
    model = FakeModel(info=FakeInfo("en", 1.0))
    called = {"detect": False}

    def detect(path):
        called["detect"] = True
        return {"en": 0.1, "ru": 0.9}

    t = Transcriber(model, language="en", allowed_languages=["en", "ru"], detect_language=detect)
    t.transcribe("/tmp/a.ogg")
    assert model.calls[0]["language"] == "en"
    assert called["detect"] is False


def test_warmup_primes_model():
    model = FakeModel(info=FakeInfo("en", 0.0))
    t = Transcriber(model, beam_size=1)
    t.warmup(audio=[0.0])  # explicit audio avoids needing numpy in tests
    assert model.calls
    assert model.calls[0]["audio"] == [0.0]
    assert model.calls[0]["vad_filter"] is False


def test_warmup_never_raises_on_model_error():
    class BoomModel:
        def transcribe(self, audio, **kwargs):
            raise RuntimeError("boom")

    Transcriber(BoomModel()).warmup(audio=[0.0])  # must not raise
