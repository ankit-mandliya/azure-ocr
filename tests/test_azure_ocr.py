from io import BytesIO

from PIL import Image

from app.main import app
from app.api.deps import get_storage
from app.modules.azure_ocr.mapper import map_document
from app.modules.azure_ocr.service import AzureOCRService
from app.storage.json_storage import JsonContactStorage
from fastapi.testclient import TestClient
from azure.ai.formrecognizer import DocumentField


def sample_image() -> bytes:
    buffer = BytesIO()
    Image.new("RGB", (200, 100), "white").save(buffer, format="JPEG")
    return buffer.getvalue()


def test_status_reports_missing_configuration(monkeypatch):
    monkeypatch.setattr("app.modules.azure_ocr.router.settings.azure_document_intelligence_endpoint", None)
    monkeypatch.setattr("app.modules.azure_ocr.router.settings.azure_document_intelligence_key", None)
    client = TestClient(app)
    response = client.get("/api/azure-ocr/status")
    assert response.status_code == 200
    assert response.json()["configured"] is False


def test_extract_rejects_empty_upload():
    client = TestClient(app)
    response = client.post(
        "/api/azure-ocr/extract",
        files={"file": ("card.jpg", b"", "image/jpeg")},
    )
    assert response.status_code == 400


def test_extract_rejects_invalid_type():
    client = TestClient(app)
    response = client.post(
        "/api/azure-ocr/extract",
        files={"file": ("card.gif", b"GIF89a", "image/gif")},
    )
    assert response.status_code == 415


def test_mapper_maps_multiple_values():
    document = {
        "fields": {
            "Names": {"value": {"FirstName": {"content": "Priya", "confidence": 0.9}, "LastName": {"content": "Sharma", "confidence": 0.88}}, "confidence": 0.89},
            "CompanyNames": {"value": "Tech Innovations", "confidence": 0.95},
            "Emails": {"values": [{"content": "priya@example.com", "confidence": 0.99}]},
        }
    }
    mapped = map_document(document)
    assert mapped["first_name"] == "Priya"
    assert mapped["last_name"] == "Sharma"
    assert mapped["emails"][0]["value"] == "priya@example.com"
    assert mapped["company_name"] == "Tech Innovations"


def test_mapper_unwraps_azure_sdk_list_fields():
    name = DocumentField(
        value_type="dictionary",
        value={
            "FirstName": DocumentField(value_type="string", value="Priya", confidence=0.98),
            "LastName": DocumentField(value_type="string", value="Sharma", confidence=0.97),
        },
        confidence=0.984,
    )
    document = {
        "fields": {
            "ContactNames": DocumentField(value_type="list", value=[name], confidence=0.984),
            "CompanyNames": DocumentField(
                value_type="list",
                value=[DocumentField(value_type="string", value="Example Incorporated", confidence=0.91)],
                confidence=0.91,
            ),
            "Departments": DocumentField(
                value_type="list",
                value=[DocumentField(value_type="string", value="Engineering", confidence=0.973)],
                confidence=0.973,
            ),
            "JobTitles": DocumentField(
                value_type="list",
                value=[DocumentField(value_type="string", value="Chief Executive Officer", confidence=0.985)],
                confidence=0.985,
            ),
        }
    }

    mapped = map_document(document)

    assert mapped["first_name"] == "Priya"
    assert mapped["last_name"] == "Sharma"
    assert mapped["full_name"] == "Priya Sharma"
    assert mapped["company_name"] == "Example Incorporated"
    assert mapped["department"] == "Engineering"
    assert mapped["job_title"] == "Chief Executive Officer"


def test_mocked_extraction_and_save(tmp_path, monkeypatch):
    storage = JsonContactStorage(tmp_path / "azure_contacts.json")
    app.dependency_overrides[get_storage] = lambda: storage

    class MockClient:
        def analyze(self, image_bytes):
            return {
                "documents": [{
                    "fields": {
                        "Names": {"value": {"FirstName": {"content": "Asha"}, "LastName": {"content": "Patel"}}},
                        "Emails": {"values": [{"content": "asha@example.com", "confidence": 0.98}]},
                        "CompanyNames": {"value": "Example Ltd", "confidence": 0.92},
                    }
                }]
            }

    monkeypatch.setattr(
        "app.modules.azure_ocr.router.AzureOCRService",
        lambda: AzureOCRService(client=MockClient()),
    )
    client = TestClient(app)
    extracted = client.post(
        "/api/azure-ocr/extract",
        files={"file": ("card.jpg", sample_image(), "image/jpeg")},
    )
    assert extracted.status_code == 200
    assert extracted.json()["cards"][0]["first_name"] == "Asha"

    saved = client.post("/api/azure-ocr/save-contact", json={
        "first_name": "Asha",
        "last_name": "Patel",
        "email": "asha@example.com",
        "company_name": "Example Ltd",
    })
    assert saved.status_code == 201
    assert saved.json()["id"]
    app.dependency_overrides.clear()
