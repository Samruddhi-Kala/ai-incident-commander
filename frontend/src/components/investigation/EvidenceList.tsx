import React from 'react';
import { EvidenceInfo } from '../../types/investigation';

export interface EvidenceListProps {
  evidence: EvidenceInfo[];
}

export const EvidenceList: React.FC<EvidenceListProps> = ({ evidence }) => {
  if (!evidence || evidence.length === 0) {
    return (
      <div className="rounded-lg border border-slate-800 bg-slate-900/30 p-8 text-center font-mono text-xs text-slate-500">
        No empirical evidence items have been extracted yet.
      </div>
    );
  }

  return (
    <div className="space-y-4" data-testid="evidence-list">
      <div className="flex items-center justify-between">
        <div>
          <h3 className="text-sm font-semibold text-slate-200 uppercase tracking-wider font-mono">
            Collected Empirical Evidence
          </h3>
          <p className="text-xs text-slate-400 font-mono mt-0.5">
            Verified metric signals and log observations gathered across tool runs
          </p>
        </div>
        <span className="text-xs font-mono px-2.5 py-1 rounded bg-slate-800 text-slate-300 border border-slate-700">
          {evidence.length} Items
        </span>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
        {evidence.map((ev) => {
          const scorePct = Math.round(ev.relevance_score * 100);

          return (
            <div
              key={ev.id}
              className="rounded-lg border border-slate-800 bg-slate-900/50 p-4 space-y-3 hover:border-slate-700 transition-colors"
            >
              <div className="flex items-center justify-between gap-2">
                <div className="flex items-center gap-2">
                  <span className="p-1 rounded bg-slate-800 border border-slate-700 text-cyan-400 font-mono text-xs">
                    {ev.source_tool}
                  </span>
                </div>

                <div className="flex items-center gap-1.5 font-mono text-xs text-slate-400">
                  <span>Relevance:</span>
                  <span className="text-cyan-300 font-semibold">{scorePct}%</span>
                </div>
              </div>

              <p className="text-xs font-mono text-slate-200 bg-slate-950 p-3 rounded border border-slate-800/80 leading-relaxed">
                {ev.summary}
              </p>

              <div className="flex items-center justify-between text-[11px] font-mono text-slate-500 pt-1">
                <span>ID: {ev.id.slice(0, 8)}</span>
                <span>{new Date(ev.collected_at).toLocaleTimeString()}</span>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
};
