from typing import Any, Protocol

from app.core.config import settings
from app.modules.azure_ocr.exceptions import AzureOCRConfigurationError


class AzureAnalysisClient(Protocol):
    def analyze(self, image_bytes: bytes) -> Any:
        ...


class AzureDocumentIntelligenceClient:
    def __init__(self, endpoint: str | None = None, key: str | None = None):
        self.endpoint = endpoint or settings.azure_document_intelligence_endpoint
        self.key = key or settings.azure_document_intelligence_key

        if not self.endpoint or not self.key:
            raise AzureOCRConfigurationError(
                "Azure Document Intelligence is not configured. Set AZURE_DOCUMENT_INTELLIGENCE_ENDPOINT and AZURE_DOCUMENT_INTELLIGENCE_KEY."
            )

        try:
            from azure.ai.formrecognizer import DocumentAnalysisClient
            from azure.core.credentials import AzureKeyCredential
        except ImportError as exc:
            raise AzureOCRConfigurationError(
                "The Azure Document Intelligence SDK is not installed."
            ) from exc

        self._client = DocumentAnalysisClient(
            endpoint=self.endpoint,
            credential=AzureKeyCredential(self.key),
        )

    def analyze(self, image_bytes: bytes) -> Any:
        poller = self._client.begin_analyze_document(
            "prebuilt-businessCard",
            document=image_bytes,
        )
        return poller.result()
