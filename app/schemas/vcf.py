from typing import Optional

from pydantic import BaseModel, Field


class VCFContact(BaseModel):
    full_name: Optional[str] = None
    company: Optional[str] = None
    job_title: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    website: Optional[str] = None
    address: Optional[str] = None
    notes: Optional[str] = None


class VCFPreviewResponse(BaseModel):
    filename: str
    total_contacts: int
    contacts: list[VCFContact] = Field(default_factory=list)
