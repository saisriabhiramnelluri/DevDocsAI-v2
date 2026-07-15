// DevDocsAI — UML Diagram Generator Page
import { useState } from 'react';
import { GitFork } from 'lucide-react';
import toast from 'react-hot-toast';
import { GeneratorWorkspace } from '../../components/generators/GeneratorWorkspace';
import { CodeEditor, GenSelect } from '../../components/generators/GeneratorControls';
import { generatorService } from '../../services/generatorService';
import { MermaidDiagram } from '../../components/architecture/MermaidDiagram';
import { useAppStore } from '../../store/appStore';

const LANGUAGE_OPTIONS = [
  { value: 'python', label: 'Python' },
  { value: 'typescript', label: 'TypeScript' },
  { value: 'javascript', label: 'JavaScript' },
  { value: 'java', label: 'Java' },
  { value: 'go', label: 'Go' },
  { value: 'csharp', label: 'C#' },
  { value: 'rust', label: 'Rust' },
];

const DIAGRAM_OPTIONS = [
  { value: 'class', label: 'Class Diagram' },
  { value: 'sequence', label: 'Sequence Diagram' },
  { value: 'component', label: 'Component / Flow' },
];

const PLACEHOLDER = `class UserService:
    def __init__(self, db: Database):
        self.db = db

    def get_user(self, user_id: str) -> User:
        return self.db.find(user_id)

    def authenticate(self, email: str, password: str) -> Optional[str]:
        user = self.db.find_by_email(email)
        if user and user.verify_password(password):
            return generate_token(user.id)
        return None`;

export function UMLGeneratorPage() {
  const { repositories } = useAppStore();
  const readyRepos = repositories.filter((r: any) => r.status === 'ready');

  const [mode, setMode] = useState<'code' | 'repo'>('code');
  const [code, setCode] = useState('');
  const [language, setLanguage] = useState('python');
  const [diagramType, setDiagramType] = useState('class');
  const [selectedRepo, setSelectedRepo] = useState(readyRepos[0]?.id ?? '');
  const [loading, setLoading] = useState(false);
  const [mermaid, setMermaid] = useState<string | null>(null);

  const handleGenerate = async () => {
    setLoading(true);
    try {
      let res: any;
      if (mode === 'code') {
        if (!code.trim()) { toast.error('Paste some code first'); setLoading(false); return; }
        res = await generatorService.generateUMLFromCode(code, language, diagramType);
      } else {
        if (!selectedRepo) { toast.error('Select a repository'); setLoading(false); return; }
        res = await generatorService.generateUMLFromRepo(selectedRepo);
      }
      setMermaid(res.mermaid);
      toast.success('Diagram generated');
    } catch (e: any) {
      toast.error(e?.response?.data?.detail || 'Generation failed');
    } finally {
      setLoading(false);
    }
  };

  const repoOptions = readyRepos.map((r: any) => ({ value: r.id, label: r.repo_name || r.id }));

  const inputPanel = (
    <div className="space-y-4">
      {/* Mode toggle */}
      <div className="flex gap-2 p-1 glass rounded-xl border border-white/[0.08]">
        {(['code', 'repo'] as const).map((m) => (
          <button
            key={m}
            onClick={() => setMode(m)}
            className={`flex-1 py-2 rounded-lg text-xs font-semibold transition-all ${
              mode === m
                ? 'bg-brand-secondary/20 text-brand-secondary border border-brand-secondary/30'
                : 'text-text-muted hover:text-text-primary'
            }`}
          >
            {m === 'code' ? '📋 From Code' : '📦 From Repo'}
          </button>
        ))}
      </div>

      {mode === 'code' ? (
        <>
          <div className="grid grid-cols-2 gap-3">
            <GenSelect label="Language" value={language} onChange={setLanguage} options={LANGUAGE_OPTIONS} />
            <GenSelect label="Diagram Type" value={diagramType} onChange={setDiagramType} options={DIAGRAM_OPTIONS} />
          </div>
          <div>
            <label className="text-xs font-medium text-text-muted uppercase tracking-wider mb-1.5 block">Source Code</label>
            <CodeEditor value={code} onChange={setCode} placeholder={PLACEHOLDER} language={language} />
          </div>
        </>
      ) : (
        <div className="space-y-3">
          {repoOptions.length === 0 ? (
            <div className="glass rounded-2xl p-6 text-center text-text-muted text-sm border border-white/[0.05]">
              No analyzed repositories. Analyze a repo from the Dashboard first.
            </div>
          ) : (
            <GenSelect
              label="Repository"
              value={selectedRepo}
              onChange={setSelectedRepo}
              options={repoOptions}
            />
          )}
          <p className="text-xs text-text-muted">
            Reads class data directly from the repository's knowledge graph — no extra AI call needed.
          </p>
        </div>
      )}
    </div>
  );

  // For UML we show the rendered Mermaid diagram AND the raw text
  const extraOutput = mermaid ? (
    <div className="mb-6 glass-strong rounded-2xl border-glow overflow-hidden" style={{ height: 340 }}>
      <MermaidDiagram chart={mermaid} />
    </div>
  ) : null;

  return (
    <GeneratorWorkspace
      title="UML Diagram Generator"
      description="Generate class, sequence, and component diagrams as Mermaid syntax"
      icon={<GitFork size={20} />}
      accentColor="text-brand-secondary"
      inputPanel={inputPanel}
      outputContent={mermaid}
      outputLanguage="mermaid"
      loading={loading}
      onGenerate={handleGenerate}
      generateLabel="Generate Diagram"
      extraOutput={extraOutput}
    />
  );
}
