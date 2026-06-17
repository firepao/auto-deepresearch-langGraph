from utils import deduplicate_and_format_sources, format_sources, strip_thinking_tokens


def test_strip_thinking_tokens_removes_think_blocks():
    text = "visible <think>hidden</think> answer"

    assert strip_thinking_tokens(text) == "visible  answer"


def test_format_sources_builds_bullet_list():
    payload = {
        "results": [
            {"title": "Example", "url": "https://example.com"},
            {"title": "No URL"},
        ]
    }

    assert format_sources(payload) == "* Example : https://example.com"


def test_deduplicate_and_format_sources_by_url():
    payload = {
        "results": [
            {"title": "One", "url": "https://example.com", "content": "A"},
            {"title": "Duplicate", "url": "https://example.com", "content": "B"},
        ]
    }

    formatted = deduplicate_and_format_sources(payload, max_tokens_per_source=100)

    assert formatted.count("https://example.com") == 1
    assert "One" in formatted
    assert "Duplicate" not in formatted
