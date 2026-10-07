import { useState, useEffect, useCallback } from 'react';
import {
  getRemediation,
  submitRemediation,
  approveRemediation,
  rejectRemediation,
  executeRemediation,
} from '../api/remediations';
import { RemediationActionResponse } from '../types/remediation';
import { handleApiError } from '../api/client';

export function useRemediation(remediationId: string | undefined) {
  const [remediation, setRemediation] = useState<RemediationActionResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [actionLoading, setActionLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const fetchRemediation = useCallback(async () => {
    if (!remediationId) return;
    setLoading(true);
    setError(null);
    try {
      const data = await getRemediation(remediationId);
      setRemediation(data);
    } catch (err) {
      const apiErr = handleApiError(err);
      setError(apiErr.message);
    } finally {
      setLoading(false);
    }
  }, [remediationId]);

  useEffect(() => {
    fetchRemediation();
  }, [fetchRemediation]);

  const submit = async (comment?: string) => {
    if (!remediationId) return;
    setActionLoading(true);
    setError(null);
    try {
      const updated = await submitRemediation(remediationId, { comment });
      setRemediation(updated);
      return updated;
    } catch (err) {
      const apiErr = handleApiError(err);
      setError(apiErr.message);
      throw err;
    } finally {
      setActionLoading(false);
    }
  };

  const approve = async (comment?: string, approvedBy?: string) => {
    if (!remediationId) return;
    setActionLoading(true);
    setError(null);
    try {
      const updated = await approveRemediation(remediationId, {
        comment,
        approved_by: approvedBy,
        actor_type: 'HUMAN_USER',
      });
      setRemediation(updated);
      return updated;
    } catch (err) {
      const apiErr = handleApiError(err);
      setError(apiErr.message);
      throw err;
    } finally {
      setActionLoading(false);
    }
  };

  const reject = async (reason: string, rejectedBy?: string) => {
    if (!remediationId) return;
    setActionLoading(true);
    setError(null);
    try {
      const updated = await rejectRemediation(remediationId, {
        reason,
        rejected_by: rejectedBy,
        actor_type: 'HUMAN_USER',
      });
      setRemediation(updated);
      return updated;
    } catch (err) {
      const apiErr = handleApiError(err);
      setError(apiErr.message);
      throw err;
    } finally {
      setActionLoading(false);
    }
  };

  const execute = async () => {
    if (!remediationId) return;
    setActionLoading(true);
    setError(null);
    try {
      const updated = await executeRemediation(remediationId);
      setRemediation(updated);
      return updated;
    } catch (err) {
      const apiErr = handleApiError(err);
      setError(apiErr.message);
      throw err;
    } finally {
      setActionLoading(false);
    }
  };

  return {
    remediation,
    loading,
    actionLoading,
    error,
    refetch: fetchRemediation,
    submit,
    approve,
    reject,
    execute,
  };
}
