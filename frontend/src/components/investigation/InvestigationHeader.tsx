import React from 'react';
import { InvestigationRunResponse } from '../../types/investigation';
import { StatusBadge } from '../common/StatusBadge';
import { ConfidenceMeter } from '../common/ConfidenceMeter';
import { Clock, ShieldCheck, Hash } from 'lucide-react';

export interface InvestigationHeaderProps {
  investigation: InvestigationRunResponse;
  incidentTitle?: string;
  serviceName?: string;
  severity?: string;
}

export const InvestigationHeader: React.FC<InvestigationHeaderProps> = ({
  investigation,
  incidentTitle,
  serviceName,
  severity,
}) => {
  const createdDate = new Date(investigation.created_at).toLocaleString();
  const completedDate = investigation.completed_at
    ? new Date(investigation.completed_at).toLocaleString()
    : null;

  return (
    <div
      className="rounded-lg border border-slate-800 bg-slate-900/60 p-6 shadow-xl"
      data-testid="investigation-header"
    >
      <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-6">
        <div className="space-y-2">
          <div className="flex flex-wrap items-center gap-3">
            <span className="inline-flex items-center gap-1 px-2.5 py-1 rounded bg-slate-800 border border-slate-700 font-mono text-xs text-cyan-400 font-semibold">
              <Hash className="w-3.5 h-3.5" />
              {investigation.investigation_number}
            </span>
            <StatusBadge status={investigation.status} />
            {severity && (
              <span className="font-mono text-xs px-2 py-0.5 rounded bg-slate-800/80 border border-slate-700 text-slate-300">
                {severity}
              </span>
            )}
            {serviceName && (
              <span className="font-mono text-xs px-2 py-0.5 rounded bg-slate-800/80 border border-slate-700 text-slate-300">
                svc: <span className="text-cyan-300">{serviceName}</span>
              </span>
            )}
          </div>

          <h1 className="text-xl md:text-2xl font-bold text-slate-100 tracking-tight">
            {incidentTitle || 'Automated Incident Investigation'}
          </h1>

          <div className="flex flex-wrap items-center gap-4 text-xs font-mono text-slate-400">
            <span className="flex items-center gap-1.5">
              <Clock className="w-3.5 h-3.5 text-slate-500" />
              Started: {createdDate}
            </span>
            {completedDate && (
              <span className="flex items-center gap-1.5">
                <ShieldCheck className="w-3.5 h-3.5 text-emerald-500" />
                Completed: {completedDate}
              </span>
            )}
          </div>
        </div>

        <div className="w-full lg:w-72 bg-slate-950/70 p-4 rounded-lg border border-slate-800/90 shadow-inner">
          <ConfidenceMeter confidence={investigation.confidence_score} label="Root Cause Confidence" />
        </div>
      </div>
    </div>
  );
};
