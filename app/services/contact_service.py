from datetime import datetime, timezone
from typing import Any
from uuid import uuid4

from app.schemas.contact import OCRContactResult, OCRTextLine


def build_ocr_contact(
    ocr_lines: list[dict[str, Any]],
    fields: dict[str, Any],
) -> OCRContactResult:
    """Build a validated OCRContactResult model from extracted fields and raw OCR lines."""
    scores = [
        float(line.get("confidence", 0.0))
        for line in ocr_lines
        if "confidence" in line
    ]
    overall_confidence = (sum(scores) / len(scores)) if scores else 0.0

    warnings = list(fields.pop("warnings", []))

    # Evaluate completeness criteria for review flag
    important_values = [
        fields.get("first_name"),
        fields.get("email"),
        fields.get("contact_number"),
        fields.get("company_name"),
    ]
    present_count = sum(val is not None for val in important_values)

    needs_review = (
        overall_confidence < 0.85
        or present_count < 2
        or bool(warnings)
    )

    raw_text_lines = [
        OCRTextLine(
            text=str(line.get("text", "")),
            confidence=float(line.get("confidence", 0.0)),
            box=line.get("box", []),
        )
        for line in ocr_lines
        if line.get("text")
    ]

    return OCRContactResult(
        id=str(uuid4()),
        raw_text=raw_text_lines,
        overall_confidence=round(overall_confidence, 4),
        needs_review=needs_review,
        warnings=warnings,
        created_at=datetime.now(timezone.utc),
        **fields,
    )

