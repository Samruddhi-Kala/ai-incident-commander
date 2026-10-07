import React from 'react';
import { InvestigationStepInfo } from '../../types/investigation';
import { CheckCircle2, Circle, AlertCircle, Clock } from 'lucide-react';

export interface InvestigationTimelineProps {
  steps: InvestigationStepInfo[];
}

export const InvestigationTimeline: React.FC<InvestigationTimelineProps> = ({ steps }) => {
  const sortedSteps = [...steps].sort((a, b) => a.step_order - b.step_order);

  return (
    <div
      className="rounded-lg border border-slate-800 bg-slate-900/40 p-6 space-y-4"
      data-testid="investigation-timeline"
    >
      <div className="flex items-center justify-between pb-3 border-b border-slate-800">
        <div>
          <h2 className="text-sm font-semibold text-slate-200 uppercase tracking-wider font-mono">
            Investigation Lifecycle Timeline
          </h2>
          <p className="text-xs text-slate-400 font-mono mt-0.5">
            Sequential execution trail through LangGraph state machine
          </p>
        </div>
        <span className="text-xs font-mono px-2.5 py-1 rounded bg-slate-800 text-slate-300 border border-slate-700">
          {sortedSteps.length} Steps Recorded
        </span>
      </div>

      <div className="relative pl-6 space-y-6 before:absolute before:left-2.5 before:top-3 before:bottom-3 before:w-0.5 before:bg-slate-800">
        {sortedSteps.map((step) => {
          const isCompleted = step.status.toLowerCase() === 'completed';
          const isFailed = step.status.toLowerCase() === 'failed';
          const isInProgress = step.status.toLowerCase() === 'in progress' || step.status.toLowerCase() === 'running';

          return (
            <div
              key={step.step_order}
              className="relative group transition-all"
              data-testid={`timeline-step-${step.step_order}`}
            >
              {/* Node Icon */}
              <div className="absolute -left-6 top-1 transform -translate-x-1/2 flex items-center justify-center bg-slate-950 rounded-full p-0.5 z-10">
                {isCompleted ? (
                  <CheckCircle2 className="w-4 h-4 text-emerald-400" />
                ) : isFailed ? (
                  <AlertCircle className="w-4 h-4 text-rose-400" />
                ) : isInProgress ? (
                  <Clock className="w-4 h-4 text-cyan-400 animate-spin" />
                ) : (
                  <Circle className="w-4 h-4 text-slate-600" />
                )}
              </div>

              {/* Step Card */}
              <div
                className={`rounded-lg border p-4 transition-colors ${
                  isCompleted
                    ? 'border-slate-800 bg-slate-900/60 hover:border-slate-700'
                    : isFailed
                    ? 'border-rose-900/80 bg-rose-950/20'
                    : isInProgress
                    ? 'border-cyan-800/80 bg-cyan-950/20'
                    : 'border-slate-800/50 bg-slate-950/40 text-slate-500'
                }`}
              >
                <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 mb-2">
                  <div className="flex items-center gap-2">
                    <span className="font-mono text-xs font-bold px-1.5 py-0.5 rounded bg-slate-800 text-slate-300 border border-slate-700">
                      Step {step.step_order}
                    </span>
                    <h3 className="text-sm font-semibold text-slate-200">
                      {step.title}
                    </h3>
                  </div>

                  <div className="flex items-center gap-3 text-xs font-mono">
                    <span
                      className={`px-2 py-0.5 rounded text-[11px] font-medium uppercase border ${
                        isCompleted
                          ? 'bg-emerald-950/80 text-emerald-300 border-emerald-800'
                          : isFailed
                          ? 'bg-rose-950/80 text-rose-300 border-rose-800'
                          : isInProgress
                          ? 'bg-cyan-950/80 text-cyan-300 border-cyan-800'
                          : 'bg-slate-900 text-slate-400 border-slate-800'
                      }`}
                    >
                      {step.status}
                    </span>
                    <span className="text-slate-500">
                      {new Date(step.created_at).toLocaleTimeString()}
                    </span>
                  </div>
                </div>

                {step.output_summary && (
                  <p className="text-xs text-slate-300 font-mono leading-relaxed bg-slate-950/60 p-3 rounded border border-slate-800/80 mt-2">
                    {step.output_summary}
                  </p>
                )}
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
};
