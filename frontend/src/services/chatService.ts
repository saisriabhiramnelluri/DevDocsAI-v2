// DevDocsAI — Chat API Service
import apiClient from './api';
import type {
  ChatHistoryResponse,
  ChatQueryResponse,
  ChatSession,
} from '../types/chat';

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

export const chatService = {
  async createSession(repoId: string): Promise<ChatSession> {
    const { data } = await apiClient.post<ChatSession>('/chat/sessions', {
      repo_id: repoId,
    });
    return data;
  },

  async listSessionsByRepo(repoId: string, limit = 10): Promise<ChatSession[]> {
    const { data } = await apiClient.get<ChatSession[]>(
      `/chat/sessions/repo/${repoId}?limit=${limit}`
    );
    return data;
  },

  async query(
    repoId: string,
    sessionId: string,
    question: string
  ): Promise<ChatQueryResponse> {
    const { data } = await apiClient.post<ChatQueryResponse>('/chat/query', {
      repo_id: repoId,
      session_id: sessionId,
      question,
    });
    return data;
  },

  async getHistory(sessionId: string): Promise<ChatHistoryResponse> {
    const { data } = await apiClient.get<ChatHistoryResponse>(
      `/chat/history/${sessionId}`
    );
    return data;
  },

  /**
   * Stream a chat response via SSE.
   * Calls onToken for each streamed token, onDone when complete.
   */
  async streamChat(
    repoId: string,
    sessionId: string,
    question: string,
    onToken: (token: string) => void,
    onDone: (data: { sources: any[]; intent: string; model: string }) => void,
    onError: (msg: string) => void,
  ): Promise<void> {
    const clientId = localStorage.getItem('devdocs_client_id');
    const headers: Record<string, string> = { 'Content-Type': 'application/json' };
    if (clientId) {
      headers['X-Client-Id'] = clientId;
    }

    const response = await fetch(`${API_BASE_URL}/api/v1/chat/stream`, {
      method: 'POST',
      headers,
      body: JSON.stringify({ repo_id: repoId, session_id: sessionId, question }),
    });

    if (!response.ok || !response.body) {
      const err = await response.text();
      onError(err || 'Stream request failed');
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
          const parsed = JSON.parse(raw);
          if (parsed.type === 'token') onToken(parsed.content);
          else if (parsed.type === 'done') onDone({ sources: parsed.sources ?? [], intent: parsed.intent ?? '', model: parsed.model ?? '' });
          else if (parsed.type === 'error') onError(parsed.content);
        } catch {
          // skip malformed lines
        }
      }
    }
  },
};
