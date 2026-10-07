import React from 'react';

export interface StatusBadgeProps {
  status: string;
  size?: 'sm' | 'md';
}

export const StatusBadge: React.FC<StatusBadgeProps> = ({ status, size = 'md' }) => {
  const norm = status?.toUpperCase().replace(/\s+/g, '_') || 'UNKNOWN';

  let colorClasses = 'bg-slate-800 text-slate-300 border-slate-700';

  switch (norm) {
    // Incident statuses
    case 'TRIGGERED':
      colorClasses = 'bg-rose-950/80 text-rose-300 border-rose-800 animate-pulse';
      break;
    case 'INVESTIGATING':
      colorClasses = 'bg-sky-950/80 text-sky-300 border-sky-800';
      break;
    case 'MITIGATED':
      colorClasses = 'bg-amber-950/80 text-amber-300 border-amber-800';
      break;
    case 'RESOLVED':
      colorClasses = 'bg-emerald-950/80 text-emerald-300 border-emerald-800';
      break;

    // Investigation statuses
    case 'IN_PROGRESS':
      colorClasses = 'bg-sky-950/80 text-sky-300 border-sky-800 animate-pulse';
      break;
    case 'COMPLETED':
      colorClasses = 'bg-emerald-950/80 text-emerald-300 border-emerald-800';
      break;
    case 'INCONCLUSIVE':
      colorClasses = 'bg-amber-950/80 text-amber-300 border-amber-800';
      break;
    case 'FAILED':
      colorClasses = 'bg-rose-950/80 text-rose-300 border-rose-800';
      break;

    // Remediation statuses
    case 'PROPOSED':
      colorClasses = 'bg-indigo-950/80 text-indigo-300 border-indigo-800';
      break;
    case 'PENDING_APPROVAL':
      colorClasses = 'bg-amber-950/80 text-amber-300 border-amber-800';
      break;
    case 'APPROVED':
      colorClasses = 'bg-emerald-950/80 text-emerald-300 border-emerald-800';
      break;
    case 'REJECTED':
      colorClasses = 'bg-slate-900 text-rose-400 border-rose-900';
      break;
    case 'EXECUTING':
      colorClasses = 'bg-cyan-950/80 text-cyan-300 border-cyan-800 animate-pulse';
      break;

    default:
      colorClasses = 'bg-slate-800 text-slate-300 border-slate-700';
  }

  const sizeClasses = size === 'sm' ? 'px-2 py-0.5 text-xs' : 'px-2.5 py-1 text-xs font-medium';

  return (
    <span
      className={`inline-flex items-center gap-1.5 rounded-md border font-mono tracking-wider uppercase ${sizeClasses} ${colorClasses}`}
      data-testid="status-badge"
    >
      <span className="w-1.5 h-1.5 rounded-full bg-current opacity-80" />
      {status}
    </span>
  );
};
