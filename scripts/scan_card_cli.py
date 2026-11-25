import os

# Disable MKLDNN / oneDNN on CPU
os.environ["PADDLE_PDX_ENABLE_MKLDNN_BYDEFAULT"] = "0"
os.environ["FLAGS_use_mkldnn"] = "0"
os.environ["FLAGS_enable_pir_api"] = "0"

import argparse
import json
import logging
import sys
import time
from pathlib import Path

# Add project root to path for standalone execution
project_root = Path(__file__).resolve().parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from app.core.config import settings
from app.services.contact_service import build_ocr_contact
from app.services.extraction_service import extract_contact_fields
from app.services.image_service import load_and_validate_image, preprocess_image
from app.services.ocr_service import PROFILE_CONFIG, run_ocr

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("scan_cli")


def scan_file(image_path: Path, profile: str, device: str) -> None:
    """Run full image validation, OCR, and extraction on a local file."""
    if not image_path.exists():
        logger.error("Image file does not exist: %s", image_path)
        sys.exit(1)

    logger.info("Reading image file: %s", image_path)
    file_bytes = image_path.read_bytes()

    start_time = time.perf_counter()

    # Step 1: Image loading & validation
    logger.info("Validating and preprocessing image...")
    image_array = load_and_validate_image(file_bytes)
    if settings.ocr_enable_preprocessing:
        image_array = preprocess_image(image_array)

    # Step 2: OCR text detection and recognition
    logger.info("Running PaddleOCR (Profile: %s, Device: %s)...", profile, device)
    ocr_lines = run_ocr(image_array, profile=profile, device=device)
    logger.info("Detected %d text lines.", len(ocr_lines))

    # Step 3: Semantic extraction
    logger.info("Extracting contact fields...")
    fields = extract_contact_fields(ocr_lines)

    # Step 4: Construct structured contact
    contact = build_ocr_contact(ocr_lines, fields)

    elapsed = time.perf_counter() - start_time
    logger.info("Processing completed in %.2f seconds.", elapsed)

    print("\n" + "=" * 50)
    print("EXTRACTED CONTACT RESULT")
    print("=" * 50)
    print(json.dumps(contact.model_dump(mode="json"), indent=2, ensure_ascii=False))


def main():
    parser = argparse.ArgumentParser(description="Test visiting card OCR & extraction via CLI.")
    parser.add_argument("image_path", type=Path, help="Path to visiting card image")
    parser.add_argument(
        "--profile",
        type=str,
        default=settings.ocr_default_profile,
        choices=list(PROFILE_CONFIG.keys()) + ["english", "hindi"],
        help="Language profile to use for OCR",
    )
    parser.add_argument(
        "--device",
        type=str,
        default=settings.ocr_device,
        choices=["cpu", "gpu"],
        help="Device backend for PaddleOCR",
    )

    args = parser.parse_args()
    scan_file(args.image_path, args.profile, args.device)


if __name__ == "__main__":
    main()
