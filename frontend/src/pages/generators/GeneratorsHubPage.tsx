// DevDocsAI — Generators Hub Page
// Grid landing for all AI generator tools
import { motion } from 'framer-motion';
import { useNavigate } from 'react-router-dom';
import {
  MessageSquareCode, TestTube2, GitFork, ArrowLeftRight, Zap,
  BookOpen, GitCommit, Network, FileCode2, Sparkles,
} from 'lucide-react';

interface GeneratorCard {
  id: string;
  icon: any;
  title: string;
  description: string;
  route: string;
  color: string;
  glow: string;
  badge: 'available' | 'coming-soon';
  category: 'basic' | 'advanced';
}

const GENERATORS: GeneratorCard[] = [
  // ── Basic ─────────────────────────────────────────────────────────────────
  {
    id: 'comment',
    icon: MessageSquareCode,
    title: 'DocBlock Generator',
    description: 'Add docstrings and inline comments to any source file automatically.',
    route: '/generators/comment',
    color: 'text-brand-primary',
    glow: 'hover:border-brand-primary/40 hover:shadow-[0_0_24px_rgba(139,92,246,0.15)]',
    badge: 'available',
    category: 'basic',
  },
  {
    id: 'test',
    icon: TestTube2,
    title: 'Test Generator',
    description: 'Generate comprehensive unit tests with pytest, Jest, JUnit and more.',
    route: '/generators/test',
    color: 'text-brand-accent',
    glow: 'hover:border-brand-accent/40 hover:shadow-[0_0_24px_rgba(192,132,252,0.15)]',
    badge: 'available',
    category: 'basic',
  },
  {
    id: 'uml',
    icon: GitFork,
    title: 'UML Diagram Generator',
    description: 'Class, sequence, and component diagrams as Mermaid syntax from code or repos.',
    route: '/generators/uml',
    color: 'text-brand-secondary',
    glow: 'hover:border-brand-secondary/40 hover:shadow-[0_0_24px_rgba(34,211,238,0.15)]',
    badge: 'available',
    category: 'basic',
  },
  {
    id: 'convert',
    icon: ArrowLeftRight,
    title: 'Language Converter',
    description: 'Convert code between Python, TypeScript, Go, Java, Rust and more.',
    route: '/generators/convert',
    color: 'text-green-400',
    glow: 'hover:border-green-400/40 hover:shadow-[0_0_24px_rgba(74,222,128,0.15)]',
    badge: 'available',
    category: 'basic',
  },
  {
    id: 'optimize',
    icon: Zap,
    title: 'Code Optimizer',
    description: 'Refactor and improve code quality — performance, readability, security.',
    route: '/generators/optimize',
    color: 'text-yellow-400',
    glow: 'hover:border-yellow-400/40 hover:shadow-[0_0_24px_rgba(250,204,21,0.15)]',
    badge: 'available',
    category: 'basic',
  },
  {
    id: 'swagger',
    icon: FileCode2,
    title: 'Swagger / API Docs',
    description: 'Generate human-readable API documentation from OpenAPI/Swagger specs.',
    route: '/generators/swagger',
    color: 'text-orange-400',
    glow: 'hover:border-orange-400/40 hover:shadow-[0_0_24px_rgba(251,146,60,0.15)]',
    badge: 'available',
    category: 'basic',
  },
  // ── Advanced ──────────────────────────────────────────────────────────────
  {
    id: 'readme',
    icon: BookOpen,
    title: 'Codebase Docs',
    description: 'Full README, API reference, and onboarding guide from your analyzed repo.',
    route: '/dashboard',
    color: 'text-blue-400',
    glow: 'hover:border-blue-400/40 hover:shadow-[0_0_24px_rgba(96,165,250,0.15)]',
    badge: 'available',
    category: 'advanced',
  },
  {
    id: 'release',
    icon: GitCommit,
    title: 'Release Notes',
    description: 'Automatically generate changelogs from Git commit history.',
    route: '/generators/release-notes',
    color: 'text-purple-400',
    glow: 'hover:border-purple-400/40 hover:shadow-[0_0_24px_rgba(192,132,252,0.15)]',
    badge: 'available',
    category: 'advanced',
  },
  {
    id: 'custom',
    icon: Sparkles,
    title: 'Custom Prompts',
    description: 'Create and save reusable AI prompt templates for your workflow.',
    route: '#',
    color: 'text-pink-400',
    glow: '',
    badge: 'coming-soon',
    category: 'advanced',
  },
];

const container = { hidden: {}, show: { transition: { staggerChildren: 0.07 } } };
const item = { hidden: { opacity: 0, y: 20 }, show: { opacity: 1, y: 0, transition: { duration: 0.35 } } };

export function GeneratorsHubPage() {
  const navigate = useNavigate();
  const basicGens = GENERATORS.filter((g) => g.category === 'basic');
  const advancedGens = GENERATORS.filter((g) => g.category === 'advanced');

  const handleCard = (gen: GeneratorCard) => {
    if (gen.badge === 'coming-soon') return;
    navigate(gen.route);
  };

  return (
    <div className="min-h-screen pt-24 pb-16 px-4 md:px-8">
      <div className="max-w-6xl mx-auto">
        {/* Header */}
        <motion.div
          initial={{ opacity: 0, y: 16 }}
          animate={{ opacity: 1, y: 0 }}
          className="text-center mb-14"
        >
          <div className="inline-flex items-center gap-2 px-3 py-1.5 rounded-full glass-strong border border-brand-primary/30 mb-6">
            <Sparkles size={13} className="text-brand-primary" />
            <span className="text-xs font-medium text-text-primary">AI-Powered Tools</span>
          </div>
          <h1 className="text-4xl md:text-5xl font-display font-bold mb-4">
            AI <span className="gradient-text">Generators</span>
          </h1>
          <p className="text-text-secondary max-w-xl mx-auto text-base">
            Standalone AI tools that work on any code — paste a snippet and get instant results.
            No repository analysis required.
          </p>
        </motion.div>

        {/* Basic Generators */}
        <div className="mb-12">
          <h2 className="text-xs font-bold uppercase tracking-widest text-text-muted mb-6 flex items-center gap-3">
            <span>📝 Basic Generators</span>
            <div className="flex-1 h-px bg-white/[0.06]" />
          </h2>
          <motion.div
            variants={container}
            initial="hidden"
            animate="show"
            className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-5"
          >
            {basicGens.map((gen) => (
              <GenCard key={gen.id} gen={gen} onClick={() => handleCard(gen)} />
            ))}
          </motion.div>
        </div>

        {/* Advanced Generators */}
        <div>
          <h2 className="text-xs font-bold uppercase tracking-widest text-text-muted mb-6 flex items-center gap-3">
            <span>🚀 Advanced Generators</span>
            <div className="flex-1 h-px bg-white/[0.06]" />
          </h2>
          <motion.div
            variants={container}
            initial="hidden"
            animate="show"
            className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-5"
          >
            {advancedGens.map((gen) => (
              <GenCard key={gen.id} gen={gen} onClick={() => handleCard(gen)} />
            ))}
          </motion.div>
        </div>
      </div>
    </div>
  );
}

function GenCard({ gen, onClick }: { gen: GeneratorCard; onClick: () => void }) {
  const Icon = gen.icon;
  const isAvailable = gen.badge === 'available';

  return (
    <motion.div
      variants={{ hidden: { opacity: 0, y: 20 }, show: { opacity: 1, y: 0 } }}
      onClick={onClick}
      className={`relative glass-strong rounded-2xl p-6 border transition-all duration-300 group
        ${isAvailable
          ? `cursor-pointer border-white/[0.08] ${gen.glow}`
          : 'cursor-not-allowed border-white/[0.04] opacity-55'
        }`}
    >
      {/* Available badge */}
      <div className="absolute top-4 right-4">
        {isAvailable ? (
          <span className="text-[10px] font-bold uppercase tracking-wider px-2 py-0.5 rounded-full bg-green-500/15 text-green-400 border border-green-500/25">
            Ready
          </span>
        ) : (
          <span className="text-[10px] font-bold uppercase tracking-wider px-2 py-0.5 rounded-full bg-white/5 text-text-muted border border-white/[0.06]">
            Soon
          </span>
        )}
      </div>

      {/* Icon */}
      <div className={`w-11 h-11 rounded-xl glass flex items-center justify-center mb-4 ${gen.color}
        transition-transform duration-300 group-hover:scale-110`}>
        <Icon size={22} />
      </div>

      {/* Content */}
      <h3 className="font-semibold text-text-primary mb-2 text-sm">{gen.title}</h3>
      <p className="text-xs text-text-secondary leading-relaxed">{gen.description}</p>

      {/* Hover arrow */}
      {isAvailable && (
        <div className={`mt-4 text-xs font-medium ${gen.color} opacity-0 group-hover:opacity-100 transition-opacity flex items-center gap-1`}>
          Open Generator →
        </div>
      )}
    </motion.div>
  );
}
