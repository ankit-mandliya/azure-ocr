from pathlib import Path
from typing import Optional
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application configuration loaded from environment variables or .env file."""

    app_name: str = "ContactHub"
    app_env: str = "development"
    json_storage_path: str = "data/contacts.json"
    database_url: Optional[str] = None
    max_upload_mb: int = 10
    ocr_device: str = "cpu"
    ocr_default_profile: str = "latin"
    ocr_enable_preprocessing: bool = True
    log_level: str = "INFO"
    cors_origins: list[str] = ["http://localhost:5173"]
    azure_document_intelligence_endpoint: Optional[str] = None
    azure_document_intelligence_key: Optional[str] = None

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    @property
    def json_path(self) -> Path:
        """Return Path object for the JSON storage file."""
        return Path(self.json_storage_path)


settings = Settings()
