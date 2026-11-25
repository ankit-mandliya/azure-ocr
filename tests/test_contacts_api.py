from io import BytesIO
import pytest
from fastapi.testclient import TestClient
from PIL import Image

from app.api.deps import get_storage
from app.core.config import settings
from app.main import app
from app.storage.json_storage import JsonContactStorage


def create_sample_image_bytes() -> bytes:
    """Generate a valid in-memory JPEG image for upload tests."""
    image = Image.new("RGB", (200, 100), color=(255, 255, 255))
    buf = BytesIO()
    image.save(buf, format="JPEG")
    return buf.getvalue()


@pytest.fixture
def test_storage(tmp_path):
    storage_file = tmp_path / "api_test_contacts.json"
    storage = JsonContactStorage(storage_file)
    app.dependency_overrides[get_storage] = lambda: storage
    yield storage
    app.dependency_overrides.clear()


@pytest.fixture
def client(test_storage):
    return TestClient(app)


def test_root_redirect_to_docs(client):
    response = client.get("/", follow_redirects=False)
    assert response.status_code == 307
    assert response.headers["location"] == "/docs"


def test_health_check(client):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
    assert "x-correlation-id" in response.headers
    assert "x-process-time" in response.headers


def test_readiness_check(client):
    response = client.get("/ready")
    assert response.status_code == 200
    assert response.json()["status"] == "ready"


def test_scan_unsupported_media_type(client):
    response = client.post(
        "/api/v1/contacts/scan",
        files={"file": ("test.pdf", b"%PDF-1.4...", "application/pdf")},
    )
    assert response.status_code == 415


def test_scan_empty_file(client):
    response = client.post(
        "/api/v1/contacts/scan",
        files={"file": ("empty.jpg", b"", "image/jpeg")},
    )
    assert response.status_code == 400


def test_scan_and_crud_lifecycle(client, monkeypatch):
    # Mock OCR engine so tests do not download heavy PaddleOCR weights
    mock_ocr_output = [
        {"text": "Priya Sharma", "confidence": 0.98, "box": [[0, 0], [10, 0], [10, 10], [0, 10]]},
        {"text": "Tech Innovations Pvt Ltd", "confidence": 0.95, "box": []},
        {"text": "priya@techinnovations.com", "confidence": 0.99, "box": []},
        {"text": "+91 98765 01234", "confidence": 0.97, "box": []},
    ]

    monkeypatch.setattr("app.api.routes.contacts.run_ocr", lambda *args, **kwargs: mock_ocr_output)

    # 1. POST /scan
    image_bytes = create_sample_image_bytes()
    scan_resp = client.post(
        "/api/v1/contacts/scan",
        files={"file": ("card.jpg", image_bytes, "image/jpeg")},
        data={"language_profile": "latin"},
    )

    assert scan_resp.status_code == 201
    contact = scan_resp.json()
    assert contact["first_name"] == "Priya"
    assert contact["last_name"] == "Sharma"
    assert contact["email"] == "priya@techinnovations.com"
    assert contact["company_name"] == "Tech Innovations Pvt Ltd"
    assert "raw_text" in contact
    assert len(contact["raw_text"]) == 4
    contact_id = contact["id"]

    # 2. GET /contacts/{id}
    get_resp = client.get(f"/api/v1/contacts/{contact_id}")
    assert get_resp.status_code == 200
    assert get_resp.json()["id"] == contact_id

    # 3. GET /contacts (list)
    list_resp = client.get("/api/v1/contacts")
    assert list_resp.status_code == 200
    assert len(list_resp.json()) == 1

    # 4. PUT /contacts/{id} (manual correction)
    update_resp = client.put(
        f"/api/v1/contacts/{contact_id}",
        json={"job_title": "Director of Engineering", "needs_review": False},
    )
    assert update_resp.status_code == 200
    updated = update_resp.json()
    assert updated["job_title"] == "Director of Engineering"
    assert updated["needs_review"] is False


def test_preview_does_not_save_contact(client, monkeypatch):
    mock_ocr_output = [
        {"text": "Priya Sharma", "confidence": 0.98},
        {"text": "priya@techinnovations.com", "confidence": 0.99},
    ]
    monkeypatch.setattr("app.api.routes.contacts.run_ocr", lambda *args, **kwargs: mock_ocr_output)

    response = client.post(
        "/api/v1/contacts/preview",
        files={"file": ("card.jpg", create_sample_image_bytes(), "image/jpeg")},
        data={"language_profile": "latin"},
    )

    assert response.status_code == 200
    assert response.json()["first_name"] == "Priya"
    assert "id" not in response.json()
    assert client.get("/api/v1/contacts").json() == []


def test_preview_hides_debug_fields_in_production(client, monkeypatch):
    monkeypatch.setattr("app.api.routes.contacts.run_ocr", lambda *args, **kwargs: [
        {"text": "Priya Sharma", "confidence": 0.98},
    ])
    monkeypatch.setattr(settings, "app_env", "production")

    response = client.post(
        "/api/v1/contacts/preview",
        files={"file": ("card.jpg", create_sample_image_bytes(), "image/jpeg")},
    )

    assert response.status_code == 200
    assert response.json()["overall_confidence"] is None
    assert response.json()["warnings"] == []


def test_manual_contact_create_and_delete(client):
    create_response = client.post(
        "/api/v1/contacts",
        json={"first_name": "Asha", "last_name": "Patel", "email": "asha@example.com"},
    )

    assert create_response.status_code == 201
    contact_id = create_response.json()["id"]
    assert create_response.json()["first_name"] == "Asha"

    delete_response = client.delete(f"/api/v1/contacts/{contact_id}")
    assert delete_response.status_code == 204
    assert client.get(f"/api/v1/contacts/{contact_id}").status_code == 404


def test_delete_missing_contact_returns_404(client):
    response = client.delete("/api/v1/contacts/missing")
    assert response.status_code == 404
