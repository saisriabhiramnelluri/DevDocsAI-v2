// DevDocsAI — TypeScript Types: Chat

export type MessageRole = 'user' | 'assistant';

export interface SourceReference {
  file: string;
  function?: string;
  line_start?: number;
  line_end?: number;
  content_preview?: string;
  score: number;
}

export interface Message {
  id: string;
  session_id: string;
  role: MessageRole;
  content: string;
  sources?: string;
  timestamp: string;
  // Client-side enriched fields
  sourceRefs?: SourceReference[];
  intent?: string;
  isLoading?: boolean;
  // V2 agent fields
  reasoningTrace?: import('../types/agent').ReasoningTrace;
  confidence?: number;
  agentsInvoked?: string[];
  queryType?: string;
  agentMode?: import('../types/agent').AgentMode;
}

export interface ChatSession {
  id: string;
  repo_id: string;
  title?: string;
  created_at: string;
}

export interface ChatQueryResponse {
  answer: string;
  session_id: string;
  message_id: string;
  sources: SourceReference[];
  graph_context: Record<string, unknown>[];
  intent?: string;
  model: string;
}

export interface ChatHistoryResponse {
  session_id: string;
  messages: Message[];
}

export interface DocumentationResponse {
  repo_id: string;
  doc_type: string;
  content: string;
  generated_at?: string;
}
