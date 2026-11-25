from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_preview_single_vcf_contact():
    content = b"""BEGIN:VCARD\r
VERSION:3.0\r
FN:John Smith\r
ORG:ABC Technologies\r
TITLE:Software Engineer\r
TEL:+91 9876543210\r
EMAIL:john@example.com\r
URL:https://example.com\r
ADR:;;123 Main Street;New Delhi;Delhi;110001;India\r
NOTE:Business contact\r
END:VCARD\r
"""
    response = client.post(
        "/api/vcf/preview",
        files={"file": ("john-contact.vcf", content, "text/vcard")},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["filename"] == "john-contact.vcf"
    assert payload["total_contacts"] == 1
    assert payload["contacts"][0]["full_name"] == "John Smith"
    assert payload["contacts"][0]["email"] == "john@example.com"
    assert payload["contacts"][0]["company"] == "ABC Technologies"


def test_preview_multiple_vcf_contacts():
    content = b"""BEGIN:VCARD\r
VERSION:3.0\r
FN:John Smith\r
EMAIL:john@example.com\r
END:VCARD\r
BEGIN:VCARD\r
VERSION:3.0\r
FN:Jane Smith\r
EMAIL:jane@example.com\r
END:VCARD\r
"""
    response = client.post(
        "/api/vcf/preview",
        files={"file": ("contacts.vcf", content, "text/vcard")},
    )

    assert response.status_code == 200
    assert response.json()["total_contacts"] == 2
    assert [item["full_name"] for item in response.json()["contacts"]] == ["John Smith", "Jane Smith"]


def test_vcf_rejects_wrong_extension_and_empty_file():
    wrong_extension = client.post(
        "/api/vcf/preview",
        files={"file": ("contacts.txt", b"BEGIN:VCARD", "text/plain")},
    )
    assert wrong_extension.status_code == 400

    empty = client.post(
        "/api/vcf/preview",
        files={"file": ("empty.vcf", b"", "text/vcard")},
    )
    assert empty.status_code == 400


def test_vcf_rejects_invalid_vcard():
    response = client.post(
        "/api/vcf/preview",
        files={"file": ("invalid.vcf", b"This is not a vCard", "text/vcard")},
    )
    assert response.status_code == 422
