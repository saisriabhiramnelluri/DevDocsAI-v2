// DevDocsAI — Swagger / OpenAPI Documentation Generator Page
import { useState, useRef } from 'react';
import { FileCode2, Upload, X, CheckCircle2, Download } from 'lucide-react';
import toast from 'react-hot-toast';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import { GeneratorWorkspace } from '../../components/generators/GeneratorWorkspace';
import { generatorService } from '../../services/generatorService';

const SAMPLE_SPEC = `openapi: "3.0.0"
info:
  title: Sample API
  version: "1.0.0"
  description: A simple pet store API example
paths:
  /pets:
    get:
      summary: List all pets
      parameters:
        - name: limit
          in: query
          schema:
            type: integer
      responses:
        "200":
          description: A list of pets
  /pets/{petId}:
    get:
      summary: Get a pet by ID
      parameters:
        - name: petId
          in: path
          required: true
          schema:
            type: string
      responses:
        "200":
          description: A single pet
        "404":
          description: Pet not found`;

const LANG_OPTIONS = ['python', 'javascript', 'typescript', 'curl', 'go', 'java'];

type Result = Awaited<ReturnType<typeof generatorService.generateSwaggerDocs>>;

export function SwaggerGeneratorPage() {
  const [spec, setSpec] = useState('');
  const [langSamples, setLangSamples] = useState(['python', 'javascript', 'curl']);
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<Result | null>(null);
  const [view, setView] = useState<'raw' | 'preview'>('preview');
  const fileRef = useRef<HTMLInputElement>(null);

  const toggleLang = (lang: string) => {
    setLangSamples((prev) =>
      prev.includes(lang) ? prev.filter((l) => l !== lang) : [...prev, lang]
    );
  };

  const handleFile = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;
    const reader = new FileReader();
    reader.onload = (ev) => {
      setSpec(ev.target?.result as string ?? '');
      toast.success(`Loaded ${file.name}`);
    };
    reader.readAsText(file);
  };

  const handleGenerate = async () => {
    if (!spec.trim()) { toast.error('Paste or upload an OpenAPI spec first'); return; }
    setLoading(true);
    try {
      const res = await generatorService.generateSwaggerDocs(spec, langSamples);
      setResult(res);
      toast.success(`Generated docs for ${res.title} (${res.endpoint_count} endpoints)`);
    } catch (e: any) {
      toast.error(e?.response?.data?.detail || 'Generation failed');
    } finally {
      setLoading(false);
    }
  };

  const handleDownload = () => {
    if (!result) return;
    const blob = new Blob([result.documentation], { type: 'text/markdown' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `${result.title.replace(/\s+/g, '_')}_API_Reference.md`;
    a.click();
    URL.revokeObjectURL(url);
    toast.success('Downloaded API reference');
  };

  const inputPanel = (
    <div className="space-y-4">
      {/* File upload */}
      <div
        onClick={() => fileRef.current?.click()}
        className="flex flex-col items-center justify-center gap-2 p-6 glass rounded-2xl border-2 border-dashed border-white/[0.12] hover:border-brand-primary/40 cursor-pointer transition-colors group"
      >
        <Upload size={24} className="text-text-muted group-hover:text-brand-primary transition-colors" />
        <span className="text-sm text-text-secondary group-hover:text-text-primary transition-colors">
          Drop or click to upload <span className="font-mono text-brand-primary">.json</span> / <span className="font-mono text-brand-primary">.yaml</span>
        </span>
        <input ref={fileRef} type="file" accept=".json,.yaml,.yml" className="hidden" onChange={handleFile} />
      </div>

      {/* Spec textarea */}
      <div className="relative">
        <label className="text-xs font-medium text-text-muted uppercase tracking-wider mb-1.5 block">
          Or paste OpenAPI spec (JSON / YAML)
        </label>
        <textarea
          value={spec}
          onChange={(e) => setSpec(e.target.value)}
          placeholder={SAMPLE_SPEC}
          rows={12}
          className="w-full font-mono text-xs bg-surface/60 border border-white/[0.08] rounded-xl p-3 text-text-primary resize-none focus:outline-none focus:border-brand-primary/40 transition-colors leading-relaxed"
        />
        {spec && (
          <button
            onClick={() => setSpec('')}
            className="absolute top-8 right-2 p-1 text-text-muted hover:text-text-primary"
          >
            <X size={14} />
          </button>
        )}
      </div>

      {/* Language samples */}
      <div>
        <label className="text-xs font-medium text-text-muted uppercase tracking-wider mb-2 block">
          Code Sample Languages
        </label>
        <div className="flex flex-wrap gap-2">
          {LANG_OPTIONS.map((lang) => (
            <button
              key={lang}
              onClick={() => toggleLang(lang)}
              className={`px-3 py-1 rounded-lg text-xs font-mono font-medium border transition-all ${
                langSamples.includes(lang)
                  ? 'bg-brand-primary/20 border-brand-primary/40 text-brand-primary'
                  : 'glass border-white/[0.08] text-text-muted hover:text-text-primary'
              }`}
            >
              {lang}
            </button>
          ))}
        </div>
      </div>
    </div>
  );

  const extraOutput = result ? (
    <div className="space-y-3 mb-5">
      <div className="flex flex-wrap items-center gap-3">
        <div className="glass rounded-xl px-3 py-1.5 text-xs border border-brand-primary/20 text-brand-primary">
          {result.title} v{result.version}
        </div>
        <div className="glass rounded-xl px-3 py-1.5 text-xs border border-green-400/20 text-green-400">
          <CheckCircle2 size={11} className="inline mr-1" />
          {result.endpoint_count} endpoints
        </div>
        <button
          onClick={handleDownload}
          className="ml-auto flex items-center gap-1.5 px-3 py-1.5 glass rounded-xl border border-white/[0.08] text-xs hover:border-brand-primary/30 transition-all"
        >
          <Download size={12} />
          Download .md
        </button>
      </div>
      {/* View toggle */}
      <div className="flex gap-2 p-1 glass rounded-xl border border-white/[0.08] w-fit">
        {(['preview', 'raw'] as const).map((v) => (
          <button
            key={v}
            onClick={() => setView(v)}
            className={`px-4 py-1.5 rounded-lg text-xs font-semibold transition-all ${
              view === v
                ? 'bg-brand-primary/20 text-brand-primary border border-brand-primary/30'
                : 'text-text-muted hover:text-text-primary'
            }`}
          >
            {v === 'preview' ? '📖 Preview' : '📋 Raw Markdown'}
          </button>
        ))}
      </div>
    </div>
  ) : null;

  // For preview mode, show rendered markdown instead of raw code block
  const outputContent = result
    ? view === 'raw'
      ? result.documentation
      : null   // handled below
    : null;

  const customOutput = result && view === 'preview' ? (
    <div className="flex-1 overflow-y-auto glass-strong rounded-2xl border border-white/[0.08] p-6 markdown-content">
      <ReactMarkdown remarkPlugins={[remarkGfm]}>{result.documentation}</ReactMarkdown>
    </div>
  ) : null;

  return (
    <GeneratorWorkspace
      title="Swagger / API Docs Generator"
      description="Convert OpenAPI / Swagger specs into polished human-readable documentation"
      icon={<FileCode2 size={20} />}
      accentColor="text-orange-400"
      inputPanel={inputPanel}
      outputContent={outputContent}
      outputLanguage="markdown"
      loading={loading}
      onGenerate={handleGenerate}
      generateLabel="Generate Docs"
      extraOutput={extraOutput}
      customOutput={customOutput}
    />
  );
}
