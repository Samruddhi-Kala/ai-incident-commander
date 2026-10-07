import React, { useState } from 'react';
import { Modal } from '../common/Modal';
import { RemediationActionResponse } from '../../types/remediation';
import { Ban, Loader2 } from 'lucide-react';

export interface RejectionModalProps {
  isOpen: boolean;
  onClose: () => void;
  remediation: RemediationActionResponse;
  onReject: (reason: string) => Promise<unknown>;
  isLoading?: boolean;
}

export const RejectionModal: React.FC<RejectionModalProps> = ({
  isOpen,
  onClose,
  remediation,
  onReject,
  isLoading = false,
}) => {
  const [reason, setReason] = useState('');
  const [validationError, setValidationError] = useState<string | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!reason.trim() || reason.trim().length < 3) {
      setValidationError('A specific rejection reason (min 3 characters) is required by governance policy.');
      return;
    }
    setValidationError(null);
    await onReject(reason.trim());
    onClose();
  };

  return (
    <Modal
      isOpen={isOpen}
      onClose={onClose}
      title="Reject Remediation Action"
      description="Rejecting this proposal permanently blocks execution and transitions it to REJECTED status."
    >
      <form onSubmit={handleSubmit} className="space-y-4 pt-2">
        <div className="rounded-lg bg-slate-950 border border-slate-800 p-3 space-y-2 font-mono text-xs">
          <div className="flex justify-between">
            <span className="text-slate-500">Action:</span>
            <span className="text-slate-200 font-bold">{remediation.action_name}</span>
          </div>
          <div className="flex justify-between">
            <span className="text-slate-500">Target Service:</span>
            <span className="text-cyan-300">
              {String(remediation.parameters?.service || 'target-service')}
            </span>
          </div>
        </div>

        <div className="space-y-1.5">
          <label htmlFor="rejection-reason" className="block text-xs font-mono text-slate-300 font-medium">
            Mandatory Rejection Rationale <span className="text-rose-400">*</span>:
          </label>
          <textarea
            id="rejection-reason"
            rows={3}
            required
            value={reason}
            onChange={(e) => {
              setReason(e.target.value);
              if (validationError) setValidationError(null);
            }}
            placeholder="e.g., Service deployment rollback would introduce breaking database schema regressions."
            className="w-full rounded-md bg-slate-950 border border-slate-800 p-2.5 text-xs font-mono text-slate-100 placeholder:text-slate-600 focus:outline-none focus:border-rose-500"
          />
          {validationError && (
            <p className="text-[11px] font-mono text-rose-400">{validationError}</p>
          )}
        </div>

        <div className="flex items-center justify-end gap-3 pt-3 border-t border-slate-800">
          <button
            type="button"
            onClick={onClose}
            disabled={isLoading}
            className="px-4 py-2 rounded-md bg-slate-800 hover:bg-slate-700 text-slate-300 font-mono text-xs font-medium transition-colors"
          >
            Cancel
          </button>
          <button
            type="submit"
            disabled={isLoading || !reason.trim()}
            className="inline-flex items-center gap-2 px-4 py-2 rounded-md bg-rose-600 hover:bg-rose-500 disabled:bg-rose-950 disabled:text-rose-500 text-white font-mono text-xs font-semibold shadow-lg shadow-rose-950 transition-colors"
            data-testid="confirm-reject-btn"
          >
            {isLoading ? (
              <>
                <Loader2 className="w-3.5 h-3.5 animate-spin" />
                Rejecting...
              </>
            ) : (
              <>
                <Ban className="w-3.5 h-3.5" />
                Confirm Rejection
              </>
            )}
          </button>
        </div>
      </form>
    </Modal>
  );
};
