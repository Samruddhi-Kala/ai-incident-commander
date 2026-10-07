import React from 'react';
import {
  Award,
  CheckCircle2,
  RefreshCw,
  Loader2,
  Info,
  TrendingUp,
  Sliders,
  Database,
  Cpu,
  Search,
} from 'lucide-react';
import { InvestigationEvaluationResponse } from '../../types/evaluation';

export interface EvaluationSectionProps {
  evaluation: InvestigationEvaluationResponse | null;
  loading: boolean;
  evaluating: boolean;
  error: string | null;
  onEvaluate: (force?: boolean) => Promise<unknown>;
  investigationStatus: string;
}

export const EvaluationSection: React.FC<EvaluationSectionProps> = ({
  evaluation,
  loading,
  evaluating,
  error,
  onEvaluate,
  investigationStatus,
}) => {
  const handleEvaluate = async (force = false) => {
    try {
      await onEvaluate(force);
    } catch {
      // Error handled by hook
    }
  };

  const getScoreBadgeColor = (score: number) => {
    if (score >= 80) return 'text-emerald-400 bg-emerald-950/60 border-emerald-800';
    if (score >= 60) return 'text-amber-400 bg-amber-950/60 border-amber-800';
    return 'text-rose-400 bg-rose-950/60 border-rose-800';
  };

  const getProgressBarColor = (score: number) => {
    if (score >= 80) return 'bg-emerald-500';
    if (score >= 60) return 'bg-amber-500';
    return 'bg-rose-500';
  };

  return (
    <div
      className="rounded-lg border border-slate-800 bg-slate-900/40 p-6 space-y-6"
      data-testid="evaluation-section"
    >
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-4 border-b border-slate-800">
        <div>
          <div className="flex items-center gap-2">
            <Award className="w-5 h-5 text-emerald-400" />
            <h3 className="text-base font-semibold text-slate-100 font-mono tracking-wide">
              AI Investigation Quality Evaluation
            </h3>
          </div>
          <p className="text-xs text-slate-400 font-mono mt-1">
            Explainable, deterministic heuristic audit assessing diagnostic evidence, hypothesis rigor, and tool efficiency.
          </p>
        </div>

        <div>
          {evaluation ? (
            <button
              onClick={() => handleEvaluate(true)}
              disabled={evaluating}
              className="inline-flex items-center gap-2 px-3 py-1.5 rounded-md border border-slate-700 bg-slate-800/80 hover:bg-slate-700 disabled:opacity-50 text-slate-200 text-xs font-mono transition-colors"
              data-testid="re-evaluate-btn"
            >
              {evaluating ? (
                <>
                  <Loader2 className="w-3.5 h-3.5 animate-spin text-emerald-400" />
                  <span>Re-evaluating...</span>
                </>
              ) : (
                <>
                  <RefreshCw className="w-3.5 h-3.5 text-emerald-400" />
                  <span>Re-evaluate</span>
                </>
              )}
            </button>
          ) : (
            <button
              onClick={() => handleEvaluate(false)}
              disabled={evaluating}
              className="inline-flex items-center gap-2 px-4 py-2 rounded-md bg-emerald-600 hover:bg-emerald-500 disabled:bg-emerald-900 disabled:text-emerald-400 text-white font-mono text-xs font-semibold shadow-lg shadow-emerald-950 transition-colors"
              data-testid="evaluate-investigation-btn"
            >
              {evaluating ? (
                <>
                  <Loader2 className="w-4 h-4 animate-spin text-white" />
                  <span>Calculating Quality Scores...</span>
                </>
              ) : (
                <>
                  <Award className="w-4 h-4" />
                  <span>Evaluate Investigation</span>
                </>
              )}
            </button>
          )}
        </div>
      </div>

      {/* Error state */}
      {error && (
        <div
          className="rounded-md border border-rose-900/60 bg-rose-950/30 p-4 text-xs font-mono text-rose-300 flex items-center justify-between"
          data-testid="evaluation-error"
        >
          <span>Error evaluating investigation: {error}</span>
          <button
            onClick={() => handleEvaluate(false)}
            className="underline hover:text-rose-100 ml-4"
          >
            Retry
          </button>
        </div>
      )}

      {/* Loading state */}
      {loading && !evaluation && (
        <div className="flex items-center justify-center py-12 text-slate-400 font-mono text-xs gap-3">
          <Loader2 className="w-5 h-5 animate-spin text-emerald-400" />
          <span>Retrieving evaluation records...</span>
        </div>
      )}

      {/* Empty state */}
      {!loading && !evaluation && !error && (
        <div
          className="rounded-md border border-dashed border-slate-800 p-8 text-center space-y-3"
          data-testid="evaluation-empty"
        >
          <div className="w-10 h-10 rounded-full bg-slate-800/80 flex items-center justify-center mx-auto text-slate-400">
            <Award className="w-5 h-5 text-slate-500" />
          </div>
          <div className="space-y-1">
            <h4 className="text-sm font-medium text-slate-300 font-mono">No Quality Evaluation Yet</h4>
            <p className="text-xs text-slate-500 font-mono max-w-md mx-auto">
              Run an automated quality evaluation across evidence support, hypothesis diversity, verification rigor, RAG relevance, and tool execution efficiency.
            </p>
          </div>
        </div>
      )}

      {/* Rendered Evaluation */}
      {evaluation && (
        <div className="space-y-6" data-testid="evaluation-content">
          {/* Overall score card */}
          <div className="rounded-md border border-slate-800 bg-slate-950/60 p-5 flex flex-col md:flex-row items-center justify-between gap-6">
            <div className="space-y-2 text-center md:text-left">
              <div className="flex items-center justify-center md:justify-start gap-2">
                <TrendingUp className="w-4 h-4 text-emerald-400" />
                <span className="text-xs font-semibold text-slate-300 font-mono uppercase tracking-wider">
                  Overall Investigation Score
                </span>
              </div>
              <p className="text-xs text-slate-400 font-mono max-w-xl">
                Weighted composite score across 5 audit dimensions with outcome status adjustment ({investigationStatus}).
              </p>
            </div>

            <div
              className={`px-6 py-4 rounded-lg border text-center font-mono ${getScoreBadgeColor(
                evaluation.overall_score
              )}`}
              data-testid="overall-score-badge"
            >
              <div className="text-3xl font-extrabold tracking-tight">{evaluation.overall_score}</div>
              <div className="text-[10px] uppercase font-bold tracking-wider mt-0.5 opacity-80">
                {evaluation.overall_score >= 80 ? 'High Quality' : evaluation.overall_score >= 60 ? 'Acceptable' : 'Needs Review'}
              </div>
            </div>
          </div>

          {/* 5 Sub-Scores Grid */}
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-3" data-testid="sub-scores-grid">
            {/* Evidence Support */}
            <div className="rounded-md border border-slate-800/80 bg-slate-900/60 p-3.5 space-y-2">
              <div className="flex items-center justify-between">
                <span className="text-[11px] font-semibold text-slate-300 font-mono flex items-center gap-1.5">
                  <Database className="w-3.5 h-3.5 text-cyan-400" />
                  Evidence
                </span>
                <span className="text-xs font-bold text-slate-200 font-mono">{evaluation.evidence_score}</span>
              </div>
              <div className="w-full bg-slate-800 h-1.5 rounded-full overflow-hidden">
                <div
                  className={`h-full ${getProgressBarColor(evaluation.evidence_score)}`}
                  style={{ width: `${evaluation.evidence_score}%` }}
                />
              </div>
              <div className="text-[10px] text-slate-500 font-mono">Weight: 25%</div>
            </div>

            {/* Hypothesis Quality */}
            <div className="rounded-md border border-slate-800/80 bg-slate-900/60 p-3.5 space-y-2">
              <div className="flex items-center justify-between">
                <span className="text-[11px] font-semibold text-slate-300 font-mono flex items-center gap-1.5">
                  <Sliders className="w-3.5 h-3.5 text-indigo-400" />
                  Hypothesis
                </span>
                <span className="text-xs font-bold text-slate-200 font-mono">{evaluation.hypothesis_score}</span>
              </div>
              <div className="w-full bg-slate-800 h-1.5 rounded-full overflow-hidden">
                <div
                  className={`h-full ${getProgressBarColor(evaluation.hypothesis_score)}`}
                  style={{ width: `${evaluation.hypothesis_score}%` }}
                />
              </div>
              <div className="text-[10px] text-slate-500 font-mono">Weight: 20%</div>
            </div>

            {/* Verification Rigor */}
            <div className="rounded-md border border-slate-800/80 bg-slate-900/60 p-3.5 space-y-2">
              <div className="flex items-center justify-between">
                <span className="text-[11px] font-semibold text-slate-300 font-mono flex items-center gap-1.5">
                  <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400" />
                  Verification
                </span>
                <span className="text-xs font-bold text-slate-200 font-mono">{evaluation.verification_score}</span>
              </div>
              <div className="w-full bg-slate-800 h-1.5 rounded-full overflow-hidden">
                <div
                  className={`h-full ${getProgressBarColor(evaluation.verification_score)}`}
                  style={{ width: `${evaluation.verification_score}%` }}
                />
              </div>
              <div className="text-[10px] text-slate-500 font-mono">Weight: 25%</div>
            </div>

            {/* RAG Relevance */}
            <div className="rounded-md border border-slate-800/80 bg-slate-900/60 p-3.5 space-y-2">
              <div className="flex items-center justify-between">
                <span className="text-[11px] font-semibold text-slate-300 font-mono flex items-center gap-1.5">
                  <Search className="w-3.5 h-3.5 text-purple-400" />
                  RAG Knowledge
                </span>
                <span className="text-xs font-bold text-slate-200 font-mono">{evaluation.rag_score}</span>
              </div>
              <div className="w-full bg-slate-800 h-1.5 rounded-full overflow-hidden">
                <div
                  className={`h-full ${getProgressBarColor(evaluation.rag_score)}`}
                  style={{ width: `${evaluation.rag_score}%` }}
                />
              </div>
              <div className="text-[10px] text-slate-500 font-mono">Weight: 15%</div>
            </div>

            {/* Tool Efficiency */}
            <div className="rounded-md border border-slate-800/80 bg-slate-900/60 p-3.5 space-y-2">
              <div className="flex items-center justify-between">
                <span className="text-[11px] font-semibold text-slate-300 font-mono flex items-center gap-1.5">
                  <Cpu className="w-3.5 h-3.5 text-amber-400" />
                  Tool Efficiency
                </span>
                <span className="text-xs font-bold text-slate-200 font-mono">{evaluation.tool_efficiency_score}</span>
              </div>
              <div className="w-full bg-slate-800 h-1.5 rounded-full overflow-hidden">
                <div
                  className={`h-full ${getProgressBarColor(evaluation.tool_efficiency_score)}`}
                  style={{ width: `${evaluation.tool_efficiency_score}%` }}
                />
              </div>
              <div className="text-[10px] text-slate-500 font-mono">Weight: 15%</div>
            </div>
          </div>

          {/* Reasoning Narrative */}
          <div className="rounded-md border border-slate-800 bg-slate-900/60 p-4 space-y-3">
            <span className="text-xs font-semibold text-slate-300 font-mono uppercase tracking-wider">
              Diagnostic Evaluation Reasoning
            </span>
            <pre className="text-xs text-slate-300 font-mono whitespace-pre-wrap bg-slate-950/60 p-3.5 rounded border border-slate-800 leading-relaxed">
              {evaluation.evaluation_reasoning}
            </pre>
          </div>

          {/* Heuristic Disclaimer */}
          <div className="flex items-start gap-2 p-3 rounded-md border border-slate-800/80 bg-slate-950/40 text-[11px] font-mono text-slate-500">
            <Info className="w-4 h-4 text-slate-400 shrink-0 mt-0.5" />
            <span>
              Disclaimer: Evaluation scores are transparent heuristic engineering metrics designed to audit investigation completeness,
              evidence grounding, and diagnostic efficiency. They do not constitute academic or statistically validated MTTR benchmarks.
            </span>
          </div>
        </div>
      )}
    </div>
  );
};
