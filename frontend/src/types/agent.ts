// DevDocsAI V2 — Agent TypeScript Types

export type AgentMode = 'auto' | 'v2' | 'v1';

export type QueryType =
  | 'simple'
  | 'general_code'
  | 'architecture'
  | 'documentation'
  | 'code_review'
  | 'complex_multi_hop'
  | 'unknown'
  | 'error';

export interface AgentSourceReference {
  file: string;
  function?: string;
  line_start?: number;
  line_end?: number;
  content_preview?: string;
  score: number;
}

export interface AgentStep {
  agent_name: string;
  action: string;
  tools_invoked: string[];
  confidence: number;
  duration_ms: number;
  output_summary: string;
}

export interface ReasoningTrace {
  steps: AgentStep[];
  total_duration_ms: number;
  total_tokens_used: number;
  agents_invoked: string[];
  reflection_cycles: number;
  final_confidence: number;
}

export interface AgentChatResponse {
  answer: string;
  session_id: string;
  message_id: string;
  sources: AgentSourceReference[];
  reasoning_trace: ReasoningTrace;
  confidence: number;
  agents_invoked: string[];
  query_type: QueryType;
  model: string;
  mode: AgentMode;
  error?: string;
}

export interface AgentStatusEvent {
  type: 'agent_start' | 'agent_complete' | 'token' | 'done' | 'error';
  agent_name?: string;
  content?: string;
  confidence?: number;
  duration_ms?: number;
  step_index?: number;
  total_steps?: number;
  sources?: Record<string, unknown>[];
  reasoning_trace?: Record<string, unknown>;
}

export interface AgentModeInfo {
  id: AgentMode;
  name: string;
  description: string;
  default: boolean;
}

export interface AgentModesResponse {
  modes: AgentModeInfo[];
  current_mode: string;
  confidence_threshold: number;
  max_reflection_cycles: number;
}

// Agent display metadata for UI
export const AGENT_DISPLAY: Record<string, { label: string; icon: string; color: string }> = {
  orchestrator:   { label: 'Orchestrator',   icon: '🎯', color: '#6366F1' },
  planning:       { label: 'Planning',       icon: '📋', color: '#8B5CF6' },
  repository:     { label: 'Repository',     icon: '📦', color: '#06B6D4' },
  retrieval:      { label: 'Retrieval',      icon: '🔍', color: '#10B981' },
  architecture:   { label: 'Architecture',   icon: '🏛️', color: '#F59E0B' },
  documentation:  { label: 'Documentation',  icon: '📝', color: '#EC4899' },
  code_analysis:  { label: 'Code Analysis',  icon: '🔬', color: '#EF4444' },
  reflection:     { label: 'Reflection',     icon: '🪞', color: '#14B8A6' },
  aggregator:     { label: 'Aggregator',     icon: '⚡', color: '#F97316' },
  v1_fast_path:   { label: 'V1 Fast Path',  icon: '⚡', color: '#64748B' },
  v1_fallback:    { label: 'V1 Fallback',   icon: '🔄', color: '#64748B' },
};
