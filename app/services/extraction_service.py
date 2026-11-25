import re
from typing import Any
from app.utils.text_utils import (
    extract_email,
    extract_phone_candidates,
    extract_website,
    normalize_line,
)

COMPANY_HINTS = (
    "pvt ltd", "private limited", "limited", "ltd", "llp",
    "inc", "corporation", "corp", "technologies", "technology",
    "solutions", "systems", "industries", "company", "enterprises",
    "services", "group", "labs",
)

COMPANY_WORDS = {
    "engineering",
    "technology",
    "technologies",
    "solutions",
    "systems",
    "consulting",
    "consultants",
    "software",
    "services",
    "industries",
    "group",
    "corporation",
    "corp",
    "private",
    "limited",
    "ltd",
    "pvt",
    "llp",
    "enterprise",
    "enterprises",
    "international",
    "global",
    "manufacturing",
}

ADDRESS_HINTS = (
    "road", "street", "st.", "nagar", "sector", "near",
    "building", "floor", "lane", "avenue", "pin", "postal",
    "block", "plot", "cross", "dist", "opp", "office", "park",
    "tower", "chowk", "city", "state",
)

JOB_TITLE_KEYWORDS = {
    "director", "manager", "engineer", "lead", "architect",
    "founder", "ceo", "cto", "cfo", "coo", "president",
    "consultant", "developer", "officer", "head", "specialist",
    "executive", "analyst", "designer", "administrator", "scientist",
    "sales", "marketing",
}

CORPORATE_SUFFIXES = {
    "ltd", "limited", "inc", "corp", "corporation", "llc", "llp", "gmbh", "pvt",
}


def _is_single_char_logo_token(value: str) -> bool:
    cleaned = normalize_line(value)
    if not cleaned:
        return True
    if len(cleaned) <= 1:
        return True
    if re.fullmatch(r"[^A-Za-z0-9\s]+", cleaned):
        return True
    if len(cleaned.split()) == 1 and len(cleaned) <= 2:
        return True
    return False


def _looks_like_address(value: str) -> bool:
    cleaned = normalize_line(value)
    if not cleaned:
        return False
    lower = cleaned.lower()
    if re.search(r"\d", lower) and len(cleaned.split()) >= 3:
        return True
    if any(hint in lower for hint in ADDRESS_HINTS):
        return True
    return False


def _is_name_candidate(value: str) -> bool:
    cleaned = normalize_line(value)

    if not cleaned or _is_single_char_logo_token(cleaned):
        return False

    parts = cleaned.split()
    if len(parts) < 2 or len(parts) > 4:
        return False

    lower_parts = {part.lower().strip(".,") for part in parts}
    if lower_parts & COMPANY_WORDS:
        return False
    if lower_parts & set(ADDRESS_HINTS):
        return False
    if lower_parts & JOB_TITLE_KEYWORDS:
        return False

    return all(re.match(r"^[A-Z][A-Za-z'.-]*$", part) for part in parts)


def _email_name_hints(email: str | None) -> list[str]:
    if not email:
        return []
    local_part = email.split("@", 1)[0]
    words = [word for word in re.split(r"[^A-Za-z]+", local_part) if word]
    hints: list[str] = []
    if words:
        hints.append(words[0].capitalize())
    if len(words) >= 2:
        hints.append(" ".join(word.capitalize() for word in words))
        hints.extend(word.capitalize() for word in words)
    return hints


def is_job_title(line: str) -> bool:
    """Determine if a text line represents a professional title."""
    lower = line.lower()
    tokens = set(re.findall(r"\b[a-z]+\b", lower))

    if tokens & CORPORATE_SUFFIXES:
        return False

    if tokens & JOB_TITLE_KEYWORDS or "vice president" in lower or "chief executive" in lower:
        return True

    return False


def extract_contact_fields(ocr_lines: list[dict[str, Any]]) -> dict[str, Any]:
    """Parse OCR text lines into structured contact fields using heuristic classification."""
    lines: list[str] = [
        normalize_line(item.get("text", ""))
        for item in ocr_lines
        if item.get("text", "").strip()
    ]
    full_text = "\n".join(lines)

    email = extract_email(full_text)
    website = extract_website(full_text)
    phones = extract_phone_candidates(full_text)
    email_hints = _email_name_hints(email)

    # Classify lines by category
    company_candidates: list[tuple[int, str]] = []
    address_candidates: list[str] = []
    job_title_candidates: list[str] = []

    for line in lines:
        lower_line = line.lower()
        if is_job_title(line):
            job_title_candidates.append(line)
        else:
            company_score = 0
            if any(hint in lower_line for hint in COMPANY_HINTS):
                company_score += 30
            company_score += sum(10 for word in lower_line.split() if word.rstrip(".,") in COMPANY_WORDS)
            if line == line.upper() and len(line.split()) > 1:
                company_score += 20
            if any(suffix in lower_line for suffix in ("pvt", "ltd", "limited", "llp", "inc", "corp")):
                company_score += 40
            if company_score > 0 and not _is_name_candidate(line):
                company_candidates.append((company_score, line))
            elif _looks_like_address(line):
                address_candidates.append(line)

    excluded = set(phones)
    if email:
        excluded.add(email)
    if website:
        excluded.add(website)
    company_names = {name for _, name in company_candidates}

    candidate_lines = []
    for idx, line in enumerate(lines):
        if line in excluded or line in company_names or line in address_candidates or line in job_title_candidates:
            continue
        if not _is_name_candidate(line):
            continue

        score = 0
        line_lower = line.lower()
        if email_hints and any(hint.lower() == line_lower or hint.lower() in line_lower for hint in email_hints):
            score += 50
        if idx > 0 and is_job_title(lines[idx - 1]):
            score += 80
        if idx + 1 < len(lines) and is_job_title(lines[idx + 1]):
            score += 20
        score += min(len(line.split()), 4) * 5
        if all(re.match(r"^[A-Z][A-Za-z'.-]*$", part) for part in line.split()):
            score += 20
        if any(part.lower() in COMPANY_WORDS for part in line.split()):
            score -= 100
        if _looks_like_address(line):
            score -= 100
        candidate_lines.append((score, line))

    best_name = None
    if candidate_lines:
        _, best_name = max(candidate_lines, key=lambda item: item[0])

    first_name: str | None = None
    last_name: str | None = None
    if best_name:
        parts = best_name.split()
        if len(parts) >= 2:
            first_name = parts[0]
            last_name = " ".join(parts[1:])
        elif len(parts) == 1:
            first_name = parts[0]

    warnings: list[str] = []
    if first_name or company_candidates or address_candidates:
        warnings.append(
            "Name, company, and address are heuristic candidates; verify before relying on them."
        )

    address_text = ", ".join(address_candidates) if address_candidates else None
    company_name = max(company_candidates, key=lambda item: item[0], default=(0, None))[1] if company_candidates else None

    return {
        "first_name": first_name,
        "last_name": last_name,
        "email": email,
        "contact_number": phones[0] if phones else None,
        "company_name": company_name,
        "address": address_text,
        "job_title": job_title_candidates[0] if job_title_candidates else None,
        "website": website,
        "warnings": warnings,
    }