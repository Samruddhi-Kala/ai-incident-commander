export type InvestigationStatus = 'In Progress' | 'Completed' | 'Inconclusive' | 'Failed';

export interface InvestigationStepInfo {
  step_order: number;
  title: string;
  status: string;
  output_summary?: string | null;
  created_at: string;
}

export interface EvidenceInfo {
  id: string;
  source_tool: string;
  summary: string;
  relevance_score: number;
  raw_payload: Record<string, unknown>;
  collected_at: string;
}

export interface HypothesisInfo {
  id: string;
  hypothesis_text: string;
  status: 'SUPPORTED' | 'PARTIALLY_SUPPORTED' | 'NOT_SUPPORTED' | 'INCONCLUSIVE' | 'RULED_OUT' | string;
  confidence_score: number;
  supporting_evidence_ids: string[];
  opposing_evidence_ids: string[];
  created_at: string;
}

export interface ToolCallInfo {
  id: string;
  tool_name: string;
  arguments: Record<string, unknown>;
  status: 'SUCCESS' | 'FAILED' | string;
  execution_time_ms: number;
  created_at: string;
}

export interface RetrievedSource {
  title?: string;
  source_path?: string;
  document_type?: string;
  score?: number;
  content_snippet?: string;
  [key: string]: unknown;
}

export interface InvestigationRunResponse {
  investigation_id: string;
  incident_id: string;
  investigation_number: string;
  status: InvestigationStatus;
  probable_root_cause?: string | null;
  confidence_score?: number | null;
  analysis_reasoning?: string | null;
  recommended_remediation: string[];
  steps: InvestigationStepInfo[];
  evidence: EvidenceInfo[];
  hypotheses: HypothesisInfo[];
  tool_calls: ToolCallInfo[];
  retrieved_sources: RetrievedSource[];
  created_at: string;
  completed_at?: string | null;
}

export interface InvestigationRunRequest {
  max_iterations?: number;
}
