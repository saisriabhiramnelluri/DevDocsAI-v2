// DevDocsAI V2 — Agent Chat API Service
import apiClient from './api';
import type {
  AgentChatResponse,
  AgentMode,
  AgentModesResponse,
  AgentStatusEvent,
} from '../types/agent';

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

export const agentChatService = {
  /**
   * Send a query through the V2 multi-agent pipeline.
   */
  async query(
    repoId: string,
    sessionId: string,
    question: string,
    mode: AgentMode = 'auto'
  ): Promise<AgentChatResponse> {
    const { data } = await apiClient.post<AgentChatResponse>('/agent/chat/query', {
      repo_id: repoId,
      session_id: sessionId,
      question,
      mode,
    });
    return data;
  },

  /**
   * Stream an agent chat response via SSE.
   * Emits agent status updates, answer tokens, and final metadata.
   */
  async streamChat(
    repoId: string,
    sessionId: string,
    question: string,
    mode: AgentMode = 'auto',
    callbacks: {
      onAgentStart?: (agentName: string) => void;
      onAgentComplete?: (event: AgentStatusEvent) => void;
      onToken?: (token: string) => void;
      onDone?: (data: AgentStatusEvent) => void;
      onError?: (msg: string) => void;
    }
  ): Promise<void> {
    const clientId = localStorage.getItem('devdocs_client_id');
    const headers: Record<string, string> = { 'Content-Type': 'application/json' };
    if (clientId) {
      headers['X-Client-Id'] = clientId;
    }

    const response = await fetch(`${API_BASE_URL}/api/v1/agent/chat/stream`, {
      method: 'POST',
      headers,
      body: JSON.stringify({
        repo_id: repoId,
        session_id: sessionId,
        question,
        mode,
      }),
    });

    if (!response.ok || !response.body) {
      const err = await response.text();
      callbacks.onError?.(err || 'Agent stream request failed');
      return;
    }

    const reader = response.body.getReader();
    const decoder = new TextDecoder();
    let buffer = '';

    while (true) {
      const { done, value } = await reader.read();
      if (done) break;

      buffer += decoder.decode(value, { stream: true });
      const lines = buffer.split('\n');
      buffer = lines.pop() ?? '';

      for (const line of lines) {
        if (!line.startsWith('data: ')) continue;
        const raw = line.slice(6).trim();
        try {
          const event: AgentStatusEvent = JSON.parse(raw);

          switch (event.type) {
            case 'agent_start':
              callbacks.onAgentStart?.(event.agent_name ?? 'unknown');
              break;
            case 'agent_complete':
              callbacks.onAgentComplete?.(event);
              break;
            case 'token':
              callbacks.onToken?.(event.content ?? '');
              break;
            case 'done':
              callbacks.onDone?.(event);
              break;
            case 'error':
              callbacks.onError?.(event.content ?? 'Unknown error');
              break;
          }
        } catch {
          // skip malformed SSE lines
        }
      }
    }
  },

  /**
   * Get available agent modes.
   */
  async getModes(): Promise<AgentModesResponse> {
    const { data } = await apiClient.get<AgentModesResponse>('/agent/chat/modes');
    return data;
  },
};
