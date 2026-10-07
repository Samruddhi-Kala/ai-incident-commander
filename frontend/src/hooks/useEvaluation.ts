import { useState, useEffect, useCallback } from 'react';
import { getEvaluation, evaluateInvestigation } from '../api/investigations';
import { InvestigationEvaluationResponse } from '../types/evaluation';
import { handleApiError } from '../api/client';

export function useEvaluation(investigationId: string | undefined) {
  const [evaluation, setEvaluation] = useState<InvestigationEvaluationResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [evaluating, setEvaluating] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const fetchEvaluation = useCallback(async () => {
    if (!investigationId) return;
    setLoading(true);
    setError(null);
    try {
      const data = await getEvaluation(investigationId);
      setEvaluation(data);
    } catch (err) {
      const apiErr = handleApiError(err);
      if (apiErr.status === 404) {
        setEvaluation(null);
      } else {
        setError(apiErr.message);
      }
    } finally {
      setLoading(false);
    }
  }, [investigationId]);

  useEffect(() => {
    fetchEvaluation();
  }, [fetchEvaluation]);

  const evaluate = async (force = false) => {
    if (!investigationId) return;
    setEvaluating(true);
    setError(null);
    try {
      const data = await evaluateInvestigation(investigationId, force);
      setEvaluation(data);
      return data;
    } catch (err) {
      const apiErr = handleApiError(err);
      setError(apiErr.message);
      throw err;
    } finally {
      setEvaluating(false);
    }
  };

  return {
    evaluation,
    loading,
    evaluating,
    error,
    evaluate,
    refetch: fetchEvaluation,
  };
}
