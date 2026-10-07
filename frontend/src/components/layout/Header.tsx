import React, { useState, useEffect } from 'react';
import { ShieldAlert, Activity, Terminal } from 'lucide-react';

export const Header: React.FC = () => {
  const [timeStr, setTimeStr] = useState<string>('');

  useEffect(() => {
    const updateTime = () => {
      const now = new Date();
      setTimeStr(now.toUTCString().replace('GMT', 'UTC'));
    };
    updateTime();
    const interval = setInterval(updateTime, 1000);
    return () => clearInterval(interval);
  }, []);

  return (
    <header className="h-14 border-b border-slate-800 bg-slate-950/80 backdrop-blur px-6 flex items-center justify-between z-30 sticky top-0">
      <div className="flex items-center gap-3">
        <div className="w-8 h-8 rounded bg-gradient-to-br from-cyan-600 to-blue-700 flex items-center justify-center text-white shadow-lg shadow-cyan-900/30">
          <ShieldAlert className="w-5 h-5" />
        </div>
        <div className="flex flex-col">
          <span className="text-sm font-bold tracking-wider font-mono text-slate-100 flex items-center gap-2">
            AI INCIDENT COMMANDER
            <span className="px-1.5 py-0.2 bg-cyan-950 text-cyan-400 border border-cyan-800 rounded text-[10px] uppercase font-mono">
              AGENT OPS
            </span>
          </span>
          <span className="text-[11px] text-slate-400 font-mono">
            Autonomous Investigation & Human-Governed Remediation
          </span>
        </div>
      </div>

      <div className="flex items-center gap-6">
        <div className="hidden md:flex items-center gap-2 text-xs font-mono text-slate-400 bg-slate-900/80 px-3 py-1 rounded border border-slate-800">
          <Terminal className="w-3.5 h-3.5 text-cyan-400" />
          <span>{timeStr || 'UTC'}</span>
        </div>

        <div className="flex items-center gap-2">
          <span className="relative flex h-2 w-2">
            <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75" />
            <span className="relative inline-flex rounded-full h-2 w-2 bg-emerald-500" />
          </span>
          <span className="text-xs font-mono font-medium text-emerald-400 flex items-center gap-1">
            <Activity className="w-3.5 h-3.5" />
            ONLINE
          </span>
        </div>
      </div>
    </header>
  );
};
