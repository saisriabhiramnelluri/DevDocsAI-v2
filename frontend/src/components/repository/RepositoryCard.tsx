import type { Repository } from '../../types/repository';
import { motion } from 'framer-motion';
import { GitBranch, Clock, Terminal, Activity, ArrowRight, RefreshCw } from 'lucide-react';

const STATUS_COLORS: Record<string, string> = {
  pending: 'bg-yellow-400',
  cloning: 'bg-brand-primary',
  parsing: 'bg-brand-primary',
  embedding: 'bg-brand-primary',
  graph: 'bg-brand-primary',
  summarizing: 'bg-brand-primary',
  ready: 'bg-green-400',
  failed: 'bg-red-400',
};

const STATUS_TEXT: Record<string, string> = {
  pending: 'text-yellow-400',
  ready: 'text-green-400',
  failed: 'text-red-400',
};

export function RepositoryCard({ repo, onClick }: { repo: Repository; onClick: () => void }) {
  const isProcessing = !['ready', 'failed', 'pending'].includes(repo.status);

  return (
    <motion.div
      whileHover={{ y: -4 }}
      onClick={onClick}
      className="card-hover glass-strong rounded-2xl p-5 border border-white/[0.08] cursor-pointer group"
    >
      <div className="flex justify-between items-start mb-4">
        <div>
          <h3 className="text-lg font-semibold text-white mb-1 group-hover:text-brand-primary transition-colors flex items-center gap-2">
            <GitBranch size={16} />
            {repo.repo_name || repo.repo_url.split('/').pop()}
          </h3>
          <p className="text-xs text-text-muted font-mono">{repo.owner || repo.repo_url.split('/').slice(-2, -1)[0]}</p>
        </div>
        <div className="flex items-center gap-2">
          {isProcessing ? (
            <RefreshCw size={14} className="text-brand-primary animate-spin" />
          ) : (
            <div className={`w-2 h-2 rounded-full shadow-glow-sm ${STATUS_COLORS[repo.status]}`} />
          )}
          <span className={`text-xs font-medium uppercase tracking-wider ${STATUS_TEXT[repo.status] || 'text-brand-primary'}`}>
            {repo.status}
          </span>
        </div>
      </div>

      {isProcessing && (
        <div className="mb-4">
          <div className="flex justify-between text-xs mb-1.5">
            <span className="text-text-secondary">{repo.current_stage || 'Processing...'}</span>
            <span className="text-brand-primary font-mono">{repo.progress}%</span>
          </div>
          <div className="w-full bg-surface rounded-full h-1.5 overflow-hidden">
            <div 
              className="bg-brand-primary h-full transition-all duration-500 ease-out shadow-glow-sm"
              style={{ width: `${repo.progress}%` }}
            />
          </div>
        </div>
      )}

      {repo.metadata_ && repo.status === 'ready' && (
        <div className="grid grid-cols-2 gap-3 mb-4">
          <div className="glass rounded-lg p-2 flex items-center gap-2">
            <Terminal size={14} className="text-brand-accent" />
            <div className="flex flex-col">
              <span className="text-[10px] text-text-muted uppercase">Language</span>
              <span className="text-xs font-semibold text-text-primary">{repo.primary_language || 'Mixed'}</span>
            </div>
          </div>
          <div className="glass rounded-lg p-2 flex items-center gap-2">
            <Activity size={14} className="text-brand-secondary" />
            <div className="flex flex-col">
              <span className="text-[10px] text-text-muted uppercase">Files</span>
              <span className="text-xs font-semibold text-text-primary">{repo.metadata_.total_files}</span>
            </div>
          </div>
        </div>
      )}

      <div className="flex justify-between items-center mt-4 pt-4 border-t border-white/[0.06]">
        <div className="flex items-center gap-1.5 text-xs text-text-muted">
          <Clock size={12} />
          <span>{new Date(repo.created_at).toLocaleDateString()}</span>
        </div>
        <div className="flex items-center gap-1 text-xs font-medium text-brand-primary opacity-0 group-hover:opacity-100 transition-opacity transform translate-x-2 group-hover:translate-x-0 duration-300">
          <span>View Details</span>
          <ArrowRight size={14} />
        </div>
      </div>
    </motion.div>
  );
}
