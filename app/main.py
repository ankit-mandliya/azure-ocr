import os

# Disable MKLDNN / oneDNN on CPU to avoid Windows PaddlePaddle PIR executor conversion bug:
# "NotImplementedError: (Unimplemented) ConvertPirAttribute2RuntimeAttribute not support"
os.environ["PADDLE_PDX_ENABLE_MKLDNN_BYDEFAULT"] = "0"
os.environ["FLAGS_use_mkldnn"] = "0"
os.environ["FLAGS_enable_pir_api"] = "0"

from fastapi import FastAPI
from fastapi.responses import JSONResponse, RedirectResponse
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes.contacts import router as contacts_router
from app.api.routes.vcf import router as vcf_router
from app.modules.azure_ocr.router import router as azure_ocr_router
from app.core.config import settings
from app.core.middleware import CorrelationIdMiddleware
from app.services.ocr_service import PROFILE_CONFIG

app = FastAPI(
    title=settings.app_name,
    description="Multilingual Visiting Card OCR and Contact Extraction API",
    version="1.0.0",
)

# Add correlation ID and execution time metrics middleware
app.add_middleware(CorrelationIdMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routes
app.include_router(contacts_router)
app.include_router(vcf_router, prefix="/api")
app.include_router(azure_ocr_router)


@app.get("/", include_in_schema=False)
def root():
    """Redirect root path to interactive Swagger documentation."""
    return RedirectResponse(url="/docs")


@app.get("/health", tags=["Health"])
def health():
    """Liveness probe: verifies that the application server is up and responsive."""
    return {"status": "ok"}


@app.get("/ready", tags=["Health"])
def readiness():
    """Readiness probe: verifies storage accessibility and configured OCR profiles."""
    checks = {
        "storage": False,
        "ocr_profiles_configured": list(PROFILE_CONFIG.keys()),
    }

    try:
        # Check that storage path parent is accessible / file exists
        if settings.json_path.parent.exists():
            checks["storage"] = True
    except Exception:
        pass

    all_ready = checks["storage"]
    status_code = 200 if all_ready else 503
    return JSONResponse(
        status_code=status_code,
        content={"status": "ready" if all_ready else "not ready", "checks": checks},
    )
