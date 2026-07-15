// DevDocsAI — Repository Input Component
import { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { GitBranch, Loader2, Sparkles, ArrowRight, AlertCircle } from 'lucide-react';
import { repositoryService } from '../../services/repositoryService';
import { useAppStore } from '../../store/appStore';
import { useNavigate } from 'react-router-dom';
import toast from 'react-hot-toast';

const EXAMPLE_REPOS = [
  'https://github.com/fastapi/fastapi',
  'https://github.com/tiangolo/full-stack-fastapi-template',
  'https://github.com/langchain-ai/langchain',
  'https://github.com/pallets/flask',
];

export function RepositoryInput() {
  const [url, setUrl] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const { addRepository } = useAppStore();
  const navigate = useNavigate();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!url.trim()) return;
    setError('');
    setLoading(true);

    try {
      const result = await repositoryService.analyze(url.trim());

      // Add a placeholder repo to the store
      addRepository({
        id: result.repo_id,
        repo_url: url.trim(),
        repo_name: url.trim().split('/').pop() || 'Repository',
        owner: url.trim().split('/').slice(-2)[0] || '',
        status: 'pending',
        progress: 0,
        created_at: new Date().toISOString(),
      });

      toast.success('Repository submitted for analysis!');
      navigate(`/repo/${result.repo_id}`);
    } catch (err: any) {
      setError(err.message || 'Failed to analyze repository');
      setLoading(false);
    }
  };

  const handleExample = (repo: string) => {
    setUrl(repo);
    setError('');
  };

  return (
    <div className="w-full max-w-2xl">
      {/* Input Form */}
      <form onSubmit={handleSubmit} className="relative group">
        <div className={`relative flex items-center rounded-2xl overflow-hidden transition-all duration-300 ${
          error ? 'border-glow-cyan' : 'border-glow'
        } glass-strong`}>
          <div className="flex items-center gap-2 pl-4 pr-2 flex-shrink-0">
            <GitBranch size={18} className="text-text-muted" />
          </div>
          <input
            type="url"
            value={url}
            onChange={(e) => { setUrl(e.target.value); setError(''); }}
            placeholder="https://github.com/owner/repository"
            className="flex-1 bg-transparent text-text-primary placeholder-text-muted py-4 pr-2 outline-none text-sm font-mono"
            disabled={loading}
            autoFocus
          />
          <motion.button
            type="submit"
            disabled={loading || !url.trim()}
            whileHover={{ scale: 1.02 }}
            whileTap={{ scale: 0.98 }}
            className="m-1.5 btn-brand flex items-center gap-2 px-5 py-3 rounded-xl text-sm font-semibold disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {loading ? (
              <>
                <Loader2 size={16} className="animate-spin" />
                <span>Analyzing...</span>
              </>
            ) : (
              <>
                <Sparkles size={16} />
                <span>Analyze</span>
                <ArrowRight size={14} />
              </>
            )}
          </motion.button>
        </div>

        {/* Glow on focus */}
        <div className="absolute inset-0 rounded-2xl opacity-0 group-focus-within:opacity-100 transition-opacity bg-glow-indigo pointer-events-none" />
      </form>

      {/* Error Message */}
      <AnimatePresence>
        {error && (
          <motion.div
            initial={{ opacity: 0, y: -8 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -8 }}
            className="mt-3 flex items-start gap-2 px-4 py-3 rounded-xl glass border border-red-500/30"
          >
            <AlertCircle size={16} className="text-red-400 mt-0.5 flex-shrink-0" />
            <p className="text-sm text-red-300">{error}</p>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Example Repos */}
      <div className="mt-4">
        <p className="text-xs text-text-muted mb-2 text-center">Try an example:</p>
        <div className="flex flex-wrap gap-2 justify-center">
          {EXAMPLE_REPOS.map((repo) => (
            <button
              key={repo}
              onClick={() => handleExample(repo)}
              className="text-xs px-3 py-1.5 rounded-lg glass border border-white/[0.08] text-text-secondary hover:text-text-primary hover:border-brand-primary/40 transition-all font-mono"
            >
              {repo.split('/').slice(-2).join('/')}
            </button>
          ))}
        </div>
      </div>
    </div>
  );
}
