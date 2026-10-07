import React from 'react';

export interface ConfidenceMeterProps {
  confidence?: number | null;
  label?: string;
}

export const ConfidenceMeter: React.FC<ConfidenceMeterProps> = ({
  confidence,
  label = 'Root Cause Confidence',
}) => {
  if (confidence === undefined || confidence === null) {
    return (
      <div className="flex flex-col gap-1" data-testid="confidence-meter">
        <span className="text-xs font-mono text-slate-400">{label}</span>
        <span className="text-sm font-mono text-slate-500">Unassessed</span>
      </div>
    );
  }

  const pct = Math.round(confidence * 100);

  let barColor = 'bg-slate-500';
  let textColor = 'text-slate-400';

  if (confidence >= 0.75) {
    barColor = 'bg-emerald-500';
    textColor = 'text-emerald-400';
  } else if (confidence >= 0.4) {
    barColor = 'bg-amber-500';
    textColor = 'text-amber-400';
  } else {
    barColor = 'bg-rose-500';
    textColor = 'text-rose-400';
  }

  return (
    <div className="flex flex-col gap-1.5" data-testid="confidence-meter">
      <div className="flex items-center justify-between gap-4">
        <span className="text-xs font-mono tracking-wide text-slate-400">{label}</span>
        <span className={`text-sm font-mono font-semibold ${textColor}`}>{pct}%</span>
      </div>
      <div className="w-full bg-slate-800 rounded-full h-2 overflow-hidden border border-slate-700">
        <div
          className={`h-full rounded-full transition-all duration-500 ${barColor}`}
          style={{ width: `${Math.min(100, Math.max(0, pct))}%` }}
        />
      </div>
    </div>
  );
};
