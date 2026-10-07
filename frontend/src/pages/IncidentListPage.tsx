import React, { useState } from 'react';
import { Link } from 'react-router-dom';
import { useIncidents } from '../hooks/useIncidents';
import { SeverityBadge } from '../components/common/SeverityBadge';
import { StatusBadge } from '../components/common/StatusBadge';
import { LoadingState } from '../components/common/LoadingState';
import { ErrorState } from '../components/common/ErrorState';
import { EmptyState } from '../components/common/EmptyState';
import { Filter, Search, ArrowRight, Terminal, RefreshCw } from 'lucide-react';

export const IncidentListPage: React.FC = () => {
  const [severityFilter, setSeverityFilter] = useState<string>('');
  const [statusFilter, setStatusFilter] = useState<string>('');
  const [searchTerm, setSearchTerm] = useState<string>('');

  const { incidents, loading, error, refetch } = useIncidents({
    severity: severityFilter || undefined,
    status: statusFilter || undefined,
    pageSize: 100,
  });

  const filteredIncidents = incidents.filter((inc) => {
    if (!searchTerm) return true;
    const term = searchTerm.toLowerCase();
    return (
      inc.title.toLowerCase().includes(term) ||
      inc.description.toLowerCase().includes(term) ||
      inc.service?.name.toLowerCase().includes(term)
    );
  });

  return (
    <div className="space-y-6" data-testid="incident-list-page">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-4 border-b border-slate-800">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-slate-100">
            Incident Console
          </h1>
          <p className="text-xs font-mono text-slate-400 mt-1">
            Browse and investigate platform telemetry alerts and operational triggers
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

      {/* Filters Bar */}
      <div className="rounded-lg border border-slate-800 bg-slate-900/50 p-4 flex flex-col md:flex-row gap-4 justify-between items-center">
        {/* Search Input */}
        <div className="relative w-full md:w-80">
          <Search className="w-4 h-4 text-slate-500 absolute left-3 top-1/2 transform -translate-y-1/2" />
          <input
            type="text"
            placeholder="Search incidents or services..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="w-full pl-9 pr-3 py-1.5 rounded-md bg-slate-950 border border-slate-800 text-xs font-mono text-slate-200 placeholder:text-slate-600 focus:outline-none focus:border-cyan-500"
          />
        </div>

        {/* Filter Dropdowns */}
        <div className="flex flex-wrap items-center gap-3 w-full md:w-auto">
          <div className="flex items-center gap-2 text-xs font-mono text-slate-400">
            <Filter className="w-3.5 h-3.5 text-slate-500" />
            <span>Severity:</span>
            <select
              value={severityFilter}
              onChange={(e) => setSeverityFilter(e.target.value)}
              className="bg-slate-950 border border-slate-800 rounded px-2.5 py-1 text-xs font-mono text-slate-200 focus:outline-none focus:border-cyan-500"
            >
              <option value="">All Severities</option>
              <option value="SEV-1">SEV-1</option>
              <option value="SEV-2">SEV-2</option>
              <option value="SEV-3">SEV-3</option>
              <option value="SEV-4">SEV-4</option>
            </select>
          </div>

          <div className="flex items-center gap-2 text-xs font-mono text-slate-400">
            <span>Status:</span>
            <select
              value={statusFilter}
              onChange={(e) => setStatusFilter(e.target.value)}
              className="bg-slate-950 border border-slate-800 rounded px-2.5 py-1 text-xs font-mono text-slate-200 focus:outline-none focus:border-cyan-500"
            >
              <option value="">All Statuses</option>
              <option value="Triggered">Triggered</option>
              <option value="Investigating">Investigating</option>
              <option value="Mitigated">Mitigated</option>
              <option value="Resolved">Resolved</option>
            </select>
          </div>
        </div>
      </div>

      {/* Content State Handling */}
      {loading ? (
        <LoadingState message="Loading incident telemetry list..." />
      ) : error ? (
        <ErrorState
          title="Failed to Load Incidents"
          message={error}
          onRetry={refetch}
        />
      ) : filteredIncidents.length === 0 ? (
        <EmptyState
          title="No Incidents Found"
          message={
            searchTerm || severityFilter || statusFilter
              ? 'No incidents matched your active filter criteria.'
              : 'There are currently no incidents in the database.'
          }
        />
      ) : (
        <div className="rounded-lg border border-slate-800 bg-slate-900/40 overflow-hidden shadow-xl">
          <div className="overflow-x-auto">
            <table className="w-full text-left font-mono text-xs">
              <thead className="bg-slate-950 text-slate-400 uppercase tracking-wider text-[11px] border-b border-slate-800">
                <tr>
                  <th className="py-3 px-4">Severity</th>
                  <th className="py-3 px-4">Title & Context</th>
                  <th className="py-3 px-4">Service</th>
                  <th className="py-3 px-4">Incident Status</th>
                  <th className="py-3 px-4">Investigation</th>
                  <th className="py-3 px-4">Created Time</th>
                  <th className="py-3 px-4 text-right">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800/80">
                {filteredIncidents.map((inc) => (
                  <tr
                    key={inc.id}
                    className="hover:bg-slate-800/40 transition-colors group"
                    data-testid={`incident-row-${inc.id}`}
                  >
                    <td className="py-3.5 px-4 whitespace-nowrap">
                      <SeverityBadge severity={inc.severity} size="sm" />
                    </td>
                    <td className="py-3.5 px-4 max-w-xs sm:max-w-md">
                      <Link
                        to={`/incidents/${inc.id}`}
                        className="text-slate-100 font-semibold hover:text-cyan-400 transition-colors line-clamp-1 text-sm font-sans"
                      >
                        {inc.title}
                      </Link>
                      <p className="text-[11px] text-slate-500 line-clamp-1 mt-0.5">
                        {inc.description}
                      </p>
                    </td>
                    <td className="py-3.5 px-4 whitespace-nowrap">
                      <span className="text-cyan-300 font-medium">
                        {inc.service?.name || 'unknown'}
                      </span>
                      {inc.service?.tier && (
                        <span className="text-slate-500 text-[10px] block">
                          {inc.service.tier}
                        </span>
                      )}
                    </td>
                    <td className="py-3.5 px-4 whitespace-nowrap">
                      <StatusBadge status={inc.status} size="sm" />
                    </td>
                    <td className="py-3.5 px-4 whitespace-nowrap">
                      {inc.investigation ? (
                        <Link
                          to={`/incidents/${inc.id}/investigation`}
                          className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded bg-cyan-950/80 hover:bg-cyan-900 border border-cyan-800 text-cyan-300 text-[11px] transition-colors"
                        >
                          <Terminal className="w-3 h-3 text-cyan-400" />
                          <span>{inc.investigation.status}</span>
                        </Link>
                      ) : (
                        <span className="text-slate-600 text-[11px]">Unstarted</span>
                      )}
                    </td>
                    <td className="py-3.5 px-4 whitespace-nowrap text-slate-400 text-[11px]">
                      {new Date(inc.created_at).toLocaleString()}
                    </td>
                    <td className="py-3.5 px-4 whitespace-nowrap text-right">
                      <Link
                        to={`/incidents/${inc.id}`}
                        className="inline-flex items-center gap-1 text-cyan-400 hover:text-cyan-300 font-semibold text-xs transition-colors"
                      >
                        Inspect
                        <ArrowRight className="w-3.5 h-3.5" />
                      </Link>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  );
};
