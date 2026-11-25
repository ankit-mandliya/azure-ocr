import os
from functools import lru_cache
from typing import Any
import cv2
import numpy as np

# Keep your Windows Paddle 3.x PIR workaround
os.environ["PADDLE_PDX_ENABLE_MKLDNN_BYDEFAULT"] = "0"
os.environ["FLAGS_use_mkldnn"] = "0"
os.environ["FLAGS_enable_pir_api"] = "0"

from app.core.exceptions import OCRError

PROFILE_CONFIG: dict[str, dict[str, str]] = {
    "latin": {"lang": "en"},
    "devanagari": {"lang": "hi"},
    "arabic": {"lang": "ur"},
    "tamil": {"lang": "ta"},
    "telugu": {"lang": "te"},
}

PROFILE_ALIASES: dict[str, str] = {
    "english": "latin", "en": "latin",
    "hindi": "devanagari", "hi": "devanagari", "marathi": "devanagari", "mr": "devanagari",
    "urdu": "arabic", "ur": "arabic", "arabic": "arabic", "ar": "arabic",
    "tamil": "tamil", "ta": "tamil",
    "telugu": "telugu", "te": "telugu",
}


def resolve_profile(profile_name: str) -> str:
    cleaned = (profile_name or "latin").lower().strip()
    return PROFILE_ALIASES.get(cleaned, cleaned)


def _downscale_image(image_array: np.ndarray, max_side: int = 1280) -> np.ndarray:
    """Resize large images before OCR to cut detection time dramatically."""
    h, w = image_array.shape[:2]
    if max(h, w) <= max_side:
        return image_array
    scale = max_side / max(h, w)
    new_w, new_h = int(w * scale), int(h * scale)
    return cv2.resize(image_array, (new_w, new_h), interpolation=cv2.INTER_AREA)


@lru_cache(maxsize=5)
def get_ocr_engine(profile: str, device: str = "cpu") -> Any:
    canonical_profile = resolve_profile(profile)

    if canonical_profile not in PROFILE_CONFIG:
        supported = "latin (english), devanagari (hindi/marathi), arabic (urdu), tamil, telugu"
        raise OCRError(f"Unsupported OCR profile '{profile}'. Supported profiles: {supported}")

    try:
        from paddleocr import PaddleOCR
    except ImportError as exc:
        raise OCRError("PaddleOCR is not installed.") from exc

    config = PROFILE_CONFIG[canonical_profile]

    # Use mobile models and disable extra classifiers for 3x-5x faster inference
    ocr_kwargs: dict[str, Any] = {
        "lang": config["lang"],
        "device": device,
        #ocr_version": "PP-OCRv4",                # Mobile v4 is much faster than v5 server
        "use_doc_orientation_classify": False,    # Disable full-page rotation model
        "use_doc_unwarping": False,               # Disable distortion correction model
        "use_textline_orientation": False,        # Disable per-line 180-deg classifier
        "text_det_limit_side_len": 960,           # Cap internal detector resolution
        "text_recognition_batch_size": 16,        # Process 16 text boxes in parallel
    }

    if device.lower() == "cpu":
        ocr_kwargs["enable_mkldnn"] = False
        ocr_kwargs["cpu_threads"] = min(8, os.cpu_count() or 4)

    return PaddleOCR(**ocr_kwargs)


def run_ocr(
    image_array: np.ndarray,
    profile: str = "latin",
    device: str = "cpu",
) -> list[dict]:
    canonical_profile = resolve_profile(profile)
    engine = get_ocr_engine(canonical_profile, device)

    # Downscale oversized inputs before passing to PaddleX
    optimized_img = _downscale_image(image_array, max_side=1280)

    if hasattr(engine, "predict"):
        results = engine.predict(optimized_img)
    elif callable(engine):
        results = engine(optimized_img)
    elif hasattr(engine, "ocr"):
        results = engine.ocr(optimized_img)
    else:
        raise OCRError("Unable to find callable prediction method on OCR engine")

    lines: list[dict] = []
    if not results:
        return lines

    for result in results:
        if not result:
            continue

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

    return lines
