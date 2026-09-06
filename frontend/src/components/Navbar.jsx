import React, { useState, useEffect } from 'react';
import { NavLink } from 'react-router-dom';
import { ShieldCheck, ShieldAlert, FileText, CheckCircle2, Menu, X, Info } from 'lucide-react';
import { checkHealth } from '../services/api';

export default function Navbar() {
  const [isOpen, setIsOpen] = useState(false);
  const [apiOnline, setApiOnline] = useState(null);

  useEffect(() => {
    let isMounted = true;
    const verifyApi = async () => {
      try {
        await checkHealth();
        if (isMounted) setApiOnline(true);
      } catch (err) {
        if (isMounted) setApiOnline(false);
      }
    };
    verifyApi();
    const interval = setInterval(verifyApi, 25000);
    return () => {
      isMounted = false;
      clearInterval(interval);
    };
  }, []);

  const navLinks = [
    { name: 'Home', path: '/' },
    { name: 'Generate Secure PDF', path: '/generate' },
    { name: 'Verify Document', path: '/verify' },
    { name: 'About Project', path: '/about' },
  ];

  return (
    <nav className="bg-[#0f172a] text-white border-b border-slate-800 sticky top-0 z-50 shadow-md">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between h-16">
          {/* Brand Logo & Title */}
          <NavLink to="/" className="flex items-center space-x-3 group">
            <div className="p-2 bg-gradient-to-br from-blue-600 to-indigo-600 rounded-lg shadow-inner group-hover:scale-105 transition-transform">
              <ShieldCheck className="w-6 h-6 text-white" />
            </div>
            <div>
              <div className="font-bold text-lg tracking-tight flex items-center gap-1.5 text-white">
                <span>DocAuth</span>
                <span className="text-xs uppercase px-2 py-0.5 font-mono bg-blue-500/20 text-blue-300 border border-blue-400/30 rounded">
                  SHA-256
                </span>
              </div>
              <p className="text-[11px] text-slate-400 font-medium hidden sm:block">
                Cryptographic PDF Authentication
              </p>
            </div>
          </NavLink>

          {/* Desktop Navigation Links */}
          <div className="hidden md:flex items-center space-x-1">
            {navLinks.map((link) => (
              <NavLink
                key={link.path}
                to={link.path}
                className={({ isActive }) =>
                  `px-3.5 py-2 rounded-md text-sm font-medium transition-colors ${
                    isActive
                      ? 'bg-blue-600 text-white shadow-sm'
                      : 'text-slate-300 hover:text-white hover:bg-slate-800/80'
                  }`
                }
              >
                {link.name}
              </NavLink>
            ))}
          </div>

          {/* Backend Health Badge & Mobile Toggle */}
          <div className="flex items-center space-x-3">
            <div
              className={`hidden sm:flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-mono border ${
                apiOnline === true
                  ? 'bg-emerald-950/60 text-emerald-400 border-emerald-700/50'
                  : apiOnline === false
                  ? 'bg-rose-950/60 text-rose-400 border-rose-700/50'
                  : 'bg-slate-800 text-slate-400 border-slate-700'
              }`}
              title={apiOnline ? 'FastAPI Backend is reachable' : 'Backend connection unavailable'}
            >
              <span
                className={`w-2 h-2 rounded-full ${
                  apiOnline === true
                    ? 'bg-emerald-400 animate-pulse'
                    : apiOnline === false
                    ? 'bg-rose-400'
                    : 'bg-slate-500'
                }`}
              />
              <span>{apiOnline === true ? 'Backend Online' : apiOnline === false ? 'API Offline' : 'Connecting...'}</span>
            </div>

            {/* Mobile menu button */}
            <button
              onClick={() => setIsOpen(!isOpen)}
              className="md:hidden p-2 rounded-md text-slate-400 hover:text-white hover:bg-slate-800 focus:outline-none"
              aria-label="Toggle navigation menu"
            >
              {isOpen ? <X className="w-6 h-6" /> : <Menu className="w-6 h-6 text-white" />}
            </button>
          </div>
        </div>
      </div>

      {/* Mobile Drawer */}
      {isOpen && (
        <div className="md:hidden bg-[#0a0f1d] border-b border-slate-800 px-4 pt-2 pb-4 space-y-1">
          {navLinks.map((link) => (
            <NavLink
              key={link.path}
              to={link.path}
              onClick={() => setIsOpen(false)}
              className={({ isActive }) =>
                `block px-3 py-2 rounded-md text-base font-medium ${
                  isActive
                    ? 'bg-blue-600 text-white'
                    : 'text-slate-300 hover:text-white hover:bg-slate-800'
                }`
              }
            >
              {link.name}
            </NavLink>
          ))}
          <div className="pt-2 border-t border-slate-800/80 flex items-center justify-between text-xs text-slate-400 px-3 py-2">
            <span>FastAPI Server Status:</span>
            <span className={apiOnline ? 'text-emerald-400 font-semibold' : 'text-rose-400 font-semibold'}>
              {apiOnline ? 'Operational (Port 8000)' : 'Not Connected'}
            </span>
          </div>
        </div>
      )}
    </nav>
  );
}
