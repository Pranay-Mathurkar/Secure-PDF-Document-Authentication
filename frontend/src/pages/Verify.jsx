import React, { useState } from 'react';
import {
  FileCheck2,
  AlertCircle,
  ShieldAlert,
  ShieldCheck,
  RefreshCw,
  Search
} from 'lucide-react';
import FileUpload from '../components/FileUpload';
import Loading from '../components/Loading';
import VerificationResult from '../components/VerificationResult';
import StepIndicator from '../components/StepIndicator';
import { verifyPdf } from '../services/api';

export default function Verify() {
  const [file, setFile] = useState(null);
  const [originalFile, setOriginalFile] = useState(null);
  const [isLoading, setIsLoading] = useState(false);
  const [uploadProgress, setUploadProgress] = useState(0);
  const [result, setResult] = useState(null);
  const [error, setError] = useState('');

  const steps = [
    { title: 'Upload Secured PDF' },
    { title: 'Decode QR Page' },
    { title: 'Rasterize Page 1' },
    { title: 'Verdict' },
  ];

  const currentStep = result ? 4 : isLoading ? 2 : file ? 1 : 1;

  const handleVerify = async (e) => {
    e.preventDefault();
    if (!file) {
      setError('Please select a secured PDF file to verify.');
      return;
    }

    setIsLoading(true);
    setError('');
    setUploadProgress(0);

    try {
      const data = await verifyPdf(file, originalFile, (progress) => {
        setUploadProgress(progress);
      });
      setResult(data);
    } catch (err) {
      console.error('Verification error:', err);
      const msg = err.response?.data?.detail || err.message || 'Verification failed.';
      setError(msg);
    } finally {
      setIsLoading(false);
    }
  };

  const handleReset = () => {
    setFile(null);
    setOriginalFile(null);
    setResult(null);
    setError('');
    setUploadProgress(0);
  };

  return (
    <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-10 space-y-8">
      {/* Page Header */}
      <div className="text-center space-y-2">
        <div className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full bg-emerald-50 text-emerald-700 text-xs font-mono border border-emerald-200">
          <FileCheck2 className="w-3.5 h-3.5" />
          <span>Phase 2: Document Verification</span>
        </div>
        <h1 className="text-2xl sm:text-3xl font-extrabold text-slate-900 tracking-tight">
          Verify Document Authenticity
        </h1>
        <p className="text-sm text-slate-500 max-w-xl mx-auto">
          Upload a secured 2-page PDF. The system extracts the stored cryptographic hash from Page 2's QR code
          and checks it against a newly calculated canonical hash of Page 1. For DSP comparison, upload the
          generated secured PDF after editing it; do not generate a new secured PDF from the edited source,
          because that creates a new reference document ID.
        </p>
      </div>

      {/* Progress Indicator */}
      <StepIndicator steps={steps} currentStep={currentStep} />

      {/* Error Alert */}
      {error && (
        <div className="bg-rose-50 border border-rose-200 text-rose-700 rounded-xl p-4 flex items-start gap-3 text-sm">
          <AlertCircle className="w-5 h-5 flex-shrink-0 text-rose-500 mt-0.5" />
          <div className="flex-1">
            <h4 className="font-semibold">Verification Request Error</h4>
            <p className="text-xs text-rose-600 mt-0.5">{error}</p>
          </div>
          <button onClick={() => setError('')} className="text-xs underline hover:text-rose-800">
            Dismiss
          </button>
        </div>
      )}

      {/* Main Content Area */}
      {!result ? (
        <div className="bg-white border border-slate-200 rounded-2xl p-6 sm:p-8 shadow-sm space-y-6">
          {isLoading ? (
            <Loading
              title="Performing Forensic Verification..."
              message="Extracting Page 2 QR code via OpenCV, re-rasterizing Page 1 at 150 DPI, and performing constant-time digest comparison."
              progress={uploadProgress}
            />
          ) : (
            <form onSubmit={handleVerify} className="space-y-6">
              <FileUpload
                selectedFile={file}
                onFileSelect={(selected) => {
                  setFile(selected);
                  setError('');
                }}
                title="Select Secured 2-Page PDF Document"
                description="Upload the document generated through the securing phase."
                helperText="Must contain at least 2 pages (Protected content + QR Authentication page)"
              />

              <div className="border-t border-slate-200 pt-5">
                <FileUpload
                  selectedFile={originalFile}
                  onFileSelect={(selected) => {
                    setOriginalFile(selected);
                    setError('');
                  }}
                  title="Optional: Select Original PDF for DSP Analysis"
                  description="Add the unmodified source to compare structure, frequency, edges, and tampering."
                  helperText="Leave empty to use the existing SHA-256 and QR verification workflow"
                  inputId="original-pdf-file-input"
                />
              </div>

              <div className="flex items-center justify-between pt-2">
                <div className="text-xs text-slate-500">
                  <span className="font-semibold text-slate-700">Checks:</span> Page Count &ge; 2, QR Code Decoding, SHA-256 Digest Match
                </div>

                <button
                  type="submit"
                  disabled={!file}
                  className={`px-6 py-3 rounded-xl font-semibold text-sm flex items-center gap-2 shadow-sm transition-all ${
                    file
                      ? 'bg-emerald-600 hover:bg-emerald-500 text-white shadow-emerald-600/20'
                      : 'bg-slate-200 text-slate-400 cursor-not-allowed'
                  }`}
                >
                  <Search className="w-4 h-4" />
                  <span>{originalFile ? 'Verify with DSP Analysis' : 'Verify Authenticity'}</span>
                </button>
              </div>
            </form>
          )}
        </div>
      ) : (
        <VerificationResult result={result} onReset={handleReset} />
      )}
    </div>
  );
}
