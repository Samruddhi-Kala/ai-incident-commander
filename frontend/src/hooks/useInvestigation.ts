import { useState, useEffect, useCallback, useRef } from 'react';
import { getInvestigation, runInvestigation, proposeInvestigationRemediations } from '../api/investigations';
import { InvestigationRunResponse } from '../types/investigation';
import { handleApiError } from '../api/client';

const TERMINAL_STATUSES = new Set(['Completed', 'Inconclusive', 'Failed']);
const POLLING_INTERVAL_MS = 3000;
const MAX_POLL_ATTEMPTS = 40; // 2 minutes max polling safeguard

export function useInvestigation(incidentId: string | undefined) {
  const [investigation, setInvestigation] = useState<InvestigationRunResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [running, setRunning] = useState(false);
  const [proposing, setProposing] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const pollAttempts = useRef(0);
  const pollTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  const clearTimer = () => {
    if (pollTimerRef.current) {
      clearTimeout(pollTimerRef.current);
      pollTimerRef.current = null;
    }
  };

  const fetchInvestigation = useCallback(async (isPolling = false) => {
    if (!incidentId) return;
    if (!isPolling) setLoading(true);
    setError(null);

    try {
      const data = await getInvestigation(incidentId);
      setInvestigation(data);

      // If active/in-progress, continue polling
      if (!TERMINAL_STATUSES.has(data.status)) {
        if (pollAttempts.current < MAX_POLL_ATTEMPTS) {
          pollAttempts.current += 1;
          clearTimer();
          pollTimerRef.current = setTimeout(() => {
            fetchInvestigation(true);
          }, POLLING_INTERVAL_MS);
        } else {
          // Exceeded poll limit safety boundary
          clearTimer();
        }
      } else {
        // Investigation reached terminal state - stop polling
        clearTimer();
        setRunning(false);
      }
    } catch (err) {
      // 404 simply means no investigation started yet
      const apiErr = handleApiError(err);
      if (apiErr.status === 404) {
        setInvestigation(null);
      } else {
        setError(apiErr.message);
      }
      clearTimer();
    } finally {
      if (!isPolling) setLoading(false);
    }
  }, [incidentId]);

  // Initial load
  useEffect(() => {
    pollAttempts.current = 0;
    fetchInvestigation(false);
    return () => {
      clearTimer();
    };
  }, [fetchInvestigation]);

  // Action: Trigger new investigation run
  const startInvestigation = async (maxIterations = 5) => {
    if (!incidentId) return;
    setRunning(true);
    setError(null);
    try {
      const result = await runInvestigation(incidentId, { max_iterations: maxIterations });
      setInvestigation(result);

      // If finished immediately or terminal
      if (TERMINAL_STATUSES.has(result.status)) {
        setRunning(false);
      } else {
        // Begin polling
        pollAttempts.current = 0;
        clearTimer();
        pollTimerRef.current = setTimeout(() => {
          fetchInvestigation(true);
        }, POLLING_INTERVAL_MS);
      }
      return result;
    } catch (err) {
      const apiErr = handleApiError(err);
      setError(apiErr.message);
      setRunning(false);
      throw err;
    }
  };

  // Action: Propose remediations from investigation
  const proposeRemediations = async () => {
    if (!investigation) return;
    setProposing(true);
    setError(null);
    try {
      const res = await proposeInvestigationRemediations(investigation.investigation_id);
      return res;
    } catch (err) {
      const apiErr = handleApiError(err);
      setError(apiErr.message);
      throw err;
    } finally {
      setProposing(false);
    }
  };

  return {
    investigation,
    loading,
    running,
    proposing,
    error,
    refetch: () => fetchInvestigation(false),
    startInvestigation,
    proposeRemediations,
  };
}
