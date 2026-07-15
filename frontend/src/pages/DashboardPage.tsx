import { useEffect, useState } from 'react';
import { RepositoryInput } from '../components/repository/RepositoryInput';
import { RepositoryCard } from '../components/repository/RepositoryCard';
import { DashboardSkeleton } from '../components/ui/SkeletonLoader';
import { useAppStore } from '../store/appStore';
import { repositoryService } from '../services/repositoryService';
import { motion } from 'framer-motion';
import { GitBranch, Sparkles, ChevronRight } from 'lucide-react';
import { useNavigate } from 'react-router-dom';
import toast from 'react-hot-toast';

// Quick-start example repos — clickable suggestions
const EXAMPLE_REPOS = [
  { label: 'fastapi/fastapi', url: 'https://github.com/fastapi/fastapi', lang: 'Python' },
  { label: 'vercel/next.js', url: 'https://github.com/vercel/next.js', lang: 'TypeScript' },
  { label: 'pallets/flask', url: 'https://github.com/pallets/flask', lang: 'Python' },
];

export function DashboardPage() {
  const { repositories, setRepositories } = useAppStore();
  const [loading, setLoading] = useState(true);
  const navigate = useNavigate();

  useEffect(() => {
    let mounted = true;
    const fetchRepos = async () => {
      try {
        const data = await repositoryService.list();
        if (mounted) setRepositories(data.repositories);
      } catch (err) {
        if (mounted) toast.error('Failed to load repositories');
      } finally {
        if (mounted) setLoading(false);
      }
    };
    fetchRepos();
    return () => { mounted = false; };
  }, [setRepositories]);

  return (
    <div className="min-h-screen pt-24 pb-16 px-4 md:px-8">
      <div className="max-w-7xl mx-auto">

        {/* ── Header ─────────────────────────────────────────────────── */}
        <div className="mb-14 flex flex-col items-center text-center">
          <motion.div
            initial={{ opacity: 0, y: 16 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5 }}
          >
            <div className="inline-flex items-center gap-2 px-3 py-1.5 rounded-full glass-strong border border-brand-primary/30 mb-6">
              <Sparkles size={13} className="text-brand-primary" />
              <span className="text-xs font-medium text-text-primary">AI Repository Intelligence</span>
            </div>
            <h1 className="text-4xl md:text-5xl font-display font-bold mb-4">
              Repository <span className="gradient-text">Dashboard</span>
            </h1>
            <p className="text-text-secondary max-w-xl mx-auto mb-8">
              Paste any public GitHub URL below. We'll build a complete semantic knowledge base
              so you can chat, explore, and generate documentation instantly.
            </p>
            <div className="w-full max-w-xl mx-auto">
              <RepositoryInput />
            </div>
          </motion.div>
        </div>

        <div className="w-full h-px bg-gradient-to-r from-transparent via-white/[0.08] to-transparent mb-10" />

        {/* ── Repository Grid ────────────────────────────────────────── */}
        <div>
          <div className="flex items-center justify-between mb-6">
            <h2 className="text-sm font-bold uppercase tracking-widest text-text-muted flex items-center gap-2">
              <GitBranch size={16} className="text-brand-accent" />
              Your Repositories
            </h2>
            <span className="text-xs font-mono text-text-muted glass px-2.5 py-1 rounded-lg border border-white/[0.06]">
              {repositories.length} {repositories.length === 1 ? 'repo' : 'repos'}
            </span>
          </div>

          {loading ? (
            <DashboardSkeleton count={6} />
          ) : repositories.length === 0 ? (
            <EmptyState />
          ) : (
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5"
            >
              {repositories.map((repo, i) => (
                <motion.div
                  key={repo.id}
                  initial={{ opacity: 0, y: 16 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: i * 0.06 }}
                >
                  <RepositoryCard
                    repo={repo}
                    onClick={() => navigate(`/repo/${repo.id}`)}
                  />
                </motion.div>
              ))}
            </motion.div>
          )}
        </div>
      </div>
    </div>
  );
}

function EmptyState() {
  return (
    <motion.div
      initial={{ opacity: 0, scale: 0.97 }}
      animate={{ opacity: 1, scale: 1 }}
      transition={{ duration: 0.4 }}
      className="glass-strong rounded-3xl border border-white/[0.06] p-12 text-center"
    >
      <div className="w-16 h-16 rounded-2xl glass-brand border border-brand-primary/20 flex items-center justify-center mx-auto mb-5">
        <GitBranch size={28} className="text-brand-primary" />
      </div>
      <h3 className="text-xl font-semibold text-text-primary mb-2">No repositories yet</h3>
      <p className="text-sm text-text-secondary max-w-sm mx-auto mb-8">
        Analyze a GitHub repository above to get started. Try one of these popular repos:
      </p>
      <div className="flex flex-col sm:flex-row gap-3 justify-center">
        {EXAMPLE_REPOS.map((r) => (
          <a
            key={r.label}
            href={`?url=${encodeURIComponent(r.url)}`}
            onClick={(e) => {
              e.preventDefault();
              // Pre-fill the input — dispatch custom event
              window.dispatchEvent(new CustomEvent('prefill-url', { detail: r.url }));
              window.scrollTo({ top: 0, behavior: 'smooth' });
            }}
            className="flex items-center gap-2 px-4 py-2.5 glass rounded-xl border border-white/[0.08] hover:border-brand-primary/30 transition-all text-sm group"
          >
            <GitBranch size={14} className="text-brand-primary" />
            <span className="font-mono text-text-secondary group-hover:text-text-primary transition-colors">{r.label}</span>
            <span className="text-xs text-text-muted ml-auto">{r.lang}</span>
            <ChevronRight size={13} className="text-text-muted group-hover:text-brand-primary transition-colors" />
          </a>
        ))}
      </div>
    </motion.div>
  );
}

