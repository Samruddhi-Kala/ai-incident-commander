export interface ToolInfoResponse {
  tool_name: string;
  domain: string;
  description: string;
}

export interface ToolListResponse {
  total_tools: number;
  domains: string[];
  tools: ToolInfoResponse[];
}
