class ContactHubError(Exception):
    """Base exception for application errors."""
    pass


class ImageValidationError(ContactHubError):
    """Raised when an uploaded image fails validation."""
    pass


class OCRError(ContactHubError):
    """Raised when OCR processing fails."""
    pass


class StorageError(ContactHubError):
    """Raised when contact persistence fails."""
    pass

