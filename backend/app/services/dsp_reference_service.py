"""Persistent canonical Page 1 references for the independent DSP pipeline."""
from pathlib import Path

import cv2
import fitz
import numpy as np

from app.config import settings
from app.services.preprocessing_service import render_page_to_image


def store_reference_page(document_id: str, page: fitz.Page) -> Path:
    """Render and store canonical Page 1 as a PNG under its document ID."""
    directory = settings.DSP_REFERENCE_DIR / Path(document_id).name
    directory.mkdir(parents=True, exist_ok=True)
    path = directory / "page1_reference.png"
    image = render_page_to_image(page)
    if not cv2.imwrite(str(path), cv2.cvtColor(image, cv2.COLOR_RGB2BGR)):
        raise OSError(f"Failed to store DSP reference page: {path}")
    return path


def load_reference_page(document_id: str) -> np.ndarray:
    """Load a stored canonical reference page for DSP comparison."""
    path = settings.DSP_REFERENCE_DIR / Path(document_id).name / "page1_reference.png"
    if not path.is_file():
        raise FileNotFoundError(f"DSP reference page not found for document ID: {document_id}")
    image = cv2.imread(str(path), cv2.IMREAD_COLOR)
    if image is None:
        raise OSError(f"Failed to decode DSP reference page: {path}")
    return cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
