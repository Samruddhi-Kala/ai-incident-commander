import React from 'react';
import { Severity } from '../../types/incident';

export interface SeverityBadgeProps {
  severity: Severity | string;
  size?: 'sm' | 'md';
}

export const SeverityBadge: React.FC<SeverityBadgeProps> = ({ severity, size = 'md' }) => {
  let badgeStyle = 'bg-slate-800 text-slate-300 border-slate-700';

  switch (severity) {
    case 'SEV-1':
      badgeStyle = 'bg-red-950/90 text-red-300 border-red-700 font-bold';
      break;
    case 'SEV-2':
      badgeStyle = 'bg-orange-950/90 text-orange-300 border-orange-700 font-semibold';
      break;
    case 'SEV-3':
      badgeStyle = 'bg-yellow-950/90 text-yellow-300 border-yellow-700 font-medium';
      break;
    case 'SEV-4':
      badgeStyle = 'bg-blue-950/90 text-blue-300 border-blue-700';
      break;
    default:
      badgeStyle = 'bg-slate-800 text-slate-300 border-slate-700';
  }

  const sizeClasses = size === 'sm' ? 'px-2 py-0.5 text-xs' : 'px-2.5 py-1 text-xs';

  return (
    <span
      className={`inline-flex items-center gap-1.5 rounded-md border font-mono tracking-wider ${sizeClasses} ${badgeStyle}`}
      data-testid="severity-badge"
    >
      <span className="w-1.5 h-1.5 rounded-full bg-current" />
      {severity}
    </span>
  );
};
