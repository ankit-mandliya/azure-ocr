from datetime import datetime, timezone
from typing import Any

from app.modules.azure_ocr.client import AzureDocumentIntelligenceClient
from app.modules.azure_ocr.exceptions import AzureOCRServiceError
from app.modules.azure_ocr.mapper import map_document
from app.modules.azure_ocr.schemas import AzureBusinessCard, AzureExtractionResponse, AzureExtractionMetadata


class AzureOCRService:
    def __init__(self, client: Any | None = None):
        self.client = client

    def extract(self, image_bytes: bytes) -> AzureExtractionResponse:
        try:
            client = self.client or AzureDocumentIntelligenceClient()
            result = client.analyze(image_bytes)
        except AzureOCRServiceError:
            raise
        except Exception as exc:
            raise AzureOCRServiceError(
                "Azure Document Intelligence could not analyze the business card."
            ) from exc

        documents = getattr(result, "documents", None)
        if documents is None and isinstance(result, dict):
            documents = result.get("documents")
        documents = list(documents or [])
        if not documents:
            raise AzureOCRServiceError("No business card was detected in the uploaded image.")

        cards: list[AzureBusinessCard] = []
        overall_scores: list[float] = []
        for document in documents:
            mapped = map_document(document)
            score = mapped.pop("_overall_confidence")
            if score is not None:
                overall_scores.append(score)
            cards.append(AzureBusinessCard(**mapped))

        overall = (
            round(sum(overall_scores) / len(overall_scores), 4)
            if overall_scores else None
        )
        metadata = AzureExtractionMetadata(
            timestamp=datetime.now(timezone.utc).isoformat(),
        )
        return AzureExtractionResponse(
            cards=cards,
            metadata=metadata,
            overall_confidence=overall,
        )
