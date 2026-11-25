import pytest
from app.core.exceptions import StorageError
from app.storage.json_storage import JsonContactStorage


def test_json_storage_crud(tmp_path):
    storage_file = tmp_path / "test_contacts.json"
    storage = JsonContactStorage(storage_file)

    # Initially empty
    assert storage.list_all() == []

    # Create
    item = {"id": "c1", "first_name": "Alice", "company_name": "ACME"}
    created = storage.create(item)
    assert created["id"] == "c1"

    # Read back
    fetched = storage.get_by_id("c1")
    assert fetched is not None
    assert fetched["first_name"] == "Alice"

    # List all
    all_items = storage.list_all()
    assert len(all_items) == 1
    assert all_items[0]["id"] == "c1"

    # Update
    updated = storage.update("c1", {"job_title": "Lead Architect"})
    assert updated is not None
    assert updated["job_title"] == "Lead Architect"
    assert updated["first_name"] == "Alice"

    # Non-existent
    assert storage.get_by_id("c999") is None
    assert storage.update("c999", {"first_name": "Bob"}) is None


def test_corrupted_json_storage(tmp_path):
    storage_file = tmp_path / "corrupt_contacts.json"
    storage_file.write_text("invalid json content {{{", encoding="utf-8")

    storage = JsonContactStorage(storage_file)
    with pytest.raises(StorageError):
        storage.list_all()

