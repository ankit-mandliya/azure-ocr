import argparse
import json
import logging
import sys
from pathlib import Path

# Add project root to path for standalone execution
project_root = Path(__file__).resolve().parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from app.core.config import settings
from app.storage.sql_storage import SqlContactStorage

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("migration")


def migrate_json_to_sql(json_file_path: Path, database_url: str) -> None:
    """Migrate stored contact records from a JSON file to a target SQL database."""
    if not json_file_path.exists():
        logger.error("JSON file not found at: %s", json_file_path)
        sys.exit(1)

    logger.info("Connecting to target SQL database: %s", database_url)
    storage = SqlContactStorage(database_url)

    logger.info("Reading JSON contacts from: %s", json_file_path)
    try:
        content = json_file_path.read_text(encoding="utf-8")
        contacts = json.loads(content or "[]")
    except Exception as exc:
        logger.error("Failed to parse JSON file: %s", exc)
        sys.exit(1)

    total = len(contacts)
    logger.info("Found %d contact(s) to migrate", total)

    migrated = 0
    skipped = 0

    for item in contacts:
        contact_id = item.get("id")
        if not contact_id:
            logger.warning("Skipping entry without ID: %s", item)
            continue

        existing = storage.get_by_id(contact_id)
        if existing:
            logger.info("Contact '%s' already exists in SQL database. Skipping.", contact_id)
            skipped += 1
            continue

        try:
            storage.create(item)
            migrated += 1
        except Exception as exc:
            logger.error("Failed to migrate contact '%s': %s", contact_id, exc)

    logger.info("Migration complete: %d migrated, %d skipped, %d total.", migrated, skipped, total)


def main():
    parser = argparse.ArgumentParser(description="Migrate ContactHub contacts from JSON to SQL database.")
    parser.add_argument(
        "--json-path",
        type=Path,
        default=settings.json_path,
        help="Path to contacts.json source file",
    )
    parser.add_argument(
        "--db-url",
        type=str,
        default=settings.database_url,
        help="SQLAlchemy database URL (e.g., mssql+pyodbc://... or sqlite:///data/contacts.db)",
    )

    args = parser.parse_args()

    if not args.db_url:
        logger.error("Database URL must be provided via --db-url argument or DATABASE_URL env variable.")
        sys.exit(1)

    migrate_json_to_sql(args.json_path, args.db_url)


if __name__ == "__main__":
    main()

