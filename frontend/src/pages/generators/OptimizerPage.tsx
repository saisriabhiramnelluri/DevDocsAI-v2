// DevDocsAI — Code Optimizer / Refactor AI Page
import { useState } from 'react';
import { Zap, TrendingUp, ShieldAlert, Eye } from 'lucide-react';
import toast from 'react-hot-toast';
import { motion } from 'framer-motion';
import { GeneratorWorkspace } from '../../components/generators/GeneratorWorkspace';
import { CodeEditor, GenSelect } from '../../components/generators/GeneratorControls';
import { generatorService } from '../../services/generatorService';

const LANGUAGE_OPTIONS = [
  { value: 'python', label: 'Python' },
  { value: 'typescript', label: 'TypeScript' },
  { value: 'javascript', label: 'JavaScript' },
  { value: 'java', label: 'Java' },
  { value: 'go', label: 'Go' },
  { value: 'rust', label: 'Rust' },
  { value: 'csharp', label: 'C#' },
];

const FOCUS_OPTIONS = [
  { value: 'all', label: '✨ All — performance + readability + security' },
  { value: 'performance', label: '⚡ Performance — speed & memory' },
  { value: 'readability', label: '👁️ Readability — clean, idiomatic code' },
  { value: 'security', label: '🔒 Security — vulnerabilities & validation' },
  { value: 'best_practices', label: '📐 Best Practices — SOLID & patterns' },
];

const SEVERITY_CONFIG: Record<string, { color: string; bg: string }> = {
  HIGH:   { color: 'text-red-400',    bg: 'bg-red-500/10 border-red-500/20' },
  MEDIUM: { color: 'text-yellow-400', bg: 'bg-yellow-500/10 border-yellow-500/20' },
  LOW:    { color: 'text-blue-400',   bg: 'bg-blue-500/10 border-blue-500/20' },
};

type OptResult = Awaited<ReturnType<typeof generatorService.optimizeCode>>;

export function OptimizerPage() {
  const [code, setCode] = useState('');
  const [language, setLanguage] = useState('python');
  const [focus, setFocus] = useState('all');
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<OptResult | null>(null);
  const [view, setView] = useState<'output' | 'diff'>('output');

  const handleGenerate = async () => {
    if (!code.trim()) { toast.error('Paste some code first'); return; }
    setLoading(true);
    try {
      const res = await generatorService.optimizeCode(code, language, focus);
      setResult(res);
      toast.success(`Found ${res.stats.total_improvements} improvements`);
    } catch (e: any) {
      toast.error(e?.response?.data?.detail || 'Optimization failed');
    } finally {
      setLoading(false);
    }
  };

  const inputPanel = (
    <div className="space-y-4">
      <div className="grid grid-cols-2 gap-3">
        <GenSelect label="Language" value={language} onChange={setLanguage} options={LANGUAGE_OPTIONS} />
        <GenSelect label="Focus Area" value={focus} onChange={setFocus} options={FOCUS_OPTIONS} />
      </div>
      <div>
        <label className="text-xs font-medium text-text-muted uppercase tracking-wider mb-1.5 block">Source Code</label>
        <CodeEditor value={code} onChange={setCode} language={language} />
      </div>
    </div>
  );

  const extraOutput = result ? (
    <div className="space-y-4 mb-6">
      {/* Stats row */}
      <div className="flex flex-wrap gap-2">
        {[
          { label: 'Total', value: result.stats.total_improvements, color: 'text-text-primary' },
          { label: 'High', value: result.stats.high_severity, color: 'text-red-400' },
          { label: 'Medium', value: result.stats.medium_severity, color: 'text-yellow-400' },
          { label: 'Low', value: result.stats.low_severity, color: 'text-blue-400' },
        ].map((s) => (
          <div key={s.label} className="glass rounded-xl px-3 py-1.5 border border-white/[0.06] text-xs">
            <span className="text-text-muted mr-1">{s.label}:</span>
            <span className={`font-bold ${s.color}`}>{s.value}</span>
          </div>
        ))}
      </div>

      {/* Summary */}
      {result.summary && (
        <p className="text-sm text-text-secondary glass rounded-xl p-3 border border-white/[0.06]">
          {result.summary}
        </p>
      )}

      {/* View toggle */}
      <div className="flex gap-2 p-1 glass rounded-xl border border-white/[0.08] w-fit">
        {(['output', 'diff'] as const).map((v) => (
          <button
            key={v}
            onClick={() => setView(v)}
            className={`px-4 py-1.5 rounded-lg text-xs font-semibold transition-all ${
              view === v
                ? 'bg-brand-primary/20 text-brand-primary border border-brand-primary/30'
                : 'text-text-muted hover:text-text-primary'
            }`}
          >
            {v === 'output' ? '✨ Optimized' : '📋 Changes'}
          </button>
        ))}
      </div>

      {/* Improvements list */}
      {view === 'diff' && result.improvements.length > 0 && (
        <div className="space-y-2 max-h-64 overflow-y-auto">
          {result.improvements.map((imp, i) => {
            const cfg = SEVERITY_CONFIG[imp.severity] ?? SEVERITY_CONFIG.LOW;
            return (
              <motion.div
                key={i}
                initial={{ opacity: 0, x: -8 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ delay: i * 0.04 }}
                className={`flex gap-3 p-3 rounded-xl border ${cfg.bg}`}
              >
                <div className={`text-xs font-bold uppercase mt-0.5 w-14 flex-shrink-0 ${cfg.color}`}>
                  {imp.severity}
                </div>
                <div>
                  <div className="text-xs font-medium text-text-primary">{imp.category}</div>
                  <div className="text-xs text-text-secondary mt-0.5">{imp.description}</div>
                  {imp.line_range && (
                    <div className="text-xs text-text-muted mt-1 font-mono">Lines: {imp.line_range}</div>
                  )}
                </div>
              </motion.div>
            );
          })}
        </div>
      )}
    </div>
  ) : null;

  return (
    <GeneratorWorkspace
      title="Code Optimizer"
      description="Refactor and improve code quality with AI — performance, readability, security"
      icon={<Zap size={20} />}
      accentColor="text-yellow-400"
      inputPanel={inputPanel}
      outputContent={view === 'output' ? (result?.optimized_code ?? null) : null}
      outputLanguage={language}
      loading={loading}
      onGenerate={handleGenerate}
      generateLabel="Optimize Code"
      extraOutput={extraOutput}
    />
  );
}
