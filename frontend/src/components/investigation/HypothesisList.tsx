import React from 'react';
import { HypothesisInfo } from '../../types/investigation';
import { GitBranch, Check, X, HelpCircle } from 'lucide-react';

export interface HypothesisListProps {
  hypotheses: HypothesisInfo[];
}

export const HypothesisList: React.FC<HypothesisListProps> = ({ hypotheses }) => {
  if (!hypotheses || hypotheses.length === 0) {
    return (
      <div className="rounded-lg border border-slate-800 bg-slate-900/30 p-8 text-center font-mono text-xs text-slate-500">
        No competing diagnostic hypotheses have been formulated yet.
      </div>
    );
  }

  const getStatusBadge = (status: string) => {
    const norm = status?.toUpperCase();
    if (norm === 'SUPPORTED' || norm === 'VERIFIED_STRONG') {
      return (
        <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded text-[11px] font-mono font-bold bg-emerald-950/80 text-emerald-300 border border-emerald-800">
          <Check className="w-3 h-3" />
          {status}
        </span>
      );
    }
    if (norm === 'PARTIALLY_SUPPORTED' || norm === 'VERIFIED_WEAK') {
      return (
        <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded text-[11px] font-mono font-medium bg-amber-950/80 text-amber-300 border border-amber-800">
          <HelpCircle className="w-3 h-3" />
          {status}
        </span>
      );
    }
    if (norm === 'NOT_SUPPORTED' || norm === 'RULED_OUT') {
      return (
        <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded text-[11px] font-mono font-medium bg-rose-950/80 text-rose-300 border border-rose-800">
          <X className="w-3 h-3" />
          {status}
        </span>
      );
    }
    return (
      <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded text-[11px] font-mono font-medium bg-slate-800 text-slate-300 border border-slate-700">
        {status}
      </span>
    );
  };

  return (
    <div className="space-y-4" data-testid="hypothesis-list">
      <div className="flex items-center justify-between">
        <div>
          <div className="flex items-center gap-2">
            <GitBranch className="w-4 h-4 text-cyan-400" />
            <h3 className="text-sm font-semibold text-slate-200 uppercase tracking-wider font-mono">
              Competing Hypotheses
            </h3>
          </div>
          <p className="text-xs text-slate-400 font-mono mt-0.5">
            Agent reasoning actively evaluated multiple alternative causal explanations
          </p>
        </div>
        <span className="text-xs font-mono px-2.5 py-1 rounded bg-slate-800 text-slate-300 border border-slate-700">
          {hypotheses.length} Competing Hypotheses
        </span>
      </div>

      <div className="space-y-3">
        {hypotheses.map((hypo, idx) => {
          const confidencePct = Math.round(hypo.confidence_score * 100);

          return (
            <div
              key={hypo.id || idx}
              className="rounded-lg border border-slate-800 bg-slate-900/50 p-4 space-y-3 hover:border-slate-700 transition-colors"
            >
              <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 pb-2 border-b border-slate-800/80">
                <div className="flex items-center gap-2">
                  <span className="w-6 h-6 rounded bg-slate-800 border border-slate-700 flex items-center justify-center font-mono text-xs font-bold text-cyan-300">
                    H{idx + 1}
                  </span>
                  <span className="font-mono text-xs text-slate-400">
                    Confidence: <span className="text-slate-100 font-bold">{confidencePct}%</span>
                  </span>
                </div>

                <div className="flex items-center gap-2">{getStatusBadge(hypo.status)}</div>
              </div>

              <p className="text-sm font-mono text-slate-200 leading-relaxed font-semibold">
                {hypo.hypothesis_text}
              </p>

              <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 pt-2 text-xs font-mono">
                <div className="rounded bg-slate-950/70 p-2.5 border border-slate-800">
                  <span className="text-[10px] text-emerald-400 uppercase tracking-wider block mb-1">
                    Supporting Evidence ({hypo.supporting_evidence_ids?.length || 0})
                  </span>
                  <span className="text-slate-400 text-[11px]">
                    {hypo.supporting_evidence_ids?.length
                      ? hypo.supporting_evidence_ids.map((id) => id.slice(0, 8)).join(', ')
                      : 'None mapped'}
                  </span>
                </div>

                <div className="rounded bg-slate-950/70 p-2.5 border border-slate-800">
                  <span className="text-[10px] text-rose-400 uppercase tracking-wider block mb-1">
                    Opposing Evidence ({hypo.opposing_evidence_ids?.length || 0})
                  </span>
                  <span className="text-slate-400 text-[11px]">
                    {hypo.opposing_evidence_ids?.length
                      ? hypo.opposing_evidence_ids.map((id) => id.slice(0, 8)).join(', ')
                      : 'None identified'}
                  </span>
                </div>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
};
