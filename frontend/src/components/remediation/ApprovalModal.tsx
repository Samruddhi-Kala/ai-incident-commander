import React, { useState } from 'react';
import { Modal } from '../common/Modal';
import { RemediationActionResponse } from '../../types/remediation';
import { ShieldCheck, AlertTriangle, Loader2 } from 'lucide-react';

export interface ApprovalModalProps {
  isOpen: boolean;
  onClose: () => void;
  remediation: RemediationActionResponse;
  onApprove: (comment?: string) => Promise<unknown>;
  isLoading?: boolean;
}

export const ApprovalModal: React.FC<ApprovalModalProps> = ({
  isOpen,
  onClose,
  remediation,
  onApprove,
  isLoading = false,
}) => {
  const [comment, setComment] = useState('');
  const isHighRisk = remediation.risk_level?.toUpperCase() === 'HIGH';

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    await onApprove(comment.trim() || undefined);
    onClose();
  };

  return (
    <Modal
      isOpen={isOpen}
      onClose={onClose}
      title="Authorize Remediation Action"
      description="Explicit human authorization is required to transition this proposal to APPROVED state."
    >
      <form onSubmit={handleSubmit} className="space-y-4 pt-2">
        {isHighRisk && (
          <div className="rounded-lg bg-red-950/40 border border-red-800/80 p-3 flex items-start gap-3">
            <AlertTriangle className="w-5 h-5 text-red-400 shrink-0 mt-0.5" />
            <div className="space-y-1 text-xs font-mono">
              <span className="font-bold text-red-300 uppercase">HIGH RISK ACTION</span>
              <p className="text-red-300/80 leading-relaxed">
                This action modifies service deployment or runtime parameters. Confirm you have
                reviewed the expected impact and rollback procedure.
              </p>
            </div>
          </div>
        )}

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
          {remediation.expected_impact && (
            <div className="pt-2 border-t border-slate-900">
              <span className="text-slate-500 block mb-0.5">Expected Impact:</span>
              <span className="text-slate-300">{remediation.expected_impact}</span>
            </div>
          )}
        </div>

        <div className="space-y-1.5">
          <label htmlFor="approval-comment" className="block text-xs font-mono text-slate-300 font-medium">
            Authorization Sign-Off Note (Optional):
          </label>
          <textarea
            id="approval-comment"
            rows={3}
            value={comment}
            onChange={(e) => setComment(e.target.value)}
            placeholder="e.g., Reviewed metrics on Datadog. Authorized by On-Call Lead."
            className="w-full rounded-md bg-slate-950 border border-slate-800 p-2.5 text-xs font-mono text-slate-100 placeholder:text-slate-600 focus:outline-none focus:border-cyan-500"
          />
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
            disabled={isLoading}
            className="inline-flex items-center gap-2 px-4 py-2 rounded-md bg-emerald-600 hover:bg-emerald-500 disabled:bg-emerald-950 disabled:text-emerald-500 text-white font-mono text-xs font-semibold shadow-lg shadow-emerald-950 transition-colors"
            data-testid="confirm-approve-btn"
          >
            {isLoading ? (
              <>
                <Loader2 className="w-3.5 h-3.5 animate-spin" />
                Authorizing...
              </>
            ) : (
              <>
                <ShieldCheck className="w-3.5 h-3.5" />
                Authorize & Approve
              </>
            )}
          </button>
        </div>
      </form>
    </Modal>
  );
};
