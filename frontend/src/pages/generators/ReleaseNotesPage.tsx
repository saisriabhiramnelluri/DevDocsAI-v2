// DevDocsAI — Release Notes Generator Page
import { useState } from 'react';
import { GitCommit, Plus, X, Download } from 'lucide-react';
import toast from 'react-hot-toast';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import { motion, AnimatePresence } from 'framer-motion';
import { GeneratorWorkspace } from '../../components/generators/GeneratorWorkspace';
import { generatorService } from '../../services/generatorService';

const PLACEHOLDER_COMMITS = [
  'feat(auth): add OAuth2 login with Google and GitHub',
  'fix(api): resolve rate limiting issue on /search endpoint',
  'perf(embeddings): batch processing reduces latency by 40%',
  'feat(generators): add code optimizer with severity levels',
  'fix(ui): dark mode flash on initial page load',
  'docs: update README with deployment instructions',
  'chore: upgrade dependencies to latest versions',
  'refactor(pipeline): extract embedding service to separate module',
];

type Result = Awaited<ReturnType<typeof generatorService.generateReleaseNotes>>;

export function ReleaseNotesPage() {
  const [commits, setCommits] = useState<string[]>(['']);
  const [version, setVersion] = useState('v1.0.0');
  const [fromRef, setFromRef] = useState('');
  const [toRef, setToRef] = useState('HEAD');
  const [bulkMode, setBulkMode] = useState(false);
  const [bulkText, setBulkText] = useState('');
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<Result | null>(null);
  const [view, setView] = useState<'preview' | 'raw'>('preview');

  // ── Commit list management ────────────────────────────────────────────────
  const updateCommit = (i: number, val: string) =>
    setCommits((prev) => prev.map((c, idx) => (idx === i ? val : c)));

  const addCommit = () => setCommits((prev) => [...prev, '']);

  const removeCommit = (i: number) =>
    setCommits((prev) => prev.filter((_, idx) => idx !== i));

  const loadExample = () => {
    setCommits(PLACEHOLDER_COMMITS);
    toast.success('Example commits loaded');
  };

  const parseBulk = () => {
    const lines = bulkText
      .split('\n')
      .map((l) => l.replace(/^[a-f0-9]{6,}\s+/, '').trim()) // strip hash prefix
      .filter(Boolean);
    if (!lines.length) { toast.error('No commits found'); return; }
    setCommits(lines);
    setBulkMode(false);
    toast.success(`Loaded ${lines.length} commits`);
  };

  const handleGenerate = async () => {
    const filtered = (bulkMode
      ? bulkText.split('\n').map((l) => l.replace(/^[a-f0-9]{6,}\s+/, '').trim()).filter(Boolean)
      : commits.filter(Boolean)
    );
    if (!filtered.length) { toast.error('Add at least one commit message'); return; }
    setLoading(true);
    try {
      const res = await generatorService.generateReleaseNotes(
        filtered,
        version,
        fromRef || undefined,
        toRef || undefined,
      );
      setResult(res);
      toast.success(`Generated notes for ${res.commit_count} commits`);
    } catch (e: any) {
      toast.error(e?.response?.data?.detail || 'Generation failed');
    } finally {
      setLoading(false);
    }
  };

  const handleDownload = () => {
    if (!result) return;
    const blob = new Blob([result.release_notes], { type: 'text/markdown' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `RELEASE_NOTES_${result.version.replace(/\s+/g, '_')}.md`;
    a.click();
    URL.revokeObjectURL(url);
    toast.success('Downloaded release notes');
  };

  const inputPanel = (
    <div className="space-y-4">
      {/* Version + ref range */}
      <div className="grid grid-cols-3 gap-2">
        <div className="col-span-3 sm:col-span-1">
          <label className="text-xs font-medium text-text-muted uppercase tracking-wider mb-1.5 block">Version</label>
          <input
            value={version}
            onChange={(e) => setVersion(e.target.value)}
            placeholder="v1.0.0"
            className="w-full font-mono text-sm bg-surface/60 border border-white/[0.08] rounded-xl px-3 py-2 text-text-primary focus:outline-none focus:border-brand-primary/40 transition-colors"
          />
        </div>
        <div>
          <label className="text-xs font-medium text-text-muted uppercase tracking-wider mb-1.5 block">From</label>
          <input
            value={fromRef}
            onChange={(e) => setFromRef(e.target.value)}
            placeholder="v0.9.0"
            className="w-full font-mono text-xs bg-surface/60 border border-white/[0.08] rounded-xl px-3 py-2 text-text-primary focus:outline-none focus:border-brand-primary/40 transition-colors"
          />
        </div>
        <div>
          <label className="text-xs font-medium text-text-muted uppercase tracking-wider mb-1.5 block">To</label>
          <input
            value={toRef}
            onChange={(e) => setToRef(e.target.value)}
            placeholder="HEAD"
            className="w-full font-mono text-xs bg-surface/60 border border-white/[0.08] rounded-xl px-3 py-2 text-text-primary focus:outline-none focus:border-brand-primary/40 transition-colors"
          />
        </div>
      </div>

      {/* Mode toggle */}
      <div className="flex items-center gap-3">
        <div className="flex gap-2 p-1 glass rounded-xl border border-white/[0.08]">
          {(['list', 'bulk'] as const).map((m) => (
            <button
              key={m}
              onClick={() => setBulkMode(m === 'bulk')}
              className={`px-4 py-1.5 rounded-lg text-xs font-semibold transition-all ${
                (m === 'bulk') === bulkMode
                  ? 'bg-brand-primary/20 text-brand-primary border border-brand-primary/30'
                  : 'text-text-muted hover:text-text-primary'
              }`}
            >
              {m === 'list' ? '📋 Add Individually' : '📄 Paste git log'}
            </button>
          ))}
        </div>
        <button onClick={loadExample} className="text-xs text-text-muted hover:text-brand-primary transition-colors">
          Load example →
        </button>
      </div>

      {/* Commit input */}
      {bulkMode ? (
        <div className="space-y-2">
          <label className="text-xs font-medium text-text-muted uppercase tracking-wider block">
            Paste output of <span className="font-mono text-brand-primary">git log --oneline</span>
          </label>
          <textarea
            value={bulkText}
            onChange={(e) => setBulkText(e.target.value)}
            placeholder={`abc1234 feat(auth): add OAuth login\ndef5678 fix(api): resolve rate limit\n9ab0123 docs: update README`}
            rows={8}
            className="w-full font-mono text-xs bg-surface/60 border border-white/[0.08] rounded-xl p-3 text-text-primary resize-none focus:outline-none focus:border-brand-primary/40 transition-colors leading-relaxed"
          />
          <button
            onClick={parseBulk}
            className="text-xs px-4 py-1.5 rounded-lg glass border border-white/[0.08] hover:border-brand-primary/30 transition-all"
          >
            Parse & switch to list →
          </button>
        </div>
      ) : (
        <div className="space-y-2">
          <label className="text-xs font-medium text-text-muted uppercase tracking-wider block">
            Commits ({commits.filter(Boolean).length})
          </label>
          <div className="space-y-1.5 max-h-72 overflow-y-auto pr-1">
            <AnimatePresence initial={false}>
              {commits.map((c, i) => (
                <motion.div
                  key={i}
                  initial={{ opacity: 0, height: 0 }}
                  animate={{ opacity: 1, height: 'auto' }}
                  exit={{ opacity: 0, height: 0 }}
                  className="flex gap-2 items-center"
                >
                  <span className="text-[10px] font-mono text-text-muted w-5 text-right flex-shrink-0">{i + 1}</span>
                  <input
                    value={c}
                    onChange={(e) => updateCommit(i, e.target.value)}
                    placeholder="feat: describe what changed"
                    className="flex-1 font-mono text-xs bg-surface/60 border border-white/[0.08] rounded-lg px-3 py-1.5 text-text-primary focus:outline-none focus:border-brand-primary/40 transition-colors"
                  />
                  {commits.length > 1 && (
                    <button onClick={() => removeCommit(i)} className="text-text-muted hover:text-red-400 transition-colors flex-shrink-0">
                      <X size={13} />
                    </button>
                  )}
                </motion.div>
              ))}
            </AnimatePresence>
          </div>
          <button
            onClick={addCommit}
            className="flex items-center gap-1.5 text-xs text-text-muted hover:text-brand-primary transition-colors mt-1"
          >
            <Plus size={13} /> Add commit
          </button>
        </div>
      )}
    </div>
  );

  // ── Stats pills shown above output ────────────────────────────────────────
  const extraOutput = result ? (
    <div className="flex flex-wrap items-center gap-3 mb-4">
      <div className="glass rounded-xl px-3 py-1.5 text-xs border border-brand-primary/20 text-brand-primary">
        🏷️ {result.version}
      </div>
      <div className="glass rounded-xl px-3 py-1.5 text-xs border border-white/[0.08] text-text-secondary">
        {result.commit_count} commits
      </div>
      {result.categories.slice(0, 3).map((cat) => (
        <div key={cat} className="glass rounded-xl px-2.5 py-1 text-[10px] border border-white/[0.06] text-text-muted">
          {cat}
        </div>
      ))}
      <button
        onClick={handleDownload}
        className="ml-auto flex items-center gap-1.5 px-3 py-1.5 glass rounded-xl border border-white/[0.08] text-xs hover:border-brand-primary/30 transition-all"
      >
        <Download size={12} />
        Download .md
      </button>
      {/* View toggle */}
      <div className="flex gap-1 p-1 glass rounded-xl border border-white/[0.08]">
        {(['preview', 'raw'] as const).map((v) => (
          <button
            key={v}
            onClick={() => setView(v)}
            className={`px-3 py-1 rounded-lg text-[10px] font-semibold transition-all ${
              view === v
                ? 'bg-brand-primary/20 text-brand-primary border border-brand-primary/30'
                : 'text-text-muted hover:text-text-primary'
            }`}
          >
            {v === 'preview' ? '📖 Preview' : '📋 Raw'}
          </button>
        ))}
      </div>
    </div>
  ) : null;

  const customOutput = result && view === 'preview' ? (
    <div className="flex-1 overflow-y-auto glass-strong rounded-2xl border border-white/[0.08] p-6 markdown-content">
      <ReactMarkdown remarkPlugins={[remarkGfm]}>{result.release_notes}</ReactMarkdown>
    </div>
  ) : null;

  return (
    <GeneratorWorkspace
      title="Release Notes Generator"
      description="Turn git commit history into polished, categorized release notes"
      icon={<GitCommit size={20} />}
      accentColor="text-purple-400"
      inputPanel={inputPanel}
      outputContent={view === 'raw' && result ? result.release_notes : null}
      outputLanguage="markdown"
      loading={loading}
      onGenerate={handleGenerate}
      generateLabel="Generate Notes"
      extraOutput={extraOutput}
      customOutput={customOutput}
    />
  );
}
