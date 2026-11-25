from typing import Any, Protocol


class ContactStorage(Protocol):
    """Storage contract for persisting and retrieving contacts.

    Decouples business logic from physical storage (JSON file now, SQLAlchemy MSSQL later).
    """

    def create(self, contact: dict[str, Any]) -> dict[str, Any]:
        """Persist a new contact record."""
        ...

    def get_by_id(self, contact_id: str) -> dict[str, Any] | None:
        """Retrieve a contact by its unique ID."""
        ...

    def update(self, contact_id: str, updates: dict[str, Any]) -> dict[str, Any] | None:
        """Update fields of an existing contact."""
        ...

    def delete(self, contact_id: str) -> bool:
        """Delete a contact, returning whether it existed."""
        ...

    def list_all(self) -> list[dict[str, Any]]:
        """Return all stored contacts."""
        ...

