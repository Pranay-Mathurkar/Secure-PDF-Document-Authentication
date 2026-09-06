import React from 'react';
import { Loader2, Shield } from 'lucide-react';

export default function Loading({
  title = 'Processing Document...',
  message = 'Extracting canonical pixel bytes and executing cryptographic routines.',
  progress = null,
}) {
  return (
    <div className="bg-white border border-slate-200 rounded-xl p-8 text-center shadow-sm max-w-md mx-auto my-6">
      <div className="relative mx-auto w-16 h-16 mb-4 flex items-center justify-center">
        <Loader2 className="w-16 h-16 text-blue-600 animate-spin opacity-80" />
        <Shield className="w-6 h-6 text-blue-600 absolute" />
      </div>

      <h3 className="text-lg font-semibold text-slate-800">{title}</h3>
      <p className="text-sm text-slate-500 mt-1.5 leading-relaxed">{message}</p>

      {typeof progress === 'number' && (
        <div className="mt-5 w-full">
          <div className="flex justify-between text-xs font-mono text-slate-500 mb-1.5">
            <span>Upload Progress</span>
            <span>{progress}%</span>
          </div>
          <div className="w-full bg-slate-100 rounded-full h-2 overflow-hidden border border-slate-200">
            <div
              className="bg-gradient-to-r from-blue-600 to-indigo-600 h-2 rounded-full transition-all duration-300"
              style={{ width: `${progress}%` }}
            />
          </div>
        </div>
      )}

      <div className="mt-4 inline-flex items-center gap-1.5 px-3 py-1 bg-slate-100 rounded-full text-xs text-slate-600 font-mono">
        <span className="w-2 h-2 rounded-full bg-blue-500 animate-pulse" />
        <span>Executing PyMuPDF & SHA-256 Engine</span>
      </div>
    </div>
  );
}
