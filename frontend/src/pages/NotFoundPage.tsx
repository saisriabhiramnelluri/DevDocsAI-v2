// DevDocsAI — 404 Not Found Page
import { motion } from 'framer-motion';
import { useNavigate } from 'react-router-dom';
import { Home, Sparkles, GitBranch, ArrowLeft } from 'lucide-react';

export function NotFoundPage() {
  const navigate = useNavigate();

  return (
    <div className="min-h-screen flex flex-col items-center justify-center px-4 text-center relative overflow-hidden">
      {/* Background glows */}
      <div className="absolute top-1/3 left-1/2 -translate-x-1/2 w-[600px] h-[300px] bg-brand-primary/8 rounded-full blur-[120px] pointer-events-none" />
      <div className="absolute top-1/2 left-1/3 w-[300px] h-[300px] bg-brand-accent/6 rounded-full blur-[100px] pointer-events-none" />

      <motion.div
        initial={{ opacity: 0, y: 24 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.5 }}
        className="relative z-10 max-w-lg"
      >
        {/* Glitchy 404 */}
        <div className="relative mb-8">
          <div className="text-[9rem] font-display font-black leading-none select-none">
            <span className="gradient-text">4</span>
            <span className="text-white/10">0</span>
            <span className="gradient-text">4</span>
          </div>
          <motion.div
            animate={{ opacity: [0, 1, 0] }}
            transition={{ duration: 2, repeat: Infinity, repeatDelay: 3 }}
            className="absolute inset-0 text-[9rem] font-display font-black leading-none text-brand-primary/20 blur-sm select-none"
            style={{ transform: 'translate(3px, -2px)' }}
          >
            404
          </motion.div>
        </div>

        <h1 className="text-2xl font-display font-bold text-text-primary mb-3">
          Page not found
        </h1>
        <p className="text-text-secondary text-sm mb-8 leading-relaxed">
          The page you're looking for doesn't exist or was moved.
          Let's get you back on track.
        </p>

        {/* Quick nav */}
        <div className="flex flex-col sm:flex-row gap-3 justify-center">
          <button
            onClick={() => navigate(-1)}
            className="flex items-center gap-2 px-5 py-2.5 glass rounded-xl border border-white/[0.08] hover:border-white/20 text-sm transition-all"
          >
            <ArrowLeft size={15} />
            Go Back
          </button>
          <button
            onClick={() => navigate('/')}
            className="flex items-center gap-2 px-5 py-2.5 glass rounded-xl border border-white/[0.08] hover:border-brand-primary/30 text-sm transition-all"
          >
            <Home size={15} />
            Home
          </button>
          <button
            onClick={() => navigate('/dashboard')}
            className="flex items-center gap-2 px-5 py-2.5 bg-brand-primary hover:bg-brand-primary/90 rounded-xl text-sm font-semibold text-white transition-all shadow-glow"
          >
            <GitBranch size={15} />
            Dashboard
          </button>
        </div>

        {/* Generator shortcut */}
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 0.5 }}
          className="mt-8"
        >
          <button
            onClick={() => navigate('/generators')}
            className="inline-flex items-center gap-2 text-xs text-text-muted hover:text-brand-accent transition-colors"
          >
            <Sparkles size={12} className="text-brand-accent" />
            Try AI Generators instead
          </button>
        </motion.div>
      </motion.div>
    </div>
  );
}
