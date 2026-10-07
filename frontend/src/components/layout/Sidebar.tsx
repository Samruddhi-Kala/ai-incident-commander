import React from 'react';
import { NavLink } from 'react-router-dom';
import { LayoutDashboard, AlertCircle, Wrench, Cpu, BookOpen } from 'lucide-react';

export const Sidebar: React.FC = () => {
  const navItems = [
    {
      to: '/',
      label: 'Overview',
      icon: LayoutDashboard,
      description: 'System health & active alerts',
    },
    {
      to: '/incidents',
      label: 'Incidents',
      icon: AlertCircle,
      description: 'Active & resolved telemetry',
    },
    {
      to: '/remediations',
      label: 'Remediations',
      icon: Wrench,
      description: 'Human approval lifecycle',
    },
  ];

  return (
    <aside className="w-64 border-r border-slate-800 bg-slate-950/60 flex flex-col justify-between shrink-0">
      <div className="p-4 space-y-6">
        <div>
          <span className="text-[10px] font-mono font-semibold uppercase tracking-wider text-slate-500 px-3">
            Console Navigation
          </span>
          <nav className="mt-2 space-y-1">
            {navItems.map((item) => {
              const Icon = item.icon;
              return (
                <NavLink
                  key={item.to}
                  to={item.to}
                  end={item.to === '/'}
                  className={({ isActive }) =>
                    `flex items-center gap-3 px-3 py-2.5 rounded-md text-sm font-medium transition-all group ${
                      isActive
                        ? 'bg-cyan-950/70 text-cyan-300 border border-cyan-800/80 shadow-sm shadow-cyan-950'
                        : 'text-slate-400 hover:text-slate-200 hover:bg-slate-900/80 border border-transparent'
                    }`
                  }
                >
                  {({ isActive }) => (
                    <>
                      <Icon
                        className={`w-4 h-4 transition-colors ${
                          isActive ? 'text-cyan-400' : 'text-slate-500 group-hover:text-slate-300'
                        }`}
                      />
                      <div className="flex flex-col">
                        <span>{item.label}</span>
                        <span className="text-[10px] font-mono text-slate-500 line-clamp-1">
                          {item.description}
                        </span>
                      </div>
                    </>
                  )}
                </NavLink>
              );
            })}
          </nav>
        </div>

        {/* Technical Architecture Info Box */}
        <div className="rounded-lg border border-slate-800 bg-slate-900/50 p-3.5 space-y-2 font-mono text-xs">
          <div className="flex items-center gap-1.5 text-slate-300 font-semibold text-[11px]">
            <Cpu className="w-3.5 h-3.5 text-cyan-400" />
            <span>AGENT GOVERNANCE</span>
          </div>
          <p className="text-[11px] text-slate-400 leading-relaxed">
            AI recommends hypotheses and remediation actions. Only authorized humans can approve
            consequential commands.
          </p>
          <div className="pt-1 border-t border-slate-800/80 flex items-center justify-between text-[10px] text-slate-500">
            <span>HITL BOUNDARY</span>
            <span className="text-emerald-400 font-semibold">ENFORCED</span>
          </div>
        </div>
      </div>

      <div className="p-4 border-t border-slate-800/80 text-[11px] font-mono text-slate-500 flex items-center gap-2">
        <BookOpen className="w-3.5 h-3.5 text-slate-500" />
        <span>v1.0.0-rc8 — Production</span>
      </div>
    </aside>
  );
};
