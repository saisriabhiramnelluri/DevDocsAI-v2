// DevDocsAI V2 — Agent Mode Toggle Component
// Allows switching between V1 (fast), Auto, and V2 (multi-agent) modes

import { useState } from 'react';
import { Zap, Brain, Sparkles } from 'lucide-react';
import type { AgentMode } from '../../types/agent';

interface AgentModeToggleProps {
  mode: AgentMode;
  onChange: (mode: AgentMode) => void;
  disabled?: boolean;
}

const MODE_CONFIG: Record<
  AgentMode,
  { label: string; description: string; icon: typeof Zap; color: string }
> = {
  v1: {
    label: 'Fast',
    description: 'V1 Hybrid RAG — fastest response',
    icon: Zap,
    color: '#64748B',
  },
  auto: {
    label: 'Auto',
    description: 'Smart routing — picks the best mode',
    icon: Sparkles,
    color: '#6366F1',
  },
  v2: {
    label: 'Deep',
    description: 'Multi-agent pipeline — most thorough',
    icon: Brain,
    color: '#8B5CF6',
  },
};

const MODES: AgentMode[] = ['v1', 'auto', 'v2'];

export function AgentModeToggle({ mode, onChange, disabled = false }: AgentModeToggleProps) {
  const [showTooltip, setShowTooltip] = useState<AgentMode | null>(null);

  return (
    <div className="relative inline-flex items-center rounded-lg border border-white/10 bg-white/[0.03] p-0.5">
      {MODES.map((m) => {
        const config = MODE_CONFIG[m];
        const Icon = config.icon;
        const isActive = mode === m;

        return (
          <button
            key={m}
            onClick={() => !disabled && onChange(m)}
            onMouseEnter={() => setShowTooltip(m)}
            onMouseLeave={() => setShowTooltip(null)}
            disabled={disabled}
            className={`
              relative flex items-center gap-1.5 rounded-md px-3 py-1.5 text-xs font-medium
              transition-all duration-200 ease-out
              ${isActive
                ? 'text-white shadow-lg'
                : 'text-text-secondary hover:text-text-primary'
              }
              ${disabled ? 'cursor-not-allowed opacity-50' : 'cursor-pointer'}
            `}
            style={
              isActive
                ? {
                    background: `${config.color}22`,
                    boxShadow: `0 0 16px ${config.color}30, inset 0 1px 1px ${config.color}15`,
                    border: `1px solid ${config.color}40`,
                  }
                : { border: '1px solid transparent' }
            }
          >
            <Icon
              size={13}
              style={isActive ? { color: config.color } : undefined}
            />
            <span>{config.label}</span>

            {/* Tooltip */}
            {showTooltip === m && (
              <div
                className="absolute bottom-full left-1/2 -translate-x-1/2 mb-2 z-50
                  whitespace-nowrap rounded-md px-2.5 py-1.5 text-xs
                  bg-background-secondary border border-white/10 shadow-xl
                  text-text-secondary pointer-events-none"
                style={{ boxShadow: '0 4px 20px rgba(0,0,0,0.5)' }}
              >
                {config.description}
                <div
                  className="absolute top-full left-1/2 -translate-x-1/2 -mt-px
                    border-4 border-transparent border-t-white/10"
                />
              </div>
            )}
          </button>
        );
      })}
    </div>
  );
}
