# Secure PDF Document Authentication

An end-to-end academic project for detecting visual tampering in PDF documents
using deterministic page rasterization, SHA-256 hashing, QR-code transport,
and digital-signal-processing (DSP) analysis.

The project has two related verification layers:

1. **Cryptographic layer** - authenticates the canonical visual representation
   of Page 1 using SHA-256 and a QR code placed on Page 2.
2. **Forensic DSP layer** - explains differences using SSIM, MSE, PSNR, FFT,
   DCT, edge similarity, difference masks, heatmaps, and bounding boxes.

SHA-256 is the authoritative integrity decision. DSP scores provide diagnostic
evidence and localization; they do not replace the cryptographic comparison.

Repository: <https://github.com/Pranay-Mathurkar/Secure-PDF-Document-Authentication>

---

## 1. Problem and Design

### 1.1 Why full-file PDF hashing is unsuitable here

A PDF is a structured container. Saving the same visible page can change
metadata, object ordering, compression streams, byte offsets, cross-reference
tables, or the trailer. A SHA-256 hash over the complete PDF binary changes
after any of those operations, even if the page looks identical.

Embedding an authentication page into the original PDF also changes the file
binary. Therefore, a PDF cannot reliably contain a full-file hash of itself
without creating a self-reference problem.

### 1.2 Canonical page hashing solution

This project authenticates the visual presentation of the first page:

1. Open the uploaded PDF with PyMuPDF.
2. Select Page 1.
3. Render it at exactly 150 DPI.
4. Render in RGB with no alpha channel.
5. Hash the raw, uncompressed RGB sample buffer with SHA-256.
6. Encode the digest and document metadata in a Level-H QR code.
7. Append an A4 authentication certificate as Page 2.
8. During verification, repeat the same Page 1 rendering and compare digests.

The canonical hash is:

```text
canonical_page1_sha256 = SHA256(raw_rgb_pixels(page_1, dpi=150))
```

The original source PDF is not copied in full to the secured output. The
generated document contains the original first page followed by the generated
authentication page.

### 1.3 Security boundary

The system proves that the candidate Page 1 renders to the same canonical
pixel buffer as the digest stored in the QR payload. It does not, by itself:

- establish the identity of the organization that created the QR page;
- provide a public-key digital signature;
- prevent a malicious party from replacing both Page 1 and the QR page;
- authenticate every original page when the source has more than one page;
- guarantee identical rendering across all PDF engines and library versions.

Trusted deployment should add issuer signatures, protected records, access
control, retention policies, pinned rendering dependencies, and audit logging.

---

## 2. End-to-End Architecture

```text
                         Browser
             React 18 + Vite + Tailwind CSS
                 |                       |
                 | multipart/form-data  | JSON + image URLs
                 v                       ^
       FastAPI /api/v1/generate   FastAPI /api/v1/verify
                 |                       |
                 +-----------+-----------+
                             |
                  Application services
      +----------------------+----------------------+
      |                      |                      |
  PyMuPDF               SHA-256 + QR             DSP
  PDF rendering         hash records             analysis
      |                      |                      |
      +----------------------+----------------------+
                             |
                       backend/storage
```

### 2.1 Generation flow

```text
Original PDF
    |
    +--> validate extension/content type
    |
    +--> render Page 1 at 150 DPI RGB
    |        |
    |        +--> canonical_page1_sha256
    |        +--> page1_reference.png
    |        +--> hash_records/<document_id>.json
    |
    +--> create QR JSON payload
    |
    +--> create A4 certificate page with QR and digest
    |
    +--> copy original Page 1 + certificate Page 2
    |
    +--> save outputs/<timestamp>_<name>_secured.pdf
```

### 2.2 Verification flow

```text
Secured PDF
    |
    +--> validate PDF upload
    +--> require at least two pages
    +--> render Page 1 at 150 DPI RGB
    +--> render Page 2 and decode QR
    +--> extract expected hash/document_id
    +--> compare expected and calculated hashes
    |
    +--> if document_id exists:
    |       load persisted Page 1 reference
    |       run independent DSP analysis
    |       write forensic visual artifacts
    |
    +--> return hash_analysis, dsp_analysis, authentication,
         similarity, frequency_analysis, tampering, pages, visual_results
```

---

## 3. Repository Structure

```text
.
├── backend/
│   ├── app/
│   │   ├── main.py
│   │   ├── config.py
│   │   ├── dsp_config.py
│   │   ├── routers/
│   │   │   ├── generate.py
│   │   │   └── verify.py
│   │   ├── schemas/
│   │   │   └── response_models.py
│   │   ├── services/
│   │   │   ├── authentication_service.py
│   │   │   ├── dct_service.py
│   │   │   ├── dsp_analysis_service.py
│   │   │   ├── dsp_reference_service.py
│   │   │   ├── feature_service.py
│   │   │   ├── fft_service.py
│   │   │   ├── hash_record_service.py
│   │   │   ├── hash_service.py
│   │   │   ├── pdf_service.py
│   │   │   ├── preprocessing_service.py
│   │   │   ├── qr_service.py
│   │   │   ├── similarity_service.py
│   │   │   ├── tamper_detection_service.py
│   │   │   └── verification_service.py
│   │   └── utils/
│   │       └── file_utils.py
│   ├── storage/
│   ├── requirements.txt
│   └── README.md
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   ├── pages/
│   │   ├── services/api.js
│   │   ├── App.jsx
│   │   └── main.jsx
│   ├── package.json
│   ├── vite.config.js
│   └── README.md
├── backend/tests/
├── test_e2e.py
└── README.md
```

### 3.1 Backend module responsibilities

| Module | Responsibility |
|---|---|
| `main.py` | Creates the FastAPI app, initializes storage, configures CORS, mounts routers and visual-result directories. |
| `config.py` | Loads settings, environment overrides, storage paths, file limit, hash algorithm, and canonical DPI. |
| `dsp_config.py` | Centralizes preprocessing, FFT, DCT, edge, alignment, threshold, and authentication-weight configuration. |
| `routers/generate.py` | Validates source PDFs, creates records and references, generates QR codes, assembles secured PDFs, and serves downloads. |
| `routers/verify.py` | Handles verification uploads, hash-record lookup, persistent-reference DSP analysis, optional legacy comparison, and visual URLs. |
| `hash_service.py` | Computes deterministic canonical Page 1 SHA-256 hashes. |
| `hash_record_service.py` | Persists source-file, canonical-page, and secured-file hashes independently of DSP. |
| `qr_service.py` | Generates Level-H QR images, decodes QR codes from rendered pages, and extracts legacy or JSON payloads. |
| `pdf_service.py` | Builds the A4 authentication page and combines it with the original first page. |
| `verification_service.py` | Performs the basic Page 1 hash, Page 2 QR, and constant-time verdict. |
| `dsp_reference_service.py` | Stores and loads the canonical Page 1 PNG reference. |
| `preprocessing_service.py` | Renders PDF pages and prepares image arrays for DSP. |
| `similarity_service.py` | Computes image similarity metrics such as SSIM, MSE, and PSNR. |
| `fft_service.py` | Computes 2-D FFT spectra and frequency-domain features. |
| `dct_service.py` | Computes DCT features and frequency-region energies. |
| `feature_service.py` | Computes Sobel, Canny, edge density, and document feature vectors. |
| `tamper_detection_service.py` | Aligns images, creates difference masks, extracts regions, and creates visual evidence. |
| `dsp_analysis_service.py` | Runs the independent reference-versus-candidate DSP pipeline. |
| `authentication_service.py` | Combines cryptographic and DSP scores for extended classifications. |
| `file_utils.py` | Checks PDF extension and declared content type. |
| `response_models.py` | Defines Pydantic response contracts. |

### 3.2 Frontend module responsibilities

| Location | Responsibility |
|---|---|
| `App.jsx` | Browser routes for Home, Generate, Verify, and About. |
| `services/api.js` | Axios client, API base URL, progress callbacks, upload methods, and download URL construction. |
| `pages/Home.jsx` | Product overview and entry points. |
| `pages/Generate.jsx` | Source-PDF upload, securing progress, digest display, and download. |
| `pages/Verify.jsx` | Secured-PDF upload, optional original-file workflow, result steps, and forensic dashboard. |
| `pages/About.jsx` | Project explanation and technology information. |
| `components/FileUpload.jsx` | Reusable PDF selection/dropzone UI. |
| `components/Loading.jsx` | Loading and progress presentation. |
| `components/StepIndicator.jsx` | Multi-stage securing and verification progress. |
| `components/VerificationResult.jsx` | Hash verdict, telemetry, and result presentation. |
| `components/DSPAnalysisDashboard.jsx` | Scores, images, heatmaps, and region details. |
| `components/Navbar.jsx` / `Footer.jsx` | Shared navigation and footer. |

---

## 4. Installation and Local Development

### 4.1 Requirements

- Windows, Linux, or macOS
- Python 3.10 or newer
- Node.js 18 or newer
- npm
- A PDF-capable Python environment for PyMuPDF, OpenCV, NumPy, SciPy, and
  scikit-image

### 4.2 Backend installation

Windows PowerShell:

```powershell
cd backend
python -m venv venv
.\venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
python -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

Linux/macOS:

```bash
cd backend
python3 -m venv venv
source venv/bin/activate
python -m pip install --upgrade pip
pip install -r requirements.txt
python -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

Backend URLs:

- API root: <http://127.0.0.1:8000/>
- Swagger UI: <http://127.0.0.1:8000/docs>
- ReDoc: <http://127.0.0.1:8000/redoc>
- Health: <http://127.0.0.1:8000/api/v1/health>

### 4.3 Frontend installation

```powershell
cd frontend
npm install
npm run dev
```

Frontend URL: <http://127.0.0.1:5173/>

The default frontend API URL is:

```text
http://127.0.0.1:8000/api/v1
```

To use another backend:

```powershell
$env:VITE_API_URL = "http://127.0.0.1:8000/api/v1"
npm run dev
```

For a production frontend build:

```powershell
npm run build
npm run preview
```

### 4.4 Run both services

Open two terminals:

```powershell
# Terminal 1
cd backend
.\venv\Scripts\Activate.ps1
python -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000

# Terminal 2
cd frontend
npm run dev
```

Confirm the backend before opening the browser:

```powershell
Invoke-WebRequest http://127.0.0.1:8000/api/v1/health
Invoke-WebRequest http://127.0.0.1:5173/
```

---

## 5. Configuration

Configuration is defined in `backend/app/config.py` and can be overridden by
environment variables or a `backend/.env` file.

| Setting | Default | Meaning |
|---|---:|---|
| `PROJECT_NAME` | Secure PDF Document Authentication System | Application title. |
| `VERSION` | `1.0.0` | API/application version. |
| `DEBUG` | `True` | Debug setting retained by the application configuration. |
| `API_PREFIX` | `/api/v1` | Common API prefix. |
| `HASH_ALGORITHM` | `SHA-256` | Digest algorithm used by records and QR metadata. |
| `CANONICAL_DPI` | `150` | Rendering DPI for canonical Page 1 hashing and references. |
| `CANONICAL_COLORSPACE` | `RGB` | Intended canonical color model. |
| `MAX_FILE_SIZE_MB` | `15` | Maximum upload size enforced by the verification router. |
| `CORS_ORIGINS` | localhost ports | Allowed browser origins. |

The DSP defaults in `backend/app/dsp_config.py` are:

| Setting | Default |
|---|---:|
| Image resolution | 150 DPI |
| SSIM threshold | 0.95 |
| Difference threshold | 30 |
| Tampering threshold | 0.15 |
| Minimum region area | 100 |
| FFT low-frequency ratio | 0.10 |
| DCT low-frequency ratio | 0.10 |
| DCT mid-frequency ratio | 0.30 |
| Canny lower/upper thresholds | 50 / 150 |
| Morphology kernel/iterations | 3 / 1 |
| Maximum alignment shift | 10.0 |
| Hash/SSIM/FFT/DCT/edge weights | 0.40 / 0.25 / 0.15 / 0.10 / 0.10 |
| Rendering-confidence threshold | 90.0 |
| Suspicious-confidence threshold | 70.0 |
| Significant-confidence threshold | 45.0 |
| Significant tampering percentage | 5.0% |

Storage directories are created automatically when the FastAPI application
starts:

```text
backend/storage/
├── uploads/
├── outputs/
├── temp/
├── hash_records/
├── dsp_references/
└── forensic_results/
```

---

## 6. API Reference

All API paths below include `/api/v1`.

### 6.1 Health check

```http
GET /api/v1/health
```

Example response:

```json
{
  "status": "healthy",
  "app_name": "Secure PDF Document Authentication System",
  "version": "1.0.0"
}
```

### 6.2 Generate secured PDF

```http
POST /api/v1/generate/secure-pdf
Content-Type: multipart/form-data
```

Form field:

| Field | Type | Required | Description |
|---|---|---:|---|
| `file` | PDF file | Yes | Original source PDF. |

PowerShell/cURL example:

```powershell
curl.exe -X POST `
  -F "file=@C:\path\to\source.pdf" `
  http://127.0.0.1:8000/api/v1/generate/secure-pdf
```

Example response:

```json
{
  "success": true,
  "message": "Secured 2-page PDF created successfully.",
  "file_name": "1789294397_source_secured.pdf",
  "sha256_hash": "64-character-lowercase-hex-digest",
  "algorithm": "SHA-256",
  "timestamp": "2026-10-25T13:33:43.160723+00:00",
  "download_url": "/api/v1/generate/download/1789294397_source_secured.pdf",
  "document_id": "uuid-like-document-id"
}
```

Generation behavior:

1. Validate `.pdf` extension and declared MIME type.
2. Read the upload and open it with PyMuPDF.
3. Reject a PDF with no readable pages.
4. Create a hash record containing source-file and canonical Page 1 hashes.
5. Store `page1_reference.png` for persistent DSP comparison.
6. Create JSON QR payload with `document_id`, hash, algorithm, DPI, and version.
7. Create the A4 authentication page.
8. Assemble Page 1 plus the authentication page.
9. Add the secured output SHA-256 to the record.
10. Write the output and return its download URL.

### 6.3 Download secured PDF

```http
GET /api/v1/generate/download/{file_name}
```

The router strips directory components with `Path(file_name).name` before
joining the value to `storage/outputs`. Missing files return HTTP 404.

Example:

```powershell
curl.exe -L `
  -o secured.pdf `
  http://127.0.0.1:8000/api/v1/generate/download/1789294397_source_secured.pdf
```

### 6.4 Verify secured PDF

```http
POST /api/v1/verify/verify-pdf
Content-Type: multipart/form-data
```

Form fields:

| Field | Type | Required | Description |
|---|---|---:|---|
| `file` | PDF file | Yes | Secured PDF containing Page 1 and QR Page 2. |
| `original_file` | PDF file | No | Compatibility baseline for legacy QR payloads with no persisted document ID. |

Basic request:

```powershell
curl.exe -X POST `
  -F "file=@C:\path\to\secured.pdf" `
  http://127.0.0.1:8000/api/v1/verify/verify-pdf
```

Legacy/optional baseline request:

```powershell
curl.exe -X POST `
  -F "file=@C:\path\to\secured.pdf" `
  -F "original_file=@C:\path\to\source.pdf" `
  http://127.0.0.1:8000/api/v1/verify/verify-pdf
```

Core response fields:

```json
{
  "success": true,
  "file_name": "secured.pdf",
  "is_authentic": true,
  "status_text": "AUTHENTIC",
  "original_hash": "expected-64-character-digest",
  "calculated_hash": "calculated-64-character-digest",
  "algorithm": "SHA-256",
  "verification_timestamp": "2026-10-25 13:35:11 UTC",
  "page_count": 2,
  "details": "Page 1 cryptographic hash matches QR code payload exactly.",
  "dsp_analysis_available": true
}
```

### 6.5 Verification decision matrix

| Status | Condition | Meaning |
|---|---|---|
| `AUTHENTIC` | QR hash equals calculated canonical Page 1 hash | Canonical Page 1 is unchanged. |
| `MODIFIED` | QR is readable but hashes differ | Candidate Page 1 visual representation changed. |
| `INVALID` | Fewer than two pages, invalid PDF, or QR cannot be decoded | Required authentication structure is absent or unreadable. |

The extended authentication engine can additionally use:

- `AUTHENTIC_WITH_RENDERING_DIFFERENCES`
- `SUSPICIOUS`
- `MODIFIED`
- `SIGNIFICANTLY_TAMPERED`

The primary `verification_service.py` endpoint remains intentionally simple:
matching hashes produce `AUTHENTIC`, and non-matching hashes produce
`MODIFIED`.

### 6.6 DSP response fields

When a generated document has a persisted `document_id` and reference page,
the response can include:

```json
{
  "hash_analysis": {
    "status": "MATCH",
    "document_id": "id",
    "canonical_page1": {
      "status": "MATCH",
      "match": true,
      "expected": "digest",
      "calculated": "digest"
    }
  },
  "dsp_analysis": {
    "document_id": "id",
    "reference_source": "persistent_canonical_page1",
    "candidate_source": "uploaded_pdf_page1",
    "ssim": 0.996,
    "mse": 0.0,
    "psnr": null,
    "fft_similarity": 99.72,
    "dct_similarity": 99.9,
    "edge_similarity": 99.8,
    "tampering_detected": false,
    "tampering_percentage": 0.0,
    "modified_pages": [],
    "modified_regions": 0,
    "pages": [],
    "visual_results": {
      "pages": []
    }
  },
  "authentication": {
    "status": "AUTHENTIC",
    "confidence": 100.0
  },
  "similarity": {
    "ssim": 0.996,
    "mse": 0.0,
    "psnr": null
  },
  "frequency_analysis": {
    "fft_similarity": 99.72,
    "dct_similarity": 99.9
  },
  "edge_analysis": {
    "edge_similarity": 99.8
  },
  "tampering": {
    "detected": false,
    "percentage": 0.0,
    "modified_regions": 0,
    "modified_pages": []
  },
  "visual_results": {
    "pages": []
  }
}
```

The exact values depend on the input document and rendered pixels.

### 6.7 Static visual result endpoints

Generated forensic PNGs are mounted at:

```text
/api/v1/visual-results/...
/api/v1/forensic-results/...
```

The returned URLs are relative API paths. The frontend's
`getFullDownloadUrl()` helper converts relative paths into absolute backend
URLs.

---

## 7. Detailed Processing Implementation

### 7.1 Canonical hashing

`hash_service.compute_canonical_page_hash()`:

```python
zoom = dpi / 72.0
matrix = fitz.Matrix(zoom, zoom)
pixmap = page.get_pixmap(
    matrix=matrix,
    colorspace=fitz.csRGB,
    alpha=False,
)
digest = hashlib.sha256(pixmap.samples).hexdigest()
```

Important invariants:

- fixed DPI;
- fixed RGB colorspace;
- alpha disabled;
- raw pixel bytes only;
- lowercase hexadecimal output;
- no PDF metadata or container bytes in the canonical digest.

### 7.2 Hash records

`hash_record_service.py` maintains three cryptographic values:

| Field | Meaning |
|---|---|
| `file_sha256` | SHA-256 of the uploaded source PDF bytes. |
| `canonical_page1_sha256` | SHA-256 of canonical Page 1 RGB pixels. |
| `secured_file_sha256` | SHA-256 of the final QR-bearing secured PDF bytes. |

The canonical page hash is used for visual authentication. The two binary-file
hashes provide additional audit telemetry and are not substitutes for the
canonical comparison.

Example record:

```json
{
  "document_id": "uuid-like-id",
  "algorithm": "SHA-256",
  "file_sha256": "source-file-digest",
  "canonical_page1_sha256": "canonical-page-digest",
  "created_at": "2026-10-25T13:33:43+00:00",
  "secured_file_sha256": "secured-file-digest"
}
```

Hash comparisons use `hmac.compare_digest`.

### 7.3 QR generation

`qr_service.generate_qr_image_bytes()`:

- uses the `qrcode` package;
- selects error correction Level H;
- uses automatic QR version selection;
- uses black modules on a white background;
- writes PNG bytes in memory;
- uses a two-module border and box size 10.

The generated payload is compact JSON:

```json
{
  "document_id": "uuid-like-id",
  "hash": "canonical-page1-sha256",
  "algorithm": "SHA-256",
  "dpi": 150,
  "version": "1"
}
```

The decoder renders the authentication page at 200 DPI, tries direct color
detection, tries grayscale Otsu thresholding, and retries at 300 DPI if
necessary. Payload parsing supports both structured JSON and legacy raw
64-character hexadecimal hashes.

### 7.4 Authentication-page synthesis

`pdf_service.create_authentication_page_doc()` creates a 595 x 842 point A4
page containing:

- dark header banner;
- project title;
- QR code and frame;
- two-line canonical SHA-256 digest;
- algorithm and 150-DPI metadata;
- timestamp;
- authentication scope;
- QR Level-H notice;
- verification instructions.

`assemble_secured_pdf()` creates a new PDF, copies only source Page 1, then
appends the generated certificate page.

### 7.5 Image preprocessing

The preprocessing service is responsible for:

- rendering PDF pages into image arrays;
- converting images to a DSP-compatible grayscale representation;
- validating array shape, dtype, and non-empty content;
- producing comparable page lists for the legacy original-file workflow.

The persistent-reference workflow uses the stored canonical Page 1 PNG and
renders the uploaded candidate Page 1 at the canonical DPI.

### 7.6 SSIM, MSE, and PSNR

The similarity service compares prepared reference and candidate images.

```text
MSE = (1/N) * sum((reference_pixel - candidate_pixel)^2)
PSNR = 10 * log10(MAX^2 / MSE)
```

SSIM is a structural similarity score. Identical images produce the maximum
similarity expected by the service. PSNR may be represented as `null` in JSON
when the images are identical and the mathematical value is infinite.

### 7.7 FFT analysis

`fft_service.py` calculates:

```text
F = fftshift(fft2(image))
magnitude = log(1 + abs(F))
power = abs(F)^2
```

Extracted features:

- mean frequency magnitude;
- magnitude standard deviation;
- total spectral energy;
- low-frequency energy;
- high-frequency energy;
- high-to-low frequency energy ratio.

The low-frequency region is centered in the shifted FFT and is controlled by
`fft_low_frequency_ratio` (default `0.10`). A bounded symmetric relative
similarity is computed for each feature and averaged to a 0–100 score.

The dashboard image uses percentile clipping and square-root enhancement so the
large DC component does not hide useful spectral structure.

### 7.8 DCT analysis

`dct_service.py` computes a normalized grayscale 2-D DCT using OpenCV.
Coefficient regions are divided into:

- low frequency: top-left area bounded by `0.10`;
- mid frequency: top-left area bounded by `0.30`, excluding low frequency;
- high frequency: coefficients outside the mid-frequency region.

The DCT comparison uses symmetric relative similarity across DC, total, low,
mid, and high-frequency energies.

### 7.9 Edge and structural features

`feature_service.py` provides:

- horizontal Sobel gradient;
- vertical Sobel gradient;
- combined gradient;
- Canny edge map;
- normalized edge density;
- reusable document feature vectors.

Edge maps are compared using Dice similarity:

```text
Dice(A, B) = 2 * |A intersection B| / (|A| + |B|)
```

The configured Canny thresholds are 50 and 150.

### 7.10 Tampering localization

`tamper_detection_service.py`:

1. Converts both images to grayscale.
2. Resizes the candidate to the reference dimensions if needed.
3. Estimates translation using phase correlation.
4. Rejects shifts beyond the configured maximum of 10 pixels.
5. Applies the accepted translation with affine warping.
6. Computes an absolute difference image.
7. Thresholds differences at 30 by default.
8. Applies opening, closing, dilation, and erosion.
9. Finds external contours.
10. Filters regions below 100 pixels.
11. Creates binary mask, heatmap, difference image, and bounding-box image.

No rotation, perspective correction, or non-uniform warp is applied by this
alignment function. This is deliberate: broad geometric transformations
should not silently normalize a potentially altered document.

### 7.11 Independent DSP pipeline

`dsp_analysis_service.analyze_dsp_pages()` performs DSP only. It does not call
the hash or QR services. For each corresponding reference/candidate page it
computes:

- SSIM, MSE, PSNR;
- FFT similarity;
- DCT similarity;
- edge similarity;
- tampering percentage;
- tampering region count and bounding boxes.

The router adds persisted reference metadata and writes visual artifacts.

### 7.12 Authentication score engine

`authentication_service.py` preserves the cryptographic hash as the authority
and computes a weighted confidence score:

```text
confidence =
    0.40 * hash_score
  + 0.25 * SSIM_score
  + 0.15 * FFT_score
  + 0.10 * DCT_score
  + 0.10 * edge_score
```

When hashes mismatch, visual confidence is renormalized over the visual terms
only. This prevents a zero cryptographic score from hiding useful forensic
information while still preserving the exact hash verdict.

---

## 8. Persistent Storage

```text
backend/storage/
├── uploads/
│   └── reserved for upload-related files
├── outputs/
│   ├── <timestamp>_<sanitized>_secured.pdf
│   └── analysis/<random-id>/*.png
├── temp/
├── hash_records/
│   └── <document_id>.json
├── dsp_references/
│   └── <document_id>/page1_reference.png
└── forensic_results/
    └── <document_id>/
        ├── page_1_original.png
        ├── page_1_candidate_preprocessed.png
        ├── page_1_edge_map.png
        ├── page_1_fft_spectrum.png
        ├── page_1_difference_image.png
        ├── page_1_tampering_mask.png
        ├── page_1_tampering_heatmap.png
        └── page_1_bounding_box_image.png
```

The storage layer is filesystem-based. It is not a database and has no
automatic cleanup or retention job. For production, replace or wrap it with a
database/object-storage system and define lifecycle management.

Document IDs are sanitized with `Path(document_id).name` when used in storage
paths. Generated filenames are sanitized to ASCII letters, digits, underscores,
and hyphens.

---

## 9. Frontend User Workflows

### 9.1 Generate workflow

1. Open `/generate`.
2. Select or drop a PDF.
3. The frontend sends `file` to `/generate/secure-pdf`.
4. The progress callback updates the upload state.
5. The response displays:
   - generated filename;
   - SHA-256 digest;
   - algorithm;
   - timestamp;
   - document ID;
   - download action.
6. Download the secured two-page PDF.

### 9.2 Verify workflow

1. Open `/verify`.
2. Select the secured PDF.
3. Optionally select the original source PDF for legacy/reference comparison.
4. The frontend sends multipart form data to `/verify/verify-pdf`.
5. The result UI displays:
   - upload and QR decoding progress;
   - AUTHENTIC, MODIFIED, or INVALID status;
   - stored and calculated digests;
   - page count and timestamp;
   - DSP similarity values;
   - tampering percentage and region count;
   - visual result images and bounding boxes.

### 9.3 Client API behavior

`frontend/src/services/api.js`:

- creates an Axios client;
- uses `VITE_API_URL` when defined;
- defaults to `http://127.0.0.1:8000/api/v1`;
- applies a 60-second request timeout;
- sends multipart form data;
- exposes upload progress;
- throws request errors after logging health-check failures;
- constructs absolute URLs for backend-served result files.

---

## 10. Testing

### 10.1 Backend unit tests

Tests are located under `backend/tests/`:

```text
test_authentication_service.py
test_dct_service.py
test_feature_service.py
test_fft_service.py
test_preprocessing_service.py
test_similarity_service.py
test_tamper_detection_service.py
test_verify_api.py
```

Run them from the repository root:

```powershell
python -m pytest backend/tests -q
```

### 10.2 End-to-end test

The root `test_e2e.py`:

1. creates a one-page synthetic transcript with PyMuPDF;
2. calls the generation API;
3. downloads the secured output;
4. verifies the untouched secured PDF as `AUTHENTIC`;
5. draws over Page 1 and inserts altered text;
6. verifies the changed file as `MODIFIED`;
7. verifies the original one-page PDF as `INVALID`.

Start the backend first, then run:

```powershell
python test_e2e.py
```

The script creates temporary files in its current working directory:

```text
sample_transcript.pdf
secured_transcript.pdf
tampered_transcript.pdf
```

Remove them after testing if they are not needed.

### 10.3 Frontend build

```powershell
cd frontend
npm run build
```

The build output is written to `frontend/dist/`.

### 10.4 Recommended validation order

```powershell
# Backend unit tests
python -m pytest backend/tests -q

# Frontend production build
Set-Location frontend
npm run build
Set-Location ..

# Backend must be running for this step
python test_e2e.py
```

---

## 11. Error Handling and Troubleshooting

### 11.1 Common HTTP responses

| HTTP status | Cause |
|---:|---|
| 200 | Request completed; inspect `status_text` for document verdict. |
| 400 | Wrong extension, MIME type, corrupt PDF, or no readable page. |
| 404 | Requested generated file does not exist. |
| 413 | Verification upload exceeds the configured maximum size. |
| 422 | DSP analysis could not process the reference/candidate images. |
| 500 | Unexpected generation, assembly, or analysis failure. |

### 11.2 Backend cannot import `app`

Run Uvicorn from `backend`, not the repository root:

```powershell
cd backend
python -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

### 11.3 Frontend cannot find `package.json`

Run npm from `frontend`:

```powershell
cd frontend
npm run dev
```

### 11.4 QR cannot be decoded

Check:

- the uploaded file contains the generated Page 2;
- the QR is not cropped or excessively compressed;
- Page 2 is readable at 200–300 DPI;
- the output was not re-rendered by a viewer that damaged the QR;
- OpenCV and PyMuPDF dependencies are installed correctly.

### 11.5 DSP reference unavailable

The QR payload may contain a `document_id` while the corresponding
`storage/dsp_references/<document_id>/page1_reference.png` is missing. Restore
the reference from the same generation environment or regenerate the secured
document. The basic hash result may still be available for legacy records.

### 11.6 Results differ after environment changes

Pin and preserve:

- Python version;
- PyMuPDF version;
- OpenCV version;
- color/rendering behavior;
- fonts used by the source PDF;
- canonical DPI and configuration.

Canonical hashing is deterministic for a fixed rendering environment; it is not
a promise that every PDF renderer on every platform produces identical pixels.

---

## 12. Deployment Guidance

This repository is configured for local development. A safer deployment should:

1. Set `DEBUG=False`.
2. Restrict `CORS_ORIGINS` to the real frontend origin.
3. Put the API behind HTTPS and a reverse proxy.
4. Run Uvicorn with a process manager.
5. Use a non-world-writable storage location.
6. Add authentication and authorization.
7. Add upload quotas and request rate limits.
8. Enforce file-size limits before expensive processing for every upload path.
9. Add antivirus/content inspection where required.
10. Add storage cleanup and retention policies.
11. Protect hash records and references from unauthorized replacement.
12. Add institutional signing keys if the QR needs issuer authenticity.
13. Pin dependencies and record the canonical rendering environment.
14. Avoid exposing raw forensic artifacts to unauthorized users.

Example production-style process:

```powershell
cd backend
.\venv\Scripts\Activate.ps1
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 2
```

Use a reverse proxy for TLS, request size limits, static asset caching, and
access control. Do not expose a development server directly to the internet.

---

## 13. Known Limitations

- Only Page 1 is copied and canonically authenticated in the generated output.
- The source document's later pages are not included in the secured output.
- The QR contains a digest and metadata, not an issuer digital signature.
- The filesystem persistence layer has no transactional database semantics.
- The source generation route validates extension and content type; production
  deployments should enforce the byte-size limit before processing generation
  uploads as well as verification uploads.
- DSP alignment handles size normalization and translation only.
- Thresholds are configuration values, not learned from a benchmark corpus.
- No claims of accuracy, false-positive rate, or production robustness should
  be made without a controlled evaluation dataset.
- Renderer/library changes can change canonical pixels.
- A legacy QR containing only a raw hash has no persisted document ID and cannot
  use the persistent-reference DSP path.

---

## 14. Extension Points

Potential next implementations:

1. Add a signed QR payload:

   ```text
   payload = document_id + canonical_hash + metadata + issuer_signature
   ```

2. Add an explicit canonical-rendering profile with versioned renderer,
   page-box, color, and font rules.
3. Support a manifest containing canonical hashes for every source page.
4. Store records in PostgreSQL or a tamper-evident transparency log.
5. Add an object-level PDF analysis path alongside visual hashing.
6. Add benchmark datasets and ROC/precision/recall/F1 evaluation.
7. Add adversarial tests for QR replacement, page insertion, scaling,
   rotation, image compression, and renderer differences.
8. Add an administrative document lookup and revocation workflow.

---

## 15. Academic Project Information

- **Project title:** Secure PDF Document Authentication Using Cryptographic
  Hashing and QR Codes
- **Institution:** Motilal Nehru National Institute of Technology Allahabad
- **Department:** Electronics and Communication Engineering
- **Subject:** Digital Signal Processing
- **Academic year:** 2026
- **Team members:**
  - Prajapati Vishnu Munna — 20244127
  - Pranay Mathurkar — 20244129
  - Pranav Ranjan — 20244128
  - Payel Sardar — 20244126
- **Repository:** <https://github.com/Pranay-Mathurkar/Secure-PDF-Document-Authentication>
- **License:** MIT

Supervisor name, final submission date, and any institution-specific
submission metadata should be added before final submission.

---

## 16. Quick Start

```powershell
# Terminal 1: backend
cd backend
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
python -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000

# Terminal 2: frontend
cd frontend
npm install
npm run dev

# Browser
Start-Process http://127.0.0.1:5173/
```

Use **Generate Secure PDF** to create a certificate-bearing file, then use
**Verify Document** to inspect its cryptographic verdict and DSP evidence.
