import React from 'react';
import { Check } from 'lucide-react';

export default function StepIndicator({ steps, currentStep }) {
  return (
    <div className="w-full py-4">
      <div className="flex items-center justify-between max-w-3xl mx-auto">
        {steps.map((step, index) => {
          const stepNumber = index + 1;
          const isCompleted = stepNumber < currentStep;
          const isCurrent = stepNumber === currentStep;

          return (
            <React.Fragment key={step.title}>
              {/* Step Circle & Label */}
              <div className="flex flex-col items-center flex-1 text-center">
                <div
                  className={`w-9 h-9 rounded-full flex items-center justify-center font-bold text-xs transition-all duration-200 border-2 ${
                    isCompleted
                      ? 'bg-emerald-600 border-emerald-600 text-white shadow-sm'
                      : isCurrent
                      ? 'bg-blue-600 border-blue-600 text-white ring-4 ring-blue-100 shadow-sm'
                      : 'bg-white border-slate-300 text-slate-400'
                  }`}
                >
                  {isCompleted ? <Check className="w-4 h-4 stroke-[3]" /> : stepNumber}
                </div>
                <span
                  className={`text-xs mt-2 font-medium max-w-[100px] leading-tight ${
                    isCurrent
                      ? 'text-blue-600 font-semibold'
                      : isCompleted
                      ? 'text-slate-700'
                      : 'text-slate-400'
                  }`}
                >
                  {step.title}
                </span>
              </div>

              {/* Connecting Line between steps */}
              {index < steps.length - 1 && (
                <div
                  className={`h-0.5 flex-1 -mt-5 transition-colors duration-200 ${
                    index + 1 < currentStep ? 'bg-emerald-500' : 'bg-slate-200'
                  }`}
                />
              )}
            </React.Fragment>
          );
        })}
      </div>
    </div>
  );
}
