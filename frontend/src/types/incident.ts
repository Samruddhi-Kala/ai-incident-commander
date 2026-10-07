import { ServiceResponse } from './service';

export type Severity = 'SEV-1' | 'SEV-2' | 'SEV-3' | 'SEV-4';
export type IncidentStatus = 'Triggered' | 'Investigating' | 'Mitigated' | 'Resolved';

export interface IncidentInvestigationBrief {
  id: string;
  incident_id: string;
  investigation_number: string;
  status: 'In Progress' | 'Completed' | 'Inconclusive' | 'Failed';
  probable_root_cause?: string | null;
  confidence_score?: number | null;
  created_at: string;
  completed_at?: string | null;
}

export interface IncidentResponse {
  id: string;
  title: string;
  description: string;
  severity: Severity;
  status: IncidentStatus;
  service_id: string;
  assigned_to?: string | null;
  created_at: string;
  resolved_at?: string | null;
  service?: ServiceResponse | null;
  investigation?: IncidentInvestigationBrief | null;
}

export interface IncidentListResponse {
  items: IncidentResponse[];
  total: number;
  page: number;
  page_size: number;
}

export interface IncidentCreate {
  title: string;
  description: string;
  severity?: Severity;
  status?: IncidentStatus;
  service_id: string;
  assigned_to?: string | null;
}

export interface IncidentUpdate {
  title?: string;
  description?: string;
  severity?: Severity;
  status?: IncidentStatus;
  service_id?: string;
  assigned_to?: string | null;
  resolved_at?: string | null;
}
