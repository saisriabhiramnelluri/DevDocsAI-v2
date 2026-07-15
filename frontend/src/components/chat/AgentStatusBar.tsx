// DevDocsAI V2 — Agent Status Bar Component
// Real-time display of which agents are active during a query

import { useMemo } from 'react';
import { Loader2, CheckCircle2, XCircle } from 'lucide-react';
import { AGENT_DISPLAY } from '../../types/agent';
import type { AgentStep } from '../../types/agent';

interface AgentStatusBarProps {
  steps: AgentStep[];
  activeAgent?: string | null;
  isRunning: boolean;
}

export function AgentStatusBar({ steps, activeAgent, isRunning }: AgentStatusBarProps) {
  // Build ordered list of agents that participated
  const agentSteps = useMemo(() => {
    const seen = new Set<string>();
    const ordered: Array<{
      name: string;
      step: AgentStep | null;
      status: 'pending' | 'active' | 'done' | 'error';
    }> = [];

    for (const step of steps) {
      if (!seen.has(step.agent_name)) {
        seen.add(step.agent_name);
        ordered.push({
          name: step.agent_name,
          step,
          status: step.confidence > 0 ? 'done' : 'error',
        });
      }
    }

    // Mark active agent
    if (activeAgent && !seen.has(activeAgent)) {
      ordered.push({
        name: activeAgent,
        step: null,
        status: 'active',
      });
    }

    return ordered;
  }, [steps, activeAgent]);

  if (agentSteps.length === 0 && !isRunning) return null;

  return (
    <div className="flex items-center gap-1 px-3 py-2 overflow-x-auto scrollbar-hide">
      {agentSteps.map((agent, idx) => {
        const display = AGENT_DISPLAY[agent.name] || {
          label: agent.name,
          icon: '⚙️',
          color: '#6366F1',
        };

        return (
          <div key={agent.name} className="flex items-center gap-1 flex-shrink-0">
            {/* Connector line */}
            {idx > 0 && (
              <div
                className="w-4 h-px flex-shrink-0"
                style={{
                  background:
                    agent.status === 'done'
                      ? `${display.color}60`
                      : 'rgba(255,255,255,0.1)',
                }}
              />
            )}

            {/* Agent chip */}
            <div
              className={`
                flex items-center gap-1.5 rounded-full px-2.5 py-1
                text-xs font-medium border transition-all duration-300
                ${agent.status === 'active'
                  ? 'animate-pulse border-white/20'
                  : agent.status === 'done'
                    ? 'border-white/10'
                    : agent.status === 'error'
                      ? 'border-red-500/30'
                      : 'border-white/5 opacity-40'
                }
              `}
              style={{
                background:
                  agent.status === 'active' || agent.status === 'done'
                    ? `${display.color}15`
                    : 'transparent',
                boxShadow:
                  agent.status === 'active'
                    ? `0 0 12px ${display.color}30`
                    : 'none',
              }}
              title={
                agent.step
                  ? `${display.label}: ${agent.step.action} (${agent.step.duration_ms}ms, confidence: ${(agent.step.confidence * 100).toFixed(0)}%)`
                  : `${display.label}: Running...`
              }
            >
              {/* Status icon */}
              {agent.status === 'active' ? (
                <Loader2
                  size={12}
                  className="animate-spin flex-shrink-0"
                  style={{ color: display.color }}
                />
              ) : agent.status === 'done' ? (
                <CheckCircle2
                  size={12}
                  className="flex-shrink-0"
                  style={{ color: display.color }}
                />
              ) : agent.status === 'error' ? (
                <XCircle size={12} className="flex-shrink-0 text-red-400" />
              ) : (
                <span className="text-[10px] flex-shrink-0">{display.icon}</span>
              )}

              {/* Label */}
              <span
                className="whitespace-nowrap"
                style={{
                  color:
                    agent.status === 'active' || agent.status === 'done'
                      ? display.color
                      : undefined,
                }}
              >
                {display.label}
              </span>

              {/* Duration */}
              {agent.step && agent.step.duration_ms > 0 && (
                <span className="text-text-muted text-[10px] font-mono">
                  {agent.step.duration_ms < 1000
                    ? `${agent.step.duration_ms}ms`
                    : `${(agent.step.duration_ms / 1000).toFixed(1)}s`}
                </span>
              )}
            </div>
          </div>
        );
      })}

      {/* Running indicator when no specific agent is active */}
      {isRunning && !activeAgent && agentSteps.length === 0 && (
        <div className="flex items-center gap-2 text-xs text-text-secondary">
          <Loader2 size={14} className="animate-spin text-brand-primary" />
          <span>Initializing agents...</span>
        </div>
      )}
    </div>
  );
}
