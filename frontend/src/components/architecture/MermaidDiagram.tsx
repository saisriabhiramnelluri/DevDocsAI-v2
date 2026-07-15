import { useEffect, useState, useRef } from 'react';
import mermaid from 'mermaid';
import { Loader2, ZoomIn, ZoomOut, RefreshCw } from 'lucide-react';

mermaid.initialize({
  startOnLoad: true,
  theme: 'dark',
  securityLevel: 'loose',
  fontFamily: 'JetBrains Mono',
  themeVariables: {
    primaryColor: '#6366F1',
    primaryTextColor: '#E2E8F0',
    primaryBorderColor: '#8B5CF6',
    lineColor: '#94A3B8',
    secondaryColor: '#06B6D4',
    tertiaryColor: '#0a0f1e',
  }
});

export function MermaidDiagram({ chart }: { chart: string }) {
  const containerRef = useRef<HTMLDivElement>(null);
  const [svg, setSvg] = useState<string>('');
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [scale, setScale] = useState(1);

  useEffect(() => {
    let mounted = true;

    const renderDiagram = async () => {
      setLoading(true);
      setError(null);
      try {
        const id = `mermaid-${Date.now()}`;
        const { svg: svgCode } = await mermaid.render(id, chart);
        if (mounted) {
          setSvg(svgCode);
          setLoading(false);
        }
      } catch (err: any) {
        if (mounted) {
          setError(err.message || 'Failed to render diagram');
          setLoading(false);
        }
      }
    };

    if (chart) {
      renderDiagram();
    }

    return () => { mounted = false; };
  }, [chart]);

  if (loading) {
    return (
      <div className="w-full h-64 flex items-center justify-center">
        <Loader2 size={32} className="animate-spin text-brand-primary" />
      </div>
    );
  }

  if (error) {
    return (
      <div className="w-full p-4 glass border border-red-500/30 rounded-xl text-red-400 font-mono text-xs overflow-auto">
        <p className="mb-2 font-bold text-red-500">Mermaid Render Error:</p>
        <pre>{error}</pre>
        <p className="mt-4 font-bold text-red-500">Raw Data:</p>
        <pre className="text-text-muted">{chart}</pre>
      </div>
    );
  }

  return (
    <div className="relative w-full h-full min-h-[400px] flex flex-col">
      <div className="absolute top-4 right-4 z-10 flex gap-2 glass rounded-lg p-1 border border-white/[0.08]">
        <button onClick={() => setScale(s => Math.min(s + 0.2, 3))} className="p-1.5 hover:bg-surface rounded text-text-muted hover:text-white transition-colors">
          <ZoomIn size={16} />
        </button>
        <button onClick={() => setScale(s => Math.max(s - 0.2, 0.2))} className="p-1.5 hover:bg-surface rounded text-text-muted hover:text-white transition-colors">
          <ZoomOut size={16} />
        </button>
        <button onClick={() => setScale(1)} className="p-1.5 hover:bg-surface rounded text-text-muted hover:text-white transition-colors">
          <RefreshCw size={16} />
        </button>
      </div>
      
      <div 
        className="flex-1 overflow-auto rounded-xl border border-white/[0.06] bg-black/20 flex items-center justify-center p-8 cursor-grab active:cursor-grabbing"
      >
        <div 
          ref={containerRef}
          dangerouslySetInnerHTML={{ __html: svg }} 
          className="transition-transform duration-200 origin-center [&>svg]:max-w-none"
          style={{ transform: `scale(${scale})` }}
        />
      </div>
    </div>
  );
}
