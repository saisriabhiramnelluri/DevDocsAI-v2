// DevDocsAI — Generator Workspace Layout
// Reusable 2-pane (input / output) shell for all generators
import { ReactNode, useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Copy, Check, Download, Loader2, ChevronLeft } from 'lucide-react';
import { useNavigate } from 'react-router-dom';
import toast from 'react-hot-toast';

interface Props {
  title: string;
  description: string;
  icon: ReactNode;
  accentColor: string;
  inputPanel: ReactNode;
  outputContent: string | null;
  outputLanguage?: string;
  loading: boolean;
  onGenerate: () => void;
  generateLabel?: string;
  extraOutput?: ReactNode;
  customOutput?: ReactNode;    // Optional: replaces the raw <pre> block
}

export function GeneratorWorkspace({
  title,
  description,
  icon,
  accentColor,
  inputPanel,
  outputContent,
  outputLanguage = 'text',
  loading,
  onGenerate,
  generateLabel = 'Generate',
  extraOutput,
  customOutput,
}: Props) {
  const navigate = useNavigate();
  const [copied, setCopied] = useState(false);

  const handleCopy = () => {
    if (!outputContent) return;
    navigator.clipboard.writeText(outputContent);
    setCopied(true);
    toast.success('Copied to clipboard');
    setTimeout(() => setCopied(false), 2000);
  };

  const handleDownload = () => {
    if (!outputContent) return;
    const ext = outputLanguage === 'markdown' ? 'md' : outputLanguage === 'mermaid' ? 'mmd' : 'txt';
    const blob = new Blob([outputContent], { type: 'text/plain' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `devdocsai-output.${ext}`;
    a.click();
    URL.revokeObjectURL(url);
  };

  return (
    <div className="min-h-screen bg-background text-text-primary">
      {/* Header */}
      <div className="sticky top-16 z-20 glass border-b border-white/[0.06] px-6 py-4">
        <div className="max-w-[1600px] mx-auto flex items-center gap-4">
          <button
            onClick={() => navigate('/generators')}
            className="flex items-center gap-1.5 text-sm text-text-muted hover:text-text-primary transition-colors"
          >
            <ChevronLeft size={16} />
            Generators
          </button>
          <div className="h-4 w-px bg-white/10" />
          <div className={`flex items-center gap-2 ${accentColor}`}>{icon}</div>
          <div>
            <h1 className="text-base font-bold leading-none">{title}</h1>
            <p className="text-xs text-text-muted mt-0.5">{description}</p>
          </div>

          <div className="ml-auto flex items-center gap-2">
            {outputContent && (
              <>
                <button
                  onClick={handleCopy}
                  className="flex items-center gap-1.5 text-xs px-3 py-1.5 rounded-lg glass border border-white/[0.08] hover:border-white/20 transition-all"
                >
                  {copied ? <Check size={13} className="text-green-400" /> : <Copy size={13} />}
                  {copied ? 'Copied' : 'Copy'}
                </button>
                <button
                  onClick={handleDownload}
                  className="flex items-center gap-1.5 text-xs px-3 py-1.5 rounded-lg glass border border-white/[0.08] hover:border-white/20 transition-all"
                >
                  <Download size={13} />
                  Download
                </button>
              </>
            )}
            <button
              onClick={onGenerate}
              disabled={loading}
              className={`flex items-center gap-2 px-4 py-2 rounded-xl text-sm font-semibold transition-all ${
                loading
                  ? 'opacity-60 cursor-not-allowed bg-brand-primary/40 text-white'
                  : 'bg-brand-primary hover:bg-brand-primary/90 text-white shadow-glow'
              }`}
            >
              {loading ? <Loader2 size={15} className="animate-spin" /> : null}
              {loading ? 'Generating…' : generateLabel}
            </button>
          </div>
        </div>
      </div>

      {/* 2-Pane Layout */}
      <div className="max-w-[1600px] mx-auto flex flex-col lg:flex-row gap-0 h-[calc(100vh-128px)]">
        {/* LEFT — Input */}
        <div className="w-full lg:w-[45%] border-r border-white/[0.06] overflow-y-auto">
          <div className="p-5 space-y-4">
            <h2 className="text-xs font-bold uppercase tracking-widest text-text-muted">Input</h2>
            {inputPanel}
          </div>
        </div>

        {/* RIGHT — Output */}
        <div className="flex-1 overflow-y-auto bg-[#030509]">
          <AnimatePresence mode="wait">
            {loading ? (
              <motion.div
                key="loading"
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                exit={{ opacity: 0 }}
                className="h-full flex flex-col items-center justify-center gap-4 text-brand-primary"
              >
                <div className="relative">
                  <div className="w-16 h-16 rounded-full border-2 border-brand-primary/20 animate-ping absolute inset-0" />
                  <div className="w-16 h-16 rounded-full border-2 border-brand-primary flex items-center justify-center">
                    <Loader2 size={24} className="animate-spin" />
                  </div>
                </div>
                <p className="text-sm text-text-muted">AI is working…</p>
              </motion.div>
            ) : customOutput ? (
              <motion.div
                key="custom-output"
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0 }}
                className="p-5 flex flex-col h-full"
              >
                <h2 className="text-xs font-bold uppercase tracking-widest text-text-muted mb-4">Output</h2>
                {extraOutput}
                {customOutput}
              </motion.div>
            ) : outputContent ? (
              <motion.div
                key="output"
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0 }}
                className="p-5"
              >
                <h2 className="text-xs font-bold uppercase tracking-widest text-text-muted mb-4">Output</h2>
                {extraOutput}
                <pre className="glass rounded-2xl p-5 text-sm font-mono text-text-secondary leading-relaxed overflow-x-auto border border-white/[0.06] whitespace-pre-wrap break-words">
                  {outputContent}
                </pre>
              </motion.div>
            ) : (
              <motion.div
                key="empty"
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                className="h-full flex flex-col items-center justify-center gap-3 text-center px-8"
              >
                <div className={`text-4xl opacity-20 ${accentColor}`}>{icon}</div>
                <p className="text-text-muted text-sm">
                  Configure the options on the left and click <strong className="text-text-secondary">Generate</strong>
                </p>
              </motion.div>
            )}
          </AnimatePresence>
        </div>
      </div>
    </div>
  );
}
