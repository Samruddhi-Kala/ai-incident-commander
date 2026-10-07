import { apiClient } from './client';
import { ServiceResponse, ServiceListResponse } from '../types/service';

export async function getServices(params?: { page?: number; page_size?: number }): Promise<ServiceListResponse> {
  const response = await apiClient.get<ServiceListResponse>('/services', { params });
  return response.data;
}

export async function getService(serviceId: string): Promise<ServiceResponse> {
  const response = await apiClient.get<ServiceResponse>(`/services/${serviceId}`);
  return response.data;
}
