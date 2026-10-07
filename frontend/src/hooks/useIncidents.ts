import { useState, useEffect, useCallback } from 'react';
import { getIncidents } from '../api/incidents';
import { IncidentResponse } from '../types/incident';
import { handleApiError } from '../api/client';

export interface UseIncidentsOptions {
  status?: string;
  severity?: string;
  service_id?: string;
  page?: number;
  pageSize?: number;
}

export function useIncidents(options?: UseIncidentsOptions) {
  const [incidents, setIncidents] = useState<IncidentResponse[]>([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchIncidents = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await getIncidents({
        status: options?.status,
        severity: options?.severity,
        service_id: options?.service_id,
        page: options?.page || 1,
        page_size: options?.pageSize || 50,
      });
      setIncidents(data.items);
      setTotal(data.total);
    } catch (err) {
      const apiErr = handleApiError(err);
      setError(apiErr.message);
    } finally {
      setLoading(false);
    }
  }, [options?.status, options?.severity, options?.service_id, options?.page, options?.pageSize]);

  useEffect(() => {
    fetchIncidents();
  }, [fetchIncidents]);

  return { incidents, total, loading, error, refetch: fetchIncidents };
}
