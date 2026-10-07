import React, { useState } from 'react';
import { ToolCallInfo } from '../../types/investigation';
import { Terminal, ChevronDown, ChevronRight, Clock, CheckCircle2, AlertCircle } from 'lucide-react';

export interface ToolCallsListProps {
  toolCalls: ToolCallInfo[];
}

export const ToolCallsList: React.FC<ToolCallsListProps> = ({ toolCalls }) => {
  const [expandedId, setExpandedId] = useState<string | null>(null);

  if (!toolCalls || toolCalls.length === 0) {
    return (
      <div className="rounded-lg border border-slate-800 bg-slate-900/30 p-8 text-center font-mono text-xs text-slate-500">
        No diagnostic tools were executed during this investigation.
      </div>
    );
  }

  const toggleExpand = (id: string) => {
    setExpandedId((prev) => (prev === id ? null : id));
  };

  return (
    <div className="space-y-4" data-testid="tool-calls-list">
      <div className="flex items-center justify-between">
        <div>
          <h3 className="text-sm font-semibold text-slate-200 uppercase tracking-wider font-mono">
            Diagnostic Telemetry Tool Calls
          </h3>
          <p className="text-xs text-slate-400 font-mono mt-0.5">
            Empirical queries executed through Phase 5 engineering adapters
          </p>
        </div>
        <span className="text-xs font-mono px-2.5 py-1 rounded bg-slate-800 text-slate-300 border border-slate-700">
          {toolCalls.length} Executed
        </span>
      </div>

      <div className="space-y-2">
        {toolCalls.map((tc) => {
          const isSuccess = tc.status?.toUpperCase() === 'SUCCESS';
          const isExpanded = expandedId === tc.id;
          const time = new Date(tc.created_at).toLocaleTimeString();

          return (
            <div
              key={tc.id}
              className="rounded-lg border border-slate-800 bg-slate-900/50 overflow-hidden transition-colors hover:border-slate-700"
            >
              <div
                onClick={() => toggleExpand(tc.id)}
                className="p-3.5 flex items-center justify-between gap-4 cursor-pointer select-none"
              >
                <div className="flex items-center gap-3 min-w-0">
                  <div className="text-slate-400">
                    {isExpanded ? (
                      <ChevronDown className="w-4 h-4" />
                    ) : (
                      <ChevronRight className="w-4 h-4" />
                    )}
                  </div>
                  <div className="p-1.5 rounded bg-slate-800 text-cyan-400 border border-slate-700">
                    <Terminal className="w-3.5 h-3.5" />
                  </div>
                  <div className="flex items-center gap-2 truncate">
                    <span className="font-mono text-xs font-bold text-slate-200 truncate">
                      {tc.tool_name}
                    </span>
                    <span className="font-mono text-[11px] text-slate-500 hidden sm:inline">
                      ({Object.keys(tc.arguments || {}).length} args)
                    </span>
                  </div>
                </div>

                <div className="flex items-center gap-3 shrink-0 text-xs font-mono">
                  <span className="flex items-center gap-1 text-slate-400">
                    <Clock className="w-3 h-3 text-slate-500" />
                    {tc.execution_time_ms} ms
                  </span>

                  <span
                    className={`inline-flex items-center gap-1 px-2 py-0.5 rounded text-[11px] font-semibold border ${
                      isSuccess
                        ? 'bg-emerald-950/80 text-emerald-300 border-emerald-800'
                        : 'bg-rose-950/80 text-rose-300 border-rose-800'
                    }`}
                  >
                    {isSuccess ? (
                      <CheckCircle2 className="w-3 h-3" />
                    ) : (
                      <AlertCircle className="w-3 h-3" />
                    )}
                    {tc.status}
                  </span>

                  <span className="text-slate-500 hidden md:inline">{time}</span>
                </div>
              </div>

              {isExpanded && (
                <div className="p-4 bg-slate-950 border-t border-slate-800/80 space-y-3 font-mono text-xs">
                  <div>
                    <span className="text-[10px] text-slate-500 uppercase tracking-wider block mb-1">
                      Arguments Payload
                    </span>
                    <pre className="p-2.5 rounded bg-slate-900 border border-slate-800 text-slate-300 overflow-x-auto text-[11px]">
                      {JSON.stringify(tc.arguments, null, 2)}
                    </pre>
                  </div>
                </div>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
};
