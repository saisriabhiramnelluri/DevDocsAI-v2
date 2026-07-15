// DevDocsAI V2 — Confidence Badge Component
// Color-coded confidence score display with animated glow

import { useMemo } from 'react';

interface ConfidenceBadgeProps {
  confidence: number;
  size?: 'sm' | 'md' | 'lg';
  showLabel?: boolean;
}

export function ConfidenceBadge({
  confidence,
  size = 'md',
  showLabel = true,
}: ConfidenceBadgeProps) {
  const { label, emoji, colorClass, bgClass, glowColor } = useMemo(() => {
    if (confidence >= 0.9) {
      return {
        label: 'High confidence',
        emoji: '✅',
        colorClass: 'text-emerald-400',
        bgClass: 'bg-emerald-500/10 border-emerald-500/30',
        glowColor: 'rgba(16, 185, 129, 0.2)',
      };
    }
    if (confidence >= 0.7) {
      return {
        label: 'Moderate confidence',
        emoji: '⚠️',
        colorClass: 'text-amber-400',
        bgClass: 'bg-amber-500/10 border-amber-500/30',
        glowColor: 'rgba(245, 158, 11, 0.2)',
      };
    }
    return {
      label: 'Low confidence',
      emoji: '🔍',
      colorClass: 'text-red-400',
      bgClass: 'bg-red-500/10 border-red-500/30',
      glowColor: 'rgba(239, 68, 68, 0.2)',
    };
  }, [confidence]);

  const sizeClasses = {
    sm: 'text-xs px-1.5 py-0.5 gap-1',
    md: 'text-sm px-2.5 py-1 gap-1.5',
    lg: 'text-base px-3 py-1.5 gap-2',
  };

  return (
    <span
      className={`inline-flex items-center rounded-full border font-medium ${bgClass} ${colorClass} ${sizeClasses[size]} transition-all duration-300`}
      style={{ boxShadow: `0 0 12px ${glowColor}` }}
      title={`${label} — ${(confidence * 100).toFixed(0)}%`}
    >
      <span className="flex-shrink-0">{emoji}</span>
      <span className="font-mono">{(confidence * 100).toFixed(0)}%</span>
      {showLabel && size !== 'sm' && (
        <span className="hidden sm:inline opacity-75">{label}</span>
      )}
    </span>
  );
}
