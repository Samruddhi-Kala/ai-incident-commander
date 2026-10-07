import { render, screen, fireEvent } from '@testing-library/react';
import { describe, it, expect, vi } from 'vitest';
import { LoadingState } from '../components/common/LoadingState';
import { ErrorState } from '../components/common/ErrorState';
import { EmptyState } from '../components/common/EmptyState';

describe('Common UI States Suite', () => {
  it('renders LoadingState with custom message', () => {
    render(<LoadingState message="Loading diagnostic artifacts..." />);
    expect(screen.getByText('Loading diagnostic artifacts...')).toBeInTheDocument();
  });

  it('renders ErrorState and triggers retry handler on button click', () => {
    const onRetry = vi.fn();
    render(
      <ErrorState
        title="Telemetry Fetch Failed"
        message="503 Service Unavailable"
        onRetry={onRetry}
      />
    );

    expect(screen.getByText('Telemetry Fetch Failed')).toBeInTheDocument();
    expect(screen.getByText('503 Service Unavailable')).toBeInTheDocument();

    const retryBtn = screen.getByTestId('error-retry-btn');
    fireEvent.click(retryBtn);
    expect(onRetry).toHaveBeenCalledTimes(1);
  });

  it('renders EmptyState with title and message', () => {
    render(
      <EmptyState
        title="No Incidents Triggered"
        message="All production microservices are reporting healthy metrics."
      />
    );

    expect(screen.getByText('No Incidents Triggered')).toBeInTheDocument();
    expect(
      screen.getByText('All production microservices are reporting healthy metrics.')
    ).toBeInTheDocument();
  });
});
