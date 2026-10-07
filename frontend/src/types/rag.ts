export interface SearchResult {
  chunk_id: string;
  document_id: string;
  content: string;
  score: number;
  metadata: Record<string, unknown>;
}

export interface RetrievalResponse {
  query: string;
  mode: string;
  total_results: number;
  results: SearchResult[];
}
