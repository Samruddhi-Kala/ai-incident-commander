import React from 'react';
import { Link } from 'react-router-dom';
import { RemediationActionResponse } from '../../types/remediation';
import { StatusBadge } from '../common/StatusBadge';
import { RiskBadge } from '../common/RiskBadge';
import { Wrench, ArrowRight, ShieldCheck, Clock } from 'lucide-react';

export interface RemediationCardProps {
  remediation: RemediationActionResponse;
}

export const RemediationCard: React.FC<RemediationCardProps> = ({ remediation }) => {
  const service = String(remediation.parameters?.service || 'target-service');
  const targetVersion = remediation.parameters?.target_version
    ? String(remediation.parameters.target_version)
    : null;
  const replicas = remediation.parameters?.replicas
    ? String(remediation.parameters.replicas)
    : null;

  return (
    <div
      className="rounded-lg border border-slate-800 bg-slate-900/50 p-5 space-y-4 hover:border-slate-700 transition-colors shadow-lg"
      data-testid={`remediation-card-${remediation.id}`}
    >
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 pb-3 border-b border-slate-800">
        <div className="flex items-center gap-2.5">
          <div className="p-2 rounded bg-slate-800 border border-slate-700 text-cyan-400">
            <Wrench className="w-4 h-4" />
          </div>
          <div>
            <h3 className="text-base font-bold text-slate-100 font-mono">
              {remediation.action_name}
            </h3>
            <span className="text-xs text-slate-400 font-mono">
              Target: <span className="text-cyan-300 font-semibold">{service}</span>
              {targetVersion && <span className="text-slate-400"> → {targetVersion}</span>}
              {replicas && <span className="text-slate-400"> → {replicas} replicas</span>}
            </span>
          </div>
        </div>

        <div className="flex items-center gap-2">
          <RiskBadge risk={remediation.risk_level} />
          <StatusBadge status={remediation.approval_status} />
        </div>
      </div>

      <p className="text-xs font-mono text-slate-300 leading-relaxed bg-slate-950/70 p-3 rounded border border-slate-800/80">
        {remediation.reasoning}
      </p>

      <div className="flex items-center justify-between pt-1 text-xs font-mono">
        <div className="flex items-center gap-3 text-slate-500 text-[11px]">
          <span className="flex items-center gap-1">
            <Clock className="w-3 h-3" />
            {new Date(remediation.created_at).toLocaleDateString()}
          </span>
          {remediation.approved_by && (
            <span className="flex items-center gap-1 text-emerald-400">
              <ShieldCheck className="w-3 h-3" />
              Human Authorized
            </span>
          )}
        </div>

        <Link
          to={`/remediations/${remediation.id}`}
          className="inline-flex items-center gap-1 text-xs font-mono font-semibold text-cyan-400 hover:text-cyan-300 transition-colors"
        >
          View Action Details
          <ArrowRight className="w-3.5 h-3.5" />
        </Link>
      </div>
    </div>
  );
};
