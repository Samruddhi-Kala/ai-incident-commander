import React from 'react';
import { Link } from 'react-router-dom';
import { useIncidents } from '../hooks/useIncidents';
import { useRemediations } from '../hooks/useRemediations';
import { SeverityBadge } from '../components/common/SeverityBadge';
import { StatusBadge } from '../components/common/StatusBadge';
import { RiskBadge } from '../components/common/RiskBadge';
import { LoadingState } from '../components/common/LoadingState';
import { ErrorState } from '../components/common/ErrorState';
import {
  AlertTriangle,
  Flame,
  Search,
  CheckSquare,
  ArrowRight,
  ShieldCheck,
  Terminal,
  Server,
} from 'lucide-react';

export const OverviewPage: React.FC = () => {
  const {
    incidents,
    loading: incidentsLoading,
    error: incidentsError,
    refetch: refetchIncidents,
  } = useIncidents({ pageSize: 50 });

  const {
    remediations,
    loading: remediationsLoading,
    error: remediationsError,
    refetch: refetchRemediations,
  } = useRemediations();

  if (incidentsLoading || remediationsLoading) {
    return <LoadingState message="Connecting to AI Incident Commander telemetry..." />;
  }

  if (incidentsError || remediationsError) {
    return (
      <ErrorState
        title="Failed to Load Operational Telemetry"
        message={incidentsError || remediationsError || 'Network error'}
        onRetry={() => {
          refetchIncidents();
          refetchRemediations();
        }}
      />
    );
  }

  // Derive metrics strictly from real backend responses (NO FAKE METRICS)
  const activeIncidents = incidents.filter(
    (i) => i.status === 'Triggered' || i.status === 'Investigating'
  );
  const criticalIncidents = incidents.filter((i) => i.severity === 'SEV-1');
  const investigationsInProgress = incidents.filter(
    (i) => i.investigation?.status === 'In Progress'
  );
  const pendingApprovals = remediations.filter(
    (r) => r.approval_status === 'PENDING_APPROVAL'
  );

  return (
    <div className="space-y-8" data-testid="overview-page">
      {/* Top Banner */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 p-6 rounded-lg border border-slate-800 bg-gradient-to-r from-slate-900 via-slate-900 to-slate-950 shadow-xl">
        <div className="space-y-1">
          <div className="flex items-center gap-2">
            <span className="w-2 h-2 rounded-full bg-cyan-400 animate-ping" />
            <span className="text-xs font-mono font-bold tracking-wider uppercase text-cyan-400">
              Operations Command Center
            </span>
          </div>
          <h1 className="text-2xl font-bold tracking-tight text-slate-100">
            Autonomous Diagnostic Fleet Overview
          </h1>
          <p className="text-xs font-mono text-slate-400 max-w-xl">
            Live incident stream monitored by LangGraph agent with strict human authorization
            barriers for consequential mitigation.
          </p>
        </div>

        <div className="flex items-center gap-3">
          <Link
            to="/incidents"
            className="inline-flex items-center gap-2 px-4 py-2 rounded-md bg-cyan-600 hover:bg-cyan-500 text-white font-mono text-xs font-semibold shadow-lg shadow-cyan-950 transition-colors"
          >
            <Server className="w-4 h-4" />
            Inspect Incidents
          </Link>
        </div>
      </div>

      {/* KPI Cards — Derived exclusively from real backend data */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        {/* Active Incidents */}
        <div className="rounded-lg border border-slate-800 bg-slate-900/60 p-5 space-y-2">
          <div className="flex items-center justify-between text-slate-400">
            <span className="text-xs font-mono uppercase tracking-wider">Active Incidents</span>
            <AlertTriangle className="w-4 h-4 text-amber-400" />
          </div>
          <div className="flex items-baseline gap-2">
            <span className="text-3xl font-bold font-mono text-slate-100">
              {activeIncidents.length}
            </span>
            <span className="text-xs font-mono text-slate-500">/ {incidents.length} total</span>
          </div>
          <p className="text-[11px] font-mono text-slate-400">
            Unmitigated triggers requiring response
          </p>
        </div>

        {/* Critical Incidents */}
        <div className="rounded-lg border border-slate-800 bg-slate-900/60 p-5 space-y-2">
          <div className="flex items-center justify-between text-slate-400">
            <span className="text-xs font-mono uppercase tracking-wider">Critical (SEV-1)</span>
            <Flame className="w-4 h-4 text-rose-500" />
          </div>
          <div className="flex items-baseline gap-2">
            <span className="text-3xl font-bold font-mono text-rose-400">
              {criticalIncidents.length}
            </span>
            <span className="text-xs font-mono text-slate-500">high priority</span>
          </div>
          <p className="text-[11px] font-mono text-slate-400">P99 outage / user impact alerts</p>
        </div>

        {/* Investigations In Progress */}
        <div className="rounded-lg border border-slate-800 bg-slate-900/60 p-5 space-y-2">
          <div className="flex items-center justify-between text-slate-400">
            <span className="text-xs font-mono uppercase tracking-wider">Investigations Active</span>
            <Search className="w-4 h-4 text-cyan-400" />
          </div>
          <div className="flex items-baseline gap-2">
            <span className="text-3xl font-bold font-mono text-cyan-300">
              {investigationsInProgress.length}
            </span>
            <span className="text-xs font-mono text-slate-500">evaluating telemetry</span>
          </div>
          <p className="text-[11px] font-mono text-slate-400">Automated diagnostic cycles</p>
        </div>

        {/* Pending Remediation Approvals */}
        <div className="rounded-lg border border-slate-800 bg-slate-900/60 p-5 space-y-2">
          <div className="flex items-center justify-between text-slate-400">
            <span className="text-xs font-mono uppercase tracking-wider">Pending Approvals</span>
            <CheckSquare className="w-4 h-4 text-amber-400" />
          </div>
          <div className="flex items-baseline gap-2">
            <span className="text-3xl font-bold font-mono text-amber-300">
              {pendingApprovals.length}
            </span>
            <span className="text-xs font-mono text-slate-500">awaiting human review</span>
          </div>
          <p className="text-[11px] font-mono text-slate-400">HITL governance gated</p>
        </div>
      </div>

      {/* Main Grid: Active Incidents & Pending Remediation Approvals */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Active Incidents Section */}
        <div className="rounded-lg border border-slate-800 bg-slate-900/40 p-6 space-y-4">
          <div className="flex items-center justify-between pb-3 border-b border-slate-800">
            <div>
              <h2 className="text-sm font-bold text-slate-200 uppercase tracking-wider font-mono">
                Active Telemetry Incidents
              </h2>
              <p className="text-xs text-slate-400 font-mono mt-0.5">
                Real-time incident records from monitoring systems
              </p>
            </div>
            <Link
              to="/incidents"
              className="text-xs font-mono text-cyan-400 hover:text-cyan-300 flex items-center gap-1 font-semibold"
            >
              View all
              <ArrowRight className="w-3.5 h-3.5" />
            </Link>
          </div>

          <div className="space-y-3">
            {incidents.slice(0, 5).map((inc) => (
              <div
                key={inc.id}
                className="p-4 rounded-lg bg-slate-950/70 border border-slate-800/80 hover:border-slate-700 transition-colors flex flex-col sm:flex-row sm:items-center justify-between gap-3"
              >
                <div className="space-y-1 min-w-0">
                  <div className="flex items-center gap-2">
                    <SeverityBadge severity={inc.severity} size="sm" />
                    <StatusBadge status={inc.status} size="sm" />
                    <span className="font-mono text-xs text-slate-400 truncate">
                      {inc.service?.name || 'service'}
                    </span>
                  </div>
                  <h3 className="text-sm font-semibold text-slate-200 truncate">
                    {inc.title}
                  </h3>
                </div>

                <div className="flex items-center gap-2 shrink-0">
                  <Link
                    to={`/incidents/${inc.id}`}
                    className="px-3 py-1.5 rounded bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs font-mono font-medium transition-colors"
                  >
                    Details
                  </Link>
                  {inc.investigation && (
                    <Link
                      to={`/incidents/${inc.id}/investigation`}
                      className="px-3 py-1.5 rounded bg-cyan-950 hover:bg-cyan-900 text-cyan-300 border border-cyan-800 text-xs font-mono font-medium transition-colors flex items-center gap-1"
                    >
                      <Terminal className="w-3 h-3" />
                      INV
                    </Link>
                  )}
                </div>
              </div>
            ))}

            {incidents.length === 0 && (
              <p className="text-xs font-mono text-slate-500 py-6 text-center">
                No incident records found.
              </p>
            )}
          </div>
        </div>

        {/* Pending Remediation Approvals Section */}
        <div className="rounded-lg border border-slate-800 bg-slate-900/40 p-6 space-y-4">
          <div className="flex items-center justify-between pb-3 border-b border-slate-800">
            <div>
              <h2 className="text-sm font-bold text-slate-200 uppercase tracking-wider font-mono">
                Pending Remediation Approvals
              </h2>
              <p className="text-xs text-slate-400 font-mono mt-0.5">
                Proposals awaiting human sign-off before dispatch
              </p>
            </div>
            <Link
              to="/remediations"
              className="text-xs font-mono text-cyan-400 hover:text-cyan-300 flex items-center gap-1 font-semibold"
            >
              Console
              <ArrowRight className="w-3.5 h-3.5" />
            </Link>
          </div>

          <div className="space-y-3">
            {pendingApprovals.slice(0, 5).map((rem) => (
              <div
                key={rem.id}
                className="p-4 rounded-lg bg-slate-950/70 border border-amber-900/40 hover:border-amber-700/60 transition-colors space-y-2.5"
              >
                <div className="flex items-center justify-between gap-2">
                  <div className="flex items-center gap-2">
                    <span className="font-mono text-xs font-bold text-slate-200">
                      {rem.action_name}
                    </span>
                    <span className="font-mono text-[11px] text-cyan-300">
                      ({String(rem.parameters?.service || 'service')})
                    </span>
                  </div>
                  <RiskBadge risk={rem.risk_level} />
                </div>

                <p className="text-xs font-mono text-slate-400 line-clamp-2">
                  {rem.reasoning}
                </p>

                <div className="flex items-center justify-between pt-1 text-xs font-mono">
                  <span className="text-slate-500 text-[11px]">
                    {new Date(rem.created_at).toLocaleDateString()}
                  </span>
                  <Link
                    to={`/remediations/${rem.id}`}
                    className="text-amber-400 hover:text-amber-300 font-semibold flex items-center gap-1"
                  >
                    <ShieldCheck className="w-3.5 h-3.5" />
                    Review & Authorize
                  </Link>
                </div>
              </div>
            ))}

            {pendingApprovals.length === 0 && (
              <div className="text-center py-10 font-mono text-xs text-slate-500 space-y-1">
                <CheckSquare className="w-8 h-8 text-slate-600 mx-auto mb-2" />
                <p>No actions pending human approval.</p>
                <p className="text-slate-600 text-[11px]">All proposals reviewed or completed.</p>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};
