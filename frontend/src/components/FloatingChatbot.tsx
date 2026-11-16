import React, { useState, useEffect, useRef } from 'react';
import {
  Sparkles,
  Send,
  X,
  Minus,
  RotateCcw,
  Copy,
  Check,
  Terminal,
  AlertCircle,
  Maximize2,
  TrendingUp,
  Database,
  ArrowRight
} from 'lucide-react';
import { api, ApiError, ChatResponse, TelemetryEvent } from '../services/api';
import { AgentTelemetryCard } from './AgentTelemetryCard';
import { ContextualAIPayload } from '../types/contextualAi';

interface ChatMessage {
  id: string;
  role: 'user' | 'assistant';
  text: string;
  response?: ChatResponse;
  timestamp: Date;
  isError?: boolean;
}

const WELCOME_TEXT = "Hi! I'm NovaNest AI. Ask me about your business data, analytics, programming, or any other topic. How can I help you today?";

const SUGGESTED_QUESTIONS = [
  "Analyze my business performance.",
  "What is our total revenue?",
  "Explain customer churn.",
  "How can I improve restaurant performance?",
  "Explain a technical concept.",
  "Help me write Python or SQL code."
];

/**
 * Compact CodeBlock with one-click clipboard copy
 */
const MiniCodeBlock: React.FC<{ language: string; code: string }> = ({ language, code }) => {
  const [copied, setCopied] = useState(false);

  const handleCopy = () => {
    navigator.clipboard.writeText(code);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <div className="my-2 rounded-lg overflow-hidden border border-slate-200 bg-slate-50 font-mono text-xs shadow-xs">
      <div className="flex items-center justify-between px-3 py-1 bg-slate-100 border-b border-slate-200 text-[10px] text-slate-600">
        <div className="flex items-center gap-1 font-bold uppercase text-blue-600">
          <Terminal size={11} />
          <span>{language || 'code'}</span>
        </div>
        <button
          onClick={handleCopy}
          className="flex items-center gap-1 px-1.5 py-0.5 rounded hover:bg-slate-200 text-slate-600 hover:text-slate-900 transition-colors"
          title="Copy code"
        >
          {copied ? <Check size={11} className="text-green-600" /> : <Copy size={11} />}
          <span className="text-[10px]">{copied ? 'Copied' : 'Copy'}</span>
        </button>
      </div>
      <div className="p-2.5 overflow-x-auto text-slate-800 leading-relaxed font-mono text-[11px] bg-white">
        <pre><code>{code}</code></pre>
      </div>
    </div>
  );
};

/**
 * Lightweight, robust Markdown and Table renderer for chat bubbles
 */
const MiniFormattedContent: React.FC<{ content: string }> = ({ content }) => {
  if (!content) return null;

  // Split code blocks
  const parts = content.split(/(```[\s\S]*?```)/g);

  return (
    <div className="space-y-1.5 text-xs sm:text-[13px] leading-relaxed text-slate-800">
      {parts.map((part, pIdx) => {
        if (part.startsWith('```') && part.endsWith('```')) {
          const firstLineEnd = part.indexOf('\n');
          const lang = part.substring(3, firstLineEnd).trim();
          const code = part.substring(firstLineEnd + 1, part.length - 3).trim();
          return <MiniCodeBlock key={pIdx} language={lang} code={code} />;
        }

        const lines = part.split('\n');
        const elements: React.ReactNode[] = [];
        let inTable = false;
        let tableRows: string[][] = [];

        const flushTable = (key: string) => {
          if (tableRows.length > 0) {
            const [header, , ...body] = tableRows;
            elements.push(
              <div key={key} className="my-2 overflow-x-auto rounded border border-slate-200">
                <table className="w-full text-left text-[11px] border-collapse font-sans">
                  {header && (
                    <thead className="bg-slate-100 text-slate-700 border-b border-slate-200 font-semibold text-[10px]">
                      <tr>
                        {header.map((col, cIdx) => (
                          <th key={cIdx} className="p-1.5 border-r border-slate-200 last:border-r-0">{col.trim()}</th>
                        ))}
                      </tr>
                    </thead>
                  )}
                  <tbody className="divide-y divide-slate-100 bg-white font-mono text-[10px]">
                    {body.map((row, rIdx) => (
                      <tr key={rIdx} className="hover:bg-slate-50">
                        {row.map((cell, cIdx) => (
                          <td key={cIdx} className="p-1.5 text-slate-700 border-r border-slate-200 last:border-r-0 font-sans">{cell.trim()}</td>
                        ))}
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            );
            tableRows = [];
          }
          inTable = false;
        };

        lines.forEach((line, lIdx) => {
          const trimmed = line.trim();

          // Table detection
          if (trimmed.startsWith('|') && trimmed.endsWith('|')) {
            inTable = true;
            const cells = trimmed.slice(1, -1).split('|');
            tableRows.push(cells);
            return;
          } else if (inTable) {
            flushTable(`tbl_${pIdx}_${lIdx}`);
          }

          if (!trimmed) {
            elements.push(<div key={`sp_${lIdx}`} className="h-1" />);
            return;
          }

          // Headers
          if (trimmed.startsWith('### ')) {
            elements.push(
              <h4 key={`h3_${lIdx}`} className="text-xs sm:text-sm font-bold text-sapphire-300 mt-2 mb-0.5">
                {trimmed.replace('### ', '')}
              </h4>
            );
          } else if (trimmed.startsWith('## ')) {
            elements.push(
              <h3 key={`h2_${lIdx}`} className="text-sm font-extrabold text-sapphire-400 mt-2 mb-1">
                {trimmed.replace('## ', '')}
              </h3>
            );
          } else if (trimmed.startsWith('# ')) {
            elements.push(
              <h2 key={`h1_${lIdx}`} className="text-sm sm:text-base font-extrabold text-white mt-2 mb-1">
                {trimmed.replace('# ', '')}
              </h2>
            );
          }
          // Bullet lists
          else if (trimmed.startsWith('- ') || trimmed.startsWith('* ')) {
            const rawText = trimmed.replace(/^[-*]\s+/, '');
            elements.push(
              <div key={`li_${lIdx}`} className="flex items-start gap-1.5 ml-1">
                <span className="text-sapphire-400 mt-1 text-[8px]">●</span>
                <span className="flex-1 text-slate-300">{renderInline(rawText)}</span>
              </div>
            );
          }
          // Numbered lists
          else if (/^\d+\.\s+/.test(trimmed)) {
            const numMatch = trimmed.match(/^(\d+)\.\s+(.*)/);
            if (numMatch) {
              elements.push(
                <div key={`nli_${lIdx}`} className="flex items-start gap-1.5 ml-1">
                  <span className="text-cyan-400 font-mono font-bold text-[10px] mt-0.5">{numMatch[1]}.</span>
                  <span className="flex-1 text-slate-300">{renderInline(numMatch[2])}</span>
                </div>
              );
            }
          }
          // Normal paragraphs
          else {
            elements.push(
              <p key={`p_${lIdx}`} className="text-slate-200">
                {renderInline(trimmed)}
              </p>
            );
          }
        });

        if (inTable) {
          flushTable(`tbl_end_${pIdx}`);
        }

        return <div key={pIdx} className="space-y-1">{elements}</div>;
      })}
    </div>
  );
};

// Inline bold and code formatter helper
function renderInline(text: string): React.ReactNode {
  const parts = text.split(/(\*\*.*?\*\*|`.*?`)/g);
  return parts.map((seg, i) => {
    if (seg.startsWith('**') && seg.endsWith('**')) {
      return <strong key={i} className="font-semibold text-white">{seg.slice(2, -2)}</strong>;
    }
    if (seg.startsWith('`') && seg.endsWith('`')) {
      return <code key={i} className="px-1 py-0.5 rounded bg-slate-800 text-cyan-300 font-mono text-[11px]">{seg.slice(1, -1)}</code>;
    }
    return seg;
  });
}

export const FloatingChatbot: React.FC = () => {
  const [isOpen, setIsOpen] = useState(false);
  const [messages, setMessages] = useState<ChatMessage[]>([
    {
      id: 'welcome',
      role: 'assistant',
      text: WELCOME_TEXT,
      timestamp: new Date()
    }
  ]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [liveTelemetry, setLiveTelemetry] = useState<TelemetryEvent[]>([]);
  const [sessionId] = useState(() => `float_session_${Date.now()}`);
  const [hasUnread, setHasUnread] = useState(false);
  const [activeContext, setActiveContext] = useState<ContextualAIPayload | null>(null);

  const messagesEndRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLTextAreaElement>(null);

  // Auto-scroll to bottom of chat when new message arrives
  useEffect(() => {
    if (isOpen) {
      messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
    }
  }, [messages, isOpen, loading]);

  // Focus input when opened
  useEffect(() => {
    if (isOpen) {
      setHasUnread(false);
      setTimeout(() => inputRef.current?.focus(), 150);
    }
  }, [isOpen]);

  // Listen for Contextual AI launches across dashboards
  useEffect(() => {
    const handleContextualLaunch = (e: Event) => {
      const customEvt = e as CustomEvent<{ payload: ContextualAIPayload; prompt: string }>;
      if (!customEvt.detail) return;
      const { payload, prompt } = customEvt.detail;

      setIsOpen(true);
      setActiveContext(payload);

      if (payload.autoSubmit) {
        handleSend(prompt, payload);
      } else {
        setInput(prompt);
        setTimeout(() => inputRef.current?.focus(), 150);
      }
    };

    window.addEventListener('novanest-launch-contextual-ai', handleContextualLaunch);
    return () => window.removeEventListener('novanest-launch-contextual-ai', handleContextualLaunch);
  }, []);

  const handleSend = async (queryText?: string, overrideContext?: ContextualAIPayload | null) => {
    const q = (queryText || input).trim();
    if (!q || loading) return;

    const ctx = overrideContext !== undefined ? overrideContext : activeContext;

    const userMsg: ChatMessage = {
      id: `u_${Date.now()}`,
      role: 'user',
      text: q,
      timestamp: new Date()
    };

    setMessages(prev => [...prev, userMsg]);
    setInput('');
    setLoading(true);
    setLiveTelemetry([]);

    const cityFilter = ctx?.city && ctx.city !== 'All' ? ctx.city : undefined;
    const contextualData = ctx
      ? {
          dashboard_name: ctx.dashboardName,
          kpi_or_chart_id: ctx.kpiOrChartId,
          selected_metric: ctx.selectedMetric,
          city: ctx.city,
          entity_type: ctx.entityType,
          entity_id: ctx.entityId,
          entity_name: ctx.entityName,
          source_component: ctx.sourceComponent,
          active_filters: ctx.activeFilters,
          date_range: ctx.dateRange,
        }
      : undefined;

    try {
      const res = await api.askAiStream(
        q,
        sessionId,
        cityFilter,
        (evt) => {
          setLiveTelemetry(prev => [...prev, evt]);
        },
        undefined,
        contextualData
      );
      const assistantMsg: ChatMessage = {
        id: `a_${Date.now()}`,
        role: 'assistant',
        text: res.answer || "I have analyzed your inquiry.",
        response: res,
        timestamp: new Date()
      };
      setMessages(prev => [...prev, assistantMsg]);
      if (!isOpen) {
        setHasUnread(true);
      }
    } catch (err: any) {
      const isAuthErr = err instanceof ApiError && (err.status === 401 || err.status === 403);
      const errorMsg: ChatMessage = {
        id: `err_${Date.now()}`,
        role: 'assistant',
        text: isAuthErr
          ? `🔒 **Authentication Required (${err.status}):** Please unlock your API session token in any protected dashboard panel or enter a valid key before querying Ask NovaNest AI.`
          : `⚠️ **Service Notice:** Unable to reach AI intelligence backend (${err?.message || 'Connection Error'}). Please check that the local server is running on port 8000.`,
        timestamp: new Date(),
        isError: true
      };
      setMessages(prev => [...prev, errorMsg]);
    } finally {
      setLoading(false);
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  const handleResetConversation = async () => {
    try {
      await api.resetAiSession(sessionId);
    } catch {
      // Ignored if offline
    }
    setActiveContext(null);
    setMessages([
      {
        id: `welcome_${Date.now()}`,
        role: 'assistant',
        text: WELCOME_TEXT,
        timestamp: new Date()
      }
    ]);
  };

  return (
    <>
      {/* ======================================================== */}
      {/* 1. FLOATING CHATBOT BUTTON (BOTTOM-RIGHT)                */}
      {/* ======================================================== */}
      {!isOpen && (
        <aside aria-label="Ask NovaNest AI floating trigger" className="fixed bottom-6 right-5 sm:right-6 z-50">
          <button
            onClick={() => setIsOpen(true)}
            className="group relative flex items-center gap-2.5 px-4 sm:px-5 py-3 rounded-full bg-blue-600 hover:bg-blue-700 text-white shadow-xl shadow-blue-600/30 hover:scale-[1.03] active:scale-[0.98] transition-all duration-300 animate-bot-glow cursor-pointer border border-blue-500"
            aria-label="Open Ask NovaNest AI Assistant"
            title="Ask NovaNest AI Assistant"
          >
            {/* Blinking / Pulsing Live Beacon Indicator */}
            <span className="relative flex h-2.5 w-2.5">
              <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-orange-400 opacity-75" />
              <span className="relative inline-flex rounded-full h-2.5 w-2.5 bg-orange-400 animate-beacon-blink" />
            </span>

            {/* AI Assistant Icon with soft glow */}
            <div className="flex items-center justify-center w-7 h-7 rounded-full bg-white/20 text-white shadow-xs group-hover:rotate-12 transition-transform duration-300">
              <Sparkles size={15} className="animate-pulse" />
            </div>

            {/* Label */}
            <div className="flex flex-col text-left">
              <span className="text-xs sm:text-sm font-semibold tracking-wide text-white">
                Ask NovaNest
              </span>
              <span className="text-[10px] text-blue-100 font-mono -mt-0.5">
                AI Assistant
              </span>
            </div>

            {/* Unread Message Notification Dot */}
            {hasUnread && (
              <span className="absolute -top-1 -right-1 flex h-3.5 w-3.5 items-center justify-center rounded-full bg-orange-500 text-[9px] font-bold text-white shadow-md">
                1
              </span>
            )}
          </button>
        </aside>
      )}

      {/* ======================================================== */}
      {/* 2. CHATBOT WINDOW (FLOATING GLASSMORPHIC MODAL)         */}
      {/* ======================================================== */}
      {isOpen && (
        <section
          aria-label="Ask NovaNest AI assistant dialog"
          className="fixed bottom-5 right-4 sm:bottom-6 sm:right-6 z-50 w-[calc(100vw-2rem)] sm:w-[420px] md:w-[460px] h-[580px] max-h-[calc(100vh-5rem)] flex flex-col rounded-2xl bg-white border border-slate-200 shadow-2xl overflow-hidden transition-all duration-300 animate-in fade-in slide-in-from-bottom-4"
        >
          {/* Top Gradient Accent Line */}
          <div className="h-1 w-full bg-blue-600" />

          {/* Window Header */}
          <header className="px-4 py-3 bg-slate-50 border-b border-slate-200 flex items-center justify-between">
            <div className="flex items-center gap-2.5">
              <div className="flex items-center justify-center w-8 h-8 rounded-lg bg-blue-600 text-white shadow-xs">
                <Sparkles size={16} />
              </div>
              <div className="flex flex-col">
                <div className="flex items-center gap-2">
                  <h3 className="text-xs sm:text-sm font-bold text-slate-800 leading-tight">
                    Ask NovaNest AI
                  </h3>
                  <span className="inline-flex items-center gap-1 px-1.5 py-0.5 rounded-full bg-green-50 border border-green-200 text-[9px] font-mono text-green-700">
                    <span className="h-1.5 w-1.5 rounded-full bg-green-500 animate-pulse" />
                    Online
                  </span>
                </div>
                <p className="text-[10px] text-slate-500 font-medium">
                  Your Intelligent Business Assistant
                </p>
              </div>
            </div>

            {/* Window Controls */}
            <div className="flex items-center gap-1">
              {/* Reset Conversation Button */}
              <button
                onClick={handleResetConversation}
                className="p-1.5 rounded-lg text-slate-400 hover:text-slate-700 hover:bg-slate-200/80 transition-colors"
                title="New Chat / Reset Conversation"
                aria-label="New Chat"
              >
                <RotateCcw size={14} />
              </button>
              {/* Minimize Button */}
              <button
                onClick={() => setIsOpen(false)}
                className="p-1.5 rounded-lg text-slate-400 hover:text-slate-700 hover:bg-slate-200/80 transition-colors"
                title="Minimize Chat"
                aria-label="Minimize Chat"
              >
                <Minus size={15} />
              </button>
              {/* Close Button */}
              <button
                onClick={() => setIsOpen(false)}
                className="p-1.5 rounded-lg text-slate-400 hover:text-red-600 hover:bg-slate-200/80 transition-colors"
                title="Close Chat"
                aria-label="Close Chat"
              >
                <X size={16} />
              </button>
            </div>
          </header>

          {/* ACTIVE DASHBOARD CONTEXT BANNER */}
          {activeContext && (
            <div className="px-3.5 py-1.5 bg-blue-50 border-b border-blue-200 flex items-center justify-between text-[11px] text-blue-700 animate-fadeIn">
              <div className="flex items-center gap-1.5 truncate">
                <Sparkles size={12} className="text-blue-600 shrink-0 animate-pulse" />
                <span className="font-semibold text-slate-800 truncate">{activeContext.dashboardName}</span>
                <span className="text-slate-400">›</span>
                <span className="text-blue-700 truncate">
                  {activeContext.selectedMetric ||
                    activeContext.entityName ||
                    activeContext.entityId ||
                    activeContext.kpiOrChartId.replace(/_/g, ' ')}
                </span>
                {activeContext.city && activeContext.city !== 'All' && (
                  <span className="px-1.5 py-0.2 rounded bg-blue-100 text-[10px] text-blue-800 font-medium">
                    {activeContext.city}
                  </span>
                )}
              </div>
              <button
                onClick={() => setActiveContext(null)}
                className="text-slate-400 hover:text-slate-700 p-0.5 rounded hover:bg-blue-100 transition-colors ml-2"
                title="Clear Context"
                aria-label="Clear Context"
              >
                <X size={12} />
              </button>
            </div>
          )}

          {/* Messages Scroll View */}
          <div className="flex-1 overflow-y-auto p-3.5 sm:p-4 space-y-3.5 bg-slate-50">
            {messages.map((msg) => {
              const isUser = msg.role === 'user';
              return (
                <div
                  key={msg.id}
                  className={`flex items-start gap-2 ${isUser ? 'justify-end' : 'justify-start'}`}
                >
                  {/* Assistant Avatar */}
                  {!isUser && (
                    <div className="mt-0.5 flex-shrink-0 flex items-center justify-center w-6 h-6 rounded-full bg-blue-600 text-white shadow-xs">
                      <Sparkles size={12} />
                    </div>
                  )}

                  {/* Message Bubble */}
                  <div
                    className={`rounded-2xl text-xs sm:text-[13px] leading-relaxed shadow-xs transition-all ${
                      isUser
                        ? 'bg-blue-600 text-white px-3.5 py-2.5 rounded-tr-sm max-w-[85%]'
                        : msg.isError
                        ? 'bg-red-50 border border-red-200 text-red-800 p-3 rounded-tl-sm max-w-[92%]'
                        : 'bg-white border border-slate-200 text-slate-800 p-3.5 rounded-tl-sm max-w-[92%]'
                    }`}
                  >
                    {isUser ? (
                      <p className="whitespace-pre-wrap">{msg.text}</p>
                    ) : (
                      <>
                        {msg.response && (msg.response.agents_invoked?.length || msg.response.verification_outcome) && (
                          <div className="mb-2 flex flex-wrap items-center gap-1 text-[9px] font-mono">
                            {msg.response.verification_outcome && (
                              <span
                                className={`px-1.5 py-0.5 rounded border ${
                                  msg.response.grounding_verified
                                    ? 'bg-green-50 border-green-200 text-green-700'
                                    : 'bg-orange-50 border-orange-200 text-orange-700'
                                }`}
                              >
                                verified:{msg.response.verification_outcome}
                              </span>
                            )}
                            {msg.response.agents_invoked?.map((ag, idx) => (
                              <span
                                key={`${ag.agent_id}_${idx}`}
                                className={`px-1.5 py-0.5 rounded border ${
                                  ag.status === 'success'
                                    ? 'bg-blue-50 border-blue-200 text-blue-700'
                                    : 'bg-red-50 border-red-200 text-red-700'
                                }`}
                              >
                                {ag.agent_id}:{ag.status}
                              </span>
                            ))}
                          </div>
                        )}

                        {/* PHASE 06.5 MULTI-AGENT TELEMETRY CARD */}
                        {msg.response?.agents_invoked && msg.response.agents_invoked.length > 0 && (
                          <AgentTelemetryCard
                            agentsInvoked={msg.response.agents_invoked}
                            verificationOutcome={msg.response.verification_outcome}
                            isVerified={msg.response.grounding_verified}
                            totalElapsedMs={msg.response.agents_invoked.reduce((acc, a) => acc + (a.elapsed_ms || 0), 0)}
                            isLive={false}
                          />
                        )}

                        <MiniFormattedContent content={msg.text} />

                        {msg.response?.limitations && msg.response.limitations.length > 0 && (
                          <div className="mt-2 p-2 rounded bg-red-50 border border-red-200 text-[10px] text-red-700">
                            <strong>Limitations:</strong> {msg.response.limitations.join(' | ')}
                          </div>
                        )}

                        {msg.response?.ml_confidence_warnings && msg.response.ml_confidence_warnings.length > 0 && (
                          <div className="mt-2 p-2 rounded bg-orange-50 border border-orange-200 text-[10px] text-orange-800">
                            <strong>ML Notice:</strong> Experimental models are non-production baselines; validated CSV metrics prioritized.
                          </div>
                        )}

                        {/* Verified Metrics Cards (if business response) */}
                        {msg.response?.verified_metrics && msg.response.verified_metrics.length > 0 && (
                          <div className="mt-2.5 pt-2 border-t border-slate-200 grid grid-cols-2 gap-1.5">
                            {msg.response.verified_metrics.slice(0, 4).map((m, mIdx) => (
                              <div key={mIdx} className="bg-slate-50 p-1.5 rounded border border-slate-200">
                                <span className="block text-[9px] text-slate-500 truncate">{m.label || (m as any).metric || 'Metric'}</span>
                                <span className="text-[11px] font-bold font-mono text-blue-700">{m.value}</span>
                              </div>
                            ))}
                          </div>
                        )}

                        {/* Provenance Tag */}
                        {msg.response?.provenance && (
                          <div className="mt-2 pt-1 border-t border-slate-200 flex items-center justify-between text-[9px] text-slate-400 font-mono">
                            <span>{msg.response.provenance.data_source}</span>
                            <span>{msg.response.provenance.access_mode || 'Read-Only Secure'}</span>
                          </div>
                        )}

                        {/* Follow-up suggestions */}
                        {msg.response?.follow_up_suggestions && msg.response.follow_up_suggestions.length > 0 && (
                          <div className="mt-2 pt-2 border-t border-slate-200 flex flex-wrap gap-1">
                            {msg.response.follow_up_suggestions.slice(0, 2).map((sugg, sIdx) => (
                              <button
                                key={sIdx}
                                onClick={() => handleSend(sugg)}
                                className="flex items-center gap-1 text-[10px] text-blue-700 hover:text-blue-800 bg-blue-50 hover:bg-blue-100 border border-blue-200 px-2 py-0.5 rounded-full transition-colors text-left"
                              >
                                <ArrowRight size={9} />
                                <span className="truncate max-w-[200px]">{sugg}</span>
                              </button>
                            ))}
                          </div>
                        )}
                      </>
                    )}
                  </div>
                </div>
              );
            })}

            {/* Loading Indicator with Live Telemetry */}
            {loading && (
              <div className="flex flex-col gap-2 w-full">
                <div className="flex items-start gap-2 justify-start">
                  <div className="mt-0.5 flex-shrink-0 flex items-center justify-center w-6 h-6 rounded-full bg-blue-600 text-white shadow-xs">
                    <Sparkles size={12} className="animate-spin text-white" />
                  </div>
                  <div className="bg-white border border-slate-200 p-2.5 rounded-2xl rounded-tl-sm text-xs text-slate-500 flex items-center gap-2 shadow-xs">
                    <div className="h-3 w-3 rounded-full border-2 border-blue-600 border-t-transparent animate-spin" />
                    <span>Coordinating multi-agent domain intelligence...</span>
                  </div>
                </div>
                {liveTelemetry.length > 0 && (
                  <AgentTelemetryCard events={liveTelemetry} isLive={true} />
                )}
              </div>
            )}

            <div ref={messagesEndRef} />
          </div>

          {/* Suggested Starter Chips (show when conversation is at beginning) */}
          {messages.length <= 2 && !loading && (
            <div className="px-3.5 py-2 bg-white border-t border-slate-200">
              <span className="block text-[10px] font-medium text-slate-500 mb-1.5 uppercase tracking-wider">
                Suggested Questions:
              </span>
              <div className="flex flex-wrap gap-1.5 max-h-24 overflow-y-auto pr-1">
                {SUGGESTED_QUESTIONS.map((chip, idx) => (
                  <button
                    key={idx}
                    onClick={() => handleSend(chip)}
                    className="text-[11px] text-slate-600 hover:text-blue-700 bg-slate-50 hover:bg-blue-50/60 border border-slate-200 hover:border-blue-300 rounded-full px-2.5 py-1 transition-all text-left truncate shadow-2xs"
                  >
                    {chip}
                  </button>
                ))}
              </div>
            </div>
          )}

          {/* Input & Send Area */}
          <footer className="p-3 bg-white border-t border-slate-200">
            <div className="flex items-end gap-2 bg-slate-50 border border-slate-200 focus-within:border-blue-600 focus-within:bg-white rounded-xl px-3 py-1.5 transition-colors">
              <textarea
                ref={inputRef}
                value={input}
                onChange={(e) => setInput(e.target.value)}
                onKeyDown={handleKeyDown}
                placeholder="Ask about revenue, Python, churn, or anything..."
                rows={1}
                className="flex-1 bg-transparent text-xs sm:text-sm text-slate-800 placeholder-slate-400 focus:outline-none resize-none max-h-24 py-1 leading-relaxed"
              />
              <button
                onClick={() => handleSend()}
                disabled={!input.trim() || loading}
                className={`p-2 rounded-lg transition-all flex items-center justify-center flex-shrink-0 ${
                  input.trim() && !loading
                    ? 'bg-orange-500 hover:bg-orange-600 text-white shadow-xs cursor-pointer'
                    : 'bg-slate-200 text-slate-400 cursor-not-allowed'
                }`}
                title="Send message (Enter)"
                aria-label="Send message"
              >
                <Send size={14} />
              </button>
            </div>
            <div className="flex items-center justify-between mt-1 px-1 text-[10px] text-slate-400 font-mono">
              <span>Enter to send · Shift+Enter for new line</span>
              <span>Universal AI Analyst</span>
            </div>
          </footer>
        </section>
      )}
    </>
  );
};
