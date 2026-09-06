import React, { useState } from 'react';
import {
  ShieldCheck,
  ShieldAlert,
  AlertOctagon,
  Copy,
  Check,
  Calendar,
  FileText,
  Hash,
  Binary,
  Layers
} from 'lucide-react';

export default function VerificationResult({ result, onReset }) {
  const [copiedField, setCopiedField] = useState(null);

  if (!result) return null;

  // Determine status categorization: AUTHENTIC, MODIFIED, or INVALID
  const statusUpper = (result.status_text || '').toUpperCase();
  let statusType = 'INVALID';

  if (result.is_authentic || statusUpper.includes('AUTHENTIC')) {
    statusType = 'AUTHENTIC';
  } else if (statusUpper.includes('MODIFIED')) {
    statusType = 'MODIFIED';
  } else {
    statusType = 'INVALID';
  }

  const copyToClipboard = (text, fieldName) => {
    if (!text) return;
    navigator.clipboard.writeText(text);
    setCopiedField(fieldName);
    setTimeout(() => setCopiedField(null), 2000);
  };

  // Status configuration mapping
  const statusStyles = {
    AUTHENTIC: {
      badgeBg: 'bg-emerald-50 border-emerald-300 text-emerald-800',
      icon: <ShieldCheck className="w-10 h-10 text-emerald-600" />,
      title: 'AUTHENTIC DOCUMENT',
      subtitle: 'The document integrity is verified. Cryptographic hash matches the QR code seal.',
      accentBorder: 'border-emerald-500',
      tagColor: 'bg-emerald-600 text-white',
    },
    MODIFIED: {
      badgeBg: 'bg-orange-50 border-orange-300 text-orange-800',
      icon: <ShieldAlert className="w-10 h-10 text-orange-600" />,
      title: 'DOCUMENT HAS BEEN MODIFIED',
      subtitle: 'Tampering detected! The calculated first-page hash does NOT match the stored QR code.',
      accentBorder: 'border-orange-500',
      tagColor: 'bg-orange-600 text-white',
    },
    INVALID: {
      badgeBg: 'bg-rose-50 border-rose-300 text-rose-800',
      icon: <AlertOctagon className="w-10 h-10 text-rose-600" />,
      title: 'INVALID DOCUMENT',
      subtitle: result.details || 'The document does not meet verification specifications (e.g. missing QR page or less than 2 pages).',
      accentBorder: 'border-rose-500',
      tagColor: 'bg-rose-600 text-white',
    },
  };

  const currentTheme = statusStyles[statusType] || statusStyles.INVALID;

  return (
    <div className="bg-white border border-slate-200 rounded-2xl shadow-md overflow-hidden">
      {/* Top Banner with Verdict */}
      <div className={`p-6 border-b ${currentTheme.badgeBg} flex flex-col sm:flex-row items-center sm:items-start gap-4`}>
        <div className="p-3 bg-white/80 rounded-2xl shadow-sm border border-black/5 flex-shrink-0">
          {currentTheme.icon}
        </div>
        <div className="text-center sm:text-left flex-1">
          <div className="flex flex-wrap items-center justify-center sm:justify-start gap-2 mb-1">
            <span className={`px-2.5 py-0.5 rounded text-xs font-bold uppercase tracking-wide ${currentTheme.tagColor}`}>
              Status: {statusType}
            </span>
            <span className="text-xs text-slate-500 font-mono">Algorithm: SHA-256</span>
          </div>
          <h2 className="text-2xl font-extrabold tracking-tight text-slate-900">
            {currentTheme.title}
          </h2>
          <p className="text-sm text-slate-600 mt-1 max-w-2xl leading-relaxed">
            {currentTheme.subtitle}
          </p>
        </div>
      </div>

      {/* Forensic Hash Comparison Section */}
      <div className="p-6 space-y-6">
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
          {/* Original Hash (from QR) */}
          <div className="bg-slate-50 border border-slate-200 rounded-xl p-4">
            <div className="flex items-center justify-between mb-2">
              <span className="text-xs font-bold uppercase tracking-wider text-slate-500 flex items-center gap-1.5">
                <Binary className="w-4 h-4 text-blue-600" /> Stored Hash (From QR Code)
              </span>
              {result.original_hash && (
                <button
                  onClick={() => copyToClipboard(result.original_hash, 'original')}
                  className="text-xs text-slate-500 hover:text-blue-600 flex items-center gap-1 transition-colors"
                  title="Copy hash"
                >
                  {copiedField === 'original' ? <Check className="w-3.5 h-3.5 text-emerald-600" /> : <Copy className="w-3.5 h-3.5" />}
                  <span>{copiedField === 'original' ? 'Copied' : 'Copy'}</span>
                </button>
              )}
            </div>
            <div className="bg-white border border-slate-200 rounded-lg p-3 font-mono text-xs text-slate-800 break-all select-all shadow-inner">
              {result.original_hash || <span className="text-slate-400 italic">No QR code payload extracted</span>}
            </div>
          </div>

          {/* Calculated Hash (recomputed from Page 1) */}
          <div className="bg-slate-50 border border-slate-200 rounded-xl p-4">
            <div className="flex items-center justify-between mb-2">
              <span className="text-xs font-bold uppercase tracking-wider text-slate-500 flex items-center gap-1.5">
                <Hash className="w-4 h-4 text-indigo-600" /> Calculated Hash (Page 1 Raster)
              </span>
              {result.calculated_hash && (
                <button
                  onClick={() => copyToClipboard(result.calculated_hash, 'calculated')}
                  className="text-xs text-slate-500 hover:text-indigo-600 flex items-center gap-1 transition-colors"
                  title="Copy hash"
                >
                  {copiedField === 'calculated' ? <Check className="w-3.5 h-3.5 text-emerald-600" /> : <Copy className="w-3.5 h-3.5" />}
                  <span>{copiedField === 'calculated' ? 'Copied' : 'Copy'}</span>
                </button>
              )}
            </div>
            <div className="bg-white border border-slate-200 rounded-lg p-3 font-mono text-xs text-slate-800 break-all select-all shadow-inner">
              {result.calculated_hash || <span className="text-slate-400 italic">Could not calculate Page 1 hash</span>}
            </div>
          </div>
        </div>

        {/* Metadata Details Table */}
        <div className="border border-slate-200 rounded-xl overflow-hidden">
          <div className="bg-slate-100/70 px-4 py-2.5 border-b border-slate-200 text-xs font-semibold text-slate-700">
            Document Verification Telemetry
          </div>
          <div className="divide-y divide-slate-100 text-xs text-slate-600">
            <div className="px-4 py-2.5 flex items-center justify-between">
              <span className="font-medium text-slate-500 flex items-center gap-1.5">
                <FileText className="w-3.5 h-3.5 text-slate-400" /> File Name
              </span>
              <span className="font-mono text-slate-800 font-semibold">{result.file_name}</span>
            </div>
            <div className="px-4 py-2.5 flex items-center justify-between">
              <span className="font-medium text-slate-500 flex items-center gap-1.5">
                <Calendar className="w-3.5 h-3.5 text-slate-400" /> Verification Timestamp
              </span>
              <span className="font-mono text-slate-700">{result.verification_timestamp || new Date().toISOString()}</span>
            </div>
            <div className="px-4 py-2.5 flex items-center justify-between">
              <span className="font-medium text-slate-500 flex items-center gap-1.5">
                <Layers className="w-3.5 h-3.5 text-slate-400" /> Document Page Count
              </span>
              <span className="font-mono text-slate-700">{result.page_count ?? 'N/A'} pages</span>
            </div>
            {result.details && (
              <div className="px-4 py-2.5 flex items-start justify-between gap-4">
                <span className="font-medium text-slate-500">Diagnostics</span>
                <span className="text-right text-slate-700">{result.details}</span>
              </div>
            )}
          </div>
        </div>

        {/* Action Button */}
        {onReset && (
          <div className="flex justify-end pt-2">
            <button
              onClick={onReset}
              className="px-5 py-2.5 bg-slate-800 hover:bg-slate-900 text-white rounded-xl text-sm font-medium transition-colors shadow-sm"
            >
              Verify Another Document
            </button>
          </div>
        )}
      </div>
    </div>
  );
}
