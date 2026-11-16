import React, { useState } from 'react';
import { AlertCircle, Database, KeyRound, RefreshCw, ShieldAlert } from 'lucide-react';
import { ApiError, clearApiToken, getApiToken, setApiToken } from '../services/api';

interface ApiErrorStateProps {
  title?: string;
  error: unknown;
  onRetry?: () => void;
}

/**
 * Standardized API Error & Session Auth panel across all NovaNest dashboard views.
 * Prompts interactively for an API token on HTTP 401/403 without embedding credentials.
 */
export const ApiErrorState: React.FC<ApiErrorStateProps> = ({
  title = 'Telemetry Request Failed',
  error,
  onRetry,
}) => {
  const apiErr = error instanceof ApiError ? error : null;
  const status = apiErr?.status;
  const message =
    error instanceof Error
      ? error.message
      : typeof error === 'string'
        ? error
        : 'Unable to communicate with NovaNest FastAPI backend.';

  const isAuthError =
    status === 401 ||
    status === 403 ||
    /\b(401|403|unauthorized|forbidden|authentication required|invalid api key)\b/i.test(message);

  const [tokenInput, setTokenInput] = useState<string>(() => getApiToken());
  const [savedNotice, setSavedNotice] = useState<string | null>(null);

  const handleApplyToken = (e: React.FormEvent) => {
    e.preventDefault();
    const cleaned = tokenInput.trim();
    if (!cleaned) {
      setSavedNotice('Please enter a valid bearer/API token from your session administrator.');
      return;
    }
    setApiToken(cleaned);
    setSavedNotice(null);
    window.dispatchEvent(new Event('novanest-auth-updated'));
    if (onRetry) onRetry();
  };

  const handleClearToken = () => {
    clearApiToken();
    setTokenInput('');
    setSavedNotice('Cleared stored session token.');
  };

  return (
    <div className="min-h-[300px] flex items-center justify-center p-4">
      <div className="glass-card max-w-lg w-full p-6 border border-crimson-500/35 bg-obsidian-900/90 space-y-4">
        <div className="flex items-start gap-3">
          <div
            className={`p-2.5 rounded-xl border ${
              isAuthError
                ? 'bg-amber-500/15 border-amber-500/30 text-amber-400'
                : 'bg-crimson-500/15 border-crimson-500/30 text-crimson-400'
            }`}
          >
            {isAuthError ? <ShieldAlert size={22} /> : <AlertCircle size={22} />}
          </div>
          <div className="flex-1 min-w-0">
            <div className="flex items-center gap-2 flex-wrap">
              <h3 className="text-base font-bold text-white">
                {isAuthError ? 'API Session Authentication Required' : title}
              </h3>
              {status ? (
                <span className="px-2 py-0.5 rounded bg-slate-800 border border-slate-700 text-[10px] font-mono text-slate-300">
                  HTTP {status}
                </span>
              ) : null}
            </div>
            <p className="text-xs text-slate-300 mt-1 break-words">{message}</p>
          </div>
        </div>

        {isAuthError ? (
          <form onSubmit={handleApplyToken} className="space-y-3 pt-1">
            <label className="block text-[11px] font-semibold uppercase tracking-wider text-slate-400">
              Session API Key / Bearer Token (stored only in browser sessionStorage)
            </label>
            <div className="flex flex-col sm:flex-row gap-2">
              <div className="relative flex-1">
                <KeyRound size={14} className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-500" />
                <input
                  type="password"
                  value={tokenInput}
                  onChange={(e) => setTokenInput(e.target.value)}
                  placeholder="Enter NOVANEST_VIEWER_KEY or NOVANEST_API_KEY..."
                  className="w-full pl-9 pr-3 py-2 rounded-lg bg-obsidian-950 border border-slate-700 focus:border-sapphire-500 outline-none text-xs text-white font-mono"
                />
              </div>
              <button
                type="submit"
                className="px-4 py-2 rounded-lg bg-sapphire-600 hover:bg-sapphire-500 text-white text-xs font-semibold flex items-center justify-center gap-1.5 transition-colors shrink-0"
              >
                <RefreshCw size={13} />
                Authenticate & Retry
              </button>
            </div>
            <div className="flex items-center justify-between text-[11px] text-slate-400">
              <span>{savedNotice || 'Unauthenticated requests are blocked on protected analytics routes.'}</span>
              {getApiToken() ? (
                <button
                  type="button"
                  onClick={handleClearToken}
                  className="text-rose-400 hover:text-rose-300 underline ml-2 shrink-0"
                >
                  Clear Token
                </button>
              ) : null}
            </div>
          </form>
        ) : (
          onRetry && (
            <div className="flex items-center justify-between gap-3 pt-1">
              <span className="text-[11px] text-slate-400">
                Verify FastAPI is running on port 8000 and retry.
              </span>
              <button
                type="button"
                onClick={onRetry}
                className="px-4 py-2 rounded-lg bg-sapphire-600 hover:bg-sapphire-500 text-white text-xs font-semibold flex items-center gap-1.5 transition-colors shrink-0"
              >
                <RefreshCw size={13} />
                Retry Request
              </button>
            </div>
          )
        )}
      </div>
    </div>
  );
};

interface EmptyStateCardProps {
  title?: string;
  description?: string;
  actionLabel?: string;
  onAction?: () => void;
}

export const EmptyStateCard: React.FC<EmptyStateCardProps> = ({
  title = 'No Records Available',
  description = 'No empirical telemetry rows matched the current filter or dataset scope.',
  actionLabel,
  onAction,
}) => (
  <div className="glass-card p-8 border border-slate-800 bg-obsidian-900/60 flex flex-col items-center justify-center text-center space-y-2">
    <div className="p-2.5 rounded-xl bg-slate-800/80 text-slate-400">
      <Database size={20} />
    </div>
    <h4 className="text-sm font-bold text-slate-200">{title}</h4>
    <p className="text-xs text-slate-400 max-w-md">{description}</p>
    {actionLabel && onAction ? (
      <button
        type="button"
        onClick={onAction}
        className="mt-2 px-3.5 py-1.5 rounded-lg bg-sapphire-600 hover:bg-sapphire-500 text-white text-xs font-semibold transition-colors"
      >
        {actionLabel}
      </button>
    ) : null}
  </div>
);

