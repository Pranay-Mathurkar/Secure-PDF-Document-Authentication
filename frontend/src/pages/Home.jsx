import React from 'react';
import { Link } from 'react-router-dom';
import {
  ShieldCheck,
  FileCheck2,
  Lock,
  QrCode,
  Layers,
  ArrowRight,
  Fingerprint,
  Cpu,
  FileSearch,
  Sparkles
} from 'lucide-react';
import FeatureCard from '../components/FeatureCard';

export default function Home() {
  const steps = [
    {
      number: '01',
      title: 'Canonical Page Isolation',
      desc: 'Decouples first-page visual presentation from binary PDF metadata and xref tables.',
      icon: Layers,
    },
    {
      number: '02',
      title: 'SHA-256 Pixel Hashing',
      desc: 'Renders raw RGB pixel buffers at 150 DPI to generate an immutable cryptographic digest.',
      icon: Fingerprint,
    },
    {
      number: '03',
      title: 'High-Density QR Embedding',
      desc: 'Encodes the cryptographic digest with Error Correction Level H into an appended authentication page.',
      icon: QrCode,
    },
    {
      number: '04',
      title: 'Zero-Knowledge Verification',
      desc: 'Authenticates any secured document in seconds without relying on a centralized database.',
      icon: FileSearch,
    },
  ];

  return (
    <div className="space-y-16 pb-16">
      {/* Hero Section */}
      <section className="relative overflow-hidden bg-gradient-to-b from-[#0f172a] via-[#1e293b] to-[#0f172a] text-white pt-16 pb-20 px-4 sm:px-6 lg:px-8 border-b border-slate-800">
        <div className="max-w-5xl mx-auto text-center relative z-10 space-y-6">
          <div className="inline-flex items-center gap-2 px-3.5 py-1.5 rounded-full bg-blue-500/10 border border-blue-400/30 text-blue-300 text-xs font-mono">
            <Sparkles className="w-3.5 h-3.5 text-blue-400" />
            <span>Academic Final-Year Engineering Project</span>
          </div>

          <h1 className="text-3xl sm:text-5xl font-extrabold tracking-tight text-white leading-tight">
            Secure PDF Document Authentication Using{' '}
            <span className="bg-gradient-to-r from-blue-400 via-indigo-300 to-purple-400 bg-clip-text text-transparent">
              Cryptographic Hashing &amp; QR Codes
            </span>
          </h1>

          <p className="max-w-2xl mx-auto text-slate-300 text-base sm:text-lg leading-relaxed">
            A tamper-proof document security platform solving full-binary hash mutation through
            deterministic canonical page rasterization, cryptographic SHA-256 digests, and embedded 2D QR validation.
          </p>

          {/* Action CTAs */}
          <div className="flex flex-col sm:flex-row items-center justify-center gap-4 pt-4">
            <Link
              to="/generate"
              className="w-full sm:w-auto px-6 py-3.5 rounded-xl bg-blue-600 hover:bg-blue-500 text-white font-semibold text-sm shadow-lg shadow-blue-600/30 hover:shadow-blue-600/50 transition-all flex items-center justify-center gap-2 group"
            >
              <Lock className="w-4 h-4" />
              <span>Generate Secure PDF</span>
              <ArrowRight className="w-4 h-4 group-hover:translate-x-0.5 transition-transform" />
            </Link>

            <Link
              to="/verify"
              className="w-full sm:w-auto px-6 py-3.5 rounded-xl bg-slate-800 hover:bg-slate-700 border border-slate-700 text-slate-100 font-semibold text-sm transition-colors flex items-center justify-center gap-2"
            >
              <FileCheck2 className="w-4 h-4 text-emerald-400" />
              <span>Verify Document Authenticity</span>
            </Link>
          </div>
        </div>

        {/* Subtle Background Glow Elements */}
        <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[600px] h-[300px] bg-blue-500/10 rounded-full blur-3xl pointer-events-none" />
      </section>

      {/* Workflow Process Steps */}
      <section className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="text-center max-w-2xl mx-auto mb-12">
          <h2 className="text-xs font-mono uppercase tracking-widest text-blue-600 font-bold mb-2">
            Deterministic Pipeline
          </h2>
          <h3 className="text-2xl sm:text-3xl font-bold text-slate-900 tracking-tight">
            How the Authentication Engine Works
          </h3>
          <p className="text-sm text-slate-500 mt-2">
            Overcoming PDF metadata mutability through reproducible rasterization.
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
          {steps.map((step) => {
            const Icon = step.icon;
            return (
              <div
                key={step.number}
                className="bg-white border border-slate-200 rounded-2xl p-6 shadow-sm hover:shadow-md transition-shadow relative"
              >
                <div className="text-3xl font-extrabold font-mono text-slate-200 mb-3">
                  {step.number}
                </div>
                <div className="w-10 h-10 rounded-xl bg-blue-50 text-blue-600 flex items-center justify-center mb-3">
                  <Icon className="w-5 h-5" />
                </div>
                <h4 className="text-base font-bold text-slate-800 mb-1.5">{step.title}</h4>
                <p className="text-xs text-slate-500 leading-relaxed">{step.desc}</p>
              </div>
            );
          })}
        </div>
      </section>

      {/* Architecture Highlights Grid */}
      <section className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="text-center max-w-2xl mx-auto mb-12">
          <h2 className="text-xs font-mono uppercase tracking-widest text-indigo-600 font-bold mb-2">
            Engineering Rigor
          </h2>
          <h3 className="text-2xl sm:text-3xl font-bold text-slate-900 tracking-tight">
            Key Architectural Advantages
          </h3>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          <FeatureCard
            icon={Fingerprint}
            title="Deterministic Canonical Hashing"
            description="Eliminates the file-trailer modification paradox by hashing raw 150 DPI RGB pixel buffers rather than the entire PDF binary stream."
            badge="SHA-256 Engine"
            tagColor="blue"
          />
          <FeatureCard
            icon={QrCode}
            title="Self-Contained Verification"
            description="The document carries its own cryptographic seal on an appended page. No external database lookup is required for instant authenticity checks."
            badge="Level H Error Correction"
            tagColor="purple"
          />
          <FeatureCard
            icon={Cpu}
            title="Computer Vision QR Extraction"
            description="Uses OpenCV QRCodeDetector on high-resolution rasterized second pages to guarantee zero-loss string recovery even with document noise."
            badge="OpenCV + PyMuPDF"
            tagColor="emerald"
          />
        </div>
      </section>

      {/* Quick Launch Banner */}
      <section className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="bg-gradient-to-r from-[#0f172a] to-[#1e3a8a] text-white rounded-3xl p-8 sm:p-12 shadow-xl flex flex-col md:flex-row items-center justify-between gap-8">
          <div className="space-y-3 text-center md:text-left">
            <h3 className="text-2xl sm:text-3xl font-bold tracking-tight">
              Ready to secure or verify a PDF document?
            </h3>
            <p className="text-slate-300 text-sm max-w-xl leading-relaxed">
              Upload any single or multi-page PDF document to test the cryptographic pipeline and download a verified 2-page protected copy.
            </p>
          </div>
          <div className="flex flex-wrap gap-4 justify-center">
            <Link
              to="/generate"
              className="px-6 py-3 bg-white text-slate-900 hover:bg-slate-100 font-semibold rounded-xl text-sm transition-colors shadow-md"
            >
              Start Securing
            </Link>
            <Link
              to="/verify"
              className="px-6 py-3 bg-blue-500 hover:bg-blue-400 text-white font-semibold rounded-xl text-sm transition-colors"
            >
              Open Verifier
            </Link>
          </div>
        </div>
      </section>
    </div>
  );
}
