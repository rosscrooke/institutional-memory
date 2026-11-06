import pytest

from dashboard.core import Briefing, briefing_cache_key, parse_briefing

KNOWN = {"/global/prod-access.md", "/global/team.md"}


def test_parses_json_even_when_wrapped_in_a_code_fence():
    raw = """Here you go:
```json
{"relevant": [{"path": "/global/prod-access.md", "why": "You will need prod to debug"}],
 "questions": ["How do I get read-only prod access?", "Who is on call?"]}
```"""
    b = parse_briefing(raw, KNOWN)

    assert b == Briefing(
        relevant=[("/global/prod-access.md", "You will need prod to debug")],
        questions=["How do I get read-only prod access?", "Who is on call?"],
    )


def test_drops_paths_the_store_does_not_contain():
    raw = '{"relevant": [{"path": "/global/made-up.md", "why": "x"}, {"path": "/global/team.md", "why": "y"}], "questions": []}'

    assert parse_briefing(raw, KNOWN).relevant == [("/global/team.md", "y")]


def test_unparseable_response_raises_value_error():
    with pytest.raises(ValueError):
        parse_briefing("sorry, I can't", KNOWN)


def test_cache_key_changes_when_role_or_any_memory_changes():
    base = briefing_cache_key("Backend Engineer", {"/a.md": "h1", "/b.md": "h2"})

    assert base == briefing_cache_key("Backend Engineer", {"/b.md": "h2", "/a.md": "h1"})
    assert base != briefing_cache_key("SRE", {"/a.md": "h1", "/b.md": "h2"})
    assert base != briefing_cache_key("Backend Engineer", {"/a.md": "h1", "/b.md": "CHANGED"})
    assert base != briefing_cache_key("Backend Engineer", {"/a.md": "h1"})
