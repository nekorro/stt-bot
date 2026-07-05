# syntax=docker/dockerfile:1
FROM python:3.14-slim AS base

ENV PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    WHISPER_DOWNLOAD_ROOT=/models \
    WHISPER_MODEL=base \
    WHISPER_COMPUTE_TYPE=int8 \
    METRICS_PORT=9100

WORKDIR /app

# faster-whisper decodes audio via bundled PyAV, so no system ffmpeg is needed.
COPY pyproject.toml ./
COPY src ./src
RUN pip install ".[whisper]"

# Bake the CTranslate2 base model so startup needs no network and no PVC.
RUN mkdir -p /models \
    && python -c "from faster_whisper import WhisperModel; WhisperModel('base', device='cpu', compute_type='int8', download_root='/models')" \
    && chmod -R a+rX /models

# Force offline mode after bake so runtime never contacts HuggingFace Hub and uses the baked model.
ENV HF_HUB_OFFLINE=1

# Non-root runtime user.
RUN useradd --uid 1000 --create-home --shell /usr/sbin/nologin appuser
USER 1000

EXPOSE 9100
ENTRYPOINT ["python", "-m", "stt_bot"]
