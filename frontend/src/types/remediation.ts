export type RemediationStatus =
  | 'PROPOSED'
  | 'PENDING_APPROVAL'
  | 'APPROVED'
  | 'REJECTED'
  | 'EXECUTING'
  | 'COMPLETED'
  | 'FAILED';

export type RiskLevel = 'LOW' | 'MEDIUM' | 'HIGH';

export interface RemediationExecutionResult {
  status: 'COMPLETED' | 'FAILED' | 'REJECTED' | 'EXECUTING' | string;
  action?: string;
  started_at?: string;
  completed_at?: string;
  execution_time_ms?: number;
  output?: Record<string, unknown> | null;
  error?: string | null;
  failure_reason?: string | null;
  rejection_reason?: string | null;
  rejected_by?: string | null;
  rejected_at?: string | null;
  [key: string]: unknown;
}

export interface RemediationActionResponse {
  id: string;
  investigation_id: string;
  action_name: string;
  description?: string | null;
  parameters: Record<string, unknown>;
  reasoning: string;
  risk_level: RiskLevel;
  approval_status: RemediationStatus;
  expected_impact?: string | null;
  rollback_plan?: string | null;
  approved_by?: string | null;
  approval_timestamp?: string | null;
  execution_result?: RemediationExecutionResult | null;
  created_at: string;
}

export interface RemediationListResponse {
  items: RemediationActionResponse[];
  total: number;
}

export interface RemediationActionCreate {
  investigation_id: string;
  action_name: string;
  parameters?: Record<string, unknown>;
  reasoning: string;
  risk_level?: RiskLevel;
  description?: string;
  expected_impact?: string;
  rollback_plan?: string;
}

export interface RemediationApprovalRequest {
  approved_by?: string;
  actor_type?: 'HUMAN_USER';
  comment?: string;
}

export interface RemediationRejectionRequest {
  rejected_by?: string;
  actor_type?: 'HUMAN_USER';
  reason: string;
}

export interface RemediationSubmitRequest {
  submitted_by?: string;
  comment?: string;
}
