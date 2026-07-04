from uebot.textsplit import split_message, TELEGRAM_MAX_CHARS


def test_short_text_single_chunk():
    assert split_message("hello") == ["hello"]


def test_empty_text_returns_empty_list():
    assert split_message("") == []
    assert split_message("   ") == []


def test_splits_on_limit():
    text = "a" * 5000
    chunks = split_message(text, limit=4096)
    assert all(len(c) <= 4096 for c in chunks)
    assert "".join(chunks) == text


def test_prefers_newline_boundary():
    text = "line1\n" + ("x" * 4090) + "\nline3"
    chunks = split_message(text, limit=4096)
    assert all(len(c) <= 4096 for c in chunks)
    assert chunks[0] == "line1"


def test_default_limit_is_telegram_max():
    assert TELEGRAM_MAX_CHARS == 4096
