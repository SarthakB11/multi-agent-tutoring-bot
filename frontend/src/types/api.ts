export interface QueryRequest {
  question: string;
  session_id?: string;
  user_id?: string;
  debug?: boolean;
}

export interface AgentDetails {
  name: string;
  confidence?: number;
  tools_used?: string[];
  reasoning?: string;
}

export interface ErrorDetails {
  code: string;
  message: string;
  details?: any;
  trace_id?: string;
  retry?: boolean;
}

export interface QueryResponse {
  request_id: string;
  session_id: string;
  query: string;
  answer: string;
  agent_details?: AgentDetails;
  debug_info?: any;
}

export interface Message {
  id: string;
  type: 'user' | 'bot';
  content: string;
  timestamp: Date;
  agentDetails?: AgentDetails;
  isError?: boolean;
  errorDetails?: ErrorDetails;
}
