from typing import Optional

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class ExtractedValue(BaseModel):
    value: Optional[str] = None
    confidence: Optional[float] = Field(default=None, ge=0.0, le=1.0)


class AzureBusinessCard(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    first_name: Optional[str] = Field(default=None, max_length=100)
    last_name: Optional[str] = Field(default=None, max_length=100)
    full_name: Optional[str] = Field(default=None, max_length=200)
    company_name: Optional[str] = Field(default=None, max_length=200)
    department: Optional[str] = Field(default=None, max_length=150)
    job_title: Optional[str] = Field(default=None, max_length=150)
    emails: list[ExtractedValue] = Field(default_factory=list)
    websites: list[ExtractedValue] = Field(default_factory=list)
    mobile_phones: list[ExtractedValue] = Field(default_factory=list)
    work_phones: list[ExtractedValue] = Field(default_factory=list)
    other_phones: list[ExtractedValue] = Field(default_factory=list)
    fax_numbers: list[ExtractedValue] = Field(default_factory=list)
    addresses: list[ExtractedValue] = Field(default_factory=list)


class AzureExtractionMetadata(BaseModel):
    provider: str = "azure-document-intelligence"
    model_id: str = "prebuilt-businessCard"
    timestamp: str
    status: str = "succeeded"


class AzureExtractionResponse(BaseModel):
    success: bool = True
    cards: list[AzureBusinessCard] = Field(default_factory=list)
    metadata: AzureExtractionMetadata
    overall_confidence: Optional[float] = Field(default=None, ge=0.0, le=1.0)


class ReviewedAzureContact(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    first_name: Optional[str] = Field(default=None, max_length=100)
    last_name: Optional[str] = Field(default=None, max_length=100)
    email: Optional[EmailStr] = None
    contact_number: Optional[str] = Field(default=None, max_length=30)
    company_name: Optional[str] = Field(default=None, max_length=200)
    address: Optional[str] = Field(default=None, max_length=500)
    job_title: Optional[str] = Field(default=None, max_length=150)
    website: Optional[str] = Field(default=None, max_length=200)
    department: Optional[str] = Field(default=None, max_length=150)
