# Secure PDF Document Authentication Using Cryptographic Hashing and QR Codes

An end-to-end academic project implementing tamper-evident digital document verification using **deterministic canonical page rasterization**, **cryptographic SHA-256 digests**, and **embedded 2D QR codes**.

---

## Architecture Overview

```
+-------------------------------------------------------------------------+
|                              CLIENT LAYER                               |
|          React 18 + Vite + Tailwind CSS (Responsive Web Portal)          |
|    - Phase 1: Document Securing (Upload, Canonical Hash, Download)      |
|    - Phase 2: Document Verification (Forensic Dual-Hash Inspector)      |
+------------------------------------+------------------------------------+
                                     |  REST API / Multipart Form Data
                                     v
+------------------------------------+------------------------------------+
|                         BACKEND API LAYER                               |
|               FastAPI (Asynchronous High-Throughput ASGI)               |
|    - CORS Middleware, File Validation, Error Handling, Routing          |
+------------------+----------------------------------+-------------------+
                   |                                  |
                   v                                  v
       [ /api/v1/generate ]                 [ /api/v1/verify ]
                   |                                  |
+------------------v----------------------------------v-------------------+
|                       CORE ENGINE / SERVICES LAYER                      |
+-------------------------------------------------------------------------+
| 1. PDF Processing Service (PyMuPDF / fitz)                             |
|    - Page 1 extraction & A4 authentication certificate synthesis        |
+-------------------------------------------------------------------------+
| 2. Canonical Hashing Service (hashlib)                                  |
|    - Deterministic 150 DPI raw RGB rasterization (No alpha channel)     |
|    - Invariant SHA-256 digest computation                               |
+-------------------------------------------------------------------------+
| 3. QR Code Service (qrcode + OpenCV + Pillow)                           |
|    - Level H (30% error recovery) QR generation                         |
|    - Computer vision barcode extraction (cv2.QRCodeDetector)            |
+-------------------------------------------------------------------------+
| 4. Verification Service (hmac.compare_digest)                           |
|    - Constant-time hash comparison preventing timing attacks            |
+-------------------------------------------------------------------------+
```

### The Problem: The Full-Binary Hash Mutation Paradox
Standard cryptographic verification computes the SHA-256 hash of an entire file binary. However, embedding a verification artifact (like an authentication page or QR code) directly into a PDF alters its internal byte offsets, cross-reference (XREF) table, and trailer, **permanently invalidating any self-contained full-file binary hash**.

### The Solution: Deterministic Canonical Page Rasterization
This framework decouples document verification from volatile file container structures:
1. Isolates the visual presentation of Page 1.
2. Renders the page into an uncompressed, raw 3-channel RGB pixel buffer at an invariant 150 DPI resolution.
3. Computes the SHA-256 hash strictly on the **visual representation** of the content.
4. Encodes this hash into a high-error-correction QR code and stamps it onto an appended A4 authentication certificate (Page 2).
5. During verification, Page 1 is re-rendered using the identical canonical matrix, guaranteeing 100% byte-for-byte reproducibility.

---

## Repository Structure

```text
├── backend/                         # Python FastAPI Microservice
│   ├── app/
│   │   ├── main.py                  # API entry point & CORS
│   │   ├── config.py                # Pipeline settings (DPI, storage)
│   │   ├── routers/                 # API endpoints (/generate, /verify)
│   │   ├── services/                # PyMuPDF, OpenCV, Hash, Verification
│   │   ├── schemas/                 # Pydantic request/response models
│   │   └── utils/                   # File validation helpers
│   ├── storage/                     # Ephemeral file storage
│   ├── requirements.txt             # Python dependencies
│   └── README.md
│
├── frontend/                        # React Single Page Application (SPA)
│   ├── src/
│   │   ├── components/              # Reusable UI (Navbar, Footer, Dropzone, etc.)
│   │   ├── pages/                   # Home, Generate, Verify, About
│   │   ├── services/                # Axios API client
│   │   ├── App.jsx                  # React Router setup
│   │   └── index.css                # Tailwind CSS theme
│   ├── package.json
│   ├── vite.config.js
│   ├── tailwind.config.js
│   └── README.md
│
├── test_e2e.py                      # Automated forensic verification test suite
└── README.md
```

---

## Status Verdict Matrix

| Status | Theme | Forensic Condition | Interpretation |
|---|---|---|---|
| **AUTHENTIC** | Emerald Green | `Original Hash == Calculated Hash` | Document integrity verified. Page 1 is 100% unmodified. |
| **MODIFIED** | Crimson / Orange | `Original Hash != Calculated Hash` | Tampering detected. Even a single character or pixel changed. |
| **INVALID** | Red | `Page Count < 2` or `No QR Detected` | Document lacks authentication page or barcode is unreadable. |

## Independent Hash and DSP Pipelines

Generation assigns a unique `document_id` and writes separate records:

```text
backend/storage/
├── hash_records/<document_id>.json
├── dsp_references/<document_id>/page1_reference.png
└── forensic_results/<document_id>/
```

The hash pipeline performs SHA-256 verification and QR metadata handling only.
The DSP pipeline retrieves the persisted canonical Page 1 reference and performs
preprocessing, SSIM, FFT, DCT, edge, difference, and contour analysis. The
verification endpoint orchestrates both pipelines and returns independent
`hash_analysis` and `dsp_analysis` objects. Legacy QR payloads containing only a
raw hash remain supported; those documents can still use the optional
`original_file` DSP comparison path.

---

## Installation & Setup

### 1. Prerequisites
- Python 3.10+
- Node.js 18+ & npm

### 2. Backend Setup
```bash
cd backend
python -m venv venv

# Windows
.\venv\Scripts\Activate.ps1

# Linux / macOS
source venv/bin/activate

pip install -r requirements.txt
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```
API Documentation: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)

### 3. Frontend Setup
```bash
cd frontend
npm install
npm run dev
```
Web Application: [http://127.0.0.1:5173/](http://127.0.0.1:5173/)

### 4. Running the Automated Forensic Verification Tests
```bash
python test_e2e.py
```

---

## Academic Project Information
- **Project Title**: Secure PDF Document Authentication Using Cryptographic Hashing and QR Codes
- **Developer**: [Pranay Mathurkar](https://github.com/Pranay-Mathurkar)
- **License**: MIT
