from dashboard.core import StoreRegistry


def test_creates_user_store_once_and_reuses_it_across_instances(tmp_path):
    created = []

    def create_store(name: str) -> str:
        created.append(name)
        return f"memstore_{len(created)}"

    path = tmp_path / "users.json"
    first = StoreRegistry(path, create_store).user_store("Alice")
    again = StoreRegistry(path, create_store).user_store("alice ")

    assert first == "memstore_1"
    assert again == "memstore_1"
    assert len(created) == 1


def test_different_users_get_different_stores(tmp_path):
    ids = iter(["memstore_a", "memstore_b"])
    reg = StoreRegistry(tmp_path / "users.json", lambda name: next(ids))

    assert reg.user_store("Alice") != reg.user_store("Bob")
