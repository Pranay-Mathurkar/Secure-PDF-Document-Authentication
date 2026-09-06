"""
Pydantic schemas for API requests and responses.
"""
from typing import Optional
from pydantic import BaseModel, Field


class BaseApiResponse(BaseModel):
    success: bool = True
    message: str = ""


class HealthResponse(BaseModel):
    status: str = "healthy"
    app_name: str
    version: str


class DocumentGenerationResponse(BaseApiResponse):
    file_name: str
    sha256_hash: str
    algorithm: str = "SHA-256"
    timestamp: str
    download_url: str


class DocumentVerificationResponse(BaseApiResponse):
    file_name: str
    is_authentic: bool
    status_text: str  # "AUTHENTIC DOCUMENT" or "DOCUMENT HAS BEEN MODIFIED"
    original_hash: Optional[str] = None
    calculated_hash: Optional[str] = None
    algorithm: str = "SHA-256"
    verification_timestamp: str
    page_count: int
    details: Optional[str] = None
