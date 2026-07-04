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


def test_no_chunk_has_leading_or_trailing_whitespace():
    text = "word " * 2000  # spaces force boundary breaks
    chunks = split_message(text, limit=100)
    assert chunks  # non-empty
    for c in chunks:
        assert c == c.strip()
        assert 0 < len(c) <= 100


def test_hard_split_preserves_content_exactly():
    # A single unbroken token (no whitespace) is hard-split and fully preserved.
    text = "x" * 9000
    chunks = split_message(text, limit=4096)
    assert "".join(chunks) == text
    assert all(len(c) <= 4096 for c in chunks)


def test_all_words_preserved_across_boundaries():
    # Whitespace at split points is dropped, but no word is lost or merged.
    text = " ".join(f"w{i}" for i in range(500))
    chunks = split_message(text, limit=40)
    joined_words = " ".join(chunks).split()
    assert joined_words == text.split()
