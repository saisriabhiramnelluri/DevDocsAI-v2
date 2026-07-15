// DevDocsAI — Landing Page (Module 3 — Investor Polish)
import { useRef } from 'react';
import { motion, useInView } from 'framer-motion';
import { useNavigate } from 'react-router-dom';
import {
  Code2, Network, MessageSquare, ArrowRight, Zap, Database,
  Globe, GitBranch, Brain, FileText, Sparkles, TestTube2,
  MessageSquareCode, CheckCircle2, Star, Users, Building,
} from 'lucide-react';
import { RepositoryInput } from '../components/repository/RepositoryInput';

// ── Animation helpers ──────────────────────────────────────────────────────
const fadeUp = {
  hidden: { opacity: 0, y: 32 },
  show: (delay = 0) => ({
    opacity: 1, y: 0,
    transition: { duration: 0.55, delay, ease: [0.22, 1, 0.36, 1] },
  }),
};

function FadeUp({ children, delay = 0, className = '' }: any) {
  const ref = useRef(null);
  const inView = useInView(ref, { once: true, margin: '-60px' });
  return (
    <motion.div
      ref={ref}
      variants={fadeUp}
      initial="hidden"
      animate={inView ? fadeUp.show(delay) : 'hidden'}
      className={className}
    >
      {children}
    </motion.div>
  );
}

// ── Data ───────────────────────────────────────────────────────────────────
const FEATURES = [
  {
    icon: MessageSquare,
    title: 'Chat with Your Codebase',
    description: 'Ask anything in natural language. Get answers with exact file paths, line numbers, and source citations.',
    color: 'text-brand-primary',
    glow: 'group-hover:shadow-[0_0_30px_rgba(99,102,241,0.2)]',
    bg: 'bg-brand-primary/10 border-brand-primary/20',
  },
  {
    icon: Network,
    title: 'Architecture Graphs',
    description: 'Auto-generated Mermaid dependency graphs. Understand how 200 files connect in 30 seconds.',
    color: 'text-brand-secondary',
    glow: 'group-hover:shadow-[0_0_30px_rgba(6,182,212,0.2)]',
    bg: 'bg-brand-secondary/10 border-brand-secondary/20',
  },
  {
    icon: Code2,
    title: 'Auto Documentation',
    description: 'One-click README, API reference, and onboarding guides that stay in sync with your code.',
    color: 'text-brand-accent',
    glow: 'group-hover:shadow-[0_0_30px_rgba(139,92,246,0.2)]',
    bg: 'bg-brand-accent/10 border-brand-accent/20',
  },
  {
    icon: MessageSquareCode,
    title: 'DocBlock Generator',
    description: 'Add Google-style, JSDoc, or Javadoc comments to any file. Works on Python, TS, Java, Go, Rust.',
    color: 'text-green-400',
    glow: 'group-hover:shadow-[0_0_30px_rgba(74,222,128,0.2)]',
    bg: 'bg-green-400/10 border-green-400/20',
  },
  {
    icon: TestTube2,
    title: 'Test Generator',
    description: 'Paste code, get a full test suite. pytest, Jest, JUnit — auto-detected for your language.',
    color: 'text-yellow-400',
    glow: 'group-hover:shadow-[0_0_30px_rgba(250,204,21,0.2)]',
    bg: 'bg-yellow-400/10 border-yellow-400/20',
  },
  {
    icon: Zap,
    title: 'Code Optimizer',
    description: 'AI refactoring with structured change reports: severity levels, line ranges, performance gains.',
    color: 'text-orange-400',
    glow: 'group-hover:shadow-[0_0_30px_rgba(251,146,60,0.2)]',
    bg: 'bg-orange-400/10 border-orange-400/20',
  },
];

const HOW_IT_WORKS = [
  {
    step: '01',
    title: 'Paste a GitHub URL',
    description: 'Any public repository. We handle the rest.',
    color: 'text-brand-primary',
  },
  {
    step: '02',
    title: 'We Analyze Everything',
    description: 'Clone → AST parse → knowledge graph → vector embeddings.',
    color: 'text-brand-accent',
  },
  {
    step: '03',
    title: 'Chat, Explore, Generate',
    description: 'Ask questions, view diagrams, generate docs — instantly.',
    color: 'text-brand-secondary',
  },
];

const TECH_STACK = [
  { icon: Database, label: 'ChromaDB Vectors' },
  { icon: Network, label: 'NetworkX Graphs' },
  { icon: Brain, label: 'BGE Embeddings' },
  { icon: Zap, label: 'Celery Pipelines' },
  { icon: Globe, label: 'DeepSeek V3 LLM' },
  { icon: GitBranch, label: 'Tree-sitter AST' },
];

const PRICING = [
  {
    name: 'Free',
    price: '$0',
    period: 'forever',
    description: 'Perfect for individual developers',
    features: [
      '5 repositories',
      'Chat with codebase',
      'Architecture diagrams',
      'Basic documentation',
      'All AI generators',
      'Community support',
    ],
    cta: 'Get Started Free',
    highlight: false,
    ctaStyle: 'btn-outline',
  },
  {
    name: 'Pro',
    price: '$19',
    period: 'per month',
    description: 'For professional developers',
    features: [
      'Unlimited repositories',
      'Priority AI processing',
      'Private repository support',
      'Full documentation suite',
      'Custom prompt templates',
      'API access',
      'Priority support',
    ],
    cta: 'Start Free Trial',
    highlight: true,
    ctaStyle: 'btn-brand',
  },
  {
    name: 'Enterprise',
    price: 'Custom',
    period: '',
    description: 'For teams and organizations',
    features: [
      'Everything in Pro',
      'Team workspaces',
      'SSO / SAML',
      'Dedicated instance',
      'SLA guarantee',
      'Custom integrations',
      'Dedicated support',
    ],
    cta: 'Contact Sales',
    highlight: false,
    ctaStyle: 'btn-outline',
  },
];

const STATS = [
  { value: '10+', label: 'Languages Supported' },
  { value: '8', label: 'AI Generators' },
  { value: '< 15min', label: 'Avg Analysis Time' },
  { value: '100%', label: 'Free to Start' },
];

// ── Component ──────────────────────────────────────────────────────────────
export function LandingPage() {
  const navigate = useNavigate();

  return (
    <div className="relative min-h-screen overflow-hidden">

      {/* ── HERO ─────────────────────────────────────────────────────────── */}
      <section className="relative pt-32 pb-20 px-4">
        {/* Background glows */}
        <div className="absolute top-0 left-1/4 w-[600px] h-[600px] bg-brand-primary/10 rounded-full blur-[140px] pointer-events-none -translate-x-1/2" />
        <div className="absolute top-20 right-1/4 w-[500px] h-[500px] bg-brand-accent/10 rounded-full blur-[140px] pointer-events-none translate-x-1/2" />

        <div className="relative z-10 container mx-auto flex flex-col items-center text-center max-w-4xl">
          {/* Badge */}
          <motion.div
            initial={{ opacity: 0, scale: 0.9 }}
            animate={{ opacity: 1, scale: 1 }}
            transition={{ duration: 0.4 }}
            className="inline-flex items-center gap-2 px-3 py-1.5 rounded-full glass-strong border border-brand-primary/30 mb-8"
          >
            <span className="flex h-2 w-2 relative">
              <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-brand-primary opacity-75" />
              <span className="relative inline-flex rounded-full h-2 w-2 bg-brand-primary" />
            </span>
            <span className="text-xs font-medium text-text-primary">Now in Beta · Free to use · No credit card</span>
          </motion.div>

          {/* Headline */}
          <motion.h1
            initial={{ opacity: 0, y: 24 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6, delay: 0.1 }}
            className="text-5xl md:text-7xl font-display font-bold tracking-tight mb-6 leading-[1.05]"
          >
            Understand any codebase
            <br />
            <span className="gradient-text">instantly with AI</span>
          </motion.h1>

          {/* Subtext */}
          <motion.p
            initial={{ opacity: 0, y: 16 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6, delay: 0.2 }}
            className="text-lg md:text-xl text-text-secondary mb-10 max-w-2xl leading-relaxed"
          >
            Paste a GitHub URL. We clone, parse, build a knowledge graph, and embed every function.
            You get instant chat, architecture diagrams, and AI-generated docs — in one platform.
          </motion.p>

          {/* CTA */}
          <motion.div
            initial={{ opacity: 0, y: 16 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6, delay: 0.3 }}
            className="flex flex-col items-center gap-4 w-full max-w-xl"
          >
            <RepositoryInput />
            <div className="flex items-center gap-4 text-xs text-text-muted">
              <span className="flex items-center gap-1.5"><CheckCircle2 size={13} className="text-green-400" /> Free forever</span>
              <span className="flex items-center gap-1.5"><CheckCircle2 size={13} className="text-green-400" /> No setup required</span>
              <span className="flex items-center gap-1.5"><CheckCircle2 size={13} className="text-green-400" /> Any public repo</span>
            </div>
          </motion.div>

          {/* Generators pill */}
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ delay: 0.55 }}
            className="mt-6"
          >
            <button
              onClick={() => navigate('/generators')}
              className="inline-flex items-center gap-2 text-sm text-text-muted hover:text-brand-accent transition-colors"
            >
              <Sparkles size={14} className="text-brand-accent" />
              Try AI Generators — DocBlocks, Tests, UML, and more
              <ArrowRight size={13} />
            </button>
          </motion.div>
        </div>
      </section>

      {/* ── STATS STRIP ──────────────────────────────────────────────────── */}
      <FadeUp className="container mx-auto px-4 mb-20">
        <div className="max-w-4xl mx-auto grid grid-cols-2 md:grid-cols-4 gap-px bg-white/[0.04] rounded-2xl overflow-hidden border border-white/[0.06]">
          {STATS.map((s, i) => (
            <div key={i} className="bg-surface/60 px-6 py-5 text-center">
              <div className="text-2xl md:text-3xl font-display font-bold gradient-text">{s.value}</div>
              <div className="text-xs text-text-muted mt-1">{s.label}</div>
            </div>
          ))}
        </div>
      </FadeUp>

      {/* ── FEATURES GRID ────────────────────────────────────────────────── */}
      <section className="container mx-auto px-4 mb-28">
        <FadeUp className="text-center mb-12">
          <p className="text-xs font-bold uppercase tracking-widest text-text-muted mb-3">Everything you need</p>
          <h2 className="text-3xl md:text-4xl font-display font-bold">
            One platform. Every tool.
          </h2>
        </FadeUp>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5 max-w-6xl mx-auto">
          {FEATURES.map((f, i) => {
            const Icon = f.icon;
            return (
              <FadeUp key={i} delay={i * 0.07}>
                <div className={`group glass-strong rounded-2xl p-6 border transition-all duration-300 cursor-default ${f.glow} border-white/[0.08]`}>
                  <div className={`w-11 h-11 rounded-xl border flex items-center justify-center mb-4 ${f.bg} ${f.color} transition-transform duration-300 group-hover:scale-110`}>
                    <Icon size={22} />
                  </div>
                  <h3 className="font-semibold text-text-primary mb-2">{f.title}</h3>
                  <p className="text-sm text-text-secondary leading-relaxed">{f.description}</p>
                </div>
              </FadeUp>
            );
          })}
        </div>
      </section>

      {/* ── HOW IT WORKS ─────────────────────────────────────────────────── */}
      <section className="container mx-auto px-4 mb-28">
        <FadeUp className="text-center mb-12">
          <p className="text-xs font-bold uppercase tracking-widest text-text-muted mb-3">Simple as 1-2-3</p>
          <h2 className="text-3xl md:text-4xl font-display font-bold">How it works</h2>
        </FadeUp>

        <div className="max-w-4xl mx-auto relative">
          {/* Connector line */}
          <div className="hidden md:block absolute top-10 left-[16.5%] right-[16.5%] h-px bg-gradient-to-r from-brand-primary/30 via-brand-accent/50 to-brand-secondary/30" />

          <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
            {HOW_IT_WORKS.map((step, i) => (
              <FadeUp key={i} delay={i * 0.12}>
                <div className="flex flex-col items-center text-center">
                  <div className={`w-20 h-20 rounded-2xl glass-strong border border-white/[0.1] flex flex-col items-center justify-center mb-5 ${step.color}`}>
                    <span className="text-xs font-mono font-bold opacity-60">{step.step}</span>
                    <span className="text-xl font-display font-bold">{i === 0 ? '🔗' : i === 1 ? '⚙️' : '✨'}</span>
                  </div>
                  <h3 className="font-semibold text-text-primary mb-2">{step.title}</h3>
                  <p className="text-sm text-text-secondary">{step.description}</p>
                </div>
              </FadeUp>
            ))}
          </div>
        </div>
      </section>

      {/* ── PRICING ──────────────────────────────────────────────────────── */}
      <section className="container mx-auto px-4 mb-28" id="pricing">
        <FadeUp className="text-center mb-12">
          <p className="text-xs font-bold uppercase tracking-widest text-text-muted mb-3">Simple pricing</p>
          <h2 className="text-3xl md:text-4xl font-display font-bold mb-4">
            Start free. <span className="gradient-text">Scale as you grow.</span>
          </h2>
          <p className="text-text-secondary max-w-lg mx-auto text-sm">
            No credit card required to start. Upgrade when you're ready.
          </p>
        </FadeUp>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 max-w-5xl mx-auto">
          {PRICING.map((plan, i) => (
            <FadeUp key={i} delay={i * 0.1}>
              <div className={`relative rounded-2xl p-7 flex flex-col h-full transition-all duration-300
                ${plan.highlight
                  ? 'glass-strong border border-brand-primary/40 shadow-[0_0_40px_rgba(99,102,241,0.15)]'
                  : 'glass border border-white/[0.08]'
                }`}
              >
                {plan.highlight && (
                  <div className="absolute -top-3 left-1/2 -translate-x-1/2">
                    <span className="flex items-center gap-1 bg-brand-primary text-white text-[10px] font-bold uppercase tracking-wider px-3 py-1 rounded-full">
                      <Star size={10} fill="currentColor" /> Most Popular
                    </span>
                  </div>
                )}

                <div className="mb-6">
                  <h3 className="text-sm font-bold text-text-muted uppercase tracking-wider mb-1">{plan.name}</h3>
                  <div className="flex items-end gap-1 mb-2">
                    <span className="text-4xl font-display font-bold text-text-primary">{plan.price}</span>
                    {plan.period && <span className="text-sm text-text-muted mb-1.5">{plan.period}</span>}
                  </div>
                  <p className="text-xs text-text-secondary">{plan.description}</p>
                </div>

                <ul className="space-y-2.5 flex-1 mb-7">
                  {plan.features.map((feat, fi) => (
                    <li key={fi} className="flex items-start gap-2 text-sm text-text-secondary">
                      <CheckCircle2 size={14} className="text-green-400 mt-0.5 flex-shrink-0" />
                      {feat}
                    </li>
                  ))}
                </ul>

                <button
                  onClick={() => navigate('/dashboard')}
                  className={`w-full py-2.5 rounded-xl text-sm font-semibold transition-all
                    ${plan.highlight
                      ? 'bg-brand-primary hover:bg-brand-primary/90 text-white shadow-glow'
                      : 'glass border border-white/[0.12] text-text-primary hover:border-white/25'
                    }`}
                >
                  {plan.cta}
                </button>
              </div>
            </FadeUp>
          ))}
        </div>
      </section>

      {/* ── TECH STACK ───────────────────────────────────────────────────── */}
      <FadeUp className="container mx-auto px-4 mb-20">
        <div className="max-w-4xl mx-auto py-8 border-t border-white/[0.06]">
          <p className="text-center text-xs font-bold uppercase tracking-widest text-text-muted mb-6">
            Built on battle-tested open-source
          </p>
          <div className="flex flex-wrap justify-center gap-8">
            {TECH_STACK.map((tech, i) => {
              const Icon = tech.icon;
              return (
                <div key={i} className="flex items-center gap-2 text-text-muted hover:text-text-secondary transition-colors">
                  <Icon size={16} className="text-brand-primary/60" />
                  <span className="text-sm">{tech.label}</span>
                </div>
              );
            })}
          </div>
        </div>
      </FadeUp>

      {/* ── FINAL CTA ────────────────────────────────────────────────────── */}
      <FadeUp className="container mx-auto px-4 pb-24">
        <div className="max-w-3xl mx-auto glass-strong rounded-3xl p-12 border border-white/[0.1] text-center relative overflow-hidden">
          <div className="absolute inset-0 bg-gradient-to-br from-brand-primary/5 via-transparent to-brand-secondary/5 pointer-events-none" />
          <div className="relative z-10">
            <h2 className="text-3xl md:text-4xl font-display font-bold mb-4">
              Ready to understand your codebase?
            </h2>
            <p className="text-text-secondary mb-8 max-w-lg mx-auto">
              Join developers who use DevDocsAI to onboard faster, ship better docs, and understand any repo in minutes.
            </p>
            <div className="flex flex-col sm:flex-row gap-3 justify-center">
              <button
                onClick={() => navigate('/dashboard')}
                className="btn-brand px-8 py-3 rounded-xl text-sm font-semibold flex items-center gap-2 justify-center"
              >
                Start Analyzing Free <ArrowRight size={16} />
              </button>
              <button
                onClick={() => navigate('/generators')}
                className="glass border border-white/[0.12] hover:border-brand-accent/40 px-8 py-3 rounded-xl text-sm font-semibold flex items-center gap-2 justify-center transition-all"
              >
                <Sparkles size={14} className="text-brand-accent" />
                Try AI Generators
              </button>
            </div>
          </div>
        </div>
      </FadeUp>

    </div>
  );
}
