// DevDocsAI — Code Language Converter Page
import { useState } from 'react';
import { ArrowLeftRight, AlertTriangle } from 'lucide-react';
import toast from 'react-hot-toast';
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
  { value: 'kotlin', label: 'Kotlin' },
  { value: 'swift', label: 'Swift' },
  { value: 'ruby', label: 'Ruby' },
  { value: 'php', label: 'PHP' },
];

const PLACEHOLDER = `async function fetchUser(userId: string): Promise<User | null> {
  try {
    const response = await fetch(\`/api/users/\${userId}\`);
    if (!response.ok) return null;
    return await response.json() as User;
  } catch (error) {
    console.error('Failed to fetch user:', error);
    return null;
  }
}`;

export function ConvertGeneratorPage() {
  const [code, setCode] = useState('');
  const [sourceLang, setSourceLang] = useState('typescript');
  const [targetLang, setTargetLang] = useState('python');
  const [preserveComments, setPreserveComments] = useState(true);
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<{
    converted_code: string;
    original_lines: number;
    output_lines: number;
    warnings: string[];
  } | null>(null);

  const swapLanguages = () => {
    setSourceLang(targetLang);
    setTargetLang(sourceLang);
    setResult(null);
  };

  const handleGenerate = async () => {
    if (!code.trim()) { toast.error('Paste some code first'); return; }
    if (sourceLang === targetLang) { toast.error('Source and target languages must differ'); return; }
    setLoading(true);
    try {
      const res = await generatorService.convertCode(code, sourceLang, targetLang, preserveComments);
      setResult(res);
      toast.success(`Converted to ${targetLang}`);
    } catch (e: any) {
      toast.error(e?.response?.data?.detail || 'Conversion failed');
    } finally {
      setLoading(false);
    }
  };

  const inputPanel = (
    <div className="space-y-4">
      {/* Language pair */}
      <div className="flex items-end gap-2">
        <div className="flex-1">
          <GenSelect label="From" value={sourceLang} onChange={setSourceLang} options={LANGUAGE_OPTIONS} />
        </div>
        <button
          onClick={swapLanguages}
          className="mb-0.5 p-2.5 glass rounded-xl border border-white/[0.08] hover:border-brand-primary/40 hover:text-brand-primary transition-all"
          title="Swap languages"
        >
          <ArrowLeftRight size={16} />
        </button>
        <div className="flex-1">
          <GenSelect label="To" value={targetLang} onChange={setTargetLang} options={LANGUAGE_OPTIONS} />
        </div>
      </div>

      {/* Preserve comments toggle */}
      <label className="flex items-center gap-3 cursor-pointer group">
        <div
          onClick={() => setPreserveComments((p) => !p)}
          className={`relative w-10 h-5 rounded-full transition-colors ${
            preserveComments ? 'bg-brand-primary' : 'bg-surface border border-white/10'
          }`}
        >
          <span
            className={`absolute top-0.5 left-0.5 w-4 h-4 bg-white rounded-full shadow transition-transform ${
              preserveComments ? 'translate-x-5' : ''
            }`}
          />
        </div>
        <span className="text-sm text-text-secondary group-hover:text-text-primary transition-colors">
          Preserve comments
        </span>
      </label>

      <div>
        <label className="text-xs font-medium text-text-muted uppercase tracking-wider mb-1.5 block">
          Source Code ({sourceLang})
        </label>
        <CodeEditor value={code} onChange={setCode} placeholder={PLACEHOLDER} language={sourceLang} />
      </div>
    </div>
  );

  const extraOutput = result ? (
    <div className="flex flex-wrap items-center gap-3 mb-4">
      <div className="glass rounded-xl px-3 py-1.5 text-xs border border-brand-primary/20 text-brand-primary">
        {result.original_lines} → {result.output_lines} lines
      </div>
      {result.warnings.map((w, i) => (
        <div key={i} className="flex items-center gap-1.5 glass rounded-xl px-3 py-1.5 text-xs border border-yellow-500/20 text-yellow-400">
          <AlertTriangle size={11} />
          {w}
        </div>
      ))}
    </div>
  ) : null;

  return (
    <GeneratorWorkspace
      title="Code Language Converter"
      description="Convert code between programming languages using idiomatic patterns"
      icon={<ArrowLeftRight size={20} />}
      accentColor="text-green-400"
      inputPanel={inputPanel}
      outputContent={result?.converted_code ?? null}
      outputLanguage={targetLang}
      loading={loading}
      onGenerate={handleGenerate}
      generateLabel="Convert Code"
      extraOutput={extraOutput}
    />
  );
}
