"""Split transcripts into Telegram-sized message chunks."""
from __future__ import annotations

TELEGRAM_MAX_CHARS = 4096


def split_message(text: str, limit: int = TELEGRAM_MAX_CHARS) -> list[str]:
    text = text.strip()
    if not text:
        return []

    chunks: list[str] = []
    remaining = text
    while len(remaining) > limit:
        window = remaining[:limit]
        # Prefer a newline boundary, then a space, else a hard cut.
        cut = window.rfind("\n")
        if cut <= 0:
            cut = window.rfind(" ")
        if cut <= 0:
            cut = limit
        chunk = remaining[:cut].strip()
        if chunk:
            chunks.append(chunk)
        remaining = remaining[cut:].strip()

    if remaining:
        chunks.append(remaining)
    return chunks
