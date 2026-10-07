import React, { useState } from 'react';
import { useRemediations } from '../hooks/useRemediations';
import { RemediationCard } from '../components/remediation/RemediationCard';
import { LoadingState } from '../components/common/LoadingState';
import { ErrorState } from '../components/common/ErrorState';
import { EmptyState } from '../components/common/EmptyState';
import { Filter, RefreshCw, ShieldAlert } from 'lucide-react';

export const RemediationListPage: React.FC = () => {
  const [statusFilter, setStatusFilter] = useState<string>('');
  const [riskFilter, setRiskFilter] = useState<string>('');

  const { remediations, loading, error, refetch } = useRemediations({
    status: statusFilter || undefined,
  });

  const filteredRemediations = remediations.filter((rem) => {
    if (riskFilter && rem.risk_level !== riskFilter) return false;
    return true;
  });

  return (
    <div className="space-y-6" data-testid="remediation-list-page">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-4 border-b border-slate-800">
        <div>
          <div className="flex items-center gap-2">
            <span className="p-1 rounded bg-amber-950 border border-amber-800 text-amber-400">
              <ShieldAlert className="w-3.5 h-3.5" />
            </span>
            <span className="text-xs font-mono font-semibold uppercase tracking-wider text-amber-400">
              Human-in-the-Loop Governance
            </span>
          </div>
          <h1 className="text-2xl font-bold tracking-tight text-slate-100 mt-1">
            Remediation Governance Console
          </h1>
          <p className="text-xs font-mono text-slate-400 mt-0.5">
            Phase 7 proposals awaiting human approval or dispatching simulated actions
          </p>
        </div>

        <button
          onClick={() => refetch()}
          className="inline-flex items-center gap-2 px-3 py-1.5 rounded-md bg-slate-800 hover:bg-slate-700 text-slate-300 font-mono text-xs font-medium border border-slate-700 transition-colors self-start sm:self-auto"
        >
          <RefreshCw className="w-3.5 h-3.5" />
          Refresh
        </button>
      </div>

      {/* Filter Bar */}
      <div className="rounded-lg border border-slate-800 bg-slate-900/50 p-4 flex flex-wrap gap-4 items-center justify-between">
        <div className="flex flex-wrap items-center gap-4">
          <div className="flex items-center gap-2 text-xs font-mono text-slate-400">
            <Filter className="w-3.5 h-3.5 text-slate-500" />
            <span>Approval Lifecycle:</span>
            <select
              value={statusFilter}
              onChange={(e) => setStatusFilter(e.target.value)}
              className="bg-slate-950 border border-slate-800 rounded px-2.5 py-1 text-xs font-mono text-slate-200 focus:outline-none focus:border-cyan-500"
            >
              <option value="">All Statuses</option>
              <option value="PROPOSED">PROPOSED</option>
              <option value="PENDING_APPROVAL">PENDING_APPROVAL</option>
              <option value="APPROVED">APPROVED</option>
              <option value="EXECUTING">EXECUTING</option>
              <option value="COMPLETED">COMPLETED</option>
              <option value="REJECTED">REJECTED</option>
              <option value="FAILED">FAILED</option>
            </select>
          </div>

          <div className="flex items-center gap-2 text-xs font-mono text-slate-400">
            <span>Risk Level:</span>
            <select
              value={riskFilter}
              onChange={(e) => setRiskFilter(e.target.value)}
              className="bg-slate-950 border border-slate-800 rounded px-2.5 py-1 text-xs font-mono text-slate-200 focus:outline-none focus:border-cyan-500"
            >
              <option value="">All Risk Levels</option>
              <option value="HIGH">HIGH</option>
              <option value="MEDIUM">MEDIUM</option>
              <option value="LOW">LOW</option>
            </select>
          </div>
        </div>

        <div className="text-xs font-mono text-slate-500">
          Total: <span className="text-slate-300 font-semibold">{filteredRemediations.length}</span>{' '}
          proposals
        </div>
      </div>

      {/* List Display */}
      {loading ? (
        <LoadingState message="Loading remediation proposals..." />
      ) : error ? (
        <ErrorState
          title="Failed to Load Remediations"
          message={error}
          onRetry={refetch}
        />
      ) : filteredRemediations.length === 0 ? (
        <EmptyState
          title="No Remediation Proposals Found"
          message={
            statusFilter || riskFilter
              ? 'No remediation actions match your current filter settings.'
              : 'No remediation proposals have been generated yet. Run an investigation to generate recommendations.'
          }
        />
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {filteredRemediations.map((rem) => (
            <RemediationCard key={rem.id} remediation={rem} />
          ))}
        </div>
      )}
    </div>
  );
};
