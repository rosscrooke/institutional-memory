from datetime import datetime, timezone
from types import SimpleNamespace as NS

from dashboard.core import build_timeline, load_seed, seed_store


def test_load_seed_maps_files_to_store_paths(tmp_path):
    (tmp_path / "policies").mkdir()
    (tmp_path / "policies" / "prod-access-policy.md").write_text("# Prod access\n")
    (tmp_path / "README.txt").write_text("ignored: not markdown")

    assert load_seed(tmp_path) == {"/policies/prod-access-policy.md": "# Prod access\n"}


def test_seeds_every_file_into_an_empty_store():
    created = {}
    seed = {"/a.md": "A", "/b/c.md": "C"}

    written = seed_store(existing_paths=[], seed=seed, create=lambda p, c: created.__setitem__(p, c))

    assert created == seed
    assert written == ["/a.md", "/b/c.md"]


def test_never_touches_a_store_the_team_has_already_written_to():
    created = []

    written = seed_store(existing_paths=["/x.md"], seed={"/a.md": "A"}, create=lambda p, c: created.append(p))

    assert created == written == []


def test_seeded_versions_are_attributed_to_initial_knowledge():
    seeded = NS(
        created_at=datetime(2026, 1, 1, tzinfo=timezone.utc),
        operation="created",
        content="x\n",
        created_by=NS(type="api_actor", api_key_id="apikey_1"),
    )

    timeline = build_timeline([seeded], lambda sid: "agent")

    assert timeline[0].author == "initial knowledge (seed)"
