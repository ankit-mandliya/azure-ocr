from app.services.extraction_service import extract_contact_fields
from app.utils.text_utils import (
    extract_email,
    extract_phone_candidates,
    extract_website,
    normalize_line,
)


def test_normalize_line():
    raw = "  \u200bAnkit   Sharma   \ufeff "
    assert normalize_line(raw) == "Ankit Sharma"


def test_extract_email():
    text = "Feel free to email me at Ankit.Sharma@Example.Co.In for inquiries."
    assert extract_email(text) == "ankit.sharma@example.co.in"


def test_extract_website():
    text = "Visit https://www.contacthub.io or info@contacthub.io"
    assert extract_website(text) == "https://www.contacthub.io"


def test_extract_website_without_protocol():
    text = "Website: www.mycompany.com"
    assert extract_website(text) == "https://www.mycompany.com"


def test_extract_phone_candidates():
    text = "Call us: +91 98765-43210 or 022 12345678"
    candidates = extract_phone_candidates(text)
    assert "+91 98765-43210" in candidates
    assert "022 12345678" in candidates


def test_extract_contact_fields():
    lines = [
        {"text": "Rahul Verma", "confidence": 0.99},
        {"text": "Chief Technology Officer", "confidence": 0.96},
        {"text": "Apex Software Technologies Pvt Ltd", "confidence": 0.98},
        {"text": "124 Park Avenue, Sector 5, Bangalore", "confidence": 0.95},
        {"text": "rahul.verma@apextech.com", "confidence": 0.99},
        {"text": "+91 91234 56789", "confidence": 0.97},
        {"text": "www.apextech.com", "confidence": 0.94},
    ]

    result = extract_contact_fields(lines)

    assert result["first_name"] == "Rahul"
    assert result["last_name"] == "Verma"
    assert result["job_title"] == "Chief Technology Officer"
    assert result["company_name"] == "Apex Software Technologies Pvt Ltd"
    assert "Sector 5" in result["address"]
    assert result["email"] == "rahul.verma@apextech.com"
    assert result["contact_number"] == "+91 91234 56789"
    assert result["website"] == "https://www.apextech.com"
    assert len(result["warnings"]) > 0




