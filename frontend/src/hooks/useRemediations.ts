import { useState, useEffect, useCallback } from 'react';
import { getRemediations } from '../api/remediations';
import { RemediationActionResponse } from '../types/remediation';
import { handleApiError } from '../api/client';

export interface UseRemediationsOptions {
  status?: string;
  skip?: number;
  limit?: number;
}

export function useRemediations(options?: UseRemediationsOptions) {
  const [remediations, setRemediations] = useState<RemediationActionResponse[]>([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchRemediations = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await getRemediations({
        status: options?.status,
        skip: options?.skip || 0,
        limit: options?.limit || 50,
      });
      setRemediations(data.items);
      setTotal(data.total);
    } catch (err) {
      const apiErr = handleApiError(err);
      setError(apiErr.message);
    } finally {
      setLoading(false);
    }
  }, [options?.status, options?.skip, options?.limit]);

  useEffect(() => {
    fetchRemediations();
  }, [fetchRemediations]);

  return { remediations, total, loading, error, refetch: fetchRemediations };
}
