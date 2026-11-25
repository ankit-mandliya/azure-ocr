from datetime import datetime, timezone
from typing import Optional
from sqlalchemy import Boolean, DateTime, Float, String, Unicode, UnicodeText
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    """Base declarative class for SQLAlchemy models."""
    pass


class ContactModel(Base):
    """SQLAlchemy model for persisting contact details with full multilingual NVARCHAR support."""

    __tablename__ = "contacts"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    first_name: Mapped[Optional[str]] = mapped_column(Unicode(100), nullable=True)
    last_name: Mapped[Optional[str]] = mapped_column(Unicode(100), nullable=True)
    email: Mapped[Optional[str]] = mapped_column(Unicode(320), nullable=True, index=True)
    contact_number: Mapped[Optional[str]] = mapped_column(Unicode(30), nullable=True, index=True)
    company_name: Mapped[Optional[str]] = mapped_column(Unicode(200), nullable=True)
    address: Mapped[Optional[str]] = mapped_column(Unicode(500), nullable=True)
    job_title: Mapped[Optional[str]] = mapped_column(Unicode(150), nullable=True)
    website: Mapped[Optional[str]] = mapped_column(Unicode(200), nullable=True)
    overall_confidence: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    needs_review: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
    )

    def to_dict(self) -> dict:
        """Convert model instance to dictionary representation."""
        return {
            "id": self.id,
            "first_name": self.first_name,
            "last_name": self.last_name,
            "email": self.email,
            "contact_number": self.contact_number,
            "company_name": self.company_name,
            "address": self.address,
            "job_title": self.job_title,
            "website": self.website,
            "overall_confidence": self.overall_confidence,
            "needs_review": self.needs_review,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }

