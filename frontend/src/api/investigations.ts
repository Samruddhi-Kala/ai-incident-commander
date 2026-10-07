import { apiClient } from './client';
import { InvestigationRunResponse, InvestigationRunRequest } from '../types/investigation';
import { RemediationListResponse } from '../types/remediation';
import { PostmortemResponse } from '../types/postmortem';
import { InvestigationEvaluationResponse, EvaluationListResponse } from '../types/evaluation';

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

export async function getPostmortem(investigationId: string): Promise<PostmortemResponse> {
  const response = await apiClient.get<PostmortemResponse>(
    `/investigations/${investigationId}/postmortem`
  );
  return response.data;
}

export async function createPostmortem(
  investigationId: string,
  regenerate = false
): Promise<PostmortemResponse> {
  const response = await apiClient.post<PostmortemResponse>(
    `/investigations/${investigationId}/postmortem`,
    {},
    { params: { regenerate } }
  );
  return response.data;
}

export async function getEvaluation(
  investigationId: string
): Promise<InvestigationEvaluationResponse> {
  const response = await apiClient.get<InvestigationEvaluationResponse>(
    `/investigations/${investigationId}/evaluation`
  );
  return response.data;
}

export async function evaluateInvestigation(
  investigationId: string,
  force = false
): Promise<InvestigationEvaluationResponse> {
  const response = await apiClient.post<InvestigationEvaluationResponse>(
    `/investigations/${investigationId}/evaluate`,
    {},
    { params: { force } }
  );
  return response.data;
}

export async function listEvaluations(
  skip = 0,
  limit = 50
): Promise<EvaluationListResponse> {
  const response = await apiClient.get<EvaluationListResponse>('/evaluations', {
    params: { skip, limit },
  });
  return response.data;
}

