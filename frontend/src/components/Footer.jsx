import React from 'react';
import { Shield, Code, Cpu } from 'lucide-react';

export default function Footer() {
  return (
    <footer className="bg-[#0a0f1d] text-slate-400 border-t border-slate-800/80 py-8 mt-auto">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex flex-col md:flex-row items-center justify-between gap-4">
          <div>
            <div className="flex items-center space-x-2 text-slate-200 font-semibold">
              <Shield className="w-5 h-5 text-blue-500" />
              <span>Secure PDF Document Authentication System</span>
            </div>
            <p className="text-xs text-slate-500 mt-1 max-w-xl">
              Academic Project: Cryptographic verification of PDF documents using deterministic canonical SHA-256 pixel rasterization and high-density 2D QR encoding.
            </p>
          </div>

          <div className="flex flex-wrap items-center gap-4 text-xs font-mono text-slate-400">
            <span className="flex items-center gap-1">
              <Cpu className="w-3.5 h-3.5 text-indigo-400" /> FastAPI + PyMuPDF
            </span>
            <span className="text-slate-600">•</span>
            <span className="flex items-center gap-1">
              <Code className="w-3.5 h-3.5 text-blue-400" /> React 18 + Vite + Tailwind
            </span>
            <span className="text-slate-600">•</span>
            <span>Final Year Engineering Project</span>
          </div>
        </div>

        <div className="mt-6 pt-4 border-t border-slate-800/50 flex flex-col sm:flex-row items-center justify-between text-xs text-slate-500">
          <span>&copy; 2026 Academic Document Security Project. All rights reserved.</span>
          <span className="mt-2 sm:mt-0">Decoupled Zero-Knowledge Verification Architecture</span>
        </div>
      </div>
    </footer>
  );
}
