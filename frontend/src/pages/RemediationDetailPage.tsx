import React, { useState } from 'react';
import { useParams, Link } from 'react-router-dom';
import { useRemediation } from '../hooks/useRemediation';
import { StatusBadge } from '../components/common/StatusBadge';
import { RiskBadge } from '../components/common/RiskBadge';
import { LoadingState } from '../components/common/LoadingState';
import { ErrorState } from '../components/common/ErrorState';
import { ApprovalModal } from '../components/remediation/ApprovalModal';
import { RejectionModal } from '../components/remediation/RejectionModal';
import { ExecutionPanel } from '../components/remediation/ExecutionPanel';
import {
  Wrench,
  ShieldCheck,
  Ban,
  Send,
  Clock,
  Layers,
} from 'lucide-react';

export const RemediationDetailPage: React.FC = () => {
  const { remediationId } = useParams<{ remediationId: string }>();
  const [isApproveOpen, setIsApproveOpen] = useState(false);
  const [isRejectOpen, setIsRejectOpen] = useState(false);

  const {
    remediation,
    loading,
    actionLoading,
    error,
    refetch,
    submit,
    approve,
    reject,
    execute,
  } = useRemediation(remediationId);

  if (loading) {
    return <LoadingState message="Loading remediation proposal details..." />;
  }

  if (error || !remediation) {
    return (
      <ErrorState
        title="Remediation Not Found"
        message={error || `Remediation action with ID '${remediationId}' was not found.`}
        onRetry={refetch}
      />
    );
  }

  const isProposed = remediation.approval_status === 'PROPOSED';
  const isPendingApproval = remediation.approval_status === 'PENDING_APPROVAL';
  const isRejected = remediation.approval_status === 'REJECTED';

  // Lifecycle steps for visual stepper
  const lifecycleSteps = [
    { id: 'PROPOSED', label: '1. Proposed' },
    { id: 'PENDING_APPROVAL', label: '2. Pending Sign-Off' },
    { id: 'APPROVED', label: '3. Human Approved' },
    { id: 'EXECUTING', label: '4. Executing' },
    { id: 'COMPLETED', label: '5. Completed' },
  ];

  return (
    <div className="space-y-6" data-testid="remediation-detail-page">
      {/* Navigation */}
      <div>
        <Link
          to="/remediations"
          className="text-xs font-mono text-slate-400 hover:text-slate-200 inline-flex items-center gap-1.5 transition-colors"
        >
          ← Back to Remediation Console
        </Link>
      </div>

      {/* Main Header */}
      <div className="rounded-lg border border-slate-800 bg-slate-900/60 p-6 space-y-4 shadow-xl">
        <div className="flex flex-col md:flex-row md:items-start justify-between gap-4 pb-4 border-b border-slate-800">
          <div className="space-y-2">
            <div className="flex flex-wrap items-center gap-3">
              <RiskBadge risk={remediation.risk_level} />
              <StatusBadge status={remediation.approval_status} />
              <span className="font-mono text-xs px-2.5 py-1 rounded bg-slate-800 border border-slate-700 text-cyan-300 font-semibold">
                {String(remediation.parameters?.service || 'service')}
              </span>
            </div>

            <div className="flex items-center gap-3">
              <div className="p-2 rounded bg-slate-800 border border-slate-700 text-cyan-400">
                <Wrench className="w-5 h-5" />
              </div>
              <h1 className="text-2xl font-bold tracking-tight text-slate-100 font-mono">
                {remediation.action_name}
              </h1>
            </div>

            <div className="flex flex-wrap items-center gap-4 text-xs font-mono text-slate-400">
              <span className="flex items-center gap-1">
                <Clock className="w-3.5 h-3.5 text-slate-500" />
                Created: {new Date(remediation.created_at).toLocaleString()}
              </span>
              {remediation.approval_timestamp && (
                <span className="flex items-center gap-1 text-emerald-400">
                  <ShieldCheck className="w-3.5 h-3.5" />
                  Approved: {new Date(remediation.approval_timestamp).toLocaleString()}
                </span>
              )}
            </div>
          </div>

          {/* Lifecycle Action Buttons */}
          <div className="flex flex-wrap items-center gap-2">
            {isProposed && (
              <button
                onClick={() => submit('Submitted for engineering lead authorization')}
                disabled={actionLoading}
                className="inline-flex items-center gap-2 px-4 py-2 rounded-md bg-amber-600 hover:bg-amber-500 disabled:bg-amber-950 text-white font-mono text-xs font-bold transition-colors"
                data-testid="submit-approval-btn"
              >
                <Send className="w-3.5 h-3.5" />
                Submit for Approval
              </button>
            )}

            {isPendingApproval && (
              <>
                <button
                  onClick={() => setIsRejectOpen(true)}
                  disabled={actionLoading}
                  className="inline-flex items-center gap-2 px-3.5 py-2 rounded-md bg-rose-950/80 hover:bg-rose-900 border border-rose-800 text-rose-300 font-mono text-xs font-semibold transition-colors"
                  data-testid="open-reject-btn"
                >
                  <Ban className="w-3.5 h-3.5" />
                  Reject
                </button>

                <button
                  onClick={() => setIsApproveOpen(true)}
                  disabled={actionLoading}
                  className="inline-flex items-center gap-2 px-4 py-2 rounded-md bg-emerald-600 hover:bg-emerald-500 disabled:bg-emerald-950 text-white font-mono text-xs font-bold transition-colors"
                  data-testid="open-approve-btn"
                >
                  <ShieldCheck className="w-3.5 h-3.5" />
                  Approve Remediation
                </button>
              </>
            )}
          </div>
        </div>

        {/* Visual Lifecycle Stepper */}
        <div className="py-2">
          <span className="text-[11px] font-mono text-slate-500 uppercase tracking-wider block mb-2">
            Governance Lifecycle Trail
          </span>
          <div className="grid grid-cols-2 sm:grid-cols-5 gap-2">
            {lifecycleSteps.map((step, idx) => {
              let stepState = 'pending';
              if (isRejected && step.id !== 'PROPOSED') {
                stepState = 'rejected';
              } else if (remediation.approval_status === step.id) {
                stepState = 'current';
              } else if (
                (remediation.approval_status === 'APPROVED' && idx < 2) ||
                (remediation.approval_status === 'EXECUTING' && idx < 3) ||
                (remediation.approval_status === 'COMPLETED' && idx < 4)
              ) {
                stepState = 'completed';
              }

              return (
                <div
                  key={step.id}
                  className={`p-2.5 rounded border text-center font-mono text-xs ${
                    stepState === 'current'
                      ? 'bg-cyan-950/80 border-cyan-700 text-cyan-300 font-bold'
                      : stepState === 'completed'
                      ? 'bg-emerald-950/40 border-emerald-900 text-emerald-400'
                      : stepState === 'rejected'
                      ? 'bg-slate-950 border-slate-900 text-slate-600 line-through'
                      : 'bg-slate-950/40 border-slate-800/60 text-slate-500'
                  }`}
                >
                  {step.label}
                </div>
              );
            })}
          </div>
        </div>
      </div>

      {/* Parameter Breakdown & Impact Analysis */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* Parameters */}
        <div className="rounded-lg border border-slate-800 bg-slate-900/50 p-6 space-y-4">
          <div className="flex items-center gap-2 pb-2 border-b border-slate-800">
            <Layers className="w-4 h-4 text-cyan-400" />
            <h3 className="text-sm font-bold text-slate-200 uppercase tracking-wider font-mono">
              Action Parameter Specifications
            </h3>
          </div>

          <div className="space-y-3 font-mono text-xs">
            {Object.entries(remediation.parameters || {}).map(([key, val]) => (
              <div
                key={key}
                className="flex items-center justify-between p-2 rounded bg-slate-950 border border-slate-800/80"
              >
                <span className="text-slate-400">{key}:</span>
                <span className="text-cyan-300 font-semibold">{String(val)}</span>
              </div>
            ))}
          </div>

          <div className="space-y-1 pt-2">
            <span className="text-xs font-mono text-slate-400 uppercase tracking-wider block">
              Technical Justification Reasoning:
            </span>
            <p className="text-xs font-mono text-slate-200 bg-slate-950 p-3 rounded border border-slate-800 leading-relaxed">
              {remediation.reasoning}
            </p>
          </div>
        </div>

        {/* Expected Impact & Rollback Plan */}
        <div className="rounded-lg border border-slate-800 bg-slate-900/50 p-6 space-y-4">
          <div className="flex items-center gap-2 pb-2 border-b border-slate-800">
            <ShieldCheck className="w-4 h-4 text-cyan-400" />
            <h3 className="text-sm font-bold text-slate-200 uppercase tracking-wider font-mono">
              Impact & Rollback Strategy
            </h3>
          </div>

          <div className="space-y-3 font-mono text-xs">
            <div>
              <span className="text-[11px] text-slate-400 uppercase block mb-1">
                Expected System Impact:
              </span>
              <p className="p-3 rounded bg-slate-950 border border-slate-800 text-slate-300 leading-relaxed">
                {remediation.expected_impact ||
                  'No significant customer downtime expected. Service instances restart sequentially.'}
              </p>
            </div>

            <div>
              <span className="text-[11px] text-slate-400 uppercase block mb-1">
                Contingency Rollback Plan:
              </span>
              <p className="p-3 rounded bg-slate-950 border border-slate-800 text-slate-300 leading-relaxed">
                {remediation.rollback_plan ||
                  'Re-deploy previous stable configuration if error rates do not normalize within 5 minutes.'}
              </p>
            </div>
          </div>
        </div>
      </div>

      {/* Execution Controller Section (Strictly gated to APPROVED status) */}
      <ExecutionPanel
        remediation={remediation}
        onExecute={execute}
        isLoading={actionLoading}
      />

      {/* Modals for Approval and Rejection */}
      <ApprovalModal
        isOpen={isApproveOpen}
        onClose={() => setIsApproveOpen(false)}
        remediation={remediation}
        onApprove={approve}
        isLoading={actionLoading}
      />

      <RejectionModal
        isOpen={isRejectOpen}
        onClose={() => setIsRejectOpen(false)}
        remediation={remediation}
        onReject={reject}
        isLoading={actionLoading}
      />
    </div>
  );
};
