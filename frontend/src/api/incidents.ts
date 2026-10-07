import { apiClient } from './client';
import { IncidentResponse, IncidentListResponse, IncidentCreate, IncidentUpdate } from '../types/incident';

export async function getIncidents(params?: {
  status?: string;
  severity?: string;
  service_id?: string;
  assigned_to?: string;
  page?: number;
  page_size?: number;
}): Promise<IncidentListResponse> {
  const response = await apiClient.get<IncidentListResponse>('/incidents', { params });
  return response.data;
}

export async function getIncident(incidentId: string): Promise<IncidentResponse> {
  const response = await apiClient.get<IncidentResponse>(`/incidents/${incidentId}`);
  return response.data;
}

export async function createIncident(data: IncidentCreate): Promise<IncidentResponse> {
  const response = await apiClient.post<IncidentResponse>('/incidents', data);
  return response.data;
}

export async function updateIncident(incidentId: string, data: IncidentUpdate): Promise<IncidentResponse> {
  const response = await apiClient.patch<IncidentResponse>(`/incidents/${incidentId}`, data);
  return response.data;
}
