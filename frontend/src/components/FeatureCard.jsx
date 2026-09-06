import React from 'react';

export default function FeatureCard({ icon: Icon, title, description, badge, tagColor = 'blue' }) {
  const tagColorMap = {
    blue: 'bg-blue-50 text-blue-700 border-blue-200',
    purple: 'bg-purple-50 text-purple-700 border-purple-200',
    emerald: 'bg-emerald-50 text-emerald-700 border-emerald-200',
    amber: 'bg-amber-50 text-amber-700 border-amber-200',
  };

  return (
    <div className="bg-white border border-slate-200/90 rounded-2xl p-6 shadow-sm hover:shadow-md transition-shadow duration-200 flex flex-col justify-between">
      <div>
        <div className="flex items-center justify-between mb-4">
          <div className="w-12 h-12 rounded-xl bg-gradient-to-br from-blue-500/10 to-indigo-500/10 border border-blue-100 flex items-center justify-center text-blue-600">
            {Icon && <Icon className="w-6 h-6" />}
          </div>
          {badge && (
            <span className={`text-[11px] font-mono font-medium px-2.5 py-0.5 rounded-full border ${tagColorMap[tagColor] || tagColorMap.blue}`}>
              {badge}
            </span>
          )}
        </div>
        <h3 className="text-base font-bold text-slate-800 mb-2">{title}</h3>
        <p className="text-sm text-slate-600 leading-relaxed">{description}</p>
      </div>
    </div>
  );
}
