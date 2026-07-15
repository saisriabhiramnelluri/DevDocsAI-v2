// DevDocsAI — Navbar Component
import { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import { Brain, GitBranch, Menu, X, Search, Sparkles } from 'lucide-react';
import { Link, useLocation } from 'react-router-dom';
import { useAppStore } from '../../store/appStore';
import { SearchModal } from '../search/SearchModal';

export function Navbar() {
  const { sidebarOpen, toggleSidebar } = useAppStore();
  const location = useLocation();
  const isHome = location.pathname === '/';
  const isRepoPage = location.pathname.startsWith('/repo/');
  const [searchOpen, setSearchOpen] = useState(false);

  // Cmd+K / Ctrl+K keyboard shortcut
  useEffect(() => {
    const handler = (e: KeyboardEvent) => {
      if ((e.metaKey || e.ctrlKey) && e.key === 'k') {
        e.preventDefault();
        if (isRepoPage) setSearchOpen((v) => !v);
      }
    };
    window.addEventListener('keydown', handler);
    return () => window.removeEventListener('keydown', handler);
  }, [isRepoPage]);

  return (
    <>
      <motion.header
        initial={{ y: -20, opacity: 0 }}
        animate={{ y: 0, opacity: 1 }}
        transition={{ duration: 0.4 }}
        className="fixed top-0 left-0 right-0 z-50 glass border-b border-white/[0.06]"
      >
        <div className="flex items-center justify-between px-4 py-3 max-w-screen-2xl mx-auto">
          {/* Left: Logo + sidebar toggle */}
          <div className="flex items-center gap-3">
            {!isHome && (
              <button
                onClick={toggleSidebar}
                className="p-2 rounded-lg text-text-secondary hover:text-text-primary hover:bg-surface transition-all"
              >
                {sidebarOpen ? <X size={18} /> : <Menu size={18} />}
              </button>
            )}
            <Link to="/" className="flex items-center gap-2.5 group">
              <div className="relative">
                <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-brand-primary to-brand-secondary flex items-center justify-center shadow-glow-sm group-hover:shadow-glow transition-all">
                  <Brain size={16} className="text-white" />
                </div>
                <div className="absolute inset-0 rounded-lg bg-gradient-to-br from-brand-primary to-brand-accent opacity-0 group-hover:opacity-30 blur-md transition-all" />
              </div>
              <div className="flex flex-col leading-none">
                <span className="font-display font-bold text-base text-white tracking-tight">
                  DevDocs<span className="gradient-text">AI</span>
                </span>
                <span className="text-[10px] text-text-muted font-mono tracking-widest uppercase">
                  Intelligence Platform
                </span>
              </div>
            </Link>
          </div>

          {/* Center: Search bar (only on repo pages) */}
          {isRepoPage && (
            <button
              onClick={() => setSearchOpen(true)}
              className="hidden md:flex items-center gap-2 px-4 py-2 glass rounded-xl border border-white/[0.08] text-text-muted hover:text-text-primary hover:border-brand-primary/30 transition-all text-sm w-64"
            >
              <Search size={15} />
              <span className="flex-1 text-left">Search codebase…</span>
              <kbd className="flex items-center gap-0.5 text-[10px] bg-surface px-1.5 py-0.5 rounded border border-white/[0.08]">
                ⌘K
              </kbd>
            </button>
          )}

          {/* Right: Actions */}
          <div className="flex items-center gap-2">
            {/* Mobile search for repo pages */}
            {isRepoPage && (
              <button
                onClick={() => setSearchOpen(true)}
                className="md:hidden p-2 rounded-lg text-text-secondary hover:text-text-primary hover:bg-surface transition-all"
              >
                <Search size={18} />
              </button>
            )}
            {/* Generators link — always visible */}
            <Link
              to="/generators"
              className="hidden sm:flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-sm text-text-secondary hover:text-text-primary hover:bg-surface transition-all"
            >
              <Sparkles size={14} className="text-brand-accent" />
              Generators
            </Link>
            {isHome && (
              <>
                <Link
                  to="/dashboard"
                  className="hidden sm:flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-sm text-text-secondary hover:text-text-primary hover:bg-surface transition-all"
                >
                  Dashboard
                </Link>
                <a
                  href="https://github.com"
                  target="_blank"
                  rel="noopener noreferrer"
                  className="p-2 rounded-lg text-text-secondary hover:text-text-primary hover:bg-surface transition-all"
                >
                  <GitBranch size={18} />
                </a>
              </>
            )}
            <Link
              to="/dashboard"
              className="btn-brand px-4 py-2 rounded-lg text-sm font-semibold"
            >
              Launch App
            </Link>
          </div>
        </div>
      </motion.header>

      {/* Search Modal */}
      <SearchModal isOpen={searchOpen} onClose={() => setSearchOpen(false)} />
    </>
  );
}
