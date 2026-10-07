export interface MetricScoreDetail {
  score: number;
  weight: number;
  feedback: string;
  [key: string]: any;
}

export interface EvaluationMetricsBreakdown {
  evidence: MetricScoreDetail;
  hypothesis: MetricScoreDetail;
  verification: MetricScoreDetail;
  rag: MetricScoreDetail;
  tool_efficiency: MetricScoreDetail;
  outcome: {
    status: string;
    confidence_score?: number;
    factor_applied?: number;
  };
}

export interface InvestigationEvaluationResponse {
  id: string;
  investigation_id: string;
  overall_score: number;
  evidence_score: number;
  hypothesis_score: number;
  verification_score: number;
  rag_score: number;
  tool_efficiency_score: number;
  evaluation_reasoning: string;
  metrics_breakdown: EvaluationMetricsBreakdown;
  created_at: string;
}

export interface EvaluationListResponse {
  items: InvestigationEvaluationResponse[];
  total: number;
}
