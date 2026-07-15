// DevDocsAI V2 — Reasoning Trace Panel Component
// Expandable panel showing the full reasoning trace with agent steps

import { useState } from 'react';
import {
  ChevronDown,
  ChevronRight,
  Clock,
  Cpu,
  Wrench,
  TrendingUp,
} from 'lucide-react';
import { AGENT_DISPLAY } from '../../types/agent';
import { ConfidenceBadge } from './ConfidenceBadge';
import type { ReasoningTrace, AgentStep } from '../../types/agent';

interface ReasoningTracePanelProps {
  trace: ReasoningTrace;
  className?: string;
}

export function ReasoningTracePanel({ trace, className = '' }: ReasoningTracePanelProps) {
  const [isExpanded, setIsExpanded] = useState(false);
  const [expandedSteps, setExpandedSteps] = useState<Set<number>>(new Set());

  const toggleStep = (idx: number) => {
    setExpandedSteps((prev) => {
      const next = new Set(prev);
      if (next.has(idx)) next.delete(idx);
      else next.add(idx);
      return next;
    });
  };

  if (!trace.steps || trace.steps.length === 0) return null;

  return (
    <div
      className={`rounded-lg border border-white/[0.06] bg-white/[0.02] overflow-hidden ${className}`}
    >
      {/* Header — always visible */}
      <button
        onClick={() => setIsExpanded(!isExpanded)}
        className="w-full flex items-center justify-between gap-3 px-3 py-2
          text-xs text-text-secondary hover:text-text-primary
          hover:bg-white/[0.03] transition-colors duration-200"
      >
        <div className="flex items-center gap-2">
          {isExpanded ? <ChevronDown size={14} /> : <ChevronRight size={14} />}
          <Cpu size={13} className="text-brand-primary" />
          <span className="font-medium">Reasoning Trace</span>
          <span className="text-text-muted">
            {trace.steps.length} step{trace.steps.length !== 1 ? 's' : ''}
          </span>
        </div>

        <div className="flex items-center gap-3">
          {/* Total duration */}
          <span className="flex items-center gap-1 text-text-muted font-mono">
            <Clock size={11} />
            {trace.total_duration_ms < 1000
              ? `${trace.total_duration_ms}ms`
              : `${(trace.total_duration_ms / 1000).toFixed(1)}s`}
          </span>

          {/* Reflection cycles */}
          {trace.reflection_cycles > 0 && (
            <span className="flex items-center gap-1 text-text-muted">
              <TrendingUp size={11} />
              {trace.reflection_cycles} cycle{trace.reflection_cycles !== 1 ? 's' : ''}
            </span>
          )}

          {/* Final confidence */}
          <ConfidenceBadge confidence={trace.final_confidence} size="sm" showLabel={false} />
        </div>
      </button>

      {/* Expanded steps */}
      {isExpanded && (
        <div className="border-t border-white/[0.04]">
          {trace.steps.map((step, idx) => (
            <StepRow
              key={idx}
              step={step}
              index={idx}
              isLast={idx === trace.steps.length - 1}
              isExpanded={expandedSteps.has(idx)}
              onToggle={() => toggleStep(idx)}
            />
          ))}

          {/* Summary footer */}
          <div className="flex items-center justify-between gap-2 px-3 py-2 border-t border-white/[0.04] bg-white/[0.01]">
            <span className="text-[11px] text-text-muted">
              Agents: {trace.agents_invoked.join(' → ')}
            </span>
            {trace.total_tokens_used > 0 && (
              <span className="text-[11px] text-text-muted font-mono">
                ~{trace.total_tokens_used.toLocaleString()} tokens
              </span>
            )}
          </div>
        </div>
      )}
    </div>
  );
}

// ── Individual Step Row ─────────────────────────────────────────────────────

interface StepRowProps {
  step: AgentStep;
  index: number;
  isLast: boolean;
  isExpanded: boolean;
  onToggle: () => void;
}

function StepRow({ step, index, isLast, isExpanded, onToggle }: StepRowProps) {
  const display = AGENT_DISPLAY[step.agent_name] || {
    label: step.agent_name,
    icon: '⚙️',
    color: '#6366F1',
  };

  return (
    <div
      className={`${!isLast ? 'border-b border-white/[0.03]' : ''}`}
    >
      <button
        onClick={onToggle}
        className="w-full flex items-center gap-2.5 px-3 py-2
          text-xs hover:bg-white/[0.02] transition-colors duration-150"
      >
        {/* Step number */}
        <span
          className="flex-shrink-0 w-5 h-5 rounded-full flex items-center justify-center text-[10px] font-bold"
          style={{
            background: `${display.color}20`,
            color: display.color,
            border: `1px solid ${display.color}30`,
          }}
        >
          {index + 1}
        </span>

        {/* Agent icon + name */}
        <span className="flex-shrink-0">{display.icon}</span>
        <span
          className="font-medium flex-shrink-0"
          style={{ color: display.color }}
        >
          {display.label}
        </span>

        {/* Action summary */}
        <span className="text-text-secondary truncate flex-1 text-left">
          {step.action}
        </span>

        {/* Duration */}
        <span className="flex-shrink-0 text-text-muted font-mono text-[10px]">
          {step.duration_ms < 1000
            ? `${step.duration_ms}ms`
            : `${(step.duration_ms / 1000).toFixed(1)}s`}
        </span>

        {/* Confidence dot */}
        <span
          className="flex-shrink-0 w-2 h-2 rounded-full"
          style={{
            background:
              step.confidence >= 0.9
                ? '#10B981'
                : step.confidence >= 0.7
                  ? '#F59E0B'
                  : '#EF4444',
          }}
          title={`Confidence: ${(step.confidence * 100).toFixed(0)}%`}
        />

        {/* Expand icon */}
        {isExpanded ? (
          <ChevronDown size={12} className="flex-shrink-0 text-text-muted" />
        ) : (
          <ChevronRight size={12} className="flex-shrink-0 text-text-muted" />
        )}
      </button>

      {/* Expanded details */}
      {isExpanded && (
        <div className="px-3 pb-2 pl-10 space-y-1">
          {step.output_summary && (
            <p className="text-[11px] text-text-secondary">{step.output_summary}</p>
          )}
          {step.tools_invoked.length > 0 && (
            <div className="flex items-center gap-1.5 flex-wrap">
              <Wrench size={10} className="text-text-muted" />
              {step.tools_invoked.map((tool, i) => (
                <span
                  key={i}
                  className="text-[10px] px-1.5 py-0.5 rounded bg-white/[0.04]
                    border border-white/[0.06] text-text-muted font-mono"
                >
                  {tool}
                </span>
              ))}
            </div>
          )}
          <div className="text-[10px] text-text-muted">
            Confidence: {(step.confidence * 100).toFixed(0)}% · Duration: {step.duration_ms}ms
          </div>
        </div>
      )}
    </div>
  );
}
