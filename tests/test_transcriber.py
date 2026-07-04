from uebot.transcriber import Transcriber, TranscriptionResult


class FakeModel:
    def __init__(self, result):
        self._result = result
        self.calls = []

    def transcribe(self, path, task=None, language=None):
        self.calls.append({"path": path, "task": task, "language": language})
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
    assert model.calls[0] == {"path": "/tmp/a.ogg", "task": "transcribe", "language": None}


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
