from datetime import datetime, timezone
from typing import Optional
from pydantic import BaseModel, ConfigDict, EmailStr, Field


class ContactFields(BaseModel):
    """Core contact fields shared across create, read, and OCR models."""
    model_config = ConfigDict(str_strip_whitespace=True)

    first_name: Optional[str] = Field(default=None, max_length=100)
    last_name: Optional[str] = Field(default=None, max_length=100)
    email: Optional[EmailStr] = None
    contact_number: Optional[str] = Field(default=None, max_length=30)
    company_name: Optional[str] = Field(default=None, max_length=200)
    address: Optional[str] = Field(default=None, max_length=500)
    job_title: Optional[str] = Field(default=None, max_length=150)
    website: Optional[str] = Field(default=None, max_length=200)


class OCRTextLine(BaseModel):
    """A single recognized line of text with bounding box coordinates and score."""
    text: str
    confidence: float = Field(ge=0.0, le=1.0)
    box: list[list[float]] = Field(default_factory=list)


class OCRContactResult(ContactFields):
    """Full result of scanning a visiting card, including OCR audit metadata."""
    id: str
    raw_text: list[OCRTextLine] = Field(default_factory=list)
    overall_confidence: float = Field(ge=0.0, le=1.0)
    needs_review: bool = True
    warnings: list[str] = Field(default_factory=list)
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc)
    )


class ContactCreate(ContactFields):
    """Payload for manually creating a contact."""
    pass


class ContactPreview(ContactFields):
    """Unpersisted OCR extraction shown to the user for review."""
    overall_confidence: Optional[float] = Field(default=None, ge=0.0, le=1.0)
    needs_review: bool = True
    warnings: list[str] = Field(default_factory=list)


class ContactUpdate(BaseModel):
    """Payload for updating/correcting contact details."""
    model_config = ConfigDict(str_strip_whitespace=True)

    first_name: Optional[str] = Field(default=None, max_length=100)
    last_name: Optional[str] = Field(default=None, max_length=100)
    email: Optional[EmailStr] = None
    contact_number: Optional[str] = Field(default=None, max_length=30)
    company_name: Optional[str] = Field(default=None, max_length=200)
    address: Optional[str] = Field(default=None, max_length=500)
    job_title: Optional[str] = Field(default=None, max_length=150)
    website: Optional[str] = Field(default=None, max_length=200)
    needs_review: Optional[bool] = None


class ContactResponse(ContactFields):
    """API response model for a saved contact."""
    id: str
    raw_text: list[OCRTextLine] = Field(default_factory=list)
    overall_confidence: Optional[float] = None
    needs_review: Optional[bool] = None
    warnings: list[str] = Field(default_factory=list)
    created_at: datetime
