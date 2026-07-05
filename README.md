# stt-bot

A Telegram bot that turns voice messages into text. Send it a voice note and it
replies to that message with a transcription. Russian and English are recognised by
default; the language is detected automatically for each message.

Transcription is powered by [OpenAI Whisper](https://github.com/openai/whisper),
running on CPU.

## How it works

The bot uses long polling, so it needs no public URL or inbound firewall rules — it
just needs outbound access to Telegram. For each incoming voice message it:

1. downloads the file,
2. transcribes it with Whisper (in a worker thread so the bot stays responsive),
3. replies to the original message with the text (splitting long transcripts across
   several messages).

## Configuration

All configuration is via environment variables:

| Variable | Default | Description |
|----------|---------|-------------|
| `TELEGRAM_BOT_TOKEN` | — (required) | Bot token from [@BotFather](https://t.me/BotFather). |
| `WHISPER_MODEL` | `base` | Whisper model: `tiny`, `base`, `small`, `medium`, `large`. Bigger = more accurate, slower. |
| `WHISPER_TASK` | `transcribe` | `transcribe` (keep the spoken language) or `translate` (into English). |
| `WHISPER_DEVICE` | `cpu` | Compute device. |
| `WHISPER_LANGUAGE` | auto | Force a single source language (e.g. `en`, `ru`); overrides the allowed-languages set below. |
| `WHISPER_ALLOWED_LANGUAGES` | `en,ru` | Comma-separated languages to restrict detection to (one is picked per message). Set empty to allow all languages. |
| `ALLOWED_CHAT_IDS` | all | Comma-separated chat IDs to restrict the bot to. |
| `MAX_AUDIO_DURATION_S` | `600` | Reject audio longer than this. |
| `MAX_FILE_MB` | `50` | Reject files larger than this. |
| `MAX_CONCURRENT_TRANSCRIPTIONS` | `1` | How many transcriptions may run at once. |
| `METRICS_PORT` | `9100` | Port for `/metrics`, `/healthz`, `/readyz`. |
| `LOG_LEVEL` | `INFO` | Logging level. |

## Running locally

```bash
python3.14 -m venv .venv && . .venv/bin/activate
pip install --extra-index-url https://download.pytorch.org/whl/cpu ".[whisper]"
export TELEGRAM_BOT_TOKEN="123456:your-token"
python -m stt_bot
```

You'll also need [ffmpeg](https://ffmpeg.org/) installed (Whisper uses it to decode audio).

## Running with Docker

```bash
docker run -e TELEGRAM_BOT_TOKEN="123456:your-token" nekorro/stt-bot:latest
```

The image bundles ffmpeg and the `base` model, so it starts without downloading anything.

## Monitoring

The bot exposes Prometheus metrics on `METRICS_PORT`:

- `stt_bot_messages_received_total{type}`
- `stt_bot_transcriptions_total{status}`
- `stt_bot_transcription_duration_seconds`
- `stt_bot_audio_duration_seconds`

plus `/healthz` (liveness) and `/readyz` (ready once the model is loaded).

## Development

```bash
pip install -e ".[dev]"
pytest -m "not slow"      # fast unit tests
pytest                    # include the slow end-to-end test (needs ffmpeg + the whisper extra)
```

## License

MIT
