import React from 'react';
import { RemediationActionResponse } from '../../types/remediation';
import { Play, CheckCircle2, AlertOctagon, Clock, ShieldAlert, Loader2 } from 'lucide-react';

export interface ExecutionPanelProps {
  remediation: RemediationActionResponse;
  onExecute: () => Promise<unknown>;
  isLoading?: boolean;
}

export const ExecutionPanel: React.FC<ExecutionPanelProps> = ({
  remediation,
  onExecute,
  isLoading = false,
}) => {
  const isApproved = remediation.approval_status === 'APPROVED';
  const isCompleted = remediation.approval_status === 'COMPLETED';
  const isFailed = remediation.approval_status === 'FAILED';
  const isExecuting = remediation.approval_status === 'EXECUTING';

  return (
    <div
      className="rounded-lg border border-slate-800 bg-slate-900/60 p-6 space-y-4"
      data-testid="execution-panel"
    >
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 pb-3 border-b border-slate-800">
        <div>
          <div className="flex items-center gap-2">
            <span className="px-2 py-0.5 rounded bg-amber-950/80 text-amber-300 border border-amber-800 text-[10px] font-mono font-bold uppercase tracking-wider">
              SIMULATED EXECUTION ENVIRONMENT
            </span>
          </div>
          <h3 className="text-base font-bold text-slate-100 font-mono mt-1">
            Remediation Execution Controller
          </h3>
          <p className="text-xs text-slate-400 font-mono">
            Deterministic zero-side-effect testbed enforcing the human authorization boundary.
          </p>
        </div>

        {/* Execution trigger button: STRICTLY only appears when APPROVED */}
        {isApproved && (
          <button
            onClick={onExecute}
            disabled={isLoading}
            className="inline-flex items-center gap-2 px-5 py-2.5 rounded-md bg-cyan-600 hover:bg-cyan-500 disabled:bg-cyan-950 disabled:text-cyan-400 text-white font-mono text-xs font-bold shadow-lg shadow-cyan-950 transition-colors"
            data-testid="execute-remediation-btn"
          >
            {isLoading ? (
              <>
                <Loader2 className="w-4 h-4 animate-spin" />
                Dispatching Simulated Action...
              </>
            ) : (
              <>
                <Play className="w-4 h-4 fill-current" />
                Execute Remediation
              </>
            )}
          </button>
        )}
      </div>

      {/* When NOT approved, show boundary notice */}
      {!isApproved && !isCompleted && !isFailed && !isExecuting && (
        <div
          className="rounded-lg bg-slate-950 border border-slate-800/80 p-4 text-xs font-mono text-slate-400 flex items-start gap-3"
          data-testid="execution-blocked-notice"
        >
          <ShieldAlert className="w-4 h-4 text-amber-400 shrink-0 mt-0.5" />
          <div className="space-y-1">
            <span className="font-semibold text-slate-300">Execution Boundary Enforced</span>
            <p>
              Remediation execution is blocked until this action receives explicit human authorization
              and enters <span className="text-emerald-400 font-bold">APPROVED</span> status.
            </p>
          </div>
        </div>
      )}

      {/* Executing State */}
      {isExecuting && (
        <div className="rounded-lg bg-cyan-950/40 border border-cyan-800/80 p-4 flex items-center gap-3 font-mono text-xs text-cyan-200">
          <Loader2 className="w-5 h-5 animate-spin text-cyan-400 shrink-0" />
          <div>
            <span className="font-bold">Simulated Execution In Progress...</span>
            <p className="text-[11px] text-cyan-300/80 mt-0.5">
              Target tool adapter is evaluating parameter payload and recording audit lineage.
            </p>
          </div>
        </div>
      )}

      {/* Completed State */}
      {isCompleted && remediation.execution_result && (
        <div
          className="rounded-lg bg-emerald-950/30 border border-emerald-800/80 p-4 space-y-3 font-mono text-xs"
          data-testid="execution-result-completed"
        >
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2 text-emerald-300 font-bold">
              <CheckCircle2 className="w-4 h-4 text-emerald-400" />
              <span>Execution Status: COMPLETED (Simulated)</span>
            </div>
            {remediation.execution_result.execution_time_ms !== undefined && (
              <span className="flex items-center gap-1 text-slate-400">
                <Clock className="w-3.5 h-3.5" />
                Duration: {remediation.execution_result.execution_time_ms} ms
              </span>
            )}
          </div>

          <div className="rounded bg-slate-950 p-3 border border-slate-800">
            <span className="text-[10px] text-slate-500 uppercase tracking-wider block mb-1">
              Simulated Execution Output
            </span>
            <pre className="text-[11px] text-emerald-200/90 overflow-x-auto">
              {JSON.stringify(remediation.execution_result.output || remediation.execution_result, null, 2)}
            </pre>
          </div>
        </div>
      )}

      {/* Failed State */}
      {isFailed && remediation.execution_result && (
        <div
          className="rounded-lg bg-rose-950/30 border border-rose-800/80 p-4 space-y-3 font-mono text-xs"
          data-testid="execution-result-failed"
        >
          <div className="flex items-center gap-2 text-rose-300 font-bold">
            <AlertOctagon className="w-4 h-4 text-rose-400" />
            <span>Execution Status: FAILED</span>
          </div>

          <div className="rounded bg-slate-950 p-3 border border-slate-800 text-rose-300">
            <span className="text-[10px] text-rose-400 uppercase tracking-wider block mb-1">
              Failure Reason
            </span>
            <p>
              {remediation.execution_result.failure_reason ||
                remediation.execution_result.error ||
                'Remediation simulation encountered an error.'}
            </p>
          </div>
        </div>
      )}
    </div>
  );
};
