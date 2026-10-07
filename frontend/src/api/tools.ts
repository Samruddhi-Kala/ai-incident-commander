import { apiClient } from './client';
import { ToolListResponse } from '../types/tool';

export async function getTools(): Promise<ToolListResponse> {
  const response = await apiClient.get<ToolListResponse>('/tools');
  return response.data;
}
