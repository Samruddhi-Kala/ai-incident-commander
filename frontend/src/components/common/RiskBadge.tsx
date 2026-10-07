import React from 'react';
import { RiskLevel } from '../../types/remediation';

export interface RiskBadgeProps {
  risk: RiskLevel | string;
}

export const RiskBadge: React.FC<RiskBadgeProps> = ({ risk }) => {
  const norm = risk?.toUpperCase() || 'HIGH';

  let style = 'bg-slate-800 text-slate-300 border-slate-700';

  if (norm === 'HIGH') {
    style = 'bg-red-950/80 text-red-300 border-red-800';
  } else if (norm === 'MEDIUM') {
    style = 'bg-amber-950/80 text-amber-300 border-amber-800';
  } else if (norm === 'LOW') {
    style = 'bg-emerald-950/80 text-emerald-300 border-emerald-800';
  }

  return (
    <span
      className={`inline-flex items-center gap-1.5 px-2 py-0.5 rounded text-xs font-mono font-medium border uppercase tracking-wider ${style}`}
      data-testid="risk-badge"
    >
      <span className="w-1.5 h-1.5 rounded-full bg-current" />
      {norm} RISK
    </span>
  );
};
