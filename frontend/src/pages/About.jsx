import React from 'react';
import {
  Shield,
  FileText,
  Binary,
  Lock,
  Cpu,
  CheckCircle2,
  AlertTriangle,
  Code2,
  Terminal,
  Layers
} from 'lucide-react';
import FeatureCard from '../components/FeatureCard';

export default function About() {
  return (
    <div className="max-w-5xl mx-auto px-4 sm:px-6 lg:px-8 py-12 space-y-12">
      {/* Title & Header */}
      <div className="text-center space-y-3">
        <div className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full bg-indigo-50 text-indigo-700 text-xs font-mono border border-indigo-200">
          <Shield className="w-3.5 h-3.5" />
          <span>Academic Project Report</span>
        </div>
        <h1 className="text-3xl sm:text-4xl font-extrabold text-slate-900 tracking-tight">
          Secure PDF Document Authentication
        </h1>
        <p className="text-base text-slate-600 max-w-2xl mx-auto">
          Final-Year Engineering Project exploring deterministic canonical hashing and high-density 2D barcodes
          to resolve the document modification paradox in digital document forensics.
        </p>
      </div>

      {/* Abstract Card */}
      <div className="bg-white border border-slate-200 rounded-2xl p-6 sm:p-8 shadow-sm space-y-4">
        <div className="flex items-center gap-2 text-blue-600 font-bold text-sm uppercase tracking-wider">
          <FileText className="w-4 h-4" />
          <span>Abstract</span>
        </div>
        <p className="text-sm text-slate-700 leading-relaxed text-justify">
          Digital document integrity verification is commonly achieved using cryptographic hashes such as SHA-256.
          However, embedding authentication artifacts (such as QR codes, metadata, or verification pages) into an existing PDF
          mutates the file&apos;s binary structure, byte offsets, and cross-reference table, invalidating the original hash.
          This project proposes and implements a deterministic canonical page rasterization framework using PyMuPDF and OpenCV.
          By isolating the visual representation of the primary content page at an invariant 150 DPI resolution and converting it
          to an uncompressed RGB pixel stream, a persistent cryptographic signature is calculated and embedded onto a secondary
          authentication page. The resulting 2-page document achieves decentralized, zero-knowledge tamper verification.
        </p>
      </div>

      {/* The Core Problem & The Solution */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <div className="bg-rose-50/60 border border-rose-200 rounded-2xl p-6 space-y-3">
          <div className="flex items-center gap-2 text-rose-700 font-bold text-sm">
            <AlertTriangle className="w-5 h-5 text-rose-600" />
            <span>The Technical Challenge (Full-Binary Hash Paradox)</span>
          </div>
          <p className="text-xs text-slate-600 leading-relaxed">
            A standard cryptographic hash covers all bytes of a file from start to finish. If you append a verification page or stamp a QR code onto the PDF, the byte stream changes completely. Therefore, a PDF cannot embed a full-binary hash of itself without invalidating that very hash.
          </p>
        </div>

        <div className="bg-emerald-50/60 border border-emerald-200 rounded-2xl p-6 space-y-3">
          <div className="flex items-center gap-2 text-emerald-700 font-bold text-sm">
            <CheckCircle2 className="w-5 h-5 text-emerald-600" />
            <span>The Architectural Solution (Canonical Rasterization)</span>
          </div>
          <p className="text-xs text-slate-600 leading-relaxed">
            Our system isolates the first page and deterministically rasterizes it into raw 3-channel RGB pixel samples at fixed 150 DPI. By ignoring volatile container metadata and compression streams, identical page content always produces the exact same SHA-256 hash.
          </p>
        </div>
      </div>

      {/* Technology Stack Grid */}
      <div className="space-y-4">
        <h2 className="text-xl font-bold text-slate-900 tracking-tight">
          System Technology Stack
        </h2>
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
          <div className="bg-white border border-slate-200 rounded-xl p-4">
            <span className="text-xs font-mono text-blue-600 font-semibold block">Frontend</span>
            <h4 className="font-bold text-slate-800 text-sm mt-1">React 18 + Vite</h4>
            <p className="text-xs text-slate-500 mt-1">Fast, responsive SPA with Tailwind CSS styling and clean component hierarchy.</p>
          </div>

          <div className="bg-white border border-slate-200 rounded-xl p-4">
            <span className="text-xs font-mono text-indigo-600 font-semibold block">Backend API</span>
            <h4 className="font-bold text-slate-800 text-sm mt-1">Python FastAPI</h4>
            <p className="text-xs text-slate-500 mt-1">High-performance asynchronous REST microservice with automated OpenAPI schemas.</p>
          </div>

          <div className="bg-white border border-slate-200 rounded-xl p-4">
            <span className="text-xs font-mono text-purple-600 font-semibold block">PDF Engine</span>
            <h4 className="font-bold text-slate-800 text-sm mt-1">PyMuPDF (fitz)</h4>
            <p className="text-xs text-slate-500 mt-1">Sub-millisecond page extraction, fixed-matrix DPI rendering, and multi-page assembly.</p>
          </div>

          <div className="bg-white border border-slate-200 rounded-xl p-4">
            <span className="text-xs font-mono text-emerald-600 font-semibold block">Vision &amp; Barcode</span>
            <h4 className="font-bold text-slate-800 text-sm mt-1">OpenCV + qrcode</h4>
            <p className="text-xs text-slate-500 mt-1">High-error correction Level H QR generation and computer-vision QR decoding.</p>
          </div>
        </div>
      </div>

      {/* Verdict Matrix Table */}
      <div className="bg-white border border-slate-200 rounded-2xl overflow-hidden shadow-sm">
        <div className="bg-slate-50 px-6 py-4 border-b border-slate-200">
          <h3 className="font-bold text-slate-800 text-sm">Forensic Verification Status Matrix</h3>
        </div>
        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead className="bg-slate-100/70 text-slate-700 font-semibold uppercase tracking-wider">
              <tr>
                <th className="px-6 py-3">Status Output</th>
                <th className="px-6 py-3">Color Code</th>
                <th className="px-6 py-3">Condition</th>
                <th className="px-6 py-3">Interpretation</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100 text-slate-600">
              <tr>
                <td className="px-6 py-3 font-bold text-emerald-600">AUTHENTIC</td>
                <td className="px-6 py-3 font-mono">Green (#059669)</td>
                <td className="px-6 py-3">Original Hash == Calculated Hash</td>
                <td className="px-6 py-3">Page 1 content is completely intact and unmodified.</td>
              </tr>
              <tr>
                <td className="px-6 py-3 font-bold text-orange-600">MODIFIED</td>
                <td className="px-6 py-3 font-mono">Orange (#ea580c)</td>
                <td className="px-6 py-3">Original Hash != Calculated Hash</td>
                <td className="px-6 py-3">Tampering detected. Even a single character or pixel was altered.</td>
              </tr>
              <tr>
                <td className="px-6 py-3 font-bold text-rose-600">INVALID</td>
                <td className="px-6 py-3 font-mono">Red (#dc2626)</td>
                <td className="px-6 py-3">Pages &lt; 2 or No QR detected</td>
                <td className="px-6 py-3">Document missing required authentication page or corrupted barcode.</td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
