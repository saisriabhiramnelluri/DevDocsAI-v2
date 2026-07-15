// DevDocsAI — Tree Documentation Generator Page
import { useState } from 'react';
import { Network, GitBranch, Download, Copy, Check } from 'lucide-react';
import toast from 'react-hot-toast';
import { motion, AnimatePresence } from 'framer-motion';
import { GeneratorWorkspace } from '../../components/generators/GeneratorWorkspace';
import { GenSelect } from '../../components/generators/GeneratorControls';
import { generatorService } from '../../services/generatorService';
import { useAppStore } from '../../store/appStore';

const SAMPLE_STRUCTURE = `devdocsai/
├── backend/
│   ├── app/
│   │   ├── api/
│   │   │   └── routes/
│   │   ├── core/
│   │   ├── database/
│   │   └── services/
│   ├── main.py
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   ├── pages/
│   │   └── services/
│   └── package.json
└── docs/`;

type Result = Awaited<ReturnType<typeof generatorService.treeFromRepo>>;

export function TreeGeneratorPage() {
  const { repositories } = useAppStore();
  const readyRepos = repositories.filter((r: any) => r.status === 'ready');

  const [mode, setMode] = useState<'repo' | 'paste'>('paste');
  const [selectedRepo, setSelectedRepo] = useState(readyRepos[0]?.id ?? '');
  const [structure, setStructure] = useState('');
  const [projectName, setProjectName] = useState('');
  const [depth, setDepth] = useState(4);
  const [includeDescriptions, setIncludeDescriptions] = useState(true);
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<Result | null>(null);
  const [view, setView] = useState<'tree' | 'markdown'>('markdown');
  const [copied, setCopied] = useState(false);

  const repoOptions = readyRepos.map((r: any) => ({
    value: r.id,
    label: r.repo_name || r.repo_url?.split('/').pop() || r.id,
  }));

  const depthOptions = [2, 3, 4, 5, 6].map((d) => ({ value: String(d), label: `${d} levels deep` }));

  const handleGenerate = async () => {
    setLoading(true);
    try {
      let res: Result;
      if (mode === 'repo') {
        if (!selectedRepo) { toast.error('Select a repository'); setLoading(false); return; }
        res = await generatorService.treeFromRepo(selectedRepo, depth, includeDescriptions);
      } else {
        const src = structure.trim() || SAMPLE_STRUCTURE;
        const name = projectName.trim() || 'Project';
        res = await generatorService.treeFromStructure(src, name);
      }
      setResult(res);
      toast.success(`Tree documented — ${res.file_count} files`);
    } catch (e: any) {
      toast.error(e?.response?.data?.detail || 'Generation failed');
    } finally {
      setLoading(false);
    }
  };

  const handleCopy = () => {
    if (!result) return;
    const text = view === 'tree' ? result.tree_text : result.markdown;
    navigator.clipboard.writeText(text);
    setCopied(true);
    toast.success('Copied');
    setTimeout(() => setCopied(false), 2000);
  };

  const handleDownload = () => {
    if (!result) return;
    const [content, ext, name] = view === 'tree'
      ? [result.tree_text, 'txt', 'directory_tree']
      : [result.markdown, 'md', 'CODEBASE_STRUCTURE'];
    const blob = new Blob([content], { type: 'text/plain' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `${name}.${ext}`;
    a.click();
    URL.revokeObjectURL(url);
    toast.success(`Downloaded ${name}.${ext}`);
  };

  const inputPanel = (
    <div className="space-y-4">
      {/* Mode toggle */}
      <div className="flex gap-2 p-1 glass rounded-xl border border-white/[0.08]">
        {(['paste', 'repo'] as const).map((m) => (
          <button
            key={m}
            onClick={() => setMode(m)}
            className={`flex-1 py-2 rounded-lg text-xs font-semibold transition-all ${
              mode === m
                ? 'bg-teal-400/20 text-teal-400 border border-teal-400/30'
                : 'text-text-muted hover:text-text-primary'
            }`}
          >
            {m === 'paste' ? '📋 Paste Structure' : '📦 From Repo'}
          </button>
        ))}
      </div>

      <AnimatePresence mode="wait">
        {mode === 'paste' ? (
          <motion.div
            key="paste"
            initial={{ opacity: 0, y: 8 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -8 }}
            className="space-y-3"
          >
            <div>
              <label className="text-xs font-medium text-text-muted uppercase tracking-wider mb-1.5 block">
                Project Name
              </label>
              <input
                value={projectName}
                onChange={(e) => setProjectName(e.target.value)}
                placeholder="MyProject"
                className="w-full text-sm bg-surface/60 border border-white/[0.08] rounded-xl px-3 py-2 text-text-primary focus:outline-none focus:border-teal-400/40 transition-colors"
              />
            </div>
            <div>
              <div className="flex items-center justify-between mb-1.5">
                <label className="text-xs font-medium text-text-muted uppercase tracking-wider">
                  Directory Structure
                </label>
                <button
                  onClick={() => setStructure(SAMPLE_STRUCTURE)}
                  className="text-xs text-text-muted hover:text-teal-400 transition-colors"
                >
                  Load example →
                </button>
              </div>
              <textarea
                value={structure}
                onChange={(e) => setStructure(e.target.value)}
                placeholder={SAMPLE_STRUCTURE}
                rows={12}
                className="w-full font-mono text-xs bg-surface/60 border border-white/[0.08] rounded-xl p-3 text-text-primary resize-none focus:outline-none focus:border-teal-400/40 transition-colors leading-relaxed"
              />
              <p className="text-[10px] text-text-muted mt-1">
                Paste output of <span className="font-mono text-teal-400">find . -type f | head -100</span> or any tree structure
              </p>
            </div>
          </motion.div>
        ) : (
          <motion.div
            key="repo"
            initial={{ opacity: 0, y: 8 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -8 }}
            className="space-y-3"
          >
            {repoOptions.length === 0 ? (
              <div className="glass rounded-2xl p-6 text-center text-text-muted text-sm border border-white/[0.05]">
                No analyzed repositories yet.<br />
                <span className="text-xs">Analyze one from the Dashboard first.</span>
              </div>
            ) : (
              <>
                <GenSelect
                  label="Repository"
                  value={selectedRepo}
                  onChange={setSelectedRepo}
                  options={repoOptions}
                />
                <GenSelect
                  label="Max Depth"
                  value={String(depth)}
                  onChange={(v) => setDepth(Number(v))}
                  options={depthOptions}
                />
                <label className="flex items-center gap-3 cursor-pointer group">
                  <div
                    onClick={() => setIncludeDescriptions((p) => !p)}
                    className={`relative w-10 h-5 rounded-full transition-colors ${
                      includeDescriptions ? 'bg-teal-400' : 'bg-surface border border-white/10'
                    }`}
                  >
                    <span className={`absolute top-0.5 left-0.5 w-4 h-4 bg-white rounded-full shadow transition-transform ${
                      includeDescriptions ? 'translate-x-5' : ''
                    }`} />
                  </div>
                  <span className="text-sm text-text-secondary group-hover:text-text-primary transition-colors">
                    AI-generated folder descriptions
                  </span>
                </label>
              </>
            )}
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );

  const extraOutput = result ? (
    <div className="flex flex-wrap items-center gap-3 mb-4">
      <div className="glass rounded-xl px-3 py-1.5 text-xs border border-teal-400/20 text-teal-400">
        🗂️ {result.file_count} files
      </div>
      {/* View toggle */}
      <div className="flex gap-1 p-1 glass rounded-xl border border-white/[0.08]">
        {(['markdown', 'tree'] as const).map((v) => (
          <button
            key={v}
            onClick={() => setView(v)}
            className={`px-3 py-1 rounded-lg text-[10px] font-semibold transition-all ${
              view === v
                ? 'bg-teal-400/20 text-teal-400 border border-teal-400/30'
                : 'text-text-muted hover:text-text-primary'
            }`}
          >
            {v === 'markdown' ? '📄 Markdown Doc' : '🌳 Raw Tree'}
          </button>
        ))}
      </div>
      {/* Actions */}
      <div className="ml-auto flex gap-2">
        <button
          onClick={handleCopy}
          className="flex items-center gap-1.5 px-3 py-1.5 glass rounded-xl border border-white/[0.08] text-xs hover:border-teal-400/30 transition-all"
        >
          {copied ? <Check size={12} className="text-green-400" /> : <Copy size={12} />}
          Copy
        </button>
        <button
          onClick={handleDownload}
          className="flex items-center gap-1.5 px-3 py-1.5 glass rounded-xl border border-white/[0.08] text-xs hover:border-teal-400/30 transition-all"
        >
          <Download size={12} />
          Download
        </button>
      </div>
    </div>
  ) : null;

  return (
    <GeneratorWorkspace
      title="Tree Documentation Generator"
      description="Document your project's directory structure with AI-generated folder descriptions"
      icon={<Network size={20} />}
      accentColor="text-teal-400"
      inputPanel={inputPanel}
      outputContent={result ? (view === 'tree' ? result.tree_text : result.markdown) : null}
      outputLanguage={view === 'markdown' ? 'markdown' : 'text'}
      loading={loading}
      onGenerate={handleGenerate}
      generateLabel="Generate Tree Docs"
      extraOutput={extraOutput}
    />
  );
}
