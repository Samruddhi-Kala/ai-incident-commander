import { useState, useEffect, useCallback } from 'react';
import { getPostmortem, createPostmortem } from '../api/investigations';
import { PostmortemResponse } from '../types/postmortem';
import { handleApiError } from '../api/client';

export function usePostmortem(investigationId: string | undefined) {
  const [postmortem, setPostmortem] = useState<PostmortemResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [generating, setGenerating] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const fetchPostmortem = useCallback(async () => {
    if (!investigationId) return;
    setLoading(true);
    setError(null);
    try {
      const data = await getPostmortem(investigationId);
      setPostmortem(data);
    } catch (err) {
      const apiErr = handleApiError(err);
      if (apiErr.status === 404) {
        setPostmortem(null);
      } else {
        setError(apiErr.message);
      }
    } finally {
      setLoading(false);
    }
  }, [investigationId]);

  useEffect(() => {
    fetchPostmortem();
  }, [fetchPostmortem]);

  const generate = async (regenerate = false) => {
    if (!investigationId) return;
    setGenerating(true);
    setError(null);
    try {
      const data = await createPostmortem(investigationId, regenerate);
      setPostmortem(data);
      return data;
    } catch (err) {
      const apiErr = handleApiError(err);
      setError(apiErr.message);
      throw err;
    } finally {
      setGenerating(false);
    }
  };

  return {
    postmortem,
    loading,
    generating,
    error,
    generate,
    refetch: fetchPostmortem,
  };
}
