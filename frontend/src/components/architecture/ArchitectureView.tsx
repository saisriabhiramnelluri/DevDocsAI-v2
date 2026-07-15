import { useEffect, useState } from 'react';
import { repositoryService } from '../../services/repositoryService';
import { MermaidDiagram } from './MermaidDiagram';
import type { DependencyGraph } from '../../types/repository';
import { Loader2, FileCode2, Copy, Check, Download } from 'lucide-react';
import toast from 'react-hot-toast';

export function ArchitectureView({ repoId }: { repoId: string }) {
  const [graph, setGraph] = useState<DependencyGraph | null>(null);
  const [loading, setLoading] = useState(true);
  const [copied, setCopied] = useState(false);

  useEffect(() => {
    let mounted = true;
    const fetchGraph = async () => {
      try {
        const data = await repositoryService.getDependencyGraph(repoId);
        if (mounted) { setGraph(data); setLoading(false); }
      } catch (err) {
        if (mounted) setLoading(false);
      }
    };
    fetchGraph();
    return () => { mounted = false; };
  }, [repoId]);

  const handleCopyMermaid = () => {
    if (!graph?.mermaid) return;
    navigator.clipboard.writeText(graph.mermaid);
    setCopied(true);
    toast.success('Mermaid syntax copied');
    setTimeout(() => setCopied(false), 2000);
  };

  const handleDownloadMermaid = () => {
    if (!graph?.mermaid) return;
    const blob = new Blob([graph.mermaid], { type: 'text/plain' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = 'architecture.mmd';
    a.click();
    URL.revokeObjectURL(url);
    toast.success('Downloaded architecture.mmd');
  };

  if (loading) {
    return (
      <div className="h-full flex items-center justify-center">
        <Loader2 size={32} className="animate-spin text-brand-primary" />
      </div>
    );
  }

  if (!graph) {
    return <div className="p-8 text-center text-text-muted">Failed to load architecture data.</div>;
  }

  return (
    <div className="flex flex-col lg:flex-row h-[calc(100vh-80px)] md:h-[calc(100vh-140px)] w-full gap-4 p-4 md:p-6 pb-12">
      <div className="flex-1 glass-strong rounded-2xl border-glow flex flex-col p-4">
        <div className="flex items-center justify-between mb-4 px-2">
          <h3 className="text-lg font-bold">Dependency Graph</h3>
          <div className="flex gap-2">
            <button
              onClick={handleCopyMermaid}
              className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-surface hover:bg-white/[0.1] text-text-primary text-xs transition-colors border border-white/[0.08]"
            >
              {copied ? <Check size={13} className="text-green-400" /> : <Copy size={13} />}
              {copied ? 'Copied' : 'Copy Mermaid'}
            </button>
            <button
              onClick={handleDownloadMermaid}
              className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-surface hover:bg-white/[0.1] text-text-primary text-xs transition-colors border border-white/[0.08]"
            >
              <Download size={13} />
              .mmd
            </button>
          </div>
        </div>
        <div className="flex-1 min-h-[400px]">
          <MermaidDiagram chart={graph.mermaid} />
        </div>
      </div>
      
      <div className="w-full lg:w-80 flex flex-col gap-4">
        <div className="glass rounded-2xl p-5 border border-white/[0.08] flex-1 overflow-y-auto">
          <h3 className="text-sm font-bold text-text-muted uppercase tracking-wider mb-4">Key Components</h3>
          <div className="space-y-2">
            {graph.nodes.slice(0, 20).map(node => (
              <div key={node.id} className="flex items-center gap-2 p-2 rounded bg-surface border border-white/[0.05]">
                <FileCode2 size={14} className="text-brand-accent flex-shrink-0" />
                <span className="text-xs font-mono text-text-secondary truncate">{node.name}</span>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}
