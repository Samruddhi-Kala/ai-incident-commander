import { render, screen, fireEvent } from '@testing-library/react';
import { describe, it, expect, vi } from 'vitest';
import { PostmortemSection } from '../components/investigation/PostmortemSection';
import { PostmortemResponse } from '../types/postmortem';

const mockPostmortem: PostmortemResponse = {
  id: 'pm-101',
  investigation_id: 'inv-101',
  title: 'Postmortem: Checkout Latency Spike (INV-2041)',
  summary: 'Automated postmortem for checkout-service latency degradation.',
  impact: 'SEV-1 severity. Checkout processing interrupted for 12 minutes.',
  timeline: [
    {
      timestamp: '2026-10-07T12:00:00Z',
      stage: 'Incident Triggered',
      description: 'Checkout 504 errors detected.',
      source: 'Alerting',
    },
    {
      timestamp: '2026-10-07T12:02:00Z',
      stage: 'Investigation Started',
      description: 'AI orchestrator initiated diagnosis.',
      source: 'Agent Orchestrator',
    },
  ],
  root_cause: 'Unindexed SQL join in v2.4.1 exhausted database connection pool.',
  contributing_factors: ['High write volume during promotion', 'Low pool connection ceiling (50)'],
  remediation: {
    proposals_count: 1,
    actions: [
      {
        id: 'rem-1',
        action_name: 'rollback_deployment',
        approval_status: 'COMPLETED',
        risk_level: 'HIGH',
        reasoning: 'Rollback v2.4.1',
      },
    ],
    recommended: ['Rollback v2.4.1 deployment'],
    status_summary: '1 remediation actions formulated. Approved/Executed: 1.',
  },
  lessons_learned: [
    'Connection pool alarms should trigger at 80% capacity instead of 95%.',
    'Pre-release query plans must be validated against production-scale data.',
  ],
  preventive_actions: [
    'Add index on cart_items.session_id column.',
    'Implement aggressive circuit-breaking on cart checkout queries.',
  ],
  details: {
    diagnostic_tools_used: ['query_prometheus', 'fetch_service_logs'],
    evidence_count: 3,
    hypotheses_count: 2,
    confidence_score: 0.92,
  },
  generated_at: '2026-10-07T12:15:00Z',
};

describe('PostmortemSection Component Suite', () => {
  it('renders empty state when no postmortem has been generated yet', () => {
    const handleGenerate = vi.fn();
    render(
      <PostmortemSection
        postmortem={null}
        loading={false}
        generating={false}
        error={null}
        onGenerate={handleGenerate}
        investigationStatus="Completed"
      />
    );

    expect(screen.getByText('Incident Postmortem Report')).toBeInTheDocument();
    expect(screen.getByText('No Postmortem Generated Yet')).toBeInTheDocument();
    const generateBtn = screen.getByTestId('generate-postmortem-btn');
    expect(generateBtn).toBeInTheDocument();

    fireEvent.click(generateBtn);
    expect(handleGenerate).toHaveBeenCalledWith(false);
  });

  it('renders loading indicator when generating postmortem', () => {
    render(
      <PostmortemSection
        postmortem={null}
        loading={false}
        generating={true}
        error={null}
        onGenerate={vi.fn()}
        investigationStatus="Completed"
      />
    );

    expect(screen.getByText('Synthesizing Postmortem...')).toBeInTheDocument();
  });

  it('renders error state with retry button', () => {
    const handleGenerate = vi.fn();
    render(
      <PostmortemSection
        postmortem={null}
        loading={false}
        generating={false}
        error="Investigation timeout failure"
        onGenerate={handleGenerate}
        investigationStatus="Failed"
      />
    );

    expect(screen.getByTestId('postmortem-error')).toBeInTheDocument();
    expect(screen.getByText(/Investigation timeout failure/i)).toBeInTheDocument();

    const retryBtn = screen.getByText('Retry');
    fireEvent.click(retryBtn);
    expect(handleGenerate).toHaveBeenCalledWith(false);
  });

  it('renders full postmortem content with root cause, timeline, and actions', () => {
    const handleGenerate = vi.fn();
    render(
      <PostmortemSection
        postmortem={mockPostmortem}
        loading={false}
        generating={false}
        error={null}
        onGenerate={handleGenerate}
        investigationStatus="Completed"
      />
    );

    expect(screen.getByTestId('postmortem-content')).toBeInTheDocument();
    expect(screen.getByText(mockPostmortem.title)).toBeInTheDocument();
    expect(screen.getByText(mockPostmortem.summary)).toBeInTheDocument();
    expect(screen.getByText(mockPostmortem.impact)).toBeInTheDocument();
    expect(screen.getByText(mockPostmortem.root_cause)).toBeInTheDocument();

    // Lessons learned
    expect(
      screen.getByText('Connection pool alarms should trigger at 80% capacity instead of 95%.')
    ).toBeInTheDocument();

    // Preventive actions
    expect(screen.getByText('Add index on cart_items.session_id column.')).toBeInTheDocument();

    // Regenerate button
    const regenBtn = screen.getByTestId('regenerate-postmortem-btn');
    expect(regenBtn).toBeInTheDocument();
    fireEvent.click(regenBtn);
    expect(handleGenerate).toHaveBeenCalledWith(true);
  });
});
