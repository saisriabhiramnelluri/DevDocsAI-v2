// DevDocsAI — Global Error Boundary
// Catches unhandled React render errors and shows a recovery UI
import { Component, ErrorInfo, ReactNode } from 'react';
import { RefreshCw, Home, ChevronDown, ChevronUp } from 'lucide-react';

interface Props {
  children: ReactNode;
  fallback?: ReactNode;
}

interface State {
  hasError: boolean;
  error: Error | null;
  showDetails: boolean;
}

export class ErrorBoundary extends Component<Props, State> {
  constructor(props: Props) {
    super(props);
    this.state = { hasError: false, error: null, showDetails: false };
  }

  static getDerivedStateFromError(error: Error): State {
    return { hasError: true, error, showDetails: false };
  }

  componentDidCatch(error: Error, info: ErrorInfo) {
    console.error('[ErrorBoundary] Uncaught error:', error, info.componentStack);
  }

  handleReset = () => {
    this.setState({ hasError: false, error: null, showDetails: false });
  };

  render() {
    if (!this.state.hasError) return this.props.children;

    if (this.props.fallback) return this.props.fallback;

    return (
      <div className="min-h-screen flex flex-col items-center justify-center px-4 text-center bg-background">
        <div className="max-w-md w-full glass-strong rounded-3xl p-8 border border-red-500/20">
          {/* Icon */}
          <div className="w-14 h-14 rounded-2xl bg-red-500/10 border border-red-500/20 flex items-center justify-center mx-auto mb-5">
            <span className="text-2xl">⚠️</span>
          </div>

          <h1 className="text-xl font-display font-bold text-text-primary mb-2">
            Something went wrong
          </h1>
          <p className="text-sm text-text-secondary mb-6">
            An unexpected error occurred. You can try refreshing the page or go back to the dashboard.
          </p>

          {/* Actions */}
          <div className="flex gap-3 justify-center mb-5">
            <button
              onClick={this.handleReset}
              className="flex items-center gap-2 px-4 py-2 glass rounded-xl border border-white/[0.08] hover:border-white/20 text-sm transition-all"
            >
              <RefreshCw size={14} />
              Try Again
            </button>
            <button
              onClick={() => { window.location.href = '/'; }}
              className="flex items-center gap-2 px-4 py-2 bg-brand-primary hover:bg-brand-primary/90 rounded-xl text-sm font-semibold text-white transition-all"
            >
              <Home size={14} />
              Home
            </button>
          </div>

          {/* Error details toggle */}
          <button
            onClick={() => this.setState((s) => ({ showDetails: !s.showDetails }))}
            className="flex items-center gap-1 text-xs text-text-muted hover:text-text-secondary transition-colors mx-auto"
          >
            {this.state.showDetails ? <ChevronUp size={12} /> : <ChevronDown size={12} />}
            {this.state.showDetails ? 'Hide' : 'Show'} error details
          </button>

          {this.state.showDetails && this.state.error && (
            <div className="mt-3 text-left glass rounded-xl p-3 border border-red-500/10 overflow-auto max-h-40">
              <p className="text-xs font-mono text-red-400 break-all">
                {this.state.error.toString()}
              </p>
            </div>
          )}
        </div>
      </div>
    );
  }
}
