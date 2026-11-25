import re
import unicodedata
from typing import Optional

EMAIL_PATTERN = re.compile(
    r"(?i)\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b"
)

URL_PATTERN = re.compile(
    r"(?i)\b(?:https?://)?(?:www\.)?[A-Z0-9.-]+\.[A-Z]{2,}(?:/[^\s]*)?"
)

PHONE_PATTERN = re.compile(
    r"(?<!\w)(?:\+?\d[\d\s().-]{7,}\d)(?!\w)"
)


def normalize_line(value: str) -> str:
    """Normalize unicode, remove zero-width spaces, and collapse redundant whitespace."""
    if not value:
        return ""
    value = unicodedata.normalize("NFKC", value)
    value = value.replace("\u200b", "").replace("\ufeff", "")
    return re.sub(r"\s+", " ", value).strip()


def extract_email(text: str) -> Optional[str]:
    """Extract first valid email address from text."""
    match = EMAIL_PATTERN.search(text)
    return match.group(0).lower() if match else None


def extract_website(text: str) -> Optional[str]:
    """Extract primary website URL from text, ignoring email addresses."""
    # Exclude emails so email domains aren't extracted as standalone websites
    cleaned_text = re.sub(r"<[^>]+>", " ", text)
    text_without_emails = EMAIL_PATTERN.sub("", cleaned_text)
    match = URL_PATTERN.search(text_without_emails)
    if not match:
        return None
    value = match.group(0).rstrip(".,;:/")
    lower_value = value.lower()
    if lower_value.startswith("http://"):
        value = "https://" + value.removeprefix("http://")
    elif lower_value.startswith("www."):
        value = "https://" + value
    elif not lower_value.startswith("https://"):
        value = "https://www." + value
    return value


def extract_phone_candidates(text: str) -> list[str]:
    """Extract plausible telephone numbers (8 to 15 digits)."""
    candidates: list[str] = []
    for match in PHONE_PATTERN.findall(text):
        digits = re.sub(r"\D", "", match)
        if 8 <= len(digits) <= 15:
            cleaned = match.strip(" .,;-")
            if cleaned and cleaned not in candidates:
                candidates.append(cleaned)
    return candidates

