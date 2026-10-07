import React from 'react';
import { HelpCircle, CheckCircle, AlertOctagon } from 'lucide-react';
import { ConfidenceMeter } from '../common/ConfidenceMeter';

export interface RootCausePanelProps {
  status: string;
  probableRootCause?: string | null;
  confidenceScore?: number | null;
  analysisReasoning?: string | null;
  supportingEvidence?: string[];
  alternativeHypotheses?: string[];
}

export const RootCausePanel: React.FC<RootCausePanelProps> = ({
  status,
  probableRootCause,
  confidenceScore,
  analysisReasoning,
  supportingEvidence = [],
  alternativeHypotheses = [],
}) => {
  const isInconclusive = status?.toUpperCase() === 'INCONCLUSIVE';
  const isFailed = status?.toUpperCase() === 'FAILED';

  if (isInconclusive) {
    return (
      <div
        className="rounded-lg border border-amber-800/80 bg-amber-950/20 p-6 space-y-4"
        data-testid="root-cause-inconclusive"
      >
        <div className="flex items-start gap-4">
          <div className="w-10 h-10 rounded-full bg-amber-900/40 border border-amber-700/60 flex items-center justify-center text-amber-400 shrink-0">
            <HelpCircle className="w-6 h-6" />
          </div>
          <div className="space-y-1">
            <span className="text-xs font-mono font-semibold uppercase tracking-wider text-amber-400">
              Investigation Outcome
            </span>
            <h2 className="text-lg font-bold text-amber-200">
              Inconclusive Investigation
            </h2>
            <p className="text-sm text-amber-300/80 leading-relaxed font-mono">
              Available empirical telemetry and runbook evidence did not establish a sufficiently
              supported root cause above the confidence verification threshold (0.40). No hypothesis
              could be definitively verified.
            </p>
          </div>
        </div>

        {analysisReasoning && (
          <div className="rounded-lg bg-amber-950/40 border border-amber-900/60 p-4 space-y-2">
            <span className="text-xs font-mono font-semibold text-amber-400 uppercase">
              Analytical Reasoning & Ambiguities
            </span>
            <p className="text-xs text-amber-200/90 font-mono whitespace-pre-wrap leading-relaxed">
              {analysisReasoning}
            </p>
          </div>
        )}
      </div>
    );
  }

  if (isFailed) {
    return (
      <div
        className="rounded-lg border border-rose-800/80 bg-rose-950/20 p-6 space-y-4"
        data-testid="root-cause-failed"
      >
        <div className="flex items-start gap-4">
          <div className="w-10 h-10 rounded-full bg-rose-900/40 border border-rose-700/60 flex items-center justify-center text-rose-400 shrink-0">
            <AlertOctagon className="w-6 h-6" />
          </div>
          <div className="space-y-1">
            <span className="text-xs font-mono font-semibold uppercase tracking-wider text-rose-400">
              Investigation Outcome
            </span>
            <h2 className="text-lg font-bold text-rose-200">
              Investigation Failed
            </h2>
            <p className="text-sm text-rose-300/80 font-mono leading-relaxed">
              The automated investigation workflow encountered an unrecoverable failure during
              execution. Manual investigation is advised.
            </p>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div
      className="rounded-lg border border-cyan-800/60 bg-gradient-to-b from-slate-900 to-slate-950 p-6 space-y-6 shadow-xl"
      data-testid="root-cause-panel"
    >
      <div className="flex flex-col md:flex-row md:items-start justify-between gap-6 pb-4 border-b border-slate-800">
        <div className="space-y-1">
          <div className="flex items-center gap-2">
            <CheckCircle className="w-4 h-4 text-emerald-400" />
            <span className="text-xs font-mono uppercase tracking-wider text-cyan-400 font-semibold">
              Empirical Diagnostic Synthesis
            </span>
          </div>
          <h2 className="text-xl font-bold text-slate-100 tracking-tight">
            Probable Root Cause
          </h2>
          <p className="text-xs font-mono text-slate-400">
            Evidence suggests the most supported causal hypothesis
          </p>
        </div>

        <div className="w-full md:w-64 bg-slate-950/80 p-3 rounded-lg border border-slate-800">
          <ConfidenceMeter confidence={confidenceScore} label="Root Cause Confidence" />
        </div>
      </div>

      {/* Probable Cause Box */}
      <div className="rounded-lg bg-slate-950 border border-slate-800 p-4">
        <span className="text-[11px] font-mono text-slate-500 uppercase tracking-wider block mb-1">
          Synthesized Cause Statement
        </span>
        <p className="text-base text-slate-100 font-semibold leading-relaxed">
          {probableRootCause || 'Under investigation...'}
        </p>
      </div>

      {/* Analysis Reasoning */}
      {analysisReasoning && (
        <div className="space-y-2">
          <span className="text-xs font-mono font-semibold uppercase tracking-wider text-slate-400">
            Analytical Reasoning
          </span>
          <div className="rounded-lg bg-slate-950/70 border border-slate-800/80 p-4 font-mono text-xs text-slate-300 leading-relaxed whitespace-pre-wrap">
            {analysisReasoning}
          </div>
        </div>
      )}

      {/* Supporting Evidence & Alternative Explanations */}
      {(supportingEvidence.length > 0 || alternativeHypotheses.length > 0) && (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4 pt-2">
          {supportingEvidence.length > 0 && (
            <div className="space-y-2">
              <span className="text-xs font-mono font-semibold text-emerald-400 uppercase tracking-wider">
                Key Supporting Observations
              </span>
              <ul className="space-y-1.5 text-xs font-mono text-slate-300">
                {supportingEvidence.map((ev, idx) => (
                  <li
                    key={idx}
                    className="p-2.5 rounded bg-slate-950 border border-slate-800/80 flex items-start gap-2"
                  >
                    <span className="text-emerald-500 font-bold shrink-0">•</span>
                    <span>{ev}</span>
                  </li>
                ))}
              </ul>
            </div>
          )}

          {alternativeHypotheses.length > 0 && (
            <div className="space-y-2">
              <span className="text-xs font-mono font-semibold text-slate-400 uppercase tracking-wider">
                Alternative Hypotheses Evaluated
              </span>
              <ul className="space-y-1.5 text-xs font-mono text-slate-400">
                {alternativeHypotheses.map((alt, idx) => (
                  <li
                    key={idx}
                    className="p-2.5 rounded bg-slate-950/60 border border-slate-800/60 flex items-start gap-2"
                  >
                    <span className="text-slate-600 font-bold shrink-0">•</span>
                    <span>{alt}</span>
                  </li>
                ))}
              </ul>
            </div>
          )}
        </div>
      )}
    </div>
  );
};
