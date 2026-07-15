import { useState, useEffect, useRef } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Search, FileCode2, Brackets, Box, Loader2, ArrowRight, Keyboard } from 'lucide-react';
import { searchService, type SearchResult } from '../../services/searchService';
import { useAppStore } from '../../store/appStore';
import { useParams } from 'react-router-dom';

const TYPE_ICONS: Record<string, React.ElementType> = {
  function: Brackets,
  class: Box,
  file: FileCode2,
};

const TYPE_COLORS: Record<string, string> = {
  function: 'text-brand-accent',
  class: 'text-brand-secondary',
  file: 'text-brand-primary',
  repo: 'text-green-400',
};

export function SearchModal({
  isOpen,
  onClose,
}: {
  isOpen: boolean;
  onClose: () => void;
}) {
  const [query, setQuery] = useState('');
  const [results, setResults] = useState<SearchResult[]>([]);
  const [loading, setLoading] = useState(false);
  const [selectedIdx, setSelectedIdx] = useState(0);
  const inputRef = useRef<HTMLInputElement>(null);
  const { repoId } = useParams();
  const { repositories } = useAppStore();

  // Focus input on open
  useEffect(() => {
    if (isOpen) {
      setTimeout(() => inputRef.current?.focus(), 50);
      setQuery('');
      setResults([]);
      setSelectedIdx(0);
    }
  }, [isOpen]);

  // Debounced search
  useEffect(() => {
    if (!query.trim() || !repoId) {
      setResults([]);
      return;
    }
    const timeout = setTimeout(async () => {
      setLoading(true);
      try {
        const res = await searchService.query(repoId, query, 12);
        setResults(res.results);
        setSelectedIdx(0);
      } catch {
        setResults([]);
      } finally {
        setLoading(false);
      }
    }, 350);
    return () => clearTimeout(timeout);
  }, [query, repoId]);

  // Keyboard navigation
  useEffect(() => {
    const handler = (e: KeyboardEvent) => {
      if (!isOpen) return;
      if (e.key === 'Escape') onClose();
      if (e.key === 'ArrowDown') setSelectedIdx((i) => Math.min(i + 1, results.length - 1));
      if (e.key === 'ArrowUp') setSelectedIdx((i) => Math.max(i - 1, 0));
      if (e.key === 'Enter' && results[selectedIdx]) {
        // Navigate to repo page if not already there
        if (results[selectedIdx].file) {
          onClose();
        }
      }
    };
    window.addEventListener('keydown', handler);
    return () => window.removeEventListener('keydown', handler);
  }, [isOpen, results, selectedIdx, onClose]);

  const groupedResults = results.reduce<Record<string, SearchResult[]>>((acc, r) => {
    const key = r.type || 'other';
    acc[key] = [...(acc[key] || []), r];
    return acc;
  }, {});

  const activeRepo = repositories.find((r) => r.id === repoId);

  if (!isOpen) return null;

  return (
    <AnimatePresence>
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        exit={{ opacity: 0 }}
        className="fixed inset-0 z-50 flex items-start justify-center pt-24 px-4"
        onClick={onClose}
      >
        {/* Backdrop */}
        <div className="absolute inset-0 bg-black/70 backdrop-blur-sm" />

        <motion.div
          initial={{ opacity: 0, scale: 0.95, y: -20 }}
          animate={{ opacity: 1, scale: 1, y: 0 }}
          exit={{ opacity: 0, scale: 0.95, y: -20 }}
          transition={{ type: 'spring', stiffness: 400, damping: 30 }}
          className="relative w-full max-w-2xl glass-strong rounded-2xl border-glow shadow-card overflow-hidden"
          onClick={(e) => e.stopPropagation()}
        >
          {/* Search input */}
          <div className="flex items-center gap-3 px-4 py-4 border-b border-white/[0.08]">
            {loading ? (
              <Loader2 size={20} className="text-brand-primary animate-spin flex-shrink-0" />
            ) : (
              <Search size={20} className="text-text-muted flex-shrink-0" />
            )}
            <input
              ref={inputRef}
              type="text"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              placeholder={activeRepo ? `Search in ${activeRepo.repo_name || 'repository'}…` : 'Search codebase…'}
              className="flex-1 bg-transparent text-white placeholder-text-muted outline-none text-base"
            />
            <div className="flex items-center gap-1.5 text-text-muted">
              <kbd className="px-1.5 py-0.5 rounded text-xs bg-surface border border-white/[0.08]">ESC</kbd>
            </div>
          </div>

          {/* Results */}
          <div className="max-h-[60vh] overflow-y-auto">
            {!query.trim() ? (
              <div className="py-8 text-center text-text-muted">
                <Keyboard size={32} className="mx-auto mb-3 opacity-30" />
                <p className="text-sm">Start typing to search functions, classes, and files</p>
                <p className="text-xs mt-1 opacity-60">Uses semantic + keyword hybrid search</p>
              </div>
            ) : results.length === 0 && !loading ? (
              <div className="py-8 text-center text-text-muted text-sm">
                No results for <span className="text-white font-mono">"{query}"</span>
              </div>
            ) : (
              <div className="p-2">
                {Object.entries(groupedResults).map(([type, items]) => (
                  <div key={type} className="mb-4">
                    <div className="px-3 py-1.5 flex items-center gap-2">
                      {(() => {
                        const Icon = TYPE_ICONS[type] || FileCode2;
                        return <Icon size={13} className={TYPE_COLORS[type] || 'text-text-muted'} />;
                      })()}
                      <span className="text-[11px] font-bold text-text-muted uppercase tracking-widest">
                        {type}s
                      </span>
                      <span className="text-[10px] text-text-muted bg-surface px-1.5 py-0.5 rounded-full">{items.length}</span>
                    </div>

                    {items.map((result) => {
                      const globalIdx = results.indexOf(result);
                      const isSelected = globalIdx === selectedIdx;
                      const Icon = TYPE_ICONS[result.type] || FileCode2;
                      return (
                        <div
                          key={result.chunk_id}
                          className={`group rounded-xl px-3 py-3 cursor-pointer transition-all ${
                            isSelected ? 'bg-brand-primary/15 border border-brand-primary/20' : 'hover:bg-surface'
                          }`}
                          onMouseEnter={() => setSelectedIdx(globalIdx)}
                          onClick={onClose}
                        >
                          <div className="flex items-start gap-3">
                            <Icon size={16} className={`flex-shrink-0 mt-0.5 ${TYPE_COLORS[result.type] || 'text-text-muted'}`} />
                            <div className="flex-1 min-w-0">
                              <div className="flex items-center gap-2 mb-1">
                                {result.name && (
                                  <span className="text-sm font-semibold text-white font-mono">
                                    {result.name}
                                  </span>
                                )}
                                <span className="text-xs text-text-muted font-mono truncate">
                                  {result.file}
                                  {result.line_start ? `:${result.line_start}` : ''}
                                </span>
                              </div>
                              {result.content && (
                                <p className="text-xs text-text-secondary font-mono line-clamp-2 leading-relaxed bg-black/20 rounded p-2 mt-1">
                                  {result.content.trim()}
                                </p>
                              )}
                            </div>
                            {isSelected && <ArrowRight size={14} className="text-brand-primary flex-shrink-0 mt-1" />}
                          </div>
                        </div>
                      );
                    })}
                  </div>
                ))}
              </div>
            )}
          </div>

          {/* Footer */}
          {results.length > 0 && (
            <div className="px-4 py-2 border-t border-white/[0.06] flex items-center gap-4 text-[11px] text-text-muted">
              <span className="flex items-center gap-1"><kbd className="px-1 py-0.5 rounded bg-surface border border-white/[0.08]">↑↓</kbd> navigate</span>
              <span className="flex items-center gap-1"><kbd className="px-1 py-0.5 rounded bg-surface border border-white/[0.08]">↵</kbd> select</span>
              <span className="ml-auto">{results.length} results</span>
            </div>
          )}
        </motion.div>
      </motion.div>
    </AnimatePresence>
  );
}
