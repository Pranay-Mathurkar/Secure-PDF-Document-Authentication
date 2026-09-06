# Secure PDF Document Authentication - Frontend

A React Single Page Application (SPA) built with **Vite**, **Tailwind CSS**, and **React Router DOM** for the academic project:
**"Secure PDF Document Authentication Using Cryptographic Hashing and QR Codes"**.

---

## Features
- **Modern Cybersecurity Theme**: Deep blue palette, subtle gradients, status tags, and monospace hash viewers.
- **Generate Secure PDF**: Upload any PDF to compute its deterministic Page-1 SHA-256 hash and download a sealed 2-page PDF.
- **Verify Document Authenticity**: Real-time forensic verification with dual-hash comparator (Original QR Hash vs Recomputed Hash) and status verdict (**AUTHENTIC**, **MODIFIED**, or **INVALID**).
- **Responsive Layout**: Designed for Desktop, Tablet, and Mobile devices.
- **Stateless Zero-Knowledge Architecture**: Demonstrates cryptographic integrity without needing a centralized database.

---

## Installation & Running

### 1. Install Dependencies
```bash
cd frontend
npm install
```

### 2. Start Vite Development Server
```bash
npm run dev
```

The frontend will start at: [http://127.0.0.1:5173/](http://127.0.0.1:5173/)
Connecting to FastAPI backend at: `http://127.0.0.1:8000/api/v1`
