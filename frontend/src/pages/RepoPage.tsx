import { useEffect, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { useAppStore } from '../store/appStore';
import { repositoryService } from '../services/repositoryService';
import { useStatusPoller } from '../components/repository/StatusPoller';
import { GitBranch, Activity, Layout, MessageSquare, Network, FileText, Loader2, AlertCircle } from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';

// Subcomponents to be implemented
import { ChatInterface } from '../components/chat/ChatInterface';
import { ArchitectureView } from '../components/architecture/ArchitectureView';
import { DocumentationView } from '../components/docs/DocumentationView';
import { FileExplorer } from '../components/files/FileExplorer';
import type { Repository } from '../types/repository';

type Tab = 'overview' | 'chat' | 'architecture' | 'docs' | 'files';

export function RepoPage() {
  const { repoId } = useParams();
  const navigate = useNavigate();
  const { repositories, updateRepository } = useAppStore((state: any) => state);
  const [activeTab, setActiveTab] = useState<Tab>('chat');
  const [loading, setLoading] = useState(true);
  const [graphData, setGraphData] = useState<any>(null);

  // Use our custom poller hook
  useStatusPoller(repoId);

  const repo = repositories.find((r: any) => r.id === repoId);

  useEffect(() => {
    let mounted = true;
    
    const fetchFullRepo = async () => {
      if (!repoId) return;
      try {
        const fullRepo = await repositoryService.getById(repoId);
        if (mounted) {
          updateRepository(repoId, fullRepo);
          setLoading(false);
        }
      } catch (err) {
        if (mounted) {
          setLoading(false);
        }
      }
    };

    const fetchGraph = async () => {
      if (!repoId) return;
      try {
        const data = await repositoryService.getDependencyGraph(repoId);
        if (mounted) setGraphData(data);
      } catch (err) {
        console.error("Failed to fetch graph for file explorer", err);
      }
    };

    if (!repo) {
      fetchFullRepo();
    } else {
      setLoading(false);
    }
    fetchGraph();

    return () => { mounted = false; };
  }, [repoId, repo, updateRepository]);

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <Loader2 size={32} className="animate-spin text-brand-primary" />
      </div>
    );
  }

  if (!repo) {
    return (
      <div className="min-h-screen pt-24 px-4 flex flex-col items-center">
        <AlertCircle size={48} className="text-red-400 mb-4" />
        <h2 className="text-xl font-bold mb-2">Repository Not Found</h2>
        <button onClick={() => navigate('/dashboard')} className="btn-brand px-4 py-2 rounded-lg">
          Back to Dashboard
        </button>
      </div>
    );
  }

  const isProcessing = !['ready', 'failed'].includes(repo.status);
  const isReady = repo.status === 'ready';

  return (
    <div className="min-h-screen pt-20 pb-0 flex flex-col h-screen overflow-hidden">
      {/* Header */}
      <header className="flex-shrink-0 border-b border-white/[0.06] bg-background/80 backdrop-blur-xl z-10 px-4 md:px-8 py-4">
        <div className="max-w-7xl mx-auto flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div>
            <div className="flex items-center gap-2 mb-1">
              <GitBranch size={20} className="text-brand-primary" />
              <h1 className="text-xl font-bold text-white">
                {repo.repo_name || repo.repo_url.split('/').pop()}
              </h1>
              <span className={`px-2 py-0.5 rounded text-[10px] font-bold uppercase tracking-wider ${
                isReady ? 'bg-green-500/20 text-green-400' : 
                repo.status === 'failed' ? 'bg-red-500/20 text-red-400' : 
                'bg-brand-primary/20 text-brand-primary'
              }`}>
                {repo.status}
              </span>
            </div>
            <p className="text-xs font-mono text-text-muted">{repo.repo_url}</p>
          </div>

          {/* Tabs */}
          {isReady && (
            <div className="flex bg-surface p-1 rounded-xl">
              <TabButton active={activeTab === 'overview'} onClick={() => setActiveTab('overview')} icon={Layout} label="Overview" />
              <TabButton active={activeTab === 'files'} onClick={() => setActiveTab('files')} icon={FileText} label="Files" />
              <TabButton active={activeTab === 'chat'} onClick={() => setActiveTab('chat')} icon={MessageSquare} label="Chat" />
              <TabButton active={activeTab === 'architecture'} onClick={() => setActiveTab('architecture')} icon={Network} label="Architecture" />
              <TabButton active={activeTab === 'docs'} onClick={() => setActiveTab('docs')} icon={FileText} label="Docs" />
            </div>
          )}
        </div>
      </header>

      {/* Main Content Area */}
      <main className="flex-1 overflow-y-auto relative bg-[#030509]">
        <div className="max-w-7xl mx-auto h-full">
          {isProcessing && (
            <div className="absolute inset-0 flex flex-col items-center justify-center p-6">
              <div className="glass-strong rounded-3xl p-8 max-w-md w-full border-glow text-center">
                <Loader2 size={40} className="animate-spin text-brand-primary mx-auto mb-6" />
                <h3 className="text-xl font-bold mb-2">Analyzing Repository</h3>
                <p className="text-text-secondary mb-6 text-sm">
                  {repo.current_stage || 'Preparing analysis pipeline...'}
                </p>
                <div className="w-full bg-surface rounded-full h-2 mb-2 overflow-hidden">
                  <div 
                    className="bg-brand-primary h-full transition-all duration-500 ease-out shadow-glow"
                    style={{ width: `${repo.progress}%` }}
                  />
                </div>
                <div className="flex justify-between text-xs font-mono text-text-muted">
                  <span>{repo.progress}%</span>
                  <span>100%</span>
                </div>
              </div>
            </div>
          )}

          {repo.status === 'failed' && (
            <div className="absolute inset-0 flex flex-col items-center justify-center p-6">
              <div className="glass-strong rounded-3xl p-8 max-w-md w-full border border-red-500/30 text-center">
                <AlertCircle size={40} className="text-red-400 mx-auto mb-4" />
                <h3 className="text-xl font-bold mb-2 text-white">Analysis Failed</h3>
                <p className="text-red-300 text-sm mb-6 bg-red-500/10 p-3 rounded-lg font-mono">
                  {repo.error_message || 'An unknown error occurred during analysis.'}
                </p>
                <button onClick={() => navigate('/dashboard')} className="btn-outline px-6 py-2 rounded-xl text-sm">
                  Return to Dashboard
                </button>
              </div>
            </div>
          )}

          {isReady && (
            <AnimatePresence mode="wait">
              <motion.div
                key={activeTab}
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -10 }}
                transition={{ duration: 0.2 }}
                className="h-full w-full"
              >
                {activeTab === 'overview' && <OverviewTab repo={repo} />}
                {activeTab === 'files' && graphData && <FileExplorer graph={graphData} />}
                {activeTab === 'chat' && <ChatInterface repoId={repo.id} />}
                {activeTab === 'architecture' && <ArchitectureView repoId={repo.id} />}
                {activeTab === 'docs' && <DocumentationView repoId={repo.id} />}
              </motion.div>
            </AnimatePresence>
          )}
        </div>
      </main>
    </div>
  );
}

function TabButton({ active, onClick, icon: Icon, label }: any) {
  return (
    <button
      onClick={onClick}
      className={`flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium transition-all ${
        active 
          ? 'bg-brand-primary text-white shadow-glow-sm' 
          : 'text-text-secondary hover:text-text-primary hover:bg-white/[0.05]'
      }`}
    >
      <Icon size={16} />
      <span className="hidden sm:inline">{label}</span>
    </button>
  );
}

function OverviewTab({ repo }: { repo: Repository }) {
  const meta = repo.metadata_;
  if (!meta) return <div className="p-8">No metadata available.</div>;

  const languages = meta.languages_detected ? JSON.parse(meta.languages_detected) : {};

  return (
    <div className="p-4 md:p-8 space-y-6">
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <StatCard icon={Activity} label="Total Files" value={meta.total_files} color="text-brand-primary" />
        <StatCard icon={Layout} label="Total Lines" value={meta.total_lines} color="text-brand-accent" />
        <StatCard icon={Network} label="Classes" value={meta.total_classes} color="text-brand-secondary" />
        <StatCard icon={GitBranch} label="Functions" value={meta.total_functions} color="text-green-400" />
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-2 glass-strong rounded-2xl p-6 border-glow">
          <h3 className="text-lg font-bold mb-4">Repository Summary</h3>
          <div className="prose prose-invert max-w-none text-text-secondary whitespace-pre-wrap font-mono text-sm">
            {meta.summary}
          </div>
        </div>

        <div className="space-y-6">
          <div className="glass rounded-2xl p-6 border border-white/[0.08]">
            <h3 className="text-sm font-bold text-text-muted uppercase tracking-wider mb-4">Language Breakdown</h3>
            <div className="space-y-3">
              {Object.entries(languages).slice(0, 5).map(([lang, count]: any) => (
                <div key={lang} className="flex items-center justify-between">
                  <span className="text-sm font-medium">{lang}</span>
                  <span className="text-xs text-text-muted font-mono">{count} files</span>
                </div>
              ))}
            </div>
          </div>
          
          <div className="glass rounded-2xl p-6 border border-white/[0.08]">
            <h3 className="text-sm font-bold text-text-muted uppercase tracking-wider mb-4">Architecture</h3>
            <div className="space-y-2">
              <div className="flex justify-between">
                <span className="text-sm text-text-secondary">Framework</span>
                <span className="text-sm font-medium">{meta.framework || 'Unknown'}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-sm text-text-secondary">Pattern</span>
                <span className="text-sm font-medium">{meta.architecture_type || 'Unknown'}</span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

function StatCard({ icon: Icon, label, value, color }: any) {
  return (
    <div className="glass rounded-2xl p-5 border border-white/[0.08] flex items-center gap-4">
      <div className={`p-3 rounded-xl bg-surface ${color}`}>
        <Icon size={24} />
      </div>
      <div>
        <p className="text-xs font-bold text-text-muted uppercase tracking-wider mb-1">{label}</p>
        <p className="text-2xl font-display font-bold">{value}</p>
      </div>
    </div>
  );
}
