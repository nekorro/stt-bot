from prometheus_client import generate_latest
from stt_bot import metrics


def test_counters_increment_and_render():
    metrics.MESSAGES_RECEIVED.labels(type="voice").inc()
    metrics.TRANSCRIPTIONS.labels(status="success").inc()
    metrics.TRANSCRIPTION_DURATION.observe(1.2)
    metrics.AUDIO_DURATION.observe(5.0)
    output = generate_latest().decode()
    assert "stt_bot_messages_received_total" in output
    assert "stt_bot_transcriptions_total" in output
    assert "stt_bot_transcription_duration_seconds" in output
    assert 'stt_bot_transcription_duration_seconds_bucket{le="60.0"}' in output
    assert "stt_bot_audio_duration_seconds" in output
    assert "stt_bot_build_info" in output
