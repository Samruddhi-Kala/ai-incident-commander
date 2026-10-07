import { useState, useEffect, useCallback } from 'react';
import { getIncident } from '../api/incidents';
import { IncidentResponse } from '../types/incident';
import { handleApiError } from '../api/client';

export function useIncident(incidentId: string | undefined) {
  const [incident, setIncident] = useState<IncidentResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchIncident = useCallback(async () => {
    if (!incidentId) return;
    setLoading(true);
    setError(null);
    try {
      const data = await getIncident(incidentId);
      setIncident(data);
    } catch (err) {
      const apiErr = handleApiError(err);
      setError(apiErr.message);
    } finally {
      setLoading(false);
    }
  }, [incidentId]);

  useEffect(() => {
    fetchIncident();
  }, [fetchIncident]);

  return { incident, loading, error, refetch: fetchIncident };
}
