import { render, screen } from '@testing-library/react';
import { describe, it, expect } from 'vitest';
import { StatusBadge } from '../components/common/StatusBadge';
import { SeverityBadge } from '../components/common/SeverityBadge';
import { RiskBadge } from '../components/common/RiskBadge';
import { ConfidenceMeter } from '../components/common/ConfidenceMeter';

describe('Badges and Meters Component Suite', () => {
  it('renders StatusBadge correctly for various states', () => {
    const { rerender } = render(<StatusBadge status="Triggered" />);
    expect(screen.getByText('Triggered')).toBeInTheDocument();

    rerender(<StatusBadge status="COMPLETED" />);
    expect(screen.getByText('COMPLETED')).toBeInTheDocument();

    rerender(<StatusBadge status="PENDING_APPROVAL" />);
    expect(screen.getByText('PENDING_APPROVAL')).toBeInTheDocument();
  });

  it('renders SeverityBadge correctly for SEV-1 and SEV-2', () => {
    const { rerender } = render(<SeverityBadge severity="SEV-1" />);
    expect(screen.getByText('SEV-1')).toBeInTheDocument();

    rerender(<SeverityBadge severity="SEV-2" />);
    expect(screen.getByText('SEV-2')).toBeInTheDocument();
  });

  it('renders RiskBadge correctly for HIGH risk', () => {
    render(<RiskBadge risk="HIGH" />);
    expect(screen.getByText(/HIGH RISK/i)).toBeInTheDocument();
  });

  it('renders ConfidenceMeter with Root Cause Confidence label and correct percentage', () => {
    render(<ConfidenceMeter confidence={0.88} label="Root Cause Confidence" />);
    expect(screen.getByText('Root Cause Confidence')).toBeInTheDocument();
    expect(screen.getByText('88%')).toBeInTheDocument();
  });
});
