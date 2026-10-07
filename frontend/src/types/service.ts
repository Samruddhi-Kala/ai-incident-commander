export interface ServiceResponse {
  id: string;
  name: string;
  description?: string | null;
  owner_team: string;
  tier: string;
  repository_url?: string | null;
  dependencies: string[];
  created_at: string;
  updated_at: string;
}

export interface ServiceListResponse {
  items: ServiceResponse[];
  total: number;
  page: number;
  page_size: number;
}
