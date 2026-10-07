import { apiClient } from './client';
import { InvestigationRunResponse, InvestigationRunRequest } from '../types/investigation';
import { RemediationListResponse } from '../types/remediation';

export async function getInvestigation(incidentId: string): Promise<InvestigationRunResponse> {
  const response = await apiClient.get<InvestigationRunResponse>(`/investigations/${incidentId}`);
  return response.data;
}

export async function runInvestigation(
  incidentId: string,
  request?: InvestigationRunRequest
): Promise<InvestigationRunResponse> {
  const response = await apiClient.post<InvestigationRunResponse>(
    `/investigations/${incidentId}/run`,
    request || {}
  );
  return response.data;
}

export async function getInvestigationRemediations(
  investigationId: string
): Promise<RemediationListResponse> {
  const response = await apiClient.get<RemediationListResponse>(
    `/investigations/${investigationId}/remediations`
  );
  return response.data;
}

export async function proposeInvestigationRemediations(
  investigationId: string
): Promise<RemediationListResponse> {
  const response = await apiClient.post<RemediationListResponse>(
    `/investigations/${investigationId}/remediations/propose`
  );
  return response.data;
}
