import React from 'react';
import { AlertTriangle, RefreshCw } from 'lucide-react';

export interface ErrorStateProps {
  title?: string;
  message?: string;
  onRetry?: () => void;
}

export const ErrorState: React.FC<ErrorStateProps> = ({
  title = 'System Error',
  message = 'An unexpected error occurred while communicating with the service.',
  onRetry,
}) => {
  return (
    <div
      className="flex flex-col items-center justify-center p-8 rounded-lg border border-rose-800/60 bg-rose-950/20 text-center my-6"
      data-testid="error-state"
    >
      <div className="w-12 h-12 rounded-full bg-rose-900/50 flex items-center justify-center text-rose-400 mb-3 border border-rose-700/50">
        <AlertTriangle className="w-6 h-6" />
      </div>
      <h3 className="text-base font-semibold text-rose-200 mb-1">{title}</h3>
      <p className="text-sm text-rose-300/80 max-w-md mb-4 font-mono">{message}</p>
      {onRetry && (
        <button
          onClick={onRetry}
          className="inline-flex items-center gap-2 px-3.5 py-1.5 rounded-md bg-rose-900/40 hover:bg-rose-800/60 text-rose-200 text-xs font-mono font-medium border border-rose-700 transition-colors"
          data-testid="error-retry-btn"
        >
          <RefreshCw className="w-3.5 h-3.5" />
          Retry Request
        </button>
      )}
    </div>
  );
};
