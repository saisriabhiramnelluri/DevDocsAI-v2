// DevDocsAI — Code Comment / DocBlock Generator Page
import { useState } from 'react';
import { MessageSquareCode } from 'lucide-react';
import toast from 'react-hot-toast';
import { GeneratorWorkspace } from '../../components/generators/GeneratorWorkspace';
import { CodeEditor, GenSelect } from '../../components/generators/GeneratorControls';
import { generatorService } from '../../services/generatorService';

const LANGUAGE_OPTIONS = [
  { value: 'python', label: 'Python' },
  { value: 'javascript', label: 'JavaScript' },
  { value: 'typescript', label: 'TypeScript' },
  { value: 'java', label: 'Java' },
  { value: 'go', label: 'Go' },
  { value: 'rust', label: 'Rust' },
  { value: 'csharp', label: 'C#' },
  { value: 'cpp', label: 'C++' },
];

const STYLE_OPTIONS: Record<string, { value: string; label: string }[]> = {
  python: [
    { value: 'auto', label: 'Auto (Google)' },
    { value: 'google', label: 'Google Style' },
    { value: 'numpy', label: 'NumPy Style' },
    { value: 'sphinx', label: 'Sphinx / RST' },
  ],
  javascript: [{ value: 'auto', label: 'JSDoc (Auto)' }, { value: 'jsdoc', label: 'JSDoc' }],
  typescript: [{ value: 'auto', label: 'TSDoc (Auto)' }, { value: 'jsdoc', label: 'JSDoc/TSDoc' }],
  java:   [{ value: 'auto', label: 'Javadoc (Auto)' }, { value: 'javadoc', label: 'Javadoc' }],
  go:     [{ value: 'auto', label: 'godoc (Auto)' }],
  rust:   [{ value: 'auto', label: 'rustdoc (Auto)' }],
  csharp: [{ value: 'auto', label: 'XML Docs (Auto)' }],
  cpp:    [{ value: 'auto', label: 'Doxygen (Auto)' }],
};

const PLACEHOLDER = `def authenticate(user_id: str, token: str) -> bool:
    if not user_id or not token:
        return False
    stored = get_stored_token(user_id)
    return hmac.compare_digest(stored, token)`;

export function CommentGeneratorPage() {
  const [code, setCode] = useState('');
  const [language, setLanguage] = useState('python');
  const [style, setStyle] = useState('auto');
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<{ commented_code: string; comments_added: number } | null>(null);

  const styleOptions = STYLE_OPTIONS[language] ?? [{ value: 'auto', label: 'Auto' }];

  const handleGenerate = async () => {
    if (!code.trim()) {
      toast.error('Paste some code first');
      return;
    }
    setLoading(true);
    try {
      const res = await generatorService.generateComments(code, language, style);
      setResult(res);
      toast.success(`Added ${res.comments_added} comment blocks`);
    } catch (e: any) {
      toast.error(e?.response?.data?.detail || 'Generation failed');
    } finally {
      setLoading(false);
    }
  };

  const inputPanel = (
    <div className="space-y-4">
      <div className="grid grid-cols-2 gap-3">
        <GenSelect
          label="Language"
          value={language}
          onChange={(v) => { setLanguage(v); setStyle('auto'); }}
          options={LANGUAGE_OPTIONS}
        />
        <GenSelect
          label="Doc Style"
          value={style}
          onChange={setStyle}
          options={styleOptions}
        />
      </div>
      <div>
        <label className="text-xs font-medium text-text-muted uppercase tracking-wider mb-1.5 block">
          Source Code
        </label>
        <CodeEditor
          value={code}
          onChange={setCode}
          placeholder={PLACEHOLDER}
          language={language}
        />
      </div>
    </div>
  );

  const extraOutput = result ? (
    <div className="flex items-center gap-3 mb-4">
      <div className="glass rounded-xl px-3 py-1.5 text-xs border border-green-500/20 text-green-400">
        ✓ {result.comments_added} comment blocks added
      </div>
    </div>
  ) : null;

  return (
    <GeneratorWorkspace
      title="DocBlock / Comment Generator"
      description="Add docstrings and inline comments to your source code automatically"
      icon={<MessageSquareCode size={20} />}
      accentColor="text-brand-primary"
      inputPanel={inputPanel}
      outputContent={result?.commented_code ?? null}
      outputLanguage={language}
      loading={loading}
      onGenerate={handleGenerate}
      generateLabel="Add Comments"
      extraOutput={extraOutput}
    />
  );
}
