import React from 'react';
import { Loader2 } from 'lucide-react';

export interface LoadingStateProps {
  message?: string;
}

export const LoadingState: React.FC<LoadingStateProps> = ({ message = 'Loading...' }) => {
  return (
    <div className="flex flex-col items-center justify-center py-16 px-4 text-center" data-testid="loading-state">
      <Loader2 className="w-8 h-8 text-cyan-500 animate-spin mb-4" />
      <p className="text-sm font-mono text-slate-400">{message}</p>
    </div>
  );
};
