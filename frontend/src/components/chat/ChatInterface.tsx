import { useState, useRef, useEffect, useCallback } from 'react';
import { Send, Loader2, Bot, Code2, Plus, ChevronDown, History, Brain } from 'lucide-react';
import { chatService } from '../../services/chatService';
import { agentChatService } from '../../services/agentChatService';
import { MessageBubble } from './MessageBubble';
import { AgentModeToggle } from './AgentModeToggle';
import { AgentStatusBar } from './AgentStatusBar';
import type { Message, ChatSession } from '../../types/chat';
import type { SourceReference } from '../../types/chat';
import type { AgentMode, AgentStep, AgentStatusEvent, ReasoningTrace } from '../../types/agent';
import toast from 'react-hot-toast';

const SUGGESTED_QUESTIONS = [
  'Explain the overall architecture',
  'Where is the database connection configured?',
  'How does authentication work?',
  'What are the main entry points?',
];

const MODE_LABELS: Record<AgentMode, string> = {
  v1: 'Hybrid RAG (V1 Fast)',
  auto: 'Auto (Smart Routing)',
  v2: 'Multi-Agent (V2 Deep)',
};

export function ChatInterface({ repoId }: { repoId: string }) {
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [sessions, setSessions] = useState<ChatSession[]>([]);
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [isInitializing, setIsInitializing] = useState(true);
  const [showSessionPicker, setShowSessionPicker] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  // V2 agent state
  const [agentMode, setAgentMode] = useState<AgentMode>('auto');
  const [activeAgent, setActiveAgent] = useState<string | null>(null);
  const [agentSteps, setAgentSteps] = useState<AgentStep[]>([]);

  // Auto-scroll to bottom
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  // Initialize: load existing sessions or create a new one
  useEffect(() => {
    let mounted = true;
    const init = async () => {
      try {
        const existingSessions = await chatService.listSessionsByRepo(repoId);
        if (!mounted) return;
        setSessions(existingSessions);

        if (existingSessions.length > 0) {
          // Resume the most recent session
          await loadSession(existingSessions[0].id, mounted);
        } else {
          // No sessions yet — create one
          const newSession = await chatService.createSession(repoId);
          if (!mounted) return;
          setSessions([newSession]);
          setSessionId(newSession.id);
        }
      } catch (err) {
        if (mounted) toast.error('Failed to initialize chat session');
      } finally {
        if (mounted) setIsInitializing(false);
      }
    };
    init();
    return () => { mounted = false; };
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [repoId]);

  const loadSession = async (sid: string, mounted = true) => {
    setSessionId(sid);
    setShowSessionPicker(false);
    try {
      const history = await chatService.getHistory(sid);
      if (!mounted) return;
      const loaded: Message[] = history.messages.map((m) => ({
        ...m,
        sourceRefs: m.sources ? (() => { try { return JSON.parse(m.sources!); } catch { return []; } })() : [],
      }));
      setMessages(loaded);
    } catch {
      setMessages([]);
    }
  };

  const startNewSession = async () => {
    try {
      const newSession = await chatService.createSession(repoId);
      setSessions((prev) => [newSession, ...prev]);
      setSessionId(newSession.id);
      setMessages([]);
      setShowSessionPicker(false);
    } catch {
      toast.error('Failed to create new session');
    }
  };

  const appendToken = useCallback((token: string) => {
    setMessages((prev) => {
      const last = prev[prev.length - 1];
      if (last && last.role === 'assistant' && last.isLoading) {
        return [
          ...prev.slice(0, -1),
          { ...last, content: last.content + token },
        ];
      }
      return prev;
    });
  }, []);

  const finalizeMessage = useCallback((sources: SourceReference[], intent: string) => {
    setMessages((prev) => {
      const last = prev[prev.length - 1];
      if (last && last.role === 'assistant' && last.isLoading) {
        return [...prev.slice(0, -1), { ...last, isLoading: false, sourceRefs: sources, intent }];
      }
      return prev;
    });
    setIsLoading(false);
  }, []);

  // V2-specific: finalize with reasoning trace and confidence
  const finalizeV2Message = useCallback((data: AgentStatusEvent) => {
    const trace: ReasoningTrace = (data.reasoning_trace as unknown as ReasoningTrace) || {
      steps: [],
      total_duration_ms: data.duration_ms ?? 0,
      total_tokens_used: 0,
      agents_invoked: [],
      reflection_cycles: 0,
      final_confidence: data.confidence ?? 0.5,
    };

    const sources: SourceReference[] = ((data.sources as unknown as SourceReference[]) ?? []);

    setMessages((prev) => {
      const last = prev[prev.length - 1];
      if (last && last.role === 'assistant' && last.isLoading) {
        return [
          ...prev.slice(0, -1),
          {
            ...last,
            isLoading: false,
            sourceRefs: sources,
            reasoningTrace: trace,
            confidence: data.confidence ?? trace.final_confidence,
            agentsInvoked: trace.agents_invoked,
            queryType: (data as Record<string, unknown>).query_type as string,
            agentMode,
          },
        ];
      }
      return prev;
    });
    setActiveAgent(null);
    setAgentSteps([]);
    setIsLoading(false);
  }, [agentMode]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!input.trim() || !sessionId || isLoading) return;

    const question = input.trim();
    setInput('');
    setIsLoading(true);
    setActiveAgent(null);
    setAgentSteps([]);

    // Add user message
    const userMsg: Message = {
      id: `user-${Date.now()}`,
      session_id: sessionId,
      role: 'user',
      content: question,
      timestamp: new Date().toISOString(),
    };

    // Add placeholder assistant message that we'll stream into
    const assistantPlaceholder: Message = {
      id: `assistant-${Date.now()}`,
      session_id: sessionId,
      role: 'assistant',
      content: '',
      timestamp: new Date().toISOString(),
      isLoading: true,
      agentMode,
    };

    setMessages((prev) => [...prev, userMsg, assistantPlaceholder]);

    // Decide which pipeline to use based on agent mode
    const useV2 = agentMode === 'v2' || agentMode === 'auto';

    if (useV2) {
      // ── V2 Agent Pipeline ──
      try {
        await agentChatService.streamChat(
          repoId,
          sessionId,
          question,
          agentMode,
          {
            onAgentStart: (agentName) => {
              setActiveAgent(agentName);
            },
            onAgentComplete: (event) => {
              setActiveAgent(null);
              if (event.agent_name) {
                setAgentSteps((prev) => [
                  ...prev,
                  {
                    agent_name: event.agent_name!,
                    action: event.content ?? '',
                    tools_invoked: [],
                    confidence: event.confidence ?? 0.5,
                    duration_ms: event.duration_ms ?? 0,
                    output_summary: event.content ?? '',
                  },
                ]);
              }
            },
            onToken: (token) => appendToken(token),
            onDone: (data) => finalizeV2Message(data),
            onError: (errMsg) => {
              toast.error('Agent error: ' + errMsg);
              setMessages((prev) => prev.filter((m) => m.id !== assistantPlaceholder.id));
              setInput(question);
              setIsLoading(false);
              setActiveAgent(null);
              setAgentSteps([]);
            },
          },
        );
      } catch (err: unknown) {
        // Fallback to V1 non-streaming if agent stream fails
        try {
          const response = await chatService.query(repoId, sessionId, question);
          finalizeMessage(response.sources, response.intent ?? '');
          setMessages((prev) => {
            const last = prev[prev.length - 1];
            if (last?.isLoading) {
              return [...prev.slice(0, -1), {
                ...last,
                content: response.answer,
                isLoading: false,
                sourceRefs: response.sources,
              }];
            }
            return prev;
          });
        } catch {
          toast.error('Failed to send message');
          setMessages((prev) => prev.filter((m) => !m.isLoading));
          setInput(question);
          setIsLoading(false);
        }
      }
    } else {
      // ── V1 Fast Path ──
      try {
        await chatService.streamChat(
          repoId,
          sessionId,
          question,
          (token) => appendToken(token),
          ({ sources, intent }) => finalizeMessage(sources, intent),
          (errMsg) => {
            toast.error('Chat error: ' + errMsg);
            setMessages((prev) => prev.filter((m) => m.id !== assistantPlaceholder.id));
            setInput(question);
            setIsLoading(false);
          },
        );
      } catch (err: unknown) {
        // Fallback to non-streaming if stream fails
        try {
          const response = await chatService.query(repoId, sessionId, question);
          finalizeMessage(response.sources, response.intent ?? '');
          setMessages((prev) => {
            const last = prev[prev.length - 1];
            if (last?.isLoading) {
              return [...prev.slice(0, -1), {
                ...last,
                content: response.answer,
                isLoading: false,
                sourceRefs: response.sources,
              }];
            }
            return prev;
          });
        } catch {
          toast.error('Failed to send message');
          setMessages((prev) => prev.filter((m) => !m.isLoading));
          setInput(question);
          setIsLoading(false);
        }
      }
    }
  };

  if (isInitializing) {
    return (
      <div className="h-full flex items-center justify-center">
        <Loader2 size={32} className="animate-spin text-brand-primary" />
      </div>
    );
  }

  return (
    <div className="relative flex flex-col h-[calc(100vh-140px)] w-full max-w-4xl mx-auto">
      {/* Session bar + Agent Mode Toggle */}
      <div className="flex-shrink-0 flex items-center justify-between px-4 md:px-6 py-2 border-b border-white/[0.06]">
        <div className="relative">
          <button
            onClick={() => setShowSessionPicker((v) => !v)}
            className="flex items-center gap-2 text-xs text-text-secondary hover:text-text-primary transition-colors px-3 py-1.5 rounded-lg hover:bg-surface"
          >
            <History size={14} />
            <span className="font-mono">
              {sessions.length > 0 ? `Session ${sessions.findIndex((s) => s.id === sessionId) + 1} of ${sessions.length}` : 'New Session'}
            </span>
            <ChevronDown size={12} className={`transition-transform ${showSessionPicker ? 'rotate-180' : ''}`} />
          </button>

          {showSessionPicker && (
            <div className="absolute top-full left-0 mt-1 w-64 glass-strong rounded-xl border border-white/[0.1] shadow-card z-50 overflow-hidden">
              <div className="p-2 border-b border-white/[0.06]">
                <button
                  onClick={startNewSession}
                  className="flex items-center gap-2 w-full px-3 py-2 rounded-lg text-sm text-brand-primary hover:bg-brand-primary/10 transition-colors"
                >
                  <Plus size={14} />
                  New Chat Session
                </button>
              </div>
              <div className="max-h-48 overflow-y-auto">
                {sessions.map((s, idx) => (
                  <button
                    key={s.id}
                    onClick={() => loadSession(s.id)}
                    className={`w-full text-left px-4 py-2.5 text-sm transition-colors ${
                      s.id === sessionId ? 'bg-brand-primary/20 text-white' : 'text-text-secondary hover:bg-surface'
                    }`}
                  >
                    <span className="font-medium">Session {idx + 1}</span>
                    <span className="block text-xs text-text-muted mt-0.5">
                      {new Date(s.created_at).toLocaleString()}
                    </span>
                  </button>
                ))}
              </div>
            </div>
          )}
        </div>

        <div className="flex items-center gap-3">
          {/* Agent Mode Toggle */}
          <AgentModeToggle
            mode={agentMode}
            onChange={setAgentMode}
            disabled={isLoading}
          />

          <button
            onClick={startNewSession}
            className="flex items-center gap-1.5 text-xs px-3 py-1.5 rounded-lg glass hover:bg-brand-primary/10 text-text-secondary hover:text-brand-primary transition-all border border-white/[0.06]"
          >
            <Plus size={12} />
            New Chat
          </button>
        </div>
      </div>

      {/* Agent Status Bar — shown during V2 loading */}
      {isLoading && (agentMode === 'v2' || agentMode === 'auto') && (
        <div className="flex-shrink-0 border-b border-white/[0.04] bg-white/[0.01]">
          <AgentStatusBar
            steps={agentSteps}
            activeAgent={activeAgent}
            isRunning={isLoading}
          />
        </div>
      )}

      {/* Messages Area */}
      <div className="flex-1 overflow-y-auto px-4 md:px-6 space-y-6 pt-4 pb-40">
        {messages.length === 0 ? (
          <div className="h-full flex flex-col items-center justify-center text-center p-8 opacity-70 min-h-[300px]">
            <Bot size={48} className="text-brand-primary mb-4" />
            <h3 className="text-xl font-bold mb-2">How can I help you?</h3>
            <p className="text-text-muted max-w-md mb-6 text-sm">
              Ask about architecture, find specific logic, trace data flows, or request documentation.
            </p>
            <div className="flex flex-wrap justify-center gap-2">
              {SUGGESTED_QUESTIONS.map((q) => (
                <button
                  key={q}
                  onClick={() => setInput(q)}
                  className="px-3 py-1.5 rounded-full text-xs border border-white/[0.1] hover:border-brand-primary/50 hover:text-brand-primary transition-all text-text-secondary"
                >
                  {q}
                </button>
              ))}
            </div>
          </div>
        ) : (
          messages.map((msg) => <MessageBubble key={msg.id} message={msg} />)
        )}
        <div ref={messagesEndRef} />
      </div>

      {/* Input Area — fixed at bottom of chat container */}
      <div className="absolute bottom-0 left-0 right-0 pt-8 pb-4 px-4 md:px-6 bg-gradient-to-t from-[#030509] via-[#030509]/95 to-transparent">
        <form onSubmit={handleSubmit} className="relative flex items-end glass-strong rounded-2xl border-glow">
          <textarea
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); handleSubmit(e); }
            }}
            placeholder="Ask a question about the repository… (Enter to send)"
            className="flex-1 max-h-48 min-h-[56px] w-full bg-transparent text-white placeholder-text-muted px-4 py-4 resize-none outline-none text-sm"
            disabled={isLoading}
            rows={1}
          />
          <button
            type="submit"
            disabled={!input.trim() || isLoading}
            className="m-2 p-2.5 rounded-xl bg-brand-primary text-white hover:bg-brand-secondary disabled:opacity-40 disabled:cursor-not-allowed transition-colors flex-shrink-0"
          >
            {isLoading ? <Loader2 size={18} className="animate-spin" /> : <Send size={18} />}
          </button>
        </form>
        <p className="text-center text-[10px] text-text-muted font-mono mt-2 flex items-center justify-center gap-1">
          <Brain size={11} />
          {MODE_LABELS[agentMode]} · Hybrid RAG (Vector + BM25 + Graph)
        </p>
      </div>
    </div>
  );
}
