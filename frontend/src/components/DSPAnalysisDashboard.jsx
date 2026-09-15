import React, { useState } from 'react';
import {
  AlertTriangle,
  CheckCircle2,
  Image as ImageIcon,
  MapPin,
  ShieldAlert,
  ShieldCheck,
} from 'lucide-react';
import { getFullDownloadUrl } from '../services/api';

const metricLabels = [
  ['SSIM', (result) => result.similarity?.ssim, (value) => value == null ? '—' : Number(value).toFixed(4)],
  ['MSE', (result) => result.similarity?.mse, (value) => value == null ? '—' : Number(value).toFixed(2)],
  ['PSNR', (result) => result.similarity?.psnr, (value) => value == null ? '—' : `${Number(value).toFixed(2)} dB`],
  ['FFT Similarity', (result) => result.frequency_analysis?.fft_similarity, (value) => value == null ? '—' : `${Number(value).toFixed(2)}%`],
  ['DCT Similarity', (result) => result.frequency_analysis?.dct_similarity, (value) => value == null ? '—' : `${Number(value).toFixed(2)}%`],
  ['Edge Similarity', (result) => result.edge_analysis?.edge_similarity, (value) => value == null ? '—' : `${Number(value).toFixed(2)}%`],
  ['Tampering', (result) => result.tampering?.percentage, (value) => value == null ? '—' : `${Number(value).toFixed(2)}%`],
];

const visualItems = [
  ['Original Document', 'original_image_url'],
  ['Preprocessed Image', 'preprocessed_image_url'],
  ['Edge Map', 'edge_map_url'],
  ['FFT Spectrum', 'fft_spectrum_url'],
  ['Difference Image', 'difference_image_url'],
  ['Tampering Mask', 'tampering_mask_url'],
  ['Tampering Heatmap', 'heatmap_url'],
  ['Bounding Box Result', 'bounding_box_url'],
];

function statusConfig(status) {
  const normalized = (status || '').toUpperCase();
  if (normalized === 'AUTHENTIC') {
    return {
      label: 'AUTHENTIC',
      icon: <ShieldCheck className="w-9 h-9" />,
      className: 'bg-emerald-50 border-emerald-200 text-emerald-800',
    };
  }
  if (normalized === 'SUSPICIOUS' || normalized === 'AUTHENTIC_WITH_RENDERING_DIFFERENCES') {
    return {
      label: normalized.replaceAll('_', ' '),
      icon: <AlertTriangle className="w-9 h-9" />,
      className: 'bg-amber-50 border-amber-200 text-amber-800',
    };
  }
  return {
    label: normalized || 'MODIFIED',
    icon: <ShieldAlert className="w-9 h-9" />,
    className: 'bg-rose-50 border-rose-200 text-rose-800',
  };
}

export default function DSPAnalysisDashboard({ result }) {
  const [selectedPage, setSelectedPage] = useState(0);
  if (!result?.dsp_analysis_available) {
    if (result?.dsp_analysis?.available === false) {
      return (
        <section className="mt-6 rounded-xl border border-amber-200 bg-amber-50 p-4 text-sm text-amber-800" aria-label="DSP analysis unavailable">
          <p className="font-semibold">DSP analysis was not performed</p>
          <p className="mt-1">{result.dsp_analysis.reason}</p>
        </section>
      );
    }
    return null;
  }

  const dsp = result.dsp_analysis || {};
  const authentication = result.authentication || {};
  const metrics = result.similarity || {
    ssim: dsp.ssim,
    mse: dsp.mse,
    psnr: dsp.psnr,
  };
  const frequency = result.frequency_analysis || {
    fft_similarity: dsp.fft_similarity,
    dct_similarity: dsp.dct_similarity,
  };
  const edge = result.edge_analysis || { edge_similarity: dsp.edge_similarity };
  const tampering = result.tampering || {
    detected: dsp.tampering_detected,
    percentage: dsp.tampering_percentage,
    modified_regions: dsp.modified_regions,
    modified_pages: dsp.modified_pages,
  };
  const normalizedResult = {
    ...result,
    similarity: metrics,
    frequency_analysis: frequency,
    edge_analysis: edge,
    tampering,
    pages: result.pages || dsp.pages,
    visual_results: result.visual_results || dsp.visual_results,
  };
  const status = statusConfig(authentication.status);
  const pages = normalizedResult.pages || [];
  const visualPages = normalizedResult.visual_results?.pages || [];
  const page = pages[selectedPage];
  const visualPage = visualPages[selectedPage];
  const regions = page?.tampering?.regions || [];

  return (
    <section className="mt-6 border-t border-slate-200 pt-6 space-y-6" aria-label="DSP analysis dashboard">
      <div className={`rounded-2xl border p-5 flex flex-col md:flex-row md:items-center gap-4 ${status.className}`}>
        <div className="p-3 rounded-xl bg-white/80 border border-black/5">{status.icon}</div>
        <div className="flex-1">
          <p className="text-xs font-bold uppercase tracking-wider opacity-70">Multi-layer authentication</p>
          <h3 className="text-2xl font-extrabold mt-1">{status.label}</h3>
          <p className="text-sm mt-1 opacity-80">
          SHA-256: {result.hash_analysis?.status || result.hash?.status || 'UNAVAILABLE'} · {tampering.detected ? 'Localized differences detected' : 'No localized tampering detected'}
          </p>
        </div>
        <div className="text-center md:text-right">
          <p className="text-xs font-bold uppercase tracking-wider opacity-70">Confidence</p>
          <p className="text-4xl font-black">{authentication.confidence == null ? '—' : `${Number(authentication.confidence).toFixed(1)}%`}</p>
        </div>
      </div>

      <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-4 gap-3">
        {metricLabels.map(([label, getter, formatter]) => (
          <div key={label} className="rounded-xl border border-slate-200 bg-slate-50 p-3">
            <p className="text-[11px] font-bold uppercase tracking-wide text-slate-500">{label}</p>
            <p className="mt-1 text-lg font-bold text-slate-800">{formatter(getter(normalizedResult))}</p>
          </div>
        ))}
      </div>

      {pages.length > 0 && (
        <div className="border border-slate-200 rounded-xl overflow-hidden">
          <div className="px-4 py-3 bg-slate-100/70 border-b border-slate-200 flex items-center gap-2">
            <MapPin className="w-4 h-4 text-blue-600" />
            <h4 className="text-sm font-bold text-slate-700">Page-wise analysis</h4>
          </div>
          <div className="flex overflow-x-auto border-b border-slate-200 bg-white">
            {pages.map((item, index) => (
              <button
                key={item.page || index}
                type="button"
                onClick={() => setSelectedPage(index)}
                className={`px-4 py-3 text-xs font-bold whitespace-nowrap border-b-2 transition-colors ${
                  selectedPage === index ? 'border-blue-600 text-blue-700' : 'border-transparent text-slate-500 hover:text-slate-800'
                }`}
              >
                PAGE {item.page || index + 1}
              </button>
            ))}
          </div>
          {page && (
            <div className="p-4 grid grid-cols-2 sm:grid-cols-4 gap-3 text-sm">
              <div><span className="text-slate-500 block text-xs">SSIM</span><strong>{Number(page.similarity?.ssim || 0).toFixed(4)}</strong></div>
              <div><span className="text-slate-500 block text-xs">FFT</span><strong>{Number(page.frequency?.fft_similarity || 0).toFixed(2)}%</strong></div>
              <div><span className="text-slate-500 block text-xs">Tampering</span><strong>{Number(page.tampering?.tampering_percentage || 0).toFixed(2)}%</strong></div>
              <div><span className="text-slate-500 block text-xs">Regions</span><strong>{page.tampering?.region_count || 0}</strong></div>
            </div>
          )}
        </div>
      )}

      <div className="border border-slate-200 rounded-xl overflow-hidden">
        <div className="px-4 py-3 bg-slate-100/70 border-b border-slate-200 flex items-center gap-2">
          <ImageIcon className="w-4 h-4 text-indigo-600" />
          <h4 className="text-sm font-bold text-slate-700">Visual analysis</h4>
          <span className="text-xs text-slate-400 ml-auto">Page {selectedPage + 1}</span>
        </div>
        {visualPage ? (
          <div className="p-4 grid grid-cols-1 sm:grid-cols-2 gap-4">
            {visualItems.map(([label, key]) => visualPage[key] && (
              <figure key={key} className="space-y-2">
                <figcaption className="text-xs font-semibold text-slate-600">{label}</figcaption>
                <a href={getFullDownloadUrl(visualPage[key])} target="_blank" rel="noreferrer">
                  <img
                    src={getFullDownloadUrl(visualPage[key])}
                    alt={`${label} for page ${selectedPage + 1}`}
                    className="w-full aspect-[4/3] object-contain bg-slate-100 border border-slate-200 rounded-lg"
                  />
                </a>
              </figure>
            ))}
          </div>
        ) : (
          <p className="p-5 text-sm text-slate-500">Visual analysis is unavailable for this result.</p>
        )}
      </div>

      {tampering.detected && (
        <div className="rounded-xl border border-rose-200 bg-rose-50 p-4 space-y-3">
          <div className="flex items-center gap-2 text-rose-800">
            <AlertTriangle className="w-5 h-5" />
            <h4 className="font-bold">Tampering information</h4>
          </div>
          <p className="text-sm text-rose-700">
            {tampering.modified_regions} modified region(s), {Number(tampering.percentage || 0).toFixed(2)}% of analyzed pixels.
            Modified pages: {(tampering.modified_pages || []).join(', ') || '—'}.
          </p>
          {regions.length > 0 && (
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
              {regions.map((region, index) => (
                <div key={`${region.x}-${region.y}-${index}`} className="bg-white/70 rounded-lg px-3 py-2 text-xs font-mono text-rose-800">
                  Region {index + 1}: x={region.x}, y={region.y}, w={region.width}, h={region.height}, area={Number(region.area).toFixed(0)}
                </div>
              ))}
            </div>
          )}
        </div>
      )}
    </section>
  );
}
