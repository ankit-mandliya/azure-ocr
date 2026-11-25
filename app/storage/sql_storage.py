from datetime import datetime
from typing import Any
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session, sessionmaker

from app.core.exceptions import StorageError
from app.models.contact import Base, ContactModel


class SqlContactStorage:
    """SQL database implementation of ContactStorage (MSSQL, PostgreSQL, SQLite).

    Thread-safe and multi-worker safe through connection pooling and ACID transactions.
    """

    def __init__(self, database_url: str):
        self.engine = create_engine(database_url, pool_pre_ping=True)
        self.session_factory = sessionmaker(bind=self.engine, expire_on_commit=False)
        # Create tables automatically if they do not exist
        Base.metadata.create_all(self.engine)

    def _get_session(self) -> Session:
        return self.session_factory()

    def create(self, contact: dict[str, Any]) -> dict[str, Any]:
        with self._get_session() as session:
            try:
                # Parse created_at if provided as string
                created_at = contact.get("created_at")
                if isinstance(created_at, str):
                    created_at = datetime.fromisoformat(created_at)

                model = ContactModel(
                    id=contact["id"],
                    first_name=contact.get("first_name"),
                    last_name=contact.get("last_name"),
                    email=contact.get("email"),
                    contact_number=contact.get("contact_number"),
                    company_name=contact.get("company_name"),
                    address=contact.get("address"),
                    job_title=contact.get("job_title"),
                    website=contact.get("website"),
                    overall_confidence=contact.get("overall_confidence"),
                    needs_review=contact.get("needs_review", True),
                    created_at=created_at,
                )
                session.add(model)
                session.commit()
                return model.to_dict()
            except Exception as exc:
                session.rollback()
                raise StorageError(f"Failed to persist contact to SQL database: {exc}") from exc

    def get_by_id(self, contact_id: str) -> dict[str, Any] | None:
        with self._get_session() as session:
            stmt = select(ContactModel).where(ContactModel.id == contact_id)
            model = session.scalar(stmt)
            return model.to_dict() if model else None

    def update(self, contact_id: str, updates: dict[str, Any]) -> dict[str, Any] | None:
        with self._get_session() as session:
            try:
                stmt = select(ContactModel).where(ContactModel.id == contact_id)
                model = session.scalar(stmt)
                if not model:
                    return None

                for key, value in updates.items():
                    if hasattr(model, key) and key != "id":
                        setattr(model, key, value)

                session.commit()
                return model.to_dict()
            except Exception as exc:
                session.rollback()
                raise StorageError(f"Failed to update contact in SQL database: {exc}") from exc

    def list_all(self) -> list[dict[str, Any]]:
        with self._get_session() as session:
            stmt = select(ContactModel).order_by(ContactModel.created_at.desc())
            models = session.scalars(stmt).all()
            return [model.to_dict() for model in models]

    def delete(self, contact_id: str) -> bool:
        with self._get_session() as session:
            try:
                stmt = select(ContactModel).where(ContactModel.id == contact_id)
                model = session.scalar(stmt)
                if not model:
                    return False
                session.delete(model)
                session.commit()
                return True
            except Exception as exc:
                session.rollback()
                raise StorageError(f"Failed to delete contact from SQL database: {exc}") from exc

