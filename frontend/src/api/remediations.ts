import { apiClient } from './client';
import {
  RemediationActionResponse,
  RemediationListResponse,
  RemediationActionCreate,
  RemediationApprovalRequest,
  RemediationRejectionRequest,
  RemediationSubmitRequest,
} from '../types/remediation';

export async function getRemediations(params?: {
  status?: string;
  skip?: number;
  limit?: number;
}): Promise<RemediationListResponse> {
  const response = await apiClient.get<RemediationListResponse>('/remediations', { params });
  return response.data;
}

export async function getRemediation(remediationId: string): Promise<RemediationActionResponse> {
  const response = await apiClient.get<RemediationActionResponse>(`/remediations/${remediationId}`);
  return response.data;
}

export async function createRemediation(data: RemediationActionCreate): Promise<RemediationActionResponse> {
  const response = await apiClient.post<RemediationActionResponse>('/remediations', data);
  return response.data;
}

export async function submitRemediation(
  remediationId: string,
  payload?: RemediationSubmitRequest
): Promise<RemediationActionResponse> {
  const response = await apiClient.post<RemediationActionResponse>(
    `/remediations/${remediationId}/submit`,
    payload
  );
  return response.data;
}

export async function approveRemediation(
  remediationId: string,
  payload?: RemediationApprovalRequest
): Promise<RemediationActionResponse> {
  const response = await apiClient.post<RemediationActionResponse>(
    `/remediations/${remediationId}/approve`,
    payload
  );
  return response.data;
}

export async function rejectRemediation(
  remediationId: string,
  payload: RemediationRejectionRequest
): Promise<RemediationActionResponse> {
  const response = await apiClient.post<RemediationActionResponse>(
    `/remediations/${remediationId}/reject`,
    payload
  );
  return response.data;
}

export async function executeRemediation(remediationId: string): Promise<RemediationActionResponse> {
  const response = await apiClient.post<RemediationActionResponse>(
    `/remediations/${remediationId}/execute`
  );
  return response.data;
}
