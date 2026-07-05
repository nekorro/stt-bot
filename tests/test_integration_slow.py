import shutil
import subprocess

import pytest

from stt_bot.transcriber import Transcriber, TranscriptionResult

pytestmark = pytest.mark.slow


@pytest.mark.skipif(shutil.which("ffmpeg") is None, reason="ffmpeg not installed")
def test_tiny_model_runs_end_to_end(tmp_path):
    pytest.importorskip("faster_whisper")
    wav = tmp_path / "tone.wav"
    subprocess.run(
        ["ffmpeg", "-y", "-f", "lavfi", "-i", "sine=frequency=440:duration=1",
         "-ar", "16000", str(wav)],
        check=True, capture_output=True,
    )
    t = Transcriber.load("tiny", "cpu", compute_type="int8")
    result = t.transcribe(str(wav))
    assert isinstance(result, TranscriptionResult)
