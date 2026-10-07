import { render, screen } from '@testing-library/react';
import { describe, it, expect } from 'vitest';
import { BrowserRouter } from 'react-router-dom';
import { InvestigationTimeline } from '../components/investigation/InvestigationTimeline';
import { RootCausePanel } from '../components/investigation/RootCausePanel';
import { RemediationRecommendations } from '../components/investigation/RemediationRecommendations';

describe('Investigation Visualizations Suite', () => {
  it('renders InvestigationTimeline with steps and statuses', () => {
    const steps = [
      {
        step_order: 1,
        title: 'Step 1 — Incident Intake & Entity Resolution',
        status: 'Completed',
        output_summary: 'Resolved service dependencies.',
        created_at: new Date().toISOString(),
      },
      {
        step_order: 2,
        title: 'Step 2 — Diagnostic Strategy Planning',
        status: 'Completed',
        output_summary: 'Formulated investigation questions.',
        created_at: new Date().toISOString(),
      },
    ];

    render(<InvestigationTimeline steps={steps} />);
    expect(screen.getByText('Investigation Lifecycle Timeline')).toBeInTheDocument();
    expect(screen.getByText('Step 1 — Incident Intake & Entity Resolution')).toBeInTheDocument();
    expect(screen.getByText('Step 2 — Diagnostic Strategy Planning')).toBeInTheDocument();
  });

  it('renders RootCausePanel with probable root cause and reasoning', () => {
    render(
      <RootCausePanel
        status="Completed"
        probableRootCause="Database connection exhaustion due to deployment regression."
        confidenceScore={0.88}
        analysisReasoning="Telemetry indicates steady pool starvation after v2.5.1 deployment."
        supportingEvidence={['get_error_rate: 15.3%']}
        alternativeHypotheses={['Network partition [NOT_SUPPORTED]']}
      />
    );

    expect(screen.getByText('Probable Root Cause')).toBeInTheDocument();
    expect(
      screen.getByText('Database connection exhaustion due to deployment regression.')
    ).toBeInTheDocument();
    expect(screen.getByText(/Telemetry indicates steady pool starvation/i)).toBeInTheDocument();
    expect(screen.getByText('88%')).toBeInTheDocument();
  });

  it('renders Inconclusive Investigation appropriately when confidence is low or unverified', () => {
    render(
      <RootCausePanel
        status="Inconclusive"
        probableRootCause="Ambiguous signal"
        confidenceScore={0.32}
        analysisReasoning="Metrics were noisy and contradictory."
      />
    );

    expect(screen.getByText('Inconclusive Investigation')).toBeInTheDocument();
    expect(
      screen.getByText(/did not establish a sufficiently supported root cause/i)
    ).toBeInTheDocument();
  });

  it('renders RemediationRecommendations and proposal generation button', () => {
    const recs = [
      'Roll back payment-service to v2.5.0',
      'Verify connection pool configuration',
    ];

    render(
      <BrowserRouter>
        <RemediationRecommendations
          recommendations={recs}
          onProposeRemediations={async () => {}}
        />
      </BrowserRouter>
    );

    expect(screen.getByText('AI Remediation Recommendations')).toBeInTheDocument();
    expect(screen.getByText('Roll back payment-service to v2.5.0')).toBeInTheDocument();
    expect(screen.getByTestId('propose-remediations-btn')).toBeInTheDocument();
  });
});
