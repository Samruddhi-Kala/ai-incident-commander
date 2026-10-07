import axios, { AxiosError } from 'axios';

// Create a centralized Axios client targeting the FastAPI backend.
// In dev with Vite proxy, requests to /api/v1 are forwarded to http://127.0.0.1:8000/api/v1.
export const apiClient = axios.create({
  baseURL: import.meta.env.VITE_API_URL || '/api/v1',
  headers: {
    'Content-Type': 'application/json',
  },
  timeout: 30000,
});

export interface ApiError {
  message: string;
  status?: number;
  details?: unknown;
}

export function handleApiError(error: unknown): ApiError {
  if (axios.isAxiosError(error)) {
    const axiosErr = error as AxiosError<{ detail?: string | { message?: string } }>;
    const detail = axiosErr.response?.data?.detail;
    const message =
      typeof detail === 'string'
        ? detail
        : detail && typeof detail === 'object' && 'message' in detail
        ? String(detail.message)
        : axiosErr.message || 'An unexpected API error occurred';

    return {
      message,
      status: axiosErr.response?.status,
      details: axiosErr.response?.data,
    };
  }

  return {
    message: error instanceof Error ? error.message : 'An unknown error occurred',
  };
}
