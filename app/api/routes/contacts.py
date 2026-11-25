import logging
from datetime import datetime, timezone
from uuid import uuid4
from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from pydantic import ValidationError

from app.api.deps import get_storage
from app.core.config import settings
from app.core.exceptions import ImageValidationError, OCRError, StorageError
from app.schemas.contact import ContactCreate, ContactPreview, ContactResponse, ContactUpdate
from app.services.contact_service import build_ocr_contact
from app.services.extraction_service import extract_contact_fields
from app.services.image_service import load_and_validate_image, preprocess_image
from app.services.ocr_service import run_ocr
from app.storage.base import ContactStorage

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/contacts", tags=["Contacts"])

# Modern Starlette 422 status compatibility
HTTP_422 = getattr(status, "HTTP_422_UNPROCESSABLE_CONTENT", 422)

ALLOWED_CONTENT_TYPES = {
    "image/jpeg",
    "image/png",
    "image/webp",
}


def _sanitize_response(payload: dict):
    """Hide OCR debug data in production responses."""
    if settings.app_env.lower() == "development":
        return payload

    return {
        key: value
        for key, value in payload.items()
        if key not in {"raw_text", "warnings", "overall_confidence"}
    }


@router.post("/scan", status_code=status.HTTP_201_CREATED, response_model=ContactResponse)
async def scan_visiting_card(
    file: UploadFile = File(..., description="Visiting card image (JPEG, PNG, or WEBP)"),
    language_profile: str = Form(
        default=settings.ocr_default_profile,
        description="OCR profile or language alias: 'latin' (or 'english'), 'devanagari' (or 'hindi'), 'arabic', 'tamil', 'telugu'",
    ),
    storage: ContactStorage = Depends(get_storage),
):
    """Upload visiting card image, run OCR, extract contact fields, and persist the record."""
    if file.content_type not in ALLOWED_CONTENT_TYPES:
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail=f"Unsupported media type '{file.content_type}'. Only JPEG, PNG, and WEBP are accepted.",
        )

    max_bytes = settings.max_upload_mb * 1024 * 1024
    file_bytes = await file.read(max_bytes + 1)

    if len(file_bytes) > max_bytes:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"Uploaded file exceeds limit of {settings.max_upload_mb} MB.",
        )

    if not file_bytes:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Uploaded file is empty.",
        )

    try:
        image_array = load_and_validate_image(file_bytes)
        if settings.ocr_enable_preprocessing:
            image_array = preprocess_image(image_array)

        ocr_lines = run_ocr(
            image_array,
            profile=language_profile,
            device=settings.ocr_device,
        )

        if not ocr_lines:
            raise HTTPException(
                status_code=HTTP_422,
                detail="No readable text was detected in the image.",
            )

        fields = extract_contact_fields(ocr_lines)
        contact = build_ocr_contact(ocr_lines, fields)

        saved = storage.create(contact.model_dump(mode="json"))
        return _sanitize_response(saved)

    except HTTPException:
        raise
    except ImageValidationError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))
    except OCRError as exc:
        raise HTTPException(status_code=HTTP_422, detail=str(exc))
    except ValidationError as exc:
        logger.warning("Extracted contact validation failure: %s", exc)
        raise HTTPException(
            status_code=HTTP_422,
            detail="Extracted contact data did not pass schema validation.",
        )
    except StorageError as exc:
        logger.error("Storage error during scan persistence: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error saving extracted contact.",
        )
    except Exception as exc:
        logger.exception("Unexpected error processing visiting card: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while processing the visiting card.",
        )


@router.post("/preview", response_model=ContactPreview)
async def preview_visiting_card(
    file: UploadFile = File(..., description="Visiting card image (JPEG, PNG, or WEBP)"),
    language_profile: str = Form(default=settings.ocr_default_profile),
):
    """Extract contact fields without saving; the user reviews them before creation."""
    if file.content_type not in ALLOWED_CONTENT_TYPES:
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail=f"Unsupported media type '{file.content_type}'. Only JPEG, PNG, and WEBP are accepted.",
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
        image_array = load_and_validate_image(file_bytes)
        if settings.ocr_enable_preprocessing:
            image_array = preprocess_image(image_array)
        ocr_lines = run_ocr(image_array, profile=language_profile, device=settings.ocr_device)
        if not ocr_lines:
            raise HTTPException(
                status_code=HTTP_422,
                detail="No readable text was detected in the image.",
            )

        fields = extract_contact_fields(ocr_lines)
        warnings = fields.pop("warnings", [])
        scores = [float(line.get("confidence", 0.0)) for line in ocr_lines if "confidence" in line]
        confidence = sum(scores) / len(scores) if scores else 0.0
        present_count = sum(
            fields.get(name) is not None
            for name in ("first_name", "email", "contact_number", "company_name")
        )
        preview = ContactPreview(
            **fields,
            overall_confidence=round(confidence, 4),
            needs_review=confidence < 0.85 or present_count < 2 or bool(warnings),
            warnings=warnings,
        )
        return _sanitize_response(preview.model_dump(mode="json"))
    except HTTPException:
        raise
    except ImageValidationError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))
    except OCRError as exc:
        raise HTTPException(status_code=HTTP_422, detail=str(exc))
    except ValidationError as exc:
        logger.warning("Extracted contact validation failure: %s", exc)
        raise HTTPException(status_code=HTTP_422, detail="Extracted contact data did not pass schema validation.")


@router.post("", status_code=status.HTTP_201_CREATED, response_model=ContactResponse)
def create_contact(
    payload: ContactCreate,
    storage: ContactStorage = Depends(get_storage),
):
    """Create a manually entered or user-reviewed contact."""
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
        return _sanitize_response(storage.create(contact))
    except StorageError as exc:
        logger.error("Storage error creating contact: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error saving contact.",
        )


@router.get("", response_model=list[ContactResponse])
def list_contacts(storage: ContactStorage = Depends(get_storage)):
    """Retrieve all saved contacts."""
    return [_sanitize_response(contact) for contact in storage.list_all()]


@router.get("/{contact_id}", response_model=ContactResponse)
def get_contact(contact_id: str, storage: ContactStorage = Depends(get_storage)):
    """Retrieve a single contact by ID."""
    contact = storage.get_by_id(contact_id)
    if not contact:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Contact with ID '{contact_id}' not found.",
        )
    return _sanitize_response(contact)


@router.put("/{contact_id}", response_model=ContactResponse)
def update_contact(
    contact_id: str,
    payload: ContactUpdate,
    storage: ContactStorage = Depends(get_storage),
):
    """Update or correct fields of an existing contact."""
    updates = payload.model_dump(exclude_unset=True, mode="json")
    if not updates:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No fields provided to update.",
        )

    updated = storage.update(contact_id, updates)
    if not updated:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Contact with ID '{contact_id}' not found.",
        )
    return _sanitize_response(updated)


@router.delete("/{contact_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_contact(contact_id: str, storage: ContactStorage = Depends(get_storage)):
    """Delete a saved contact."""
    try:
        deleted = storage.delete(contact_id)
    except StorageError as exc:
        logger.error("Storage error deleting contact: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error deleting contact.",
        )
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Contact with ID '{contact_id}' not found.",
        )
