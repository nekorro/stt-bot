# syntax=docker/dockerfile:1
FROM python:3.14-slim AS base

ENV PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    WHISPER_DOWNLOAD_ROOT=/models \
    WHISPER_MODEL=base \
    METRICS_PORT=9100

RUN apt-get update \
    && apt-get install -y --no-install-recommends ffmpeg \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install torch from the CPU wheel index first, then the app + whisper extra.
COPY pyproject.toml ./
COPY src ./src
RUN pip install --extra-index-url https://download.pytorch.org/whl/cpu ".[whisper]"

# Bake the model so startup needs no network and no PVC.
RUN mkdir -p /models \
    && python -c "import whisper; whisper.load_model('base', download_root='/models')" \
    && chmod -R a+rX /models

# Non-root runtime user.
RUN useradd --uid 1000 --create-home --shell /usr/sbin/nologin appuser
USER 1000

EXPOSE 9100
ENTRYPOINT ["python", "-m", "stt_bot"]
