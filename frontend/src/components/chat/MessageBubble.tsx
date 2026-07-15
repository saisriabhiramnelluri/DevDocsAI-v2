import { useState } from 'react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import { Bot, User, ChevronDown, ChevronUp, FileCode } from 'lucide-react';
import type { Message } from '../../types/chat';
import { ReasoningTracePanel } from './ReasoningTracePanel';
import { ConfidenceBadge } from './ConfidenceBadge';

export function MessageBubble({ message }: { message: Message }) {
  const isUser = message.role === 'user';
  const [showSources, setShowSources] = useState(false);

  const hasV2Data = !isUser && (message.reasoningTrace || message.confidence !== undefined);

  return (
    <div className={`flex items-start gap-4 ${isUser ? 'ml-12 flex-row-reverse' : 'mr-12'}`}>
      <div className={`w-8 h-8 rounded-full flex items-center justify-center flex-shrink-0 mt-1 ${
        isUser ? 'bg-gradient-to-br from-brand-primary to-brand-accent' : 'bg-brand-primary/20'
      }`}>
        {isUser ? <User size={16} className="text-white" /> : <Bot size={16} className="text-brand-primary" />}
      </div>
      
      <div className={`flex flex-col ${isUser ? 'items-end' : 'items-start'} max-w-[85%]`}>
        {/* V2 confidence badge in header */}
        {hasV2Data && message.confidence !== undefined && !message.isLoading && (
          <div className="flex items-center gap-2 mb-1.5">
            <ConfidenceBadge confidence={message.confidence} size="sm" />
            {message.agentMode && message.agentMode !== 'v1' && (
              <span className="text-[10px] text-text-muted font-mono px-1.5 py-0.5 rounded bg-white/[0.04] border border-white/[0.06]">
                {message.agentMode === 'v2' ? 'Multi-Agent' : 'Auto'}
              </span>
            )}
          </div>
        )}

        <div className={`px-5 py-4 rounded-2xl ${
          isUser 
            ? 'bg-gradient-to-br from-brand-primary to-brand-secondary rounded-tr-sm text-white shadow-glow-sm' 
            : 'glass border border-white/[0.08] rounded-tl-sm text-text-primary'
        }`}>
          {isUser ? (
            <p className="text-sm whitespace-pre-wrap">{message.content}</p>
          ) : (
            <div className="markdown-content text-sm">
              <ReactMarkdown remarkPlugins={[remarkGfm]}>
                {message.content}
              </ReactMarkdown>
            </div>
          )}
        </div>

        {/* V2 Reasoning Trace Panel */}
        {hasV2Data && message.reasoningTrace && !message.isLoading && (
          <ReasoningTracePanel
            trace={message.reasoningTrace}
            className="mt-2 w-full"
          />
        )}

        {/* Source References */}
        {!isUser && message.sourceRefs && message.sourceRefs.length > 0 && (
          <div className="mt-2 w-full">
            <button
              onClick={() => setShowSources(!showSources)}
              className="flex items-center gap-1.5 text-xs text-brand-primary font-medium hover:text-brand-glow transition-colors bg-brand-primary/10 px-3 py-1.5 rounded-lg"
            >
              <FileCode size={12} />
              <span>{message.sourceRefs.length} Sources used</span>
              {showSources ? <ChevronUp size={12} /> : <ChevronDown size={12} />}
            </button>
            
            {showSources && (
              <div className="mt-2 space-y-2 w-full">
                {message.sourceRefs.map((ref, idx) => (
                  <div key={idx} className="glass rounded-lg p-3 border border-white/[0.06] text-xs font-mono">
                    <div className="flex items-center gap-2 mb-1.5 text-text-muted">
                      <span className="truncate flex-1">{ref.file}</span>
                      {ref.line_start && (
                        <span className="flex-shrink-0 bg-surface px-1.5 py-0.5 rounded text-[10px]">
                          L{ref.line_start}-{ref.line_end}
                        </span>
                      )}
                    </div>
                    {ref.content_preview && (
                      <div className="bg-background/50 rounded p-2 text-text-secondary overflow-x-auto whitespace-pre">
                        {ref.content_preview}
                      </div>
                    )}
                  </div>
                ))}
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
