// DevDocsAI — Sidebar Component
import { motion, AnimatePresence } from 'framer-motion';
import {
  Archive,
  BookOpen,
  Brain,
  GitBranch,
  MessageSquare,
  Network,
  Plus,
  Trash2,
  Loader2,
} from 'lucide-react';
import { Link, useNavigate, useParams } from 'react-router-dom';
import { useAppStore } from '../../store/appStore';
import { repositoryService } from '../../services/repositoryService';
import type { Repository } from '../../types/repository';
import toast from 'react-hot-toast';

const STATUS_COLORS: Record<string, string> = {
  pending: 'text-yellow-400',
  cloning: 'text-brand-primary',
  parsing: 'text-brand-primary',
  embedding: 'text-brand-primary',
  graph: 'text-brand-primary',
  summarizing: 'text-brand-primary',
  ready: 'text-green-400',
  failed: 'text-red-400',
};

const STATUS_DOTS: Record<string, string> = {
  pending: 'bg-yellow-400',
  ready: 'bg-green-400',
  failed: 'bg-red-400',
};

function RepoItem({ repo }: { repo: Repository }) {
  const navigate = useNavigate();
  const { repoId } = useParams();
  const { removeRepository } = useAppStore();
  const isActive = repoId === repo.id;
  const isProcessing = !['ready', 'failed', 'pending'].includes(repo.status);

  const handleDelete = async (e: React.MouseEvent) => {
    e.preventDefault();
    e.stopPropagation();
    try {
      await repositoryService.delete(repo.id);
      removeRepository(repo.id);
      if (isActive) navigate('/dashboard');
      toast.success('Repository removed');
    } catch {
      toast.error('Failed to delete repository');
    }
  };

  return (
    <Link to={`/repo/${repo.id}`}>
      <motion.div
        layout
        className={`group flex items-center gap-2.5 px-3 py-2.5 rounded-lg cursor-pointer transition-all ${
          isActive
            ? 'glass-brand border border-brand-primary/30'
            : 'hover:bg-surface'
        }`}
      >
        <div className="relative flex-shrink-0">
          {isProcessing ? (
            <Loader2 size={14} className="text-brand-primary animate-spin" />
          ) : (
            <div
              className={`w-2 h-2 rounded-full ${
                STATUS_DOTS[repo.status] || 'bg-gray-500'
              }`}
            />
          )}
        </div>
        <div className="flex-1 min-w-0">
          <p className={`text-sm font-medium truncate ${isActive ? 'text-white' : 'text-text-primary'}`}>
            {repo.repo_name || repo.repo_url.split('/').slice(-2).join('/')}
          </p>
          <p className={`text-xs truncate ${STATUS_COLORS[repo.status] || 'text-text-muted'}`}>
            {isProcessing ? repo.current_stage || repo.status : repo.primary_language || repo.status}
          </p>
        </div>
        <button
          onClick={handleDelete}
          className="opacity-0 group-hover:opacity-100 p-1 rounded text-text-muted hover:text-red-400 transition-all"
        >
          <Trash2 size={12} />
        </button>
      </motion.div>
    </Link>
  );
}

export function Sidebar() {
  const { repositories, sidebarOpen } = useAppStore();
  const navigate = useNavigate();

  const navItems = [
    { icon: Archive, label: 'Repositories', path: '/dashboard' },
    { icon: MessageSquare, label: 'Chat', path: '/dashboard' },
    { icon: Network, label: 'Architecture', path: '/dashboard' },
    { icon: BookOpen, label: 'Documentation', path: '/dashboard' },
  ];

  return (
    <AnimatePresence>
      {sidebarOpen && (
        <motion.aside
          initial={{ x: -280, opacity: 0 }}
          animate={{ x: 0, opacity: 1 }}
          exit={{ x: -280, opacity: 0 }}
          transition={{ type: 'spring', stiffness: 300, damping: 30 }}
          className="sidebar fixed left-0 top-14 bottom-0 z-40 flex flex-col overflow-hidden"
        >
          {/* Add Repo Button */}
          <div className="p-4 border-b border-white/[0.06]">
            <button
              onClick={() => navigate('/dashboard')}
              className="btn-brand w-full flex items-center justify-center gap-2 px-4 py-2.5 rounded-lg text-sm font-semibold"
            >
              <Plus size={16} />
              Analyze Repository
            </button>
          </div>

          {/* Navigation */}
          <nav className="p-3 border-b border-white/[0.06]">
            {navItems.map(({ icon: Icon, label, path }) => (
              <Link key={label} to={path}>
                <div className="flex items-center gap-2.5 px-3 py-2 rounded-lg text-sm text-text-secondary hover:text-text-primary hover:bg-surface transition-all cursor-pointer">
                  <Icon size={15} />
                  <span>{label}</span>
                </div>
              </Link>
            ))}
          </nav>

          {/* Repositories List */}
          <div className="flex-1 overflow-y-auto p-3">
            <div className="flex items-center gap-1.5 px-2 mb-2">
              <GitBranch size={12} className="text-text-muted" />
              <span className="text-xs font-semibold text-text-muted uppercase tracking-wider">
                Recent Repos
              </span>
            </div>
            {repositories.length === 0 ? (
              <div className="px-3 py-6 text-center">
                <Brain size={24} className="text-text-muted mx-auto mb-2" />
                <p className="text-xs text-text-muted">No repositories yet</p>
              </div>
            ) : (
              <div className="space-y-1">
                {repositories.map((repo) => (
                  <RepoItem key={repo.id} repo={repo} />
                ))}
              </div>
            )}
          </div>

          {/* Bottom Info */}
          <div className="p-4 border-t border-white/[0.06]">
            <div className="glass rounded-lg px-3 py-2">
              <p className="text-xs text-text-muted">
                <span className="gradient-text font-semibold">DevDocsAI</span> v1.0 · Phase 1
              </p>
            </div>
          </div>
        </motion.aside>
      )}
    </AnimatePresence>
  );
}
