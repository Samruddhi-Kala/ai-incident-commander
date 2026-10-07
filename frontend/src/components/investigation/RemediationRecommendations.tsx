import React, { useState } from 'react';
import { Sparkles, ArrowRight, Loader2, CheckCircle2 } from 'lucide-react';
import { useNavigate } from 'react-router-dom';

export interface RemediationRecommendationsProps {
  recommendations: string[];
  onProposeRemediations: () => Promise<unknown>;
  isProposing?: boolean;
}

export const RemediationRecommendations: React.FC<RemediationRecommendationsProps> = ({
  recommendations,
  onProposeRemediations,
  isProposing = false,
}) => {
  const [successMessage, setSuccessMessage] = useState<string | null>(null);
  const navigate = useNavigate();

  const handlePropose = async () => {
    try {
      await onProposeRemediations();
      setSuccessMessage('Proposals formulated! Redirecting to Remediations Console...');
      setTimeout(() => {
        navigate('/remediations');
      }, 1200);
    } catch {
      // Error handled by parent hook
    }
  };

  if (!recommendations || recommendations.length === 0) {
    return null;
  }

  return (
    <div
      className="rounded-lg border border-slate-800 bg-slate-900/40 p-6 space-y-4"
      data-testid="remediation-recommendations"
    >
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-3 border-b border-slate-800">
        <div>
          <div className="flex items-center gap-2">
            <Sparkles className="w-4 h-4 text-cyan-400" />
            <h3 className="text-sm font-semibold text-slate-200 uppercase tracking-wider font-mono">
              AI Remediation Recommendations
            </h3>
          </div>
          <p className="text-xs text-slate-400 font-mono mt-0.5">
            Phase 6 non-executable recovery guidance. Formulate formal proposals for human review.
          </p>
        </div>

        <button
          onClick={handlePropose}
          disabled={isProposing}
          className="inline-flex items-center gap-2 px-4 py-2 rounded-md bg-cyan-600 hover:bg-cyan-500 disabled:bg-cyan-900 disabled:text-cyan-400 text-white font-mono text-xs font-semibold shadow-lg shadow-cyan-950 transition-colors"
          data-testid="propose-remediations-btn"
        >
          {isProposing ? (
            <>
              <Loader2 className="w-4 h-4 animate-spin" />
              Generating Proposals...
            </>
          ) : (
            <>
              Create Remediation Proposals
              <ArrowRight className="w-4 h-4" />
            </>
          )}
        </button>
      </div>

      {successMessage && (
        <div className="p-3 rounded bg-emerald-950/70 border border-emerald-800 text-emerald-300 text-xs font-mono flex items-center gap-2 animate-fade-in">
          <CheckCircle2 className="w-4 h-4 shrink-0 text-emerald-400" />
          <span>{successMessage}</span>
        </div>
      )}

      <div className="space-y-2">
        {recommendations.map((rec, index) => (
          <div
            key={index}
            className="flex items-start gap-3 p-3.5 rounded-lg bg-slate-950/60 border border-slate-800/80 font-mono text-xs text-slate-200"
          >
            <span className="w-5 h-5 rounded bg-slate-800 border border-slate-700 flex items-center justify-center text-slate-400 text-[11px] shrink-0 font-bold">
              {index + 1}
            </span>
            <span className="leading-relaxed">{rec}</span>
          </div>
        ))}
      </div>
    </div>
  );
};
