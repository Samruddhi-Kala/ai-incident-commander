import { render, screen, fireEvent } from '@testing-library/react';
import { describe, it, expect, vi } from 'vitest';
import { ExecutionPanel } from '../components/remediation/ExecutionPanel';
import { ApprovalModal } from '../components/remediation/ApprovalModal';
import { RejectionModal } from '../components/remediation/RejectionModal';
import { RemediationActionResponse } from '../types/remediation';

const mockRemediation: RemediationActionResponse = {
  id: 'rem-123',
  investigation_id: 'inv-456',
  action_name: 'rollback_deployment',
  parameters: { service: 'payment-service', target_version: 'v2.5.0' },
  reasoning: 'Regression in deployment v2.5.1',
  risk_level: 'HIGH',
  approval_status: 'PENDING_APPROVAL',
  expected_impact: 'Brief restart queuing',
  rollback_plan: 'Redeploy v2.5.1 if failure occurs',
  created_at: new Date().toISOString(),
};

describe('Remediation and Human-in-the-Loop Suite', () => {
  it('does NOT display Execute Remediation button when status is PENDING_APPROVAL', () => {
    render(
      <ExecutionPanel
        remediation={mockRemediation}
        onExecute={async () => {}}
      />
    );

    expect(screen.queryByTestId('execute-remediation-btn')).not.toBeInTheDocument();
    expect(screen.getByTestId('execution-blocked-notice')).toBeInTheDocument();
    expect(screen.getByText(/SIMULATED EXECUTION/i)).toBeInTheDocument();
  });

  it('displays Execute Remediation button ONLY when status is APPROVED', () => {
    const approvedRemediation: RemediationActionResponse = {
      ...mockRemediation,
      approval_status: 'APPROVED',
      approved_by: 'user-789',
    };

    render(
      <ExecutionPanel
        remediation={approvedRemediation}
        onExecute={async () => {}}
      />
    );

    expect(screen.getByTestId('execute-remediation-btn')).toBeInTheDocument();
    expect(screen.getByText('Execute Remediation')).toBeInTheDocument();
  });

  it('renders ApprovalModal and triggers onApprove upon confirmation', async () => {
    const onApprove = vi.fn().mockResolvedValue({});
    const onClose = vi.fn();

    render(
      <ApprovalModal
        isOpen={true}
        onClose={onClose}
        remediation={mockRemediation}
        onApprove={onApprove}
      />
    );

    expect(screen.getByText('Authorize Remediation Action')).toBeInTheDocument();
    expect(screen.getByText('HIGH RISK ACTION')).toBeInTheDocument();

    const approveBtn = screen.getByTestId('confirm-approve-btn');
    fireEvent.click(approveBtn);

    expect(onApprove).toHaveBeenCalled();
  });

  it('renders RejectionModal and validates that reason is required', async () => {
    const onReject = vi.fn().mockResolvedValue({});
    const onClose = vi.fn();

    render(
      <RejectionModal
        isOpen={true}
        onClose={onClose}
        remediation={mockRemediation}
        onReject={onReject}
      />
    );

    expect(screen.getByText('Reject Remediation Action')).toBeInTheDocument();

    const rejectBtn = screen.getByTestId('confirm-reject-btn');
    // Button should be disabled or blocked with empty string
    expect(rejectBtn).toBeDisabled();

    const textarea = screen.getByPlaceholderText(/breaking database schema/i);
    fireEvent.change(textarea, { target: { value: 'Version incompatibilities detected' } });

    expect(rejectBtn).not.toBeDisabled();
    fireEvent.click(rejectBtn);

    expect(onReject).toHaveBeenCalledWith('Version incompatibilities detected');
  });
});
