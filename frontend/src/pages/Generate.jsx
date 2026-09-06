import React, { useState } from 'react';
import { Link } from 'react-router-dom';
import {
  Lock,
  Download,
  CheckCircle2,
  AlertCircle,
  Copy,
  Check,
  FileText,
  Calendar,
  ShieldCheck,
  ArrowRight,
  RefreshCw,
  QrCode
} from 'lucide-react';
import FileUpload from '../components/FileUpload';
import Loading from '../components/Loading';
import StepIndicator from '../components/StepIndicator';
import { generateSecurePdf, getFullDownloadUrl } from '../services/api';

export default function Generate() {
  const [file, setFile] = useState(null);
  const [isLoading, setIsLoading] = useState(false);
  const [uploadProgress, setUploadProgress] = useState(0);
  const [result, setResult] = useState(null);
  const [error, setError] = useState('');
  const [copiedHash, setCopiedHash] = useState(false);

  const steps = [
    { title: 'Upload PDF' },
    { title: 'Canonical Hash' },
    { title: 'Embed QR Page' },
    { title: 'Download Ready' },
  ];

  const currentStep = result ? 4 : isLoading ? 2 : file ? 1 : 1;

  const handleGenerate = async (e) => {
    e.preventDefault();
    if (!file) {
      setError('Please select a PDF file first.');
      return;
    }

    setIsLoading(true);
    setError('');
    setUploadProgress(0);

    try {
      const data = await generateSecurePdf(file, (progress) => {
        setUploadProgress(progress);
      });
      setResult(data);
    } catch (err) {
      console.error('Generation error:', err);
      const msg = err.response?.data?.detail || err.message || 'Failed to generate secure PDF.';
      setError(msg);
    } finally {
      setIsLoading(false);
    }
  };

  const handleReset = () => {
    setFile(null);
    setResult(null);
    setError('');
    setUploadProgress(0);
  };

  const copyHash = () => {
    if (result?.sha256_hash) {
      navigator.clipboard.writeText(result.sha256_hash);
      setCopiedHash(true);
      setTimeout(() => setCopiedHash(false), 2000);
    }
  };

  return (
    <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-10 space-y-8">
      {/* Page Header */}
      <div className="text-center space-y-2">
        <div className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full bg-blue-50 text-blue-700 text-xs font-mono border border-blue-200">
          <Lock className="w-3.5 h-3.5" />
          <span>Phase 1: Document Securing</span>
        </div>
        <h1 className="text-2xl sm:text-3xl font-extrabold text-slate-900 tracking-tight">
          Generate Secure Authenticated PDF
        </h1>
        <p className="text-sm text-slate-500 max-w-xl mx-auto">
          Upload any PDF. The first page is isolated, deterministically rasterized, hashed with SHA-256,
          and appended with an immutable QR authentication page.
        </p>
      </div>

      {/* Progress Indicator */}
      <StepIndicator steps={steps} currentStep={currentStep} />

      {/* Error Alert */}
      {error && (
        <div className="bg-rose-50 border border-rose-200 text-rose-700 rounded-xl p-4 flex items-start gap-3 text-sm">
          <AlertCircle className="w-5 h-5 flex-shrink-0 text-rose-500 mt-0.5" />
          <div className="flex-1">
            <h4 className="font-semibold">Generation Failed</h4>
            <p className="text-xs text-rose-600 mt-0.5">{error}</p>
          </div>
          <button onClick={() => setError('')} className="text-xs underline hover:text-rose-800">
            Dismiss
          </button>
        </div>
      )}

      {/* Form / Processing / Result View */}
      {!result ? (
        <div className="bg-white border border-slate-200 rounded-2xl p-6 sm:p-8 shadow-sm space-y-6">
          {isLoading ? (
            <Loading
              title="Generating Cryptographic Seal..."
              message="Extracting Page 1, rendering 150 DPI raw RGB buffer, computing SHA-256 digest, and compiling the 2-page authenticated PDF."
              progress={uploadProgress}
            />
          ) : (
            <form onSubmit={handleGenerate} className="space-y-6">
              <FileUpload
                selectedFile={file}
                onFileSelect={(selected) => {
                  setFile(selected);
                  setError('');
                }}
                title="Select Original PDF Document"
                description="Upload the document whose first page needs cryptographic protection."
              />

              <div className="flex items-center justify-between pt-2">
                <div className="text-xs text-slate-500">
                  <span className="font-semibold text-slate-700">Output:</span> Secured 2-Page Document (Page 1 + Authentication QR Page)
                </div>

                <button
                  type="submit"
                  disabled={!file}
                  className={`px-6 py-3 rounded-xl font-semibold text-sm flex items-center gap-2 shadow-sm transition-all ${
                    file
                      ? 'bg-blue-600 hover:bg-blue-500 text-white shadow-blue-600/20'
                      : 'bg-slate-200 text-slate-400 cursor-not-allowed'
                  }`}
                >
                  <Lock className="w-4 h-4" />
                  <span>Generate Secured PDF</span>
                </button>
              </div>
            </form>
          )}
        </div>
      ) : (
        /* Result Card */
        <div className="bg-white border border-slate-200 rounded-2xl shadow-md overflow-hidden space-y-0">
          {/* Header Banner */}
          <div className="bg-gradient-to-r from-emerald-500 to-teal-600 text-white p-6 flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="p-2.5 bg-white/20 rounded-xl">
                <ShieldCheck className="w-7 h-7 text-white" />
              </div>
              <div>
                <h3 className="text-lg font-bold">Document Secured Successfully!</h3>
                <p className="text-xs text-emerald-100 mt-0.5">
                  The document has been sealed with an immutable SHA-256 cryptographic QR code.
                </p>
              </div>
            </div>
            <span className="hidden sm:inline-block px-3 py-1 bg-white/20 text-white text-xs font-mono font-bold rounded-full">
              2-Page PDF Generated
            </span>
          </div>

          <div className="p-6 sm:p-8 space-y-6">
            {/* Hash Display */}
            <div className="bg-slate-50 border border-slate-200 rounded-xl p-4">
              <div className="flex items-center justify-between mb-2">
                <span className="text-xs font-bold uppercase tracking-wider text-slate-500 flex items-center gap-1.5">
                  <Lock className="w-4 h-4 text-blue-600" /> Embedded SHA-256 Digest
                </span>
                <button
                  onClick={copyHash}
                  className="text-xs text-slate-500 hover:text-blue-600 flex items-center gap-1 transition-colors"
                >
                  {copiedHash ? <Check className="w-3.5 h-3.5 text-emerald-600" /> : <Copy className="w-3.5 h-3.5" />}
                  <span>{copiedHash ? 'Copied' : 'Copy Hash'}</span>
                </button>
              </div>
              <div className="bg-white border border-slate-200 rounded-lg p-3 font-mono text-xs text-slate-800 break-all select-all shadow-inner">
                {result.sha256_hash}
              </div>
            </div>

            {/* Document Telemetry */}
            <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 text-xs">
              <div className="bg-slate-50 border border-slate-200 rounded-xl p-3">
                <span className="text-slate-400 font-medium block">File Name</span>
                <span className="font-semibold text-slate-800 font-mono truncate block mt-0.5" title={result.file_name}>
                  {result.file_name}
                </span>
              </div>
              <div className="bg-slate-50 border border-slate-200 rounded-xl p-3">
                <span className="text-slate-400 font-medium block">Algorithm</span>
                <span className="font-semibold text-slate-800 font-mono block mt-0.5">
                  {result.algorithm || 'SHA-256'} (150 DPI RGB)
                </span>
              </div>
              <div className="bg-slate-50 border border-slate-200 rounded-xl p-3">
                <span className="text-slate-400 font-medium block">Securing Timestamp</span>
                <span className="font-semibold text-slate-800 font-mono block mt-0.5">
                  {result.timestamp || new Date().toISOString()}
                </span>
              </div>
            </div>

            {/* Primary Action Buttons */}
            <div className="pt-2 flex flex-col sm:flex-row items-center justify-between gap-4 border-t border-slate-100">
              <button
                onClick={handleReset}
                className="w-full sm:w-auto px-4 py-2.5 text-slate-600 hover:text-slate-900 text-xs font-semibold flex items-center justify-center gap-1.5 transition-colors"
              >
                <RefreshCw className="w-4 h-4" />
                <span>Secure Another Document</span>
              </button>

              <div className="flex items-center gap-3 w-full sm:w-auto">
                <Link
                  to="/verify"
                  className="w-full sm:w-auto px-4 py-2.5 bg-slate-100 hover:bg-slate-200 text-slate-800 rounded-xl text-xs font-semibold flex items-center justify-center gap-1.5 transition-colors"
                >
                  <span>Verify This PDF</span>
                  <ArrowRight className="w-3.5 h-3.5" />
                </Link>

                <a
                  href={getFullDownloadUrl(result.download_url)}
                  download={result.file_name}
                  className="w-full sm:w-auto px-6 py-2.5 bg-blue-600 hover:bg-blue-500 text-white rounded-xl text-xs font-semibold flex items-center justify-center gap-2 shadow-md shadow-blue-600/20 transition-all"
                >
                  <Download className="w-4 h-4" />
                  <span>Download Secured PDF</span>
                </a>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
