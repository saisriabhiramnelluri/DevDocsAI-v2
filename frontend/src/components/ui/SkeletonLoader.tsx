// DevDocsAI — Shared Skeleton Loader Components
// Pulse-animated placeholders for loading states

interface SkeletonProps {
  className?: string;
}

function SkeletonBox({ className = '' }: SkeletonProps) {
  return (
    <div
      className={`bg-white/[0.06] rounded-xl animate-pulse ${className}`}
      aria-hidden="true"
    />
  );
}

// ── Repository Card Skeleton ───────────────────────────────────────────────
export function RepositoryCardSkeleton() {
  return (
    <div className="glass-strong rounded-2xl p-5 border border-white/[0.06] space-y-4">
      <div className="flex justify-between items-start">
        <div className="space-y-2">
          <SkeletonBox className="h-5 w-40" />
          <SkeletonBox className="h-3 w-24" />
        </div>
        <SkeletonBox className="h-5 w-16 rounded-full" />
      </div>
      <div className="grid grid-cols-2 gap-3">
        <SkeletonBox className="h-10 rounded-lg" />
        <SkeletonBox className="h-10 rounded-lg" />
      </div>
      <div className="pt-4 border-t border-white/[0.06] flex justify-between">
        <SkeletonBox className="h-3 w-24" />
        <SkeletonBox className="h-3 w-20" />
      </div>
    </div>
  );
}

// ── Dashboard Grid Skeleton ────────────────────────────────────────────────
export function DashboardSkeleton({ count = 6 }: { count?: number }) {
  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
      {Array.from({ length: count }).map((_, i) => (
        <RepositoryCardSkeleton key={i} />
      ))}
    </div>
  );
}

// ── Overview Tab Skeleton ─────────────────────────────────────────────────
export function OverviewSkeleton() {
  return (
    <div className="p-6 space-y-6 max-w-6xl mx-auto">
      {/* Stats row */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        {Array.from({ length: 4 }).map((_, i) => (
          <div key={i} className="glass rounded-2xl p-4 space-y-2">
            <SkeletonBox className="h-3 w-16" />
            <SkeletonBox className="h-7 w-20" />
          </div>
        ))}
      </div>
      {/* Main content */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-2 glass-strong rounded-2xl p-6 space-y-3">
          <SkeletonBox className="h-4 w-32" />
          {Array.from({ length: 6 }).map((_, i) => (
            <SkeletonBox key={i} className={`h-3 ${i % 3 === 0 ? 'w-full' : i % 3 === 1 ? 'w-4/5' : 'w-3/5'}`} />
          ))}
        </div>
        <div className="glass rounded-2xl p-5 space-y-3">
          <SkeletonBox className="h-4 w-28" />
          {Array.from({ length: 5 }).map((_, i) => (
            <div key={i} className="flex items-center gap-2">
              <SkeletonBox className="h-2 flex-1 rounded-full" />
              <SkeletonBox className="h-3 w-8" />
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}

// ── Chat Skeleton (initial load) ──────────────────────────────────────────
export function ChatSkeleton() {
  return (
    <div className="flex flex-col h-full p-6 gap-6">
      {[0.7, 0.5, 0.85].map((w, i) => (
        <div key={i} className={`flex gap-3 ${i % 2 === 1 ? 'flex-row-reverse' : ''}`}>
          <SkeletonBox className="w-8 h-8 rounded-full flex-shrink-0" />
          <SkeletonBox className={`h-16 rounded-2xl flex-1 max-w-[${Math.round(w * 100)}%]`} style={{ maxWidth: `${w * 100}%` }} />
        </div>
      ))}
    </div>
  );
}

// ── Generic Line Skeleton (for docs loading state) ─────────────────────────
export function DocSkeleton() {
  return (
    <div className="p-8 space-y-4 max-w-3xl mx-auto">
      <SkeletonBox className="h-8 w-64 mb-6" />
      {Array.from({ length: 12 }).map((_, i) => (
        <SkeletonBox
          key={i}
          className={`h-3 ${
            i % 5 === 0 ? 'w-48 h-5 mt-6' :
            i % 4 === 0 ? 'w-3/4' :
            i % 3 === 0 ? 'w-full' : 'w-5/6'
          }`}
        />
      ))}
    </div>
  );
}
