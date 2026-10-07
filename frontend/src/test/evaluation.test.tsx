import { render, screen, fireEvent } from '@testing-library/react';
import { describe, it, expect, vi } from 'vitest';
import { EvaluationSection } from '../components/investigation/EvaluationSection';
import { InvestigationEvaluationResponse } from '../types/evaluation';

const mockEvaluation: InvestigationEvaluationResponse = {
  id: 'eval-101',
  investigation_id: 'inv-101',
  overall_score: 87.5,
  evidence_score: 92.0,
  hypothesis_score: 85.0,
  verification_score: 90.0,
  rag_score: 80.0,
  tool_efficiency_score: 85.0,
  evaluation_reasoning:
    'Investigation Quality Score: 87.5/100 (Completed).\n• Evidence Support: 92.0/100 — Collected 3 evidence items.\n• Hypothesis Quality: 85.0/100 — Formulated 2 competing hypotheses.\n• Verification Rigor: 90.0/100 — Tested 2/2 hypotheses.\n• RAG Relevance: 80.0/100 — RAG knowledge engine referenced.\n• Tool Efficiency: 85.0/100 — Executed 4 tool calls.',
  metrics_breakdown: {
    evidence: { score: 92.0, weight: 0.25, feedback: 'Strong empirical evidence' },
    hypothesis: { score: 85.0, weight: 0.20, feedback: '2 competing hypotheses' },
    verification: { score: 90.0, weight: 0.25, feedback: 'Both hypotheses tested' },
    rag: { score: 80.0, weight: 0.15, feedback: 'Runbooks utilized' },
    tool_efficiency: { score: 85.0, weight: 0.15, feedback: '4 calls, 0 failures' },
    outcome: { status: 'Completed', confidence_score: 0.92, factor_applied: 1.0 },
  },
  created_at: '2026-10-07T12:16:00Z',
};

describe('EvaluationSection Component Suite', () => {
  it('renders empty state when investigation has not been evaluated yet', () => {
    const handleEvaluate = vi.fn();
    render(
      <EvaluationSection
        evaluation={null}
        loading={false}
        evaluating={false}
        error={null}
        onEvaluate={handleEvaluate}
        investigationStatus="Completed"
      />
    );

    expect(screen.getByText('AI Investigation Quality Evaluation')).toBeInTheDocument();
    expect(screen.getByText('No Quality Evaluation Yet')).toBeInTheDocument();
    const evalBtn = screen.getByTestId('evaluate-investigation-btn');
    expect(evalBtn).toBeInTheDocument();

    fireEvent.click(evalBtn);
    expect(handleEvaluate).toHaveBeenCalledWith(false);
  });

  it('renders evaluating progress state', () => {
    render(
      <EvaluationSection
        evaluation={null}
        loading={false}
        evaluating={true}
        error={null}
        onEvaluate={vi.fn()}
        investigationStatus="Completed"
      />
    );

    expect(screen.getByText('Calculating Quality Scores...')).toBeInTheDocument();
  });

  it('renders error state with retry button', () => {
    const handleEvaluate = vi.fn();
    render(
      <EvaluationSection
        evaluation={null}
        loading={false}
        evaluating={false}
        error="Evaluation service connection failed"
        onEvaluate={handleEvaluate}
        investigationStatus="Completed"
      />
    );

    expect(screen.getByTestId('evaluation-error')).toBeInTheDocument();
    expect(screen.getByText(/Evaluation service connection failed/i)).toBeInTheDocument();

    const retryBtn = screen.getByText('Retry');
    fireEvent.click(retryBtn);
    expect(handleEvaluate).toHaveBeenCalledWith(false);
  });

  it('renders full evaluation scores, sub-scores, and reasoning breakdown', () => {
    const handleEvaluate = vi.fn();
    render(
      <EvaluationSection
        evaluation={mockEvaluation}
        loading={false}
        evaluating={false}
        error={null}
        onEvaluate={handleEvaluate}
        investigationStatus="Completed"
      />
    );

    expect(screen.getByTestId('evaluation-content')).toBeInTheDocument();
    expect(screen.getByTestId('overall-score-badge')).toHaveTextContent('87.5');
    expect(screen.getByText('High Quality')).toBeInTheDocument();

    // 5 sub-scores
    expect(screen.getByTestId('sub-scores-grid')).toBeInTheDocument();
    expect(screen.getByText('92')).toBeInTheDocument(); // Evidence score
    expect(screen.getAllByText('85').length).toBe(2); // Hypothesis and Tool Efficiency scores
    expect(screen.getByText('90')).toBeInTheDocument(); // Verification score
    expect(screen.getByText('80')).toBeInTheDocument(); // RAG score

    // Reasoning narrative
    expect(screen.getByText(/Investigation Quality Score: 87.5\/100/i)).toBeInTheDocument();

    // Disclaimer
    expect(
      screen.getByText(/heuristic engineering metrics designed to audit investigation completeness/i)
    ).toBeInTheDocument();

    // Re-evaluate button
    const reEvalBtn = screen.getByTestId('re-evaluate-btn');
    expect(reEvalBtn).toBeInTheDocument();
    fireEvent.click(reEvalBtn);
    expect(handleEvaluate).toHaveBeenCalledWith(true);
  });
});
