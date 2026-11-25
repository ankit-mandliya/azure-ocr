# ContactHub -- Multilingual Visiting Card OCR

A scalable, clean, and decoupled FastAPI service for uploading visiting cards, performing multilingual OCR (PaddleOCR PP-OCRv5), extracting key contact fields, and storing contacts with review flags.

> 📖 **Quick Start:** For step-by-step commands on Windows and Linux, see the [RUN_GUIDE.md](file:///c:/Users/User/Downloads/ocrpython/RUN_GUIDE.md).

---

## Architecture Overview

```text
Upload (JPEG/PNG/WEBP)
      │
      ▼
Image Validation (Resolution, EXIF orientation, RGB)
      │
      ▼
OCR Service (PaddleOCR PP-OCRv5 multilingual profiles)
      │
      ▼
Field Extraction (Regex + heuristic classification)
      │
      ▼
Pydantic Validation (Contact normalization & review flags)
      │
      ▼
Storage Protocol (JsonContactStorage now ──> SqlServerContactStorage later)
```

### Key Engineering Decisions
- **Decoupled OCR Engine**: OCR detection and recognition is isolated behind `ocr_service.py`. Swapping engines (or mocking in test environments) requires zero changes to route handlers or extraction logic.
- **Dependency-Injected Storage**: Persistence implements a `ContactStorage` protocol injected into endpoints using FastAPI's `Depends(get_storage)`. Migrating from JSON file storage to Microsoft SQL Server / SQLAlchemy is a single dependency configuration change.
- **Defensive Data Handling**: Raw OCR text and confidence bounding boxes are retained in `raw_text` for auditing, while extracted fields (`email`, `phones`, `name`, `company`, `address`) are validated with strict bounds and `needs_review` heuristics.

---

## Project Structure

```text
contacthub/
├── app/
│   ├── main.py                  # FastAPI application entrypoint & health checks
│   ├── api/
│   │   ├── deps.py              # Dependency injection providers (e.g., storage)
│   │   └── routes/
│   │       └── contacts.py      # OCR scan/preview and contact CRUD endpoints
│   ├── core/
│   │   ├── config.py            # Environment-driven settings (pydantic-settings)
│   │   └── exceptions.py        # Domain exceptions
│   ├── schemas/
│   │   └── contact.py           # Pydantic v2 schemas and models
│   ├── services/
│   │   ├── image_service.py     # Image decoding, EXIF rotation, and constraints
│   │   ├── ocr_service.py       # PaddleOCR multi-script adapter & caching
│   │   ├── extraction_service.py# Semantic contact field parsing & heuristics
│   │   └── contact_service.py   # Aggregation, confidence scoring, & review flags
│   ├── storage/
│   │   ├── base.py              # Storage Protocol contract
│   │   └── json_storage.py      # Thread-safe atomic JSON file storage
│   └── utils/
│       └── text_utils.py        # Unicode normalization & regex extractors
├── data/                        # JSON storage file directory (.gitignore protected)
├── frontend/                    # React + TypeScript contact management UI
├── tests/
│   ├── test_extraction.py       # Normalization and regex parsing unit tests
│   ├── test_storage.py          # Storage CRUD and error handling tests
│   └── test_contacts_api.py     # End-to-end API lifecycle & validation tests
├── requirements.txt             # Core API dependencies
├── requirements-ocr.txt         # OCR runtime dependencies (PaddleOCR / PaddlePaddle)
├── .env.example                 # Environment configuration template
└── README.md
```

---

## Getting Started

### 1. Environment Setup

Create a Python 3.10+ virtual environment:

```bash
python -m venv .venv
# Windows:
.venv\Scripts\activate
# Linux/macOS:
source .venv/bin/activate
```

### 2. Install Dependencies

Install core API dependencies:
```bash
python -m pip install -r requirements.txt
```

To run live OCR inference with PaddleOCR:
```bash
python -m pip install -r requirements-ocr.txt
```
*(For GPU-accelerated environments, install the appropriate `paddlepaddle-gpu` wheel according to your CUDA release).*

### 3. Configuration

Copy `.env.example` to `.env`:
```bash
cp .env.example .env
```

Available configuration keys:
| Variable | Default | Description |
|---|---|---|
| `APP_NAME` | `ContactHub` | Application name |
| `APP_ENV` | `development` | Environment mode |
| `JSON_STORAGE_PATH` | `data/contacts.json` | Path to JSON file storage |
| `MAX_UPLOAD_MB` | `10` | Maximum upload size in megabytes |
| `OCR_DEVICE` | `cpu` | Device for PaddleOCR (`cpu` or `gpu`) |
| `OCR_DEFAULT_PROFILE`| `latin` | Default language model profile |
| `OCR_ENABLE_PREPROCESSING` | `true` | Enable image preprocessing hook |
| `CORS_ORIGINS` | `["http://localhost:5173"]` | Allowed browser origins for direct API access |

---

## Running the API

Start the development server with Uvicorn:

```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

Interactive OpenAPI documentation is available at:
`http://localhost:8000/docs`

### Frontend

The React application and local setup instructions are in [frontend/README.md](frontend/README.md).

---

## API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/api/v1/contacts/scan` | Upload visiting card image (`multipart/form-data`), run OCR & extract fields |
| `POST` | `/api/v1/contacts/preview` | Extract visiting-card fields for review without saving |
| `POST` | `/api/v1/contacts` | Create a reviewed or manually entered contact |
| `GET` | `/api/v1/contacts` | List all saved contacts |
| `GET` | `/api/v1/contacts/{contact_id}` | Retrieve details of a specific contact |
| `PUT` | `/api/v1/contacts/{contact_id}` | Manually correct or verify contact fields |
| `DELETE` | `/api/v1/contacts/{contact_id}` | Delete an existing contact |
| `GET` | `/health` | Liveness probe (`{"status": "ok"}`) |
| `GET` | `/ready` | Readiness probe (verifies storage and OCR profiles) |

---

## Running Tests

Run the test suite with pytest:

```bash
pytest -v
```

Unit and API tests execute rapidly without loading heavy neural network weights by mocking OCR predictions.

---

## Future MSSQL / SQLAlchemy Integration

To migrate storage from JSON to Microsoft SQL Server:
1. Implement a class satisfying the `ContactStorage` protocol in `app/storage/sql_storage.py` using SQLAlchemy.
2. Update `get_storage()` in `app/api/deps.py` to yield the SQL repository.
3. The API endpoints, schemas, and OCR services remain unchanged.

