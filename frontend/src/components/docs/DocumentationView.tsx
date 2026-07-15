import { useState, useEffect } from 'react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import { repositoryService } from '../../services/repositoryService';
import { Loader2, BookOpen, Copy, Check, Download } from 'lucide-react';
import toast from 'react-hot-toast';

type DocType = 'readme' | 'api' | 'onboarding';

export function DocumentationView({ repoId }: { repoId: string }) {
  const [activeTab, setActiveTab] = useState<DocType>('readme');
  const [docs, setDocs] = useState<Record<DocType, string | null>>({
    readme: null,
    api: null,
    onboarding: null,
  });
  const [loading, setLoading] = useState(false);
  const [copied, setCopied] = useState(false);

  useEffect(() => {
    let mounted = true;
    const fetchDoc = async () => {
      if (docs[activeTab]) return; // Already cached
      
      setLoading(true);
      try {
        let res: DocumentationResponse;
        if (activeTab === 'readme') res = await repositoryService.getReadme(repoId);
        else if (activeTab === 'api') res = await repositoryService.getApiDocs(repoId);
        else res = await repositoryService.getOnboarding(repoId);
        
        if (mounted) {
          setDocs(prev => ({ ...prev, [activeTab]: res.content }));
        }
      } catch (error) {
        if (mounted) {
          setDocs(prev => ({ ...prev, [activeTab]: '# Failed to load documentation.' }));
        }
      } finally {
        if (mounted) setLoading(false);
      }
    };

    fetchDoc();
    return () => { mounted = false; };
  }, [repoId, activeTab, docs]);

  const handleCopy = () => {
    const content = docs[activeTab];
    if (content) {
      navigator.clipboard.writeText(content);
      setCopied(true);
      toast.success('Copied to clipboard');
      setTimeout(() => setCopied(false), 2000);
    }
  };

  const handleDownload = () => {
    const content = docs[activeTab];
    if (!content) return;
    const filenames: Record<DocType, string> = {
      readme: 'README.md',
      api: 'API_REFERENCE.md',
      onboarding: 'ONBOARDING.md',
    };
    const blob = new Blob([content], { type: 'text/markdown' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = filenames[activeTab];
    a.click();
    URL.revokeObjectURL(url);
    toast.success(`Downloaded ${filenames[activeTab]}`);
  };

  return (
    <div className="flex flex-col h-[calc(100vh-80px)] md:h-[calc(100vh-140px)] p-4 md:p-6 pb-12 w-full max-w-6xl mx-auto">
      {/* Doc Tabs */}
      <div className="flex gap-2 mb-4 border-b border-white/[0.06] pb-4">
        {[
          { id: 'readme', label: 'README.md' },
          { id: 'api', label: 'API Reference' },
          { id: 'onboarding', label: 'Onboarding Guide' }
        ].map(tab => (
          <button
            key={tab.id}
            onClick={() => setActiveTab(tab.id as DocType)}
            className={`px-4 py-2 rounded-lg text-sm font-medium transition-all ${
              activeTab === tab.id 
                ? 'bg-brand-primary/20 text-brand-glow border border-brand-primary/30' 
                : 'text-text-secondary hover:bg-surface border border-transparent'
            }`}
          >
            {tab.label}
          </button>
        ))}
        
        <div className="flex-1" />
        
        <div className="flex gap-2">
          <button
            onClick={handleCopy}
            disabled={!docs[activeTab] || loading}
            className="flex items-center gap-2 px-3 py-1.5 rounded-lg bg-surface hover:bg-white/[0.1] text-text-primary text-sm transition-colors border border-white/[0.08] disabled:opacity-50"
          >
            {copied ? <Check size={14} className="text-green-400" /> : <Copy size={14} />}
            <span className="hidden sm:inline">{copied ? 'Copied' : 'Copy'}</span>
          </button>
          <button
            onClick={handleDownload}
            disabled={!docs[activeTab] || loading}
            className="flex items-center gap-2 px-3 py-1.5 rounded-lg bg-surface hover:bg-white/[0.1] text-text-primary text-sm transition-colors border border-white/[0.08] disabled:opacity-50"
          >
            <Download size={14} />
            <span className="hidden sm:inline">Download</span>
          </button>
        </div>
      </div>

      {/* Doc Content */}
      <div className="flex-1 overflow-y-auto glass-strong rounded-2xl border-glow p-6 md:p-10 scrollbar-hide">
        {loading ? (
          <div className="h-full flex flex-col items-center justify-center text-brand-primary opacity-70">
            <Loader2 size={40} className="animate-spin mb-4" />
            <p>Generating documentation...</p>
          </div>
        ) : !docs[activeTab] ? (
          <div className="h-full flex flex-col items-center justify-center text-text-muted">
            <BookOpen size={48} className="mb-4 opacity-30" />
            <p>No content generated</p>
          </div>
        ) : (
          <div className="markdown-content max-w-4xl mx-auto">
            <ReactMarkdown remarkPlugins={[remarkGfm]}>
              {docs[activeTab]!}
            </ReactMarkdown>
          </div>
        )}
      </div>
    </div>
  );
}
