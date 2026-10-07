import React from 'react';
import { Inbox } from 'lucide-react';

export interface EmptyStateProps {
  title?: string;
  message?: string;
  action?: React.ReactNode;
}

export const EmptyState: React.FC<EmptyStateProps> = ({
  title = 'No Data Available',
  message = 'There are currently no items to display.',
  action,
}) => {
  return (
    <div
      className="flex flex-col items-center justify-center p-12 rounded-lg border border-slate-800 bg-slate-900/40 text-center my-6"
      data-testid="empty-state"
    >
      <div className="w-12 h-12 rounded-full bg-slate-800 flex items-center justify-center text-slate-500 mb-3 border border-slate-700">
        <Inbox className="w-6 h-6" />
      </div>
      <h3 className="text-sm font-semibold text-slate-300 mb-1">{title}</h3>
      <p className="text-xs text-slate-400 max-w-sm mb-4 font-mono">{message}</p>
      {action && <div>{action}</div>}
    </div>
  );
};
