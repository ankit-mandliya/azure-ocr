import os
from functools import lru_cache
from typing import Any
import numpy as np

# Disable MKLDNN / oneDNN on CPU to resolve the known Windows PaddlePaddle 3.x PIR regression:
# "NotImplementedError: (Unimplemented) ConvertPirAttribute2RuntimeAttribute not support [pir::ArrayAttribute<pir::DoubleAttribute>]"
os.environ["PADDLE_PDX_ENABLE_MKLDNN_BYDEFAULT"] = "0"
os.environ["FLAGS_use_mkldnn"] = "0"
os.environ["FLAGS_enable_pir_api"] = "0"

from app.core.exceptions import OCRError

# Mapping of canonical profile names to PaddleOCR language codes
PROFILE_CONFIG: dict[str, dict[str, str]] = {
    "latin": {"lang": "en"},
    "devanagari": {"lang": "hi"},
    "arabic": {"lang": "ur"},
    "tamil": {"lang": "ta"},
    "telugu": {"lang": "te"},
}

# User-friendly language aliases mapped to canonical profiles
PROFILE_ALIASES: dict[str, str] = {
    "english": "latin",
    "en": "latin",
    "hindi": "devanagari",
    "hi": "devanagari",
    "marathi": "devanagari",
    "mr": "devanagari",
    "urdu": "arabic",
    "ur": "arabic",
    "arabic": "arabic",
    "ar": "arabic",
    "tamil": "tamil",
    "ta": "tamil",
    "telugu": "telugu",
    "te": "telugu",
}


def resolve_profile(profile_name: str) -> str:
    """Normalize and resolve user input or language names to canonical profile keys."""
    cleaned = (profile_name or "latin").lower().strip()
    return PROFILE_ALIASES.get(cleaned, cleaned)


@lru_cache(maxsize=5)
def get_ocr_engine(profile: str, device: str = "cpu") -> Any:
    """Initialize and cache the PaddleOCR engine for a given profile and device."""
    canonical_profile = resolve_profile(profile)

    if canonical_profile not in PROFILE_CONFIG:
        supported = "latin (english), devanagari (hindi/marathi), arabic (urdu), tamil, telugu"
        raise OCRError(f"Unsupported OCR profile '{profile}'. Supported profiles: {supported}")

    try:
        from paddleocr import PaddleOCR
    except ImportError as exc:
        raise OCRError(
            "PaddleOCR is not installed. Please install dependencies from requirements-ocr.txt: "
            "'pip install -r requirements-ocr.txt'"
        ) from exc

    config = PROFILE_CONFIG[canonical_profile]

    # Explicitly set enable_mkldnn=False on CPU to avoid oneDNN ConvertPirAttribute2RuntimeAttribute bug
    ocr_kwargs: dict[str, Any] = {
        # "ocr_version": "PP-OCRv5",
        "lang": config["lang"],
        "device": device,
        "use_doc_orientation_classify": True,
        "use_doc_unwarping": False,
        "use_textline_orientation": True,
    }

    if device.lower() == "cpu":
        ocr_kwargs["enable_mkldnn"] = False

    return PaddleOCR(**ocr_kwargs)


def run_ocr(
    image_array: np.ndarray,
    profile: str = "latin",
    device: str = "cpu",
) -> list[dict]:
    """Run OCR text detection and recognition on an image array.

    Returns:
        List of dicts: [{"text": str, "confidence": float, "box": list[list[float]]}, ...]
    """
    canonical_profile = resolve_profile(profile)
    engine = get_ocr_engine(canonical_profile, device)

    # PaddleOCR accepts numpy RGB array
    if hasattr(engine, "predict"):
        results = engine.predict(image_array)
    elif callable(engine):
        results = engine(image_array)
    elif hasattr(engine, "ocr"):
        results = engine.ocr(image_array)
    else:
        raise OCRError("Unable to find callable prediction method on OCR engine")

    lines: list[dict] = []
    if not results:
        return lines

    for result in results:
        if not result:
            continue

        # Handle PaddleOCR 3.x structured result / JSON exporter
        data = result.json if hasattr(result, "json") else result
        if callable(data):
            data = data()

        if isinstance(data, dict) and "res" in data:
            data = data["res"]

        if isinstance(data, dict) and "rec_texts" in data:
            texts = data.get("rec_texts", [])
            scores = data.get("rec_scores", [])
            boxes = data.get("rec_polys", data.get("dt_polys", []))

            for index, text in enumerate(texts):
                score = float(scores[index]) if index < len(scores) else 0.0
                raw_box = boxes[index] if index < len(boxes) else []
                box = raw_box.tolist() if hasattr(raw_box, "tolist") else raw_box

                clean_text = str(text).strip()
                if clean_text:
                    lines.append({
                        "text": clean_text,
                        "confidence": max(0.0, min(score, 1.0)),
                        "box": box if isinstance(box, list) else [],
                    })
            continue

        # Handle classic PaddleOCR nested list format: [[[x1, y1], [x2, y2], ...], (text, score)]
        if isinstance(result, (list, tuple)):
            for item in result:
                if isinstance(item, (list, tuple)) and len(item) == 2:
                    raw_box, rec = item
                    if isinstance(rec, (list, tuple)) and len(rec) >= 2:
                        text, score = rec[0], float(rec[1])
                        box = raw_box.tolist() if hasattr(raw_box, "tolist") else list(raw_box)
                        clean_text = str(text).strip()
                        if clean_text:
                            lines.append({
                                "text": clean_text,
                                "confidence": max(0.0, min(score, 1.0)),
                                "box": box,
                            })

    return lines
