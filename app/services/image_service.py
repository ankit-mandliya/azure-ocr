from io import BytesIO
from typing import Any
import numpy as np
from PIL import Image, ImageOps, UnidentifiedImageError

from app.core.exceptions import ImageValidationError

ALLOWED_FORMATS = {"JPEG", "PNG", "WEBP"}


def load_and_validate_image(
    file_bytes: bytes,
    max_pixels: int = 20_000_000,
) -> np.ndarray:
    """Validate image format, dimension, and integrity, returning an RGB numpy array.

    Raises:
        ImageValidationError: If the image is corrupt, unsupported, or exceeds bounds.
    """
    if not file_bytes:
        raise ImageValidationError("Uploaded image is empty")

    try:
        image = Image.open(BytesIO(file_bytes))
        image_format = image.format  # Preserve format before exif_transpose creates a copy
        image = ImageOps.exif_transpose(image)
        image.load()
    except (UnidentifiedImageError, OSError, ValueError) as exc:
        raise ImageValidationError(f"Invalid or corrupt image: {exc}") from exc

    if image_format not in ALLOWED_FORMATS:
        raise ImageValidationError(
            f"Unsupported format '{image_format}'. Allowed: {', '.join(sorted(ALLOWED_FORMATS))}"
        )

    if image.width * image.height > max_pixels:
        raise ImageValidationError(
            f"Image resolution ({image.width}x{image.height}) exceeds safe limit of {max_pixels} pixels"
        )

    # Convert to RGB (normalizes grayscale, RGBA, and palette images)
    image = image.convert("RGB")
    return np.array(image)


def preprocess_image(image_array: np.ndarray) -> np.ndarray:
    """Optional preprocessing hook (contrast normalization, deskew).

    Kept conservative by default to avoid removing fine character strokes or logos.
    """
    return image_array
