class AzureOCRError(Exception):
    """Base exception for Azure OCR failures."""


class AzureOCRConfigurationError(AzureOCRError):
    """Raised when Azure credentials are not configured."""


class AzureOCRServiceError(AzureOCRError):
    """Raised when Azure analysis fails or returns no business card."""
