import React, { useState } from 'react';
import { useParams, Link, useNavigate } from 'react-router-dom';
import { useIncident } from '../hooks/useIncident';
import { useInvestigation } from '../hooks/useInvestigation';
import { SeverityBadge } from '../components/common/SeverityBadge';
import { StatusBadge } from '../components/common/StatusBadge';
import { LoadingState } from '../components/common/LoadingState';
import { ErrorState } from '../components/common/ErrorState';
import {
  Terminal,
  Play,
  ArrowRight,
  Clock,
  Server,
  Layers,
  ShieldCheck,
  Loader2,
  GitBranch,
} from 'lucide-react';

export const IncidentDetailPage: React.FC = () => {
  const { incidentId } = useParams<{ incidentId: string }>();
  const navigate = useNavigate();
  const [startError, setStartError] = useState<string | null>(null);

  const { incident, loading: incidentLoading, error: incidentError, refetch } = useIncident(incidentId);
  const {
    investigation,
    loading: investigationLoading,
    running,
    startInvestigation,
  } = useInvestigation(incidentId);

  const handleStartInvestigation = async () => {
    setStartError(null);
    try {
      await startInvestigation(5);
      navigate(`/incidents/${incidentId}/investigation`);
    } catch (err: unknown) {
      setStartError(err instanceof Error ? err.message : 'Failed to launch investigation workflow.');
    }
  };

  if (incidentLoading || investigationLoading) {
    return <LoadingState message="Retrieving incident telemetry metadata..." />;
  }

  if (incidentError || !incident) {
    return (
      <ErrorState
        title="Incident Not Found"
        message={incidentError || `Incident with ID '${incidentId}' could not be located.`}
        onRetry={refetch}
      />
    );
  }

  const hasInvestigation = Boolean(investigation || incident.investigation);

  return (
    <div className="space-y-6" data-testid="incident-detail-page">
      {/* Back Link */}
      <div>
        <Link
          to="/incidents"
          className="text-xs font-mono text-slate-400 hover:text-slate-200 inline-flex items-center gap-1.5 transition-colors"
        >
          ← Back to Incident Console
        </Link>
      </div>

      {/* Incident Header Card */}
      <div className="rounded-lg border border-slate-800 bg-slate-900/60 p-6 shadow-xl space-y-4">
        <div className="flex flex-col md:flex-row md:items-start justify-between gap-4 pb-4 border-b border-slate-800">
          <div className="space-y-2">
            <div className="flex flex-wrap items-center gap-3">
              <SeverityBadge severity={incident.severity} />
              <StatusBadge status={incident.status} />
              <span className="font-mono text-xs px-2.5 py-1 rounded bg-slate-800 border border-slate-700 text-cyan-300 font-semibold">
                {incident.service?.name || 'service'}
              </span>
            </div>

            <h1 className="text-2xl font-bold tracking-tight text-slate-100">
              {incident.title}
            </h1>

            <div className="flex flex-wrap items-center gap-4 text-xs font-mono text-slate-400">
              <span className="flex items-center gap-1.5">
                <Clock className="w-3.5 h-3.5 text-slate-500" />
                Created: {new Date(incident.created_at).toLocaleString()}
              </span>
              {incident.resolved_at && (
                <span className="flex items-center gap-1.5 text-emerald-400">
                  <ShieldCheck className="w-3.5 h-3.5" />
                  Resolved: {new Date(incident.resolved_at).toLocaleString()}
                </span>
              )}
            </div>
          </div>

          {/* Action Trigger Button */}
          <div className="shrink-0 flex flex-col gap-2">
            {hasInvestigation ? (
              <Link
                to={`/incidents/${incident.id}/investigation`}
                className="inline-flex items-center gap-2 px-5 py-2.5 rounded-md bg-cyan-600 hover:bg-cyan-500 text-white font-mono text-xs font-bold shadow-lg shadow-cyan-950 transition-colors"
                data-testid="view-investigation-btn"
              >
                <Terminal className="w-4 h-4" />
                View Investigation
                <ArrowRight className="w-4 h-4" />
              </Link>
            ) : (
              <button
                onClick={handleStartInvestigation}
                disabled={running}
                className="inline-flex items-center gap-2 px-5 py-2.5 rounded-md bg-emerald-600 hover:bg-emerald-500 disabled:bg-emerald-950 disabled:text-emerald-400 text-white font-mono text-xs font-bold shadow-lg shadow-emerald-950 transition-colors"
                data-testid="start-investigation-btn"
              >
                {running ? (
                  <>
                    <Loader2 className="w-4 h-4 animate-spin" />
                    Agent Orchestrating...
                  </>
                ) : (
                  <>
                    <Play className="w-4 h-4 fill-current" />
                    Start AI Investigation
                  </>
                )}
              </button>
            )}
          </div>
        </div>

        {/* Error notification */}
        {startError && (
          <div className="p-3.5 rounded bg-rose-950/80 border border-rose-800 text-rose-300 text-xs font-mono">
            {startError}
          </div>
        )}

        {/* Description */}
        <div className="space-y-1.5 pt-2">
          <span className="text-xs font-mono uppercase tracking-wider text-slate-400 font-semibold">
            Alert Description & Telemetry Context
          </span>
          <p className="text-sm font-mono text-slate-200 bg-slate-950/80 p-4 rounded-lg border border-slate-800/80 leading-relaxed">
            {incident.description}
          </p>
        </div>
      </div>

      {/* Grid: Affected Service Info & Investigation Status */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* Service Details */}
        <div className="rounded-lg border border-slate-800 bg-slate-900/50 p-6 space-y-4">
          <div className="flex items-center gap-2 pb-3 border-b border-slate-800">
            <Server className="w-4 h-4 text-cyan-400" />
            <h2 className="text-sm font-bold text-slate-200 uppercase tracking-wider font-mono">
              Affected Service Topology
            </h2>
          </div>

          <div className="space-y-3 font-mono text-xs">
            <div className="flex justify-between py-1 border-b border-slate-800/50">
              <span className="text-slate-500">Service Name:</span>
              <span className="text-cyan-300 font-bold">{incident.service?.name}</span>
            </div>
            <div className="flex justify-between py-1 border-b border-slate-800/50">
              <span className="text-slate-500">Tier:</span>
              <span className="text-slate-200">{incident.service?.tier || 'Tier-2'}</span>
            </div>
            <div className="flex justify-between py-1 border-b border-slate-800/50">
              <span className="text-slate-500">Owner Team:</span>
              <span className="text-slate-200">{incident.service?.owner_team || 'Core Ops'}</span>
            </div>
            <div className="py-1">
              <span className="text-slate-500 block mb-1">Dependencies:</span>
              <div className="flex flex-wrap gap-1.5">
                {incident.service?.dependencies?.length ? (
                  incident.service.dependencies.map((dep, idx) => (
                    <span
                      key={idx}
                      className="px-2 py-0.5 rounded bg-slate-800 text-slate-300 text-[11px] border border-slate-700"
                    >
                      {dep}
                    </span>
                  ))
                ) : (
                  <span className="text-slate-600">None registered</span>
                )}
              </div>
            </div>
          </div>
        </div>

        {/* Investigation Brief */}
        <div className="rounded-lg border border-slate-800 bg-slate-900/50 p-6 space-y-4">
          <div className="flex items-center gap-2 pb-3 border-b border-slate-800">
            <Layers className="w-4 h-4 text-cyan-400" />
            <h2 className="text-sm font-bold text-slate-200 uppercase tracking-wider font-mono">
              Investigation Agent Status
            </h2>
          </div>

          {hasInvestigation ? (
            <div className="space-y-3 font-mono text-xs">
              <div className="flex justify-between py-1 border-b border-slate-800/50">
                <span className="text-slate-500">Investigation Status:</span>
                <StatusBadge
                  status={investigation?.status || incident.investigation?.status || 'Unknown'}
                  size="sm"
                />
              </div>

              {investigation?.probable_root_cause && (
                <div className="py-2 space-y-1">
                  <span className="text-slate-500 block">Probable Root Cause:</span>
                  <p className="text-slate-200 bg-slate-950 p-2.5 rounded border border-slate-800 text-xs line-clamp-3">
                    {investigation.probable_root_cause}
                  </p>
                </div>
              )}

              <div className="pt-2">
                <Link
                  to={`/incidents/${incident.id}/investigation`}
                  className="inline-flex items-center gap-1.5 text-xs text-cyan-400 hover:text-cyan-300 font-semibold"
                >
                  <GitBranch className="w-3.5 h-3.5" />
                  Inspect Full Diagnostic Graph & Timeline →
                </Link>
              </div>
            </div>
          ) : (
            <div className="text-center py-8 font-mono text-xs text-slate-500 space-y-2">
              <p>No investigation workflow has been launched for this incident.</p>
              <p className="text-slate-600 text-[11px]">
                Click "Start AI Investigation" above to trigger LangGraph orchestrator.
              </p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
