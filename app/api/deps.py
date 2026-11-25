from functools import lru_cache
from app.core.config import settings
from app.storage.base import ContactStorage
from app.storage.json_storage import JsonContactStorage


@lru_cache()
def get_storage() -> ContactStorage:
    """Dependency provider for ContactStorage implementation.

    Automatically uses SqlContactStorage if `database_url` is configured,
    otherwise falls back to JsonContactStorage.
    """
    if settings.database_url:
        from app.storage.sql_storage import SqlContactStorage
        return SqlContactStorage(settings.database_url)

    return JsonContactStorage(settings.json_storage_path)
