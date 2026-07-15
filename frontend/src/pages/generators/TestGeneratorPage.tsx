// DevDocsAI — Unit Test Generator Page
import { useState } from 'react';
import { TestTube2 } from 'lucide-react';
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
];

const FRAMEWORK_OPTIONS: Record<string, { value: string; label: string }[]> = {
  python:     [{ value: 'auto', label: 'Auto (pytest)' }, { value: 'pytest', label: 'pytest' }, { value: 'unittest', label: 'unittest' }],
  javascript: [{ value: 'auto', label: 'Auto (Jest)' }, { value: 'jest', label: 'Jest' }, { value: 'vitest', label: 'Vitest' }],
  typescript: [{ value: 'auto', label: 'Auto (Jest)' }, { value: 'jest', label: 'Jest' }, { value: 'vitest', label: 'Vitest' }],
  java:       [{ value: 'auto', label: 'Auto (JUnit 5)' }, { value: 'junit', label: 'JUnit 5' }],
  go:         [{ value: 'auto', label: 'Auto (go test)' }, { value: 'gotest', label: 'go test' }],
};

const COVERAGE_OPTIONS = [
  { value: 'basic', label: 'Basic — happy path only' },
  { value: 'medium', label: 'Medium — + edge cases' },
  { value: 'high', label: 'High — full branch coverage' },
];

const PLACEHOLDER = `def calculate_discount(price: float, discount_pct: float) -> float:
    if price < 0:
        raise ValueError("Price cannot be negative")
    if not 0 <= discount_pct <= 100:
        raise ValueError("Discount must be between 0-100%")
    return price * (1 - discount_pct / 100)`;

export function TestGeneratorPage() {
  const [code, setCode] = useState('');
  const [language, setLanguage] = useState('python');
  const [framework, setFramework] = useState('auto');
  const [coverage, setCoverage] = useState('high');
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<{
    test_code: string;
    framework: string;
    estimated_test_count: number;
  } | null>(null);

  const frameworkOptions = FRAMEWORK_OPTIONS[language] ?? [{ value: 'auto', label: 'Auto' }];

  const handleGenerate = async () => {
    if (!code.trim()) { toast.error('Paste some code first'); return; }
    setLoading(true);
    try {
      const res = await generatorService.generateTests(code, language, framework, coverage);
      setResult(res);
      toast.success(`Generated ~${res.estimated_test_count} test cases`);
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
          onChange={(v) => { setLanguage(v); setFramework('auto'); }}
          options={LANGUAGE_OPTIONS}
        />
        <GenSelect
          label="Framework"
          value={framework}
          onChange={setFramework}
          options={frameworkOptions}
        />
      </div>
      <GenSelect
        label="Coverage Level"
        value={coverage}
        onChange={setCoverage}
        options={COVERAGE_OPTIONS}
      />
      <div>
        <label className="text-xs font-medium text-text-muted uppercase tracking-wider mb-1.5 block">
          Code to Test
        </label>
        <CodeEditor value={code} onChange={setCode} placeholder={PLACEHOLDER} language={language} />
      </div>
    </div>
  );

  const extraOutput = result ? (
    <div className="flex items-center gap-3 mb-4">
      <div className="glass rounded-xl px-3 py-1.5 text-xs border border-brand-accent/20 text-brand-accent">
        ~{result.estimated_test_count} test cases · {result.framework}
      </div>
    </div>
  ) : null;

  return (
    <GeneratorWorkspace
      title="Unit Test Generator"
      description="Generate comprehensive test suites for your code automatically"
      icon={<TestTube2 size={20} />}
      accentColor="text-brand-accent"
      inputPanel={inputPanel}
      outputContent={result?.test_code ?? null}
      outputLanguage={language}
      loading={loading}
      onGenerate={handleGenerate}
      generateLabel="Generate Tests"
      extraOutput={extraOutput}
    />
  );
}
