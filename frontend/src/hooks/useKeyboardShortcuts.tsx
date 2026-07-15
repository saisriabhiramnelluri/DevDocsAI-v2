// DevDocsAI — Global Keyboard Shortcuts Hook
// Registers app-wide hotkeys and shows a help overlay
import { useEffect, useState, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import { motion, AnimatePresence } from 'framer-motion';
import { Command } from 'lucide-react';

interface Shortcut {
  keys: string;
  description: string;
  action: () => void;
}

function Key({ children }: { children: string }) {
  return (
    <kbd className="inline-flex items-center px-1.5 py-0.5 text-[10px] font-mono font-semibold bg-surface border border-white/[0.12] rounded text-text-secondary">
      {children}
    </kbd>
  );
}

function ShortcutRow({ keys, description }: { keys: string[]; description: string }) {
  return (
    <div className="flex items-center justify-between py-2 border-b border-white/[0.04] last:border-0">
      <span className="text-xs text-text-secondary">{description}</span>
      <div className="flex items-center gap-1">
        {keys.map((k, i) => (
          <span key={i} className="flex items-center gap-1">
            {i > 0 && <span className="text-[10px] text-text-muted">+</span>}
            <Key>{k}</Key>
          </span>
        ))}
      </div>
    </div>
  );
}

const SHORTCUTS_DATA = [
  { keys: ['G', 'H'], description: 'Go to Home' },
  { keys: ['G', 'D'], description: 'Go to Dashboard' },
  { keys: ['G', 'G'], description: 'Go to Generators Hub' },
  { keys: ['?'], description: 'Show keyboard shortcuts' },
  { keys: ['Esc'], description: 'Close overlay / modal' },
];

export function useGlobalKeyboardShortcuts() {
  const navigate = useNavigate();
  const [showHelp, setShowHelp] = useState(false);
  const [buffer, setBuffer] = useState('');

  const handleKey = useCallback(
    (e: KeyboardEvent) => {
      // Skip if user is typing in an input / textarea / contenteditable
      const target = e.target as HTMLElement;
      if (['INPUT', 'TEXTAREA', 'SELECT'].includes(target.tagName)) return;
      if (target.isContentEditable) return;

      const key = e.key.toUpperCase();

      // Esc — close help
      if (e.key === 'Escape') {
        setShowHelp(false);
        setBuffer('');
        return;
      }

      // ? — toggle help
      if (e.key === '?') {
        setShowHelp((v) => !v);
        setBuffer('');
        return;
      }

      // Two-key sequence shortcuts (G + X)
      const next = buffer + key;
      setBuffer(next);

      if (next === 'GH') { navigate('/');           setBuffer(''); return; }
      if (next === 'GD') { navigate('/dashboard');   setBuffer(''); return; }
      if (next === 'GG') { navigate('/generators');  setBuffer(''); return; }

      // Clear buffer after 1.5s inactivity
      if (next.length > 2) setBuffer('');
    },
    [buffer, navigate],
  );

  useEffect(() => {
    window.addEventListener('keydown', handleKey);
    return () => window.removeEventListener('keydown', handleKey);
  }, [handleKey]);

  // Auto-clear buffer after 1.5s
  useEffect(() => {
    if (!buffer) return;
    const t = setTimeout(() => setBuffer(''), 1500);
    return () => clearTimeout(t);
  }, [buffer]);

  return { showHelp, setShowHelp };
}

// ── Shortcut Help Overlay ──────────────────────────────────────────────────
export function KeyboardShortcutsOverlay() {
  const { showHelp, setShowHelp } = useGlobalKeyboardShortcuts();

  return (
    <AnimatePresence>
      {showHelp && (
        <>
          {/* Backdrop */}
          <motion.div
            key="backdrop"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            onClick={() => setShowHelp(false)}
            className="fixed inset-0 z-[100] bg-black/60 backdrop-blur-sm"
          />
          {/* Modal */}
          <motion.div
            key="modal"
            initial={{ opacity: 0, scale: 0.95, y: 12 }}
            animate={{ opacity: 1, scale: 1, y: 0 }}
            exit={{ opacity: 0, scale: 0.95, y: 12 }}
            transition={{ duration: 0.2 }}
            className="fixed z-[101] top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-full max-w-sm"
          >
            <div className="glass-strong rounded-2xl border border-white/[0.1] shadow-2xl overflow-hidden">
              <div className="flex items-center gap-2 px-5 py-4 border-b border-white/[0.06]">
                <Command size={15} className="text-brand-primary" />
                <span className="text-sm font-semibold text-text-primary">Keyboard Shortcuts</span>
                <button
                  onClick={() => setShowHelp(false)}
                  className="ml-auto text-text-muted hover:text-text-primary text-xs"
                >
                  Esc
                </button>
              </div>
              <div className="px-5 py-3">
                <p className="text-[10px] text-text-muted uppercase tracking-widest font-bold mb-2">Navigation</p>
                {SHORTCUTS_DATA.map((s, i) => (
                  <ShortcutRow key={i} keys={s.keys} description={s.description} />
                ))}
              </div>
              <div className="px-5 py-3 border-t border-white/[0.04]">
                <p className="text-[10px] text-text-muted text-center">
                  Press <Key>?</Key> anywhere to toggle this overlay
                </p>
              </div>
            </div>
          </motion.div>
        </>
      )}
    </AnimatePresence>
  );
}
