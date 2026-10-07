export interface PostmortemTimelineItem {
  timestamp?: string;
  stage: string;
  description: string;
  source?: string;
}

export interface PostmortemRemediationAction {
  id: string;
  action_name: string;
  approval_status: string;
  risk_level: string;
  reasoning: string;
  execution_result?: Record<string, any>;
}

export interface PostmortemRemediationData {
  proposals_count: number;
  actions: PostmortemRemediationAction[];
  recommended: string[];
  status_summary: string;
}

export interface PostmortemResponse {
  id: string;
  investigation_id: string;
  title: string;
  summary: string;
  impact: string;
  timeline: PostmortemTimelineItem[];
  root_cause: string;
  contributing_factors: string[];
  remediation: PostmortemRemediationData;
  lessons_learned: string[];
  preventive_actions: string[];
  details: {
    symptoms?: string;
    diagnostic_tools_used?: string[];
    tool_call_count?: number;
    evidence_count?: number;
    hypotheses_count?: number;
    confidence_score?: number;
    investigation_status?: string;
    rag_knowledge_used?: string[];
    [key: string]: any;
  };
  generated_at: string;
}
