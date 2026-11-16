import React from 'react';
import { AlertTriangle, RotateCcw } from 'lucide-react';

interface ErrorBoundaryProps {
  children: React.ReactNode;
  viewKey?: string;
}

interface ErrorBoundaryState {
  hasError: boolean;
  errorMessage: string;
}

/**
 * Global/View Error Boundary preventing unhandled React render exceptions
 * from collapsing the entire application into a blank screen.
 */
export class ErrorBoundary extends React.Component<ErrorBoundaryProps, ErrorBoundaryState> {
  constructor(props: ErrorBoundaryProps) {
    super(props);
    this.state = {
      hasError: false,
      errorMessage: '',
    };
  }

  static getDerivedStateFromError(error: Error): ErrorBoundaryState {
    return {
      hasError: true,
      errorMessage: error?.message || 'Unexpected rendering error occurred.',
    };
  }

  componentDidCatch(error: Error, errorInfo: React.ErrorInfo): void {
    console.error('NovaNest UI ErrorBoundary caught error:', error, errorInfo);
  }

  componentDidUpdate(prevProps: ErrorBoundaryProps): void {
    if (this.props.viewKey !== prevProps.viewKey && this.state.hasError) {
      this.setState({ hasError: false, errorMessage: '' });
    }
  }

  private handleReset = () => {
    this.setState({ hasError: false, errorMessage: '' });
  };

  render(): React.ReactNode {
    if (this.state.hasError) {
      return (
        <div className="min-h-[320px] flex items-center justify-center p-6">
          <div className="glass-card max-w-lg w-full p-6 border border-crimson-500/40 bg-obsidian-900/95 space-y-4">
            <div className="flex items-start gap-3">
              <div className="p-2.5 rounded-xl bg-crimson-500/15 border border-crimson-500/30 text-crimson-400">
                <AlertTriangle size={22} />
              </div>
              <div>
                <h2 className="text-base font-bold text-white">Component Render Fault Intercepted</h2>
                <p className="text-xs text-slate-400 mt-1">
                  A visualization widget encountered malformed or unexpected payload data and was isolated cleanly.
                </p>
              </div>
            </div>
            <div className="p-3 rounded-lg bg-obsidian-950 border border-slate-800 text-xs font-mono text-crimson-300 break-words">
              {this.state.errorMessage}
            </div>
            <div className="flex items-center gap-3">
              <button
                type="button"
                onClick={this.handleReset}
                className="px-4 py-2 rounded-lg bg-sapphire-600 hover:bg-sapphire-500 text-white text-xs font-semibold flex items-center gap-2 transition-colors"
              >
                <RotateCcw size={14} />
                Recover View
              </button>
              <button
                type="button"
                onClick={() => window.location.reload()}
                className="px-4 py-2 rounded-lg bg-obsidian-950 hover:bg-slate-800 border border-slate-700 text-slate-300 text-xs font-semibold transition-colors"
              >
                Reload Dashboard
              </button>
            </div>
          </div>
        </div>
      );
    }

    return this.props.children;
  }
}

