import React, { useState } from 'react';
import {
  FileText,
  Clock,
  AlertTriangle,
  CheckCircle,
  RefreshCw,
  Loader2,
  ChevronDown,
  ChevronUp,
  ShieldCheck,
  Lightbulb,
  Wrench,
  Activity,
} from 'lucide-react';
import { PostmortemResponse } from '../../types/postmortem';

export interface PostmortemSectionProps {
  postmortem: PostmortemResponse | null;
  loading: boolean;
  generating: boolean;
  error: string | null;
  onGenerate: (regenerate?: boolean) => Promise<unknown>;
  investigationStatus: string;
}

export const PostmortemSection: React.FC<PostmortemSectionProps> = ({
  postmortem,
  loading,
  generating,
  error,
  onGenerate,
  investigationStatus,
}) => {
  const [timelineExpanded, setTimelineExpanded] = useState(false);

  const handleGenerate = async (regenerate = false) => {
    try {
      await onGenerate(regenerate);
    } catch {
      // Error handled by hook
    }
  };

  return (
    <div
      className="rounded-lg border border-slate-800 bg-slate-900/40 p-6 space-y-6"
      data-testid="postmortem-section"
    >
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-4 border-b border-slate-800">
        <div>
          <div className="flex items-center gap-2">
            <FileText className="w-5 h-5 text-indigo-400" />
            <h3 className="text-base font-semibold text-slate-100 font-mono tracking-wide">
              Incident Postmortem Report
            </h3>
          </div>
          <p className="text-xs text-slate-400 font-mono mt-1">
            Grounded post-incident analysis synthesized strictly from persisted investigation telemetry and evidence.
          </p>
        </div>

        <div>
          {postmortem ? (
            <button
              onClick={() => handleGenerate(true)}
              disabled={generating}
              className="inline-flex items-center gap-2 px-3 py-1.5 rounded-md border border-slate-700 bg-slate-800/80 hover:bg-slate-700 disabled:opacity-50 text-slate-200 text-xs font-mono transition-colors"
              data-testid="regenerate-postmortem-btn"
            >
              {generating ? (
                <>
                  <Loader2 className="w-3.5 h-3.5 animate-spin text-indigo-400" />
                  <span>Regenerating...</span>
                </>
              ) : (
                <>
                  <RefreshCw className="w-3.5 h-3.5 text-indigo-400" />
                  <span>Regenerate Report</span>
                </>
              )}
            </button>
          ) : (
            <button
              onClick={() => handleGenerate(false)}
              disabled={generating}
              className="inline-flex items-center gap-2 px-4 py-2 rounded-md bg-indigo-600 hover:bg-indigo-500 disabled:bg-indigo-900 disabled:text-indigo-400 text-white font-mono text-xs font-semibold shadow-lg shadow-indigo-950 transition-colors"
              data-testid="generate-postmortem-btn"
            >
              {generating ? (
                <>
                  <Loader2 className="w-4 h-4 animate-spin text-white" />
                  <span>Synthesizing Postmortem...</span>
                </>
              ) : (
                <>
                  <FileText className="w-4 h-4" />
                  <span>Generate Postmortem</span>
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
          data-testid="postmortem-error"
        >
          <span>Error loading postmortem: {error}</span>
          <button
            onClick={() => handleGenerate(false)}
            className="underline hover:text-rose-100 ml-4"
          >
            Retry
          </button>
        </div>
      )}

      {/* Loading state */}
      {loading && !postmortem && (
        <div className="flex items-center justify-center py-12 text-slate-400 font-mono text-xs gap-3">
          <Loader2 className="w-5 h-5 animate-spin text-indigo-400" />
          <span>Retrieving postmortem records...</span>
        </div>
      )}

      {/* Empty state */}
      {!loading && !postmortem && !error && (
        <div
          className="rounded-md border border-dashed border-slate-800 p-8 text-center space-y-3"
          data-testid="postmortem-empty"
        >
          <div className="w-10 h-10 rounded-full bg-slate-800/80 flex items-center justify-center mx-auto text-slate-400">
            <FileText className="w-5 h-5 text-slate-500" />
          </div>
          <div className="space-y-1">
            <h4 className="text-sm font-medium text-slate-300 font-mono">No Postmortem Generated Yet</h4>
            <p className="text-xs text-slate-500 font-mono max-w-md mx-auto">
              Generate a structured postmortem report containing incident summary, root cause, timeline, lessons learned, and preventive actions.
            </p>
          </div>
        </div>
      )}

      {/* Rendered Postmortem */}
      {postmortem && (
        <div className="space-y-6" data-testid="postmortem-content">
          {/* Metadata banner */}
          <div className="rounded-md border border-slate-800 bg-slate-950/60 p-4 space-y-2">
            <h4 className="text-sm font-bold text-slate-200 font-mono">{postmortem.title}</h4>
            <div className="flex flex-wrap items-center gap-4 text-xs text-slate-400 font-mono">
              <span className="flex items-center gap-1.5">
                <Clock className="w-3.5 h-3.5 text-slate-500" />
                Generated: {new Date(postmortem.generated_at).toLocaleString()}
              </span>
              <span className="flex items-center gap-1.5">
                <Activity className="w-3.5 h-3.5 text-slate-500" />
                Investigation: {investigationStatus}
              </span>
            </div>
          </div>

          {/* Incident Summary & Impact */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div className="rounded-md border border-slate-800/80 bg-slate-900/60 p-4 space-y-2">
              <span className="text-xs font-semibold text-slate-300 font-mono uppercase tracking-wider">
                Incident Summary
              </span>
              <p className="text-xs text-slate-300 leading-relaxed font-mono">
                {postmortem.summary}
              </p>
            </div>
            <div className="rounded-md border border-slate-800/80 bg-slate-900/60 p-4 space-y-2">
              <span className="text-xs font-semibold text-slate-300 font-mono uppercase tracking-wider">
                Impact Assessment
              </span>
              <p className="text-xs text-slate-300 leading-relaxed font-mono">
                {postmortem.impact}
              </p>
            </div>
          </div>

          {/* Root Cause & Contributing Factors */}
          <div className="rounded-md border border-slate-800 bg-slate-900/60 p-4 space-y-3">
            <div className="flex items-center gap-2">
              <AlertTriangle className="w-4 h-4 text-amber-400" />
              <span className="text-xs font-semibold text-slate-200 font-mono uppercase tracking-wider">
                Probable Root Cause
              </span>
            </div>
            <p className="text-xs text-slate-200 font-mono bg-slate-950/60 p-3 rounded border border-slate-800">
              {postmortem.root_cause}
            </p>

            {postmortem.contributing_factors && postmortem.contributing_factors.length > 0 && (
              <div className="space-y-1.5 pt-2">
                <span className="text-xs font-semibold text-slate-400 font-mono">Contributing Telemetry Factors:</span>
                <ul className="space-y-1 list-disc list-inside text-xs text-slate-300 font-mono">
                  {postmortem.contributing_factors.map((factor, idx) => (
                    <li key={idx} className="leading-relaxed">{factor}</li>
                  ))}
                </ul>
              </div>
            )}
          </div>

          {/* Timeline */}
          {postmortem.timeline && postmortem.timeline.length > 0 && (
            <div className="rounded-md border border-slate-800 bg-slate-900/60 p-4 space-y-3">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <Clock className="w-4 h-4 text-cyan-400" />
                  <span className="text-xs font-semibold text-slate-200 font-mono uppercase tracking-wider">
                    Incident Timeline ({postmortem.timeline.length} milestones)
                  </span>
                </div>
                <button
                  onClick={() => setTimelineExpanded(!timelineExpanded)}
                  className="flex items-center gap-1 text-xs text-slate-400 hover:text-slate-200 font-mono"
                >
                  <span>{timelineExpanded ? 'Collapse' : 'Expand'}</span>
                  {timelineExpanded ? <ChevronUp className="w-3.5 h-3.5" /> : <ChevronDown className="w-3.5 h-3.5" />}
                </button>
              </div>

              <div className={`space-y-2.5 transition-all ${timelineExpanded ? '' : 'max-h-48 overflow-y-auto'}`}>
                {postmortem.timeline.map((event, idx) => (
                  <div
                    key={idx}
                    className="flex items-start gap-3 p-2.5 rounded bg-slate-950/40 border border-slate-850 text-xs font-mono"
                  >
                    <span className="text-slate-500 shrink-0 text-[11px] w-28">
                      {event.timestamp ? new Date(event.timestamp).toLocaleTimeString() : '—'}
                    </span>
                    <div className="space-y-0.5 flex-1">
                      <div className="flex items-center justify-between">
                        <span className="font-semibold text-slate-200">{event.stage}</span>
                        {event.source && (
                          <span className="text-[10px] text-slate-500 bg-slate-800/60 px-1.5 py-0.5 rounded">
                            {event.source}
                          </span>
                        )}
                      </div>
                      <p className="text-slate-400 text-[11px]">{event.description}</p>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Lessons Learned & Preventive Actions */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {/* Lessons Learned */}
            <div className="rounded-md border border-slate-800 bg-slate-900/60 p-4 space-y-3">
              <div className="flex items-center gap-2">
                <Lightbulb className="w-4 h-4 text-yellow-400" />
                <span className="text-xs font-semibold text-slate-200 font-mono uppercase tracking-wider">
                  Lessons Learned
                </span>
              </div>
              <ul className="space-y-2 text-xs text-slate-300 font-mono">
                {(postmortem.lessons_learned || []).map((lesson, idx) => (
                  <li key={idx} className="flex items-start gap-2 bg-slate-950/40 p-2 rounded border border-slate-850">
                    <CheckCircle className="w-3.5 h-3.5 text-emerald-400 shrink-0 mt-0.5" />
                    <span>{lesson}</span>
                  </li>
                ))}
              </ul>
            </div>

            {/* Preventive Actions */}
            <div className="rounded-md border border-slate-800 bg-slate-900/60 p-4 space-y-3">
              <div className="flex items-center gap-2">
                <ShieldCheck className="w-4 h-4 text-emerald-400" />
                <span className="text-xs font-semibold text-slate-200 font-mono uppercase tracking-wider">
                  Preventive Actions
                </span>
              </div>
              <ul className="space-y-2 text-xs text-slate-300 font-mono">
                {(postmortem.preventive_actions || []).map((action, idx) => (
                  <li key={idx} className="flex items-start gap-2 bg-slate-950/40 p-2 rounded border border-slate-850">
                    <Wrench className="w-3.5 h-3.5 text-indigo-400 shrink-0 mt-0.5" />
                    <span>{action}</span>
                  </li>
                ))}
              </ul>
            </div>
          </div>

          {/* Remediation Summary */}
          {postmortem.remediation && (
            <div className="rounded-md border border-slate-800 bg-slate-900/60 p-4 space-y-2">
              <span className="text-xs font-semibold text-slate-300 font-mono uppercase tracking-wider">
                Remediation Actions Status
              </span>
              <p className="text-xs text-slate-300 font-mono">
                {postmortem.remediation.status_summary || 'No remediation actions executed.'}
              </p>
              {postmortem.remediation.actions && postmortem.remediation.actions.length > 0 && (
                <div className="flex flex-wrap gap-2 pt-2">
                  {postmortem.remediation.actions.map((act, idx) => (
                    <span
                      key={idx}
                      className="inline-flex items-center gap-1.5 px-2 py-1 rounded bg-slate-950 border border-slate-800 text-[11px] font-mono text-slate-300"
                    >
                      <span>{act.action_name}</span>
                      <span className="text-slate-500">•</span>
                      <span className="text-cyan-400">{act.approval_status}</span>
                    </span>
                  ))}
                </div>
              )}
            </div>
          )}
        </div>
      )}
    </div>
  );
};
