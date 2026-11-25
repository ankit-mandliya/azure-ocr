import pytest
from app.storage.sql_storage import SqlContactStorage


@pytest.fixture
def sql_storage():
    """In-memory SQLite storage fixture for testing SQL persistence without external dependencies."""
    return SqlContactStorage("sqlite:///:memory:")


def test_sql_storage_crud(sql_storage):
    # Verify initial empty state
    assert sql_storage.list_all() == []

    # Create contact
    contact_data = {
        "id": "sql-101",
        "first_name": "Vikram",
        "last_name": "Malhotra",
        "email": "vikram@example.com",
        "contact_number": "+91 99887 76655",
        "company_name": "Tech Corp",
        "address": "MG Road, Pune",
        "job_title": "Principal Architect",
        "website": "https://techcorp.example.com",
        "overall_confidence": 0.96,
        "needs_review": False,
    }
    created = sql_storage.create(contact_data)
    assert created["id"] == "sql-101"
    assert created["first_name"] == "Vikram"
    assert created["overall_confidence"] == 0.96

    # Get by ID
    fetched = sql_storage.get_by_id("sql-101")
    assert fetched is not None
    assert fetched["first_name"] == "Vikram"
    assert fetched["email"] == "vikram@example.com"

    # List all
    all_contacts = sql_storage.list_all()
    assert len(all_contacts) == 1
    assert all_contacts[0]["id"] == "sql-101"

    # Update contact
    updated = sql_storage.update("sql-101", {"job_title": "VP of Engineering", "needs_review": True})
    assert updated is not None
    assert updated["job_title"] == "VP of Engineering"
    assert updated["needs_review"] is True

    # Non-existent ID handling
    assert sql_storage.get_by_id("sql-999") is None
    assert sql_storage.update("sql-999", {"first_name": "Ghost"}) is None

