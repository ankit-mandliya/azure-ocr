import json
from pathlib import Path
from threading import Lock
from typing import Any

from app.core.exceptions import StorageError


class JsonContactStorage:
    """Thread-safe file-backed storage implementation using atomic JSON writes.

    Suitable for local development and single-process instances.
    """

    def __init__(self, file_path: str | Path):
        self.file_path = Path(file_path)
        self.lock = Lock()
        self.file_path.parent.mkdir(parents=True, exist_ok=True)

        if not self.file_path.exists():
            self.file_path.write_text("[]", encoding="utf-8")

    def _read(self) -> list[dict[str, Any]]:
        try:
            content = self.file_path.read_text(encoding="utf-8").strip()
            return json.loads(content or "[]")
        except (json.JSONDecodeError, OSError) as exc:
            raise StorageError(f"Contact JSON storage is corrupted or unreadable: {exc}") from exc

    def _write(self, contacts: list[dict[str, Any]]) -> None:
        temporary_path = self.file_path.with_suffix(".tmp")
        try:
            temporary_path.write_text(
                json.dumps(contacts, ensure_ascii=False, indent=2),
                encoding="utf-8",
            )
            temporary_path.replace(self.file_path)
        except OSError as exc:
            raise StorageError(f"Failed to persist contact to JSON: {exc}") from exc

    def create(self, contact: dict[str, Any]) -> dict[str, Any]:
        with self.lock:
            contacts = self._read()
            contacts.append(contact)
            self._write(contacts)
        return contact

    def get_by_id(self, contact_id: str) -> dict[str, Any] | None:
        with self.lock:
            contacts = self._read()
            return next((item for item in contacts if item.get("id") == contact_id), None)

    def update(self, contact_id: str, updates: dict[str, Any]) -> dict[str, Any] | None:
        with self.lock:
            contacts = self._read()
            for index, item in enumerate(contacts):
                if item.get("id") == contact_id:
                    # Update specified fields
                    updated_item = {**item, **updates}
                    contacts[index] = updated_item
                    self._write(contacts)
                    return updated_item
            return None

    def list_all(self) -> list[dict[str, Any]]:
        with self.lock:
            return self._read()

    def delete(self, contact_id: str) -> bool:
        with self.lock:
            contacts = self._read()
            remaining = [item for item in contacts if item.get("id") != contact_id]
            if len(remaining) == len(contacts):
                return False
            self._write(remaining)
            return True

