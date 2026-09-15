# Secure PDF Document Authentication Using Cryptographic Hashing and QR Codes - Backend

## Overview
This backend service provides a robust, microservice-ready REST API built with **FastAPI**, **PyMuPDF (fitz)**, **hashlib**, **qrcode**, and **OpenCV**. It enables tamper-proof academic and institutional document verification by decoupling document verification from full-file binary hashes through deterministic canonical page rasterization.

---

## Directory Structure

```text
backend/
│
├── app/
│   ├── __init__.py
│   ├── main.py                  # Application entry point, CORS, and routing
│   ├── config.py                # Environment and pipeline configurations
│   │
│   ├── routers/
│   │   ├── __init__.py
│   │   ├── generate.py          # /api/v1/generate endpoint
│   │   └── verify.py            # /api/v1/verify endpoint
│   │
│   ├── services/
│   │   ├── __init__.py
│   │   ├── pdf_service.py       # PyMuPDF rendering & page manipulation
│   │   ├── hash_service.py      # Deterministic pixel canonical SHA-256
│   │   ├── qr_service.py        # QR generation & OpenCV decoding
│   │   ├── fft_service.py       # 2D FFT features and magnitude spectra
│   │   ├── dct_service.py       # 2D DCT features and region energies
│   │   ├── feature_service.py   # Sobel, Canny, and document feature vectors
│   │   ├── tamper_detection_service.py # Localization and visual evidence
│   │   ├── authentication_service.py # Multi-layer authentication decisions
│   │   └── verification_service.py  # Orchestration & tamper checking
│   │
│   ├── schemas/
│   │   ├── __init__.py
│   │   └── response_models.py   # Pydantic data schemas
│   │
│   └── utils/
│       ├── __init__.py
│       └── file_utils.py        # File validation & path helpers
│
├── storage/                     # Auto-created storage directory
│   ├── uploads/
│   ├── outputs/
│   └── temp/
│
├── requirements.txt             # Python dependencies
└── README.md                    # Setup & documentation
```

---

### DCT analysis

`app/services/dct_service.py` calculates a normalized grayscale 2D DCT using
`cv2.dct`. DCT coordinates begin at the top-left, where `[0, 0]` is the DC
coefficient. The low-frequency region is the top-left rectangle bounded by
`dct_low_frequency_ratio`; the mid-frequency region is the larger top-left
rectangle bounded by `dct_mid_frequency_ratio`, excluding the low region; and
the high-frequency region is everything outside the mid region. Both ratios
are configurable in `app/dsp_config.py` and default to `0.10` and `0.30`.

DCT similarity compares the DC coefficient and total, low-, mid-, and
high-frequency energies using the mean of five symmetric relative similarities,
scaled to `0-100`.

---

### Structural document features

`app/services/feature_service.py` extracts horizontal, vertical, and combined
Sobel gradients, configurable Canny edge maps, normalized edge density, and
reusable document feature vectors. Edge similarity uses Dice similarity:
`2 * intersection / (edge_pixels_a + edge_pixels_b)`, scaled to `0-100`.
Feature vectors include intensity statistics, edge density, FFT features, DCT
features, and the Canny edge map used for comparison.

---

### Tampering localization

`app/services/tamper_detection_service.py` aligns pages using one optional
area-interpolation resize followed by phase-correlation translation. Shifts
larger than the configured limit are rejected; no rotation, perspective, or
non-uniform warp is applied. Absolute differences are thresholded, cleaned
with opening, closing, dilation, and erosion, and converted into contour
bounding boxes. The service returns difference, binary-mask, bounding-box, and
JET heatmap images in memory, and writes them only when an explicit directory
is provided.

---

### Multi-layer authentication

`app/services/authentication_service.py` preserves SHA-256 as the exact
cryptographic authority and combines it with SSIM, MSE, PSNR, FFT, DCT, edge,
and tampering telemetry. The default confidence weights are hash `0.40`, SSIM
`0.25`, FFT `0.15`, DCT `0.10`, and edge `0.10`; weights must sum to `1.0`.

Matching SHA-256 hashes always produce `AUTHENTIC`. For hash mismatches,
`AUTHENTIC_WITH_RENDERING_DIFFERENCES` indicates a high DSP confidence with no
localized tampering, `SUSPICIOUS` indicates an intermediate result,
`MODIFIED` indicates a lower-confidence mismatch, and
`SIGNIFICANTLY_TAMPERED` requires localized tampering above the configured
percentage threshold together with low visual confidence. The reported
`confidence_score` retains all configured weights, while
`visual_confidence_score` renormalizes the SSIM, FFT, DCT, and edge weights for
hash-mismatch status classification.

---

### Backend API integration

`POST /api/v1/verify/verify-pdf` preserves the existing secured-PDF request
contract. Newly generated documents automatically persist a document ID, an independent
hash record, and a canonical Page 1 DSP reference. Verification retrieves these
records from separate storage locations and returns `hash_analysis` and
`dsp_analysis` independently. Legacy documents may still add an optional
multipart `original_file` field to enable the compatibility DSP comparison path.
comparison. Without it, the endpoint returns the existing SHA-256/QR result
and explicitly sets `dsp_analysis_available` to `false`. With it, the response
adds structured hash, similarity, frequency, edge, tampering, page-level,
confidence, and visual-result URL fields.

Visual artifacts are served from `/api/v1/visual-results/...` and include FFT
spectrum, difference, binary mask, heatmap, and bounding-box images.

---

## Installation & Setup

### 1. Prerequisites
- Python 3.10+ (Tested on Python 3.11)
- Pip package manager

### 2. Create and Activate a Virtual Environment

#### On Windows (PowerShell):
```powershell
cd p:\dsp\backend
python -m venv venv
.\venv\Scripts\Activate.ps1
```

#### On Windows (Command Prompt):
```cmd
cd p:\dsp\backend
python -m venv venv
venv\Scripts\activate.bat
```

#### On Linux / macOS:
```bash
cd backend
python3 -m venv venv
source venv/bin/activate
```

### 3. Install Dependencies
```bash
pip install --upgrade pip
pip install -r requirements.txt
```

### 4. Run the Development Server
```bash
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

### 5. Interactive API Documentation
Once the server is running, explore the interactive documentation:
- Swagger UI: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)
- ReDoc: [http://127.0.0.1:8000/redoc](http://127.0.0.1:8000/redoc)
- Health Check: [http://127.0.0.1:8000/api/v1/health](http://127.0.0.1:8000/api/v1/health)
