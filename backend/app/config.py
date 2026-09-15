"""
Application configuration module using Pydantic BaseSettings.
Manages environmental variables, file paths, and canonical hashing parameters.
"""
from pathlib import Path
from typing import List
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # Application Metadata
    PROJECT_NAME: str = "Secure PDF Document Authentication System"
    VERSION: str = "1.0.0"
    DESCRIPTION: str = (
        "Academic final-year project for authenticating PDF documents using "
        "deterministic page-level canonical SHA-256 hashing and embedded QR codes."
    )
    DEBUG: bool = True
    API_PREFIX: str = "/api/v1"

    # CORS configuration
    CORS_ORIGINS: List[str] = [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:5174",
        "http://127.0.0.1:5174",
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ]

    # File storage locations
    BASE_DIR: Path = Path(__file__).resolve().parent.parent
    STORAGE_DIR: Path = BASE_DIR / "storage"
    UPLOAD_DIR: Path = STORAGE_DIR / "uploads"
    OUTPUT_DIR: Path = STORAGE_DIR / "outputs"
    TEMP_DIR: Path = STORAGE_DIR / "temp"
    HASH_RECORD_DIR: Path = STORAGE_DIR / "hash_records"
    DSP_REFERENCE_DIR: Path = STORAGE_DIR / "dsp_references"
    FORENSIC_RESULTS_DIR: Path = STORAGE_DIR / "forensic_results"
    # Plural aliases mirror the on-disk module boundaries.
    HASH_RECORDS_DIR: Path = STORAGE_DIR / "hash_records"
    DSP_REFERENCES_DIR: Path = STORAGE_DIR / "dsp_references"

    # Cryptographic & Canonical Rasterization Parameters
    HASH_ALGORITHM: str = "SHA-256"
    CANONICAL_DPI: int = 150  # Fixed rendering DPI (matrix zoom = DPI / 72)
    CANONICAL_COLORSPACE: str = "RGB"  # 3-channel RGB pixel buffer (no alpha channel)
    MAX_FILE_SIZE_MB: int = 15  # Limit PDF file uploads to 15MB

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore"
    )

    def init_storage(self) -> None:
        """Create storage directories if they do not exist."""
        for directory in [
            self.STORAGE_DIR,
            self.UPLOAD_DIR,
            self.OUTPUT_DIR,
            self.TEMP_DIR,
            self.HASH_RECORD_DIR,
            self.DSP_REFERENCE_DIR,
            self.FORENSIC_RESULTS_DIR,
            self.HASH_RECORDS_DIR,
            self.DSP_REFERENCES_DIR,
        ]:
            directory.mkdir(parents=True, exist_ok=True)


settings = Settings()
