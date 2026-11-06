from datetime import datetime, timezone
from types import SimpleNamespace as NS

from dashboard.core import build_timeline


def version(day, op, content, session_id=None):
    actor = NS(type="session_actor", session_id=session_id) if session_id else None
    return NS(
        created_at=datetime(2026, 5, day, tzinfo=timezone.utc),
        operation=op,
        content=content,
        created_by=actor,
    )


def test_orders_oldest_first_and_diffs_against_previous_version():
    versions = [
        version(15, "modified", "Prod access: file a Jira ticket\n", "sesn_2"),
        version(1, "created", "Prod access: ask in #sre on Slack\n", "sesn_1"),
    ]
    names = {"sesn_1": "Tom (expert)", "sesn_2": "Maya (expert)"}

    timeline = build_timeline(versions, lambda sid: names.get(sid or "", "agent"))

    assert [e.operation for e in timeline] == ["created", "modified"]
    assert timeline[0].when == "2026-05-01 00:00 UTC"
    assert timeline[0].author == "Tom (expert)"
    assert timeline[0].diff is None
    assert timeline[1].diff is not None
    assert "-Prod access: ask in #sre on Slack" in timeline[1].diff
    assert "+Prod access: file a Jira ticket" in timeline[1].diff
    assert timeline[1].author == "Maya (expert)"


def test_version_without_session_actor_is_attributed_by_resolver_default():
    timeline = build_timeline([version(1, "created", "x\n")], lambda sid: "agent" if sid is None else "?")

    assert timeline[0].author == "agent"


def test_deleted_version_has_no_content_and_diff_shows_removal():
    versions = [version(1, "created", "old fact\n"), version(2, "deleted", None)]

    timeline = build_timeline(versions, lambda sid: "agent")

    assert timeline[1].operation == "deleted"
    assert timeline[1].diff is not None
    assert "-old fact" in timeline[1].diff
