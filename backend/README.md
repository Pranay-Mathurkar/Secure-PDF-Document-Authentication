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
