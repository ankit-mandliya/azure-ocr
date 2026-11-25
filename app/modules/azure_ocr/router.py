import logging
from datetime import datetime, timezone
from uuid import uuid4

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from pydantic import ValidationError

from app.api.deps import get_storage
from app.core.config import settings
from app.core.exceptions import StorageError
from app.modules.azure_ocr.exceptions import (
    AzureOCRConfigurationError,
    AzureOCRServiceError,
)
from app.modules.azure_ocr.schemas import ReviewedAzureContact
from app.modules.azure_ocr.service import AzureOCRService
from app.storage.base import ContactStorage

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/azure-ocr", tags=["Azure OCR"])

ALLOWED_TYPES = {"image/jpeg", "image/jpg", "image/png"}


@router.get("/status")
def azure_status():
    configured = bool(
        settings.azure_document_intelligence_endpoint
        and settings.azure_document_intelligence_key
    )
    return {
        "configured": configured,
        "provider": "azure-document-intelligence",
        "model": "prebuilt-businessCard",
    }


@router.post("/extract")
async def extract_business_card(file: UploadFile = File(...)):
    if file.content_type not in ALLOWED_TYPES:
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail="Unsupported image format. Only JPG and PNG images are accepted.",
        )

    max_bytes = settings.max_upload_mb * 1024 * 1024
    file_bytes = await file.read(max_bytes + 1)
    if len(file_bytes) > max_bytes:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"Uploaded file exceeds limit of {settings.max_upload_mb} MB.",
        )
    if not file_bytes:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Uploaded file is empty.")

    try:
        return AzureOCRService().extract(file_bytes)
    except AzureOCRConfigurationError as exc:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(exc))
    except AzureOCRServiceError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc))
    except Exception:
        logger.exception("Unexpected Azure OCR extraction failure")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while processing the business card.",
        )


@router.post("/save-contact", status_code=status.HTTP_201_CREATED)
def save_reviewed_contact(
    payload: ReviewedAzureContact,
    storage: ContactStorage = Depends(get_storage),
):
    contact = {
        **payload.model_dump(mode="json"),
        "id": str(uuid4()),
        "created_at": datetime.now(timezone.utc).isoformat(),
        "needs_review": False,
        "overall_confidence": None,
        "warnings": [],
        "raw_text": [],
    }
    try:
        return storage.create(contact)
    except (ValidationError, StorageError) as exc:
        logger.warning("Azure OCR contact save failed: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error saving extracted contact.",
        )
