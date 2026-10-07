import React from 'react';
import { RetrievedSource } from '../../types/investigation';
import { FileText } from 'lucide-react';

export interface KnowledgeSourcesProps {
  sources: RetrievedSource[];
}

export const KnowledgeSources: React.FC<KnowledgeSourcesProps> = ({ sources }) => {
  if (!sources || sources.length === 0) {
    return (
      <div className="rounded-lg border border-slate-800 bg-slate-900/30 p-8 text-center font-mono text-xs text-slate-500">
        No RAG organizational knowledge sources were retrieved for this incident.
      </div>
    );
  }

  return (
    <div className="space-y-4" data-testid="knowledge-sources">
      <div className="flex items-center justify-between">
        <div>
          <h3 className="text-sm font-semibold text-slate-200 uppercase tracking-wider font-mono">
            Retrieved Runbooks & Postmortems
          </h3>
          <p className="text-xs text-slate-400 font-mono mt-0.5">
            Institutional knowledge indexed via hybrid vector & text retrieval
          </p>
        </div>
        <span className="text-xs font-mono px-2.5 py-1 rounded bg-slate-800 text-slate-300 border border-slate-700">
          {sources.length} Documents
        </span>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {sources.map((source, index) => {
          const score = typeof source.score === 'number' ? Math.round(source.score * 100) / 100 : null;
          const docType = String(source.document_type || 'RUNBOOK').toUpperCase();

          return (
            <div
              key={index}
              className="rounded-lg border border-slate-800 bg-slate-900/50 p-4 space-y-3 hover:border-slate-700 transition-colors"
            >
              <div className="flex items-start justify-between gap-3">
                <div className="flex items-start gap-2.5">
                  <div className="p-2 rounded bg-slate-800 text-cyan-400 border border-slate-700 shrink-0">
                    <FileText className="w-4 h-4" />
                  </div>
                  <div>
                    <h4 className="text-sm font-semibold text-slate-200 leading-tight">
                      {source.title || 'Untitled Document'}
                    </h4>
                    {source.source_path && (
                      <p className="text-[11px] font-mono text-slate-500 break-all mt-0.5">
                        {source.source_path}
                      </p>
                    )}
                  </div>
                </div>

                <div className="flex flex-col items-end gap-1 shrink-0">
                  <span className="px-1.5 py-0.5 rounded text-[10px] font-mono font-bold bg-slate-800 border border-slate-700 text-cyan-300 uppercase">
                    {docType}
                  </span>
                  {score !== null && (
                    <span className="text-[11px] font-mono text-slate-400">
                      Score: <span className="text-slate-200 font-semibold">{score}</span>
                    </span>
                  )}
                </div>
              </div>

              {source.content_snippet && (
                <div className="rounded bg-slate-950 p-3 border border-slate-800/80">
                  <span className="text-[10px] font-mono text-slate-500 uppercase tracking-wider block mb-1">
                    Retrieved Passage Snippet
                  </span>
                  <p className="text-xs text-slate-300 font-mono leading-relaxed line-clamp-4">
                    {source.content_snippet}
                  </p>
                </div>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
};
