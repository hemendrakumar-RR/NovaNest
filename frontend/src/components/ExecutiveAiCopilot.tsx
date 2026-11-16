import React, { useState, useEffect, useRef } from 'react';
import {
  Sparkles,
  Send,
  RefreshCw,
  Copy,
  Check,
  AlertTriangle,
  TrendingUp,
  TrendingDown,
  ShieldAlert,
  Brain,
  Sliders,
  FileText,
  HelpCircle,
  Clock,
  Layers,
  ChevronRight,
  Maximize2,
  Minimize2,
  CheckCircle2,
  XCircle,
  Database,
  ArrowRight,
  Info,
  Download,
  Trash2,
} from 'lucide-react';
import {
  api,
  CopilotResponse,
  ExecutiveSummaryPayload,
  RootCausePayload,
  BusinessAlert,
  PrescriptiveRecommendation,
} from '../services/api';

interface ExecutiveAiCopilotProps {
  activeCity?: string;
  onNavigateToTab?: (tab: string) => void;
  className?: string;
}

type CopilotTab = 'copilot' | 'summaries' | 'root_cause' | 'alerts' | 'simulator';

interface ChatMessage {
  id: string;
  sender: 'user' | 'copilot';
  text: string;
  timestamp: string;
  copilotResponse?: CopilotResponse;
  isLoading?: boolean;
}

const SUGGESTED_QUESTIONS = [
  "What is our revenue this month?",
  "Why did revenue decrease?",
  "Which city has the highest order volume?",
  "Which restaurants are underperforming?",
  "Which customers are at high churn risk?",
  "How can we improve contribution margin?",
  "Which operational problems need immediate attention?",
  "What are the biggest business opportunities?",
];

export function ExecutiveAiCopilot({ activeCity = 'All', onNavigateToTab, className = '' }: ExecutiveAiCopilotProps) {
  const getInitialSubTab = (): CopilotTab => {
    try {
      const params = new URLSearchParams(window.location.search);
      const sub = params.get('subtab') as CopilotTab;
      const valid: CopilotTab[] = ['copilot', 'summaries', 'root_cause', 'alerts', 'simulator'];
      if (sub && valid.includes(sub)) return sub;
    } catch {}
    return 'copilot';
  };

  const [activeSubTab, setActiveSubTab] = useState<CopilotTab>(getInitialSubTab);
  const [inputQuery, setInputQuery] = useState('');
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [isQuerying, setIsQuerying] = useState(false);
  const [copiedId, setCopiedId] = useState<string | null>(null);

  // Summaries State
  const [summaryType, setSummaryType] = useState('monthly');
  const [summaryData, setSummaryData] = useState<ExecutiveSummaryPayload | null>(null);
  const [isLoadingSummary, setIsLoadingSummary] = useState(false);

  // Root Cause State
  const [rcaTarget, setRcaTarget] = useState('revenue_decline');
  const [rcaData, setRcaData] = useState<RootCausePayload | null>(null);
  const [isLoadingRca, setIsLoadingRca] = useState(false);

  // Alerts State
  const [alerts, setAlerts] = useState<BusinessAlert[]>([]);
  const [isLoadingAlerts, setIsLoadingAlerts] = useState(false);

  // Simulator State
  const [simScenario, setSimScenario] = useState('promotion_optimization');
  const [simData, setSimData] = useState<any>(null);
  const [isLoadingSim, setIsLoadingSim] = useState(false);

  const messagesEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    // Initial greeting message
    if (messages.length === 0) {
      setMessages([
        {
          id: 'welcome',
          sender: 'copilot',
          text: `Welcome to the **NovaNest Executive AI Copilot**. I am directly connected to your audited MySQL database (304,405 records), the Master Orchestrator, and all 5 domain intelligence agents. Ask any operational, financial, or strategic decision question below.`,
          timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
        },
      ]);
    }
  }, []);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, isQuerying]);

  // Load Summaries when tab active
  useEffect(() => {
    if (activeSubTab === 'summaries') {
      loadSummary(summaryType);
    } else if (activeSubTab === 'root_cause') {
      loadRca(rcaTarget);
    } else if (activeSubTab === 'alerts') {
      loadAlerts();
    } else if (activeSubTab === 'simulator') {
      loadSimulation(simScenario);
    }
  }, [activeSubTab, activeCity]);

  const loadSummary = async (type: string) => {
    setIsLoadingSummary(true);
    try {
      const res = await api.getCopilotSummaries(type, activeCity);
      setSummaryData(res);
    } catch (e) {
      console.error(e);
    } finally {
      setIsLoadingSummary(false);
    }
  };

  const loadRca = async (target: string) => {
    setIsLoadingRca(true);
    try {
      const res = await api.getCopilotRootCause(target, activeCity);
      setRcaData(res);
    } catch (e) {
      console.error(e);
    } finally {
      setIsLoadingRca(false);
    }
  };

  const loadAlerts = async () => {
    setIsLoadingAlerts(true);
    try {
      const res = await api.getCopilotAlerts(activeCity);
      setAlerts(res.alerts || []);
    } catch (e) {
      console.error(e);
    } finally {
      setIsLoadingAlerts(false);
    }
  };

  const loadSimulation = async (scenario: string) => {
    setIsLoadingSim(true);
    try {
      const res = await api.simulateCopilotScenario(scenario);
      setSimData(res);
    } catch (e) {
      console.error(e);
    } finally {
      setIsLoadingSim(false);
    }
  };

  const handleSendQuery = async (queryToSend?: string) => {
    const q = (queryToSend || inputQuery).trim();
    if (!q || isQuerying) return;

    setInputQuery('');
    const userMsgId = `user-${Date.now()}`;
    const copilotMsgId = `copilot-${Date.now()}`;

    setMessages((prev) => [
      ...prev,
      {
        id: userMsgId,
        sender: 'user',
        text: q,
        timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
      },
      {
        id: copilotMsgId,
        sender: 'copilot',
        text: '',
        timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
        isLoading: true,
      },
    ]);

    setIsQuerying(true);

    try {
      const res = await api.queryCopilot(q, 'executive-copilot-session', activeCity);
      setMessages((prev) =>
        prev.map((msg) =>
          msg.id === copilotMsgId
            ? {
                ...msg,
                text: res.answer,
                copilotResponse: res,
                isLoading: false,
              }
            : msg
        )
      );
    } catch (err: any) {
      setMessages((prev) =>
        prev.map((msg) =>
          msg.id === copilotMsgId
            ? {
                ...msg,
                text: `Execution failed: ${err.message || 'Unknown network error'}. Please retry.`,
                isLoading: false,
              }
            : msg
        )
      );
    } finally {
      setIsQuerying(false);
    }
  };

  const handleCopy = (text: string, id: string) => {
    navigator.clipboard.writeText(text);
    setCopiedId(id);
    setTimeout(() => setCopiedId(null), 2000);
  };

  const handleClearHistory = () => {
    setMessages([
      {
        id: 'welcome-reset',
        sender: 'copilot',
        text: `Conversation history reset. You are ready to ask fresh business intelligence questions.`,
        timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
      },
    ]);
  };

  const handleExportMarkdown = () => {
    let md = `# NovaNest Executive AI Copilot Session Report\n`;
    md += `**Date**: ${new Date().toISOString()}\n`;
    md += `**Territory**: ${activeCity}\n`;
    md += `**Grounding**: Audited MySQL 8.0.46 Database (304,405 records)\n\n`;
    md += `## Conversation Transcripts\n\n`;
    messages.forEach((m) => {
      const role = m.sender === 'user' ? 'Executive' : 'NovaNest Copilot';
      md += `### ${role} [${m.timestamp}]\n\n${m.text}\n\n`;
      if (m.copilotResponse) {
        if (m.copilotResponse.verified_metrics && m.copilotResponse.verified_metrics.length > 0) {
          md += `**Verified Facts**:\n`;
          m.copilotResponse.verified_metrics.forEach((f) => {
            md += `- ${f.label}: ${f.value} (${f.provenance || 'MySQL'})\n`;
          });
          md += `\n`;
        }
        if (m.copilotResponse.recommendations && m.copilotResponse.recommendations.length > 0) {
          md += `**Recommendations**:\n`;
          m.copilotResponse.recommendations.forEach((r) => {
            md += `- [${r.confidence || 'RECOMMENDATION'}] ${r.title}: ${r.action} (Impact: ${r.expected_impact})\n`;
          });
          md += `\n`;
        }
      }
    });

    const blob = new Blob([md], { type: 'text/markdown;charset=utf-8' });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = `novanest_copilot_session_${new Date().toISOString().slice(0, 10)}.md`;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    URL.revokeObjectURL(url);
  };

  const handleExportJSON = () => {
    const payload = {
      session_id: 'executive-copilot-session',
      exported_at: new Date().toISOString(),
      territory: activeCity,
      canonical_database_records: 304405,
      messages: messages.map((m) => ({
        id: m.id,
        sender: m.sender,
        timestamp: m.timestamp,
        text: m.text,
        copilotResponse: m.copilotResponse,
      })),
    };
    const blob = new Blob([JSON.stringify(payload, null, 2)], { type: 'application/json;charset=utf-8' });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = `novanest_copilot_session_${new Date().toISOString().slice(0, 10)}.json`;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    URL.revokeObjectURL(url);
  };

  return (
    <div className={`flex flex-col bg-white border border-slate-200 rounded-2xl shadow-sm overflow-hidden ${className}`}>
      {/* Top Header Bar */}
      <div className="flex flex-wrap items-center justify-between px-6 py-4 border-b border-slate-200 bg-slate-50">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-xl bg-blue-50 border border-blue-200 flex items-center justify-center shadow-sm">
            <Sparkles className="w-5 h-5 text-blue-600" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <h2 className="text-base font-semibold text-slate-800 tracking-wide">NovaNest Executive AI Copilot</h2>
              <span className="px-2 py-0.5 rounded-full text-[10px] font-mono tracking-wider uppercase bg-blue-50 text-blue-700 border border-blue-200">
                Phase 14 Certified
              </span>
            </div>
            <p className="text-xs text-slate-500">
              5-Domain Multi-Agent Intelligence • Causal Root Cause • Digital Twin What-If Lab
            </p>
          </div>
        </div>

        {/* Capability Nav Tabs */}
        <div className="flex items-center gap-1.5 p-1 bg-slate-100 rounded-xl border border-slate-200 mt-2 sm:mt-0">
          {[
            { id: 'copilot', label: 'Conversational Copilot', icon: Brain },
            { id: 'summaries', label: 'Executive Summaries', icon: FileText },
            { id: 'root_cause', label: 'Root Cause AI', icon: HelpCircle },
            { id: 'alerts', label: 'Business Alerts', icon: AlertTriangle },
            { id: 'simulator', label: 'What-If Simulator', icon: Sliders },
          ].map((tab) => {
            const Icon = tab.icon;
            const isActive = activeSubTab === tab.id;
            return (
              <button
                key={tab.id}
                onClick={() => setActiveSubTab(tab.id as CopilotTab)}
                className={`flex items-center gap-2 px-3 py-1.5 rounded-lg text-xs font-medium transition-all ${
                  isActive
                    ? 'bg-white text-blue-600 border border-slate-200 shadow-sm font-semibold'
                    : 'text-slate-600 hover:text-slate-900 hover:bg-white/60'
                }`}
              >
                <Icon className={`w-3.5 h-3.5 ${isActive ? 'text-blue-600' : 'text-slate-400'}`} />
                <span>{tab.label}</span>
              </button>
            );
          })}
        </div>
      </div>

      {/* Main Content Pane */}
      <div className="flex-1 overflow-y-auto min-h-[520px] max-h-[680px] p-6 space-y-6">
        {/* ========================================================= */}
        {/* TAB 1: CONVERSATIONAL COPILOT */}
        {/* ========================================================= */}
        {activeSubTab === 'copilot' && (
          <div className="flex flex-col h-full space-y-4">
            {/* Suggested Question Chips */}
            <div className="space-y-2">
              <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 text-xs text-slate-500">
                <span className="flex items-center gap-1.5 font-medium text-slate-700">
                  <Sparkles className="w-3.5 h-3.5 text-blue-600" /> Suggested Executive Inquiries:
                </span>
                <div className="flex items-center gap-2">
                  <button
                    onClick={handleExportMarkdown}
                    className="flex items-center gap-1 text-[11px] px-2 py-1 rounded bg-white hover:bg-slate-50 text-slate-600 hover:text-blue-600 border border-slate-200 transition-colors shadow-xs"
                    title="Export conversation as Markdown"
                    aria-label="Export conversation as Markdown"
                  >
                    <Download className="w-3 h-3 text-blue-600" />
                    <span>Export MD</span>
                  </button>
                  <button
                    onClick={handleExportJSON}
                    className="flex items-center gap-1 text-[11px] px-2 py-1 rounded bg-white hover:bg-slate-50 text-slate-600 hover:text-blue-600 border border-slate-200 transition-colors shadow-xs"
                    title="Export conversation as JSON"
                    aria-label="Export conversation as JSON"
                  >
                    <FileText className="w-3 h-3 text-green-600" />
                    <span>Export JSON</span>
                  </button>
                  <button
                    onClick={handleClearHistory}
                    className="flex items-center gap-1 text-[11px] px-2 py-1 rounded bg-white hover:bg-slate-50 text-slate-500 hover:text-red-600 border border-slate-200 transition-colors shadow-xs"
                    title="Clear conversation history"
                    aria-label="Clear conversation history"
                  >
                    <Trash2 className="w-3 h-3" />
                    <span>Clear</span>
                  </button>
                </div>
              </div>
              <div className="flex flex-wrap gap-2">
                {SUGGESTED_QUESTIONS.map((q, idx) => (
                  <button
                    key={idx}
                    onClick={() => handleSendQuery(q)}
                    disabled={isQuerying}
                    className="px-3 py-1 rounded-full text-xs bg-slate-50 hover:bg-blue-50/60 text-slate-600 hover:text-blue-700 border border-slate-200 hover:border-blue-300 transition-all text-left shadow-xs disabled:opacity-50"
                  >
                    {q}
                  </button>
                ))}
              </div>
            </div>

            {/* Message Feed */}
            <div className="flex-1 space-y-4 pt-4 border-t border-slate-200">
              {messages.map((m) => (
                <div
                  key={m.id}
                  className={`flex flex-col ${m.sender === 'user' ? 'items-end' : 'items-start'} space-y-1`}
                >
                  <div className="flex items-center gap-2 px-1 text-[11px] text-slate-400">
                    <span>{m.sender === 'user' ? 'You (Executive)' : 'NovaNest Copilot'}</span>
                    <span>•</span>
                    <span>{m.timestamp}</span>
                  </div>

                  <div
                    className={`max-w-[85%] rounded-2xl px-4 py-3 text-sm leading-relaxed shadow-xs ${
                      m.sender === 'user'
                        ? 'bg-blue-600 text-white'
                        : 'bg-slate-50 text-slate-800 border border-slate-200'
                    }`}
                  >
                    {m.isLoading ? (
                      <div className="flex items-center gap-3 py-2 text-blue-600">
                        <RefreshCw className="w-4 h-4 animate-spin" />
                        <span className="text-xs">
                          Orchestrating domain agents (Financial, Customer, Operations, Restaurant, Decision)...
                        </span>
                      </div>
                    ) : (
                      <div className="space-y-3">
                        <div className="whitespace-pre-wrap">{m.text}</div>

                        {/* Rich Components attached to Copilot Response */}
                        {m.copilotResponse && (
                          <div className="pt-3 border-t border-slate-200 space-y-3">
                            {/* Multi-Agent Attribution Badges */}
                            {m.copilotResponse.agents_invoked && m.copilotResponse.agents_invoked.length > 0 && (
                              <div className="flex flex-wrap items-center gap-1.5 pt-1">
                                <span className="text-[10px] text-slate-500 font-mono">AGENTS:</span>
                                {m.copilotResponse.agents_invoked.map((ag: any, aIdx: number) => (
                                  <span
                                    key={aIdx}
                                    className="px-2 py-0.5 rounded text-[10px] font-mono bg-blue-50 text-blue-700 border border-blue-200"
                                  >
                                    {ag.agent_id} ({ag.elapsed_ms?.toFixed(0)}ms)
                                  </span>
                                ))}
                                {m.copilotResponse.grounding_verified && (
                                  <span className="px-2 py-0.5 rounded text-[10px] font-mono bg-green-50 text-green-700 border border-green-200 flex items-center gap-1">
                                    <Check className="w-2.5 h-2.5" /> OutputVerifier Certified
                                  </span>
                                )}
                              </div>
                            )}

                            {/* Epistemic Classification Strip */}
                            {m.copilotResponse.epistemic_classification && (
                              <div className="flex flex-wrap items-center gap-2 p-2 rounded-lg bg-white border border-slate-200 text-[11px]">
                                <span className="text-slate-500 font-medium">Data Grounding:</span>
                                <span className="text-blue-700 font-medium">
                                  {m.copilotResponse.epistemic_classification.verified_facts_count} Verified Facts
                                </span>
                                <span>•</span>
                                <span className="text-orange-600 font-medium">
                                  {m.copilotResponse.epistemic_classification.model_predictions_count} ML Predictions
                                </span>
                                <span>•</span>
                                <span className="text-purple-600 font-medium">
                                  {m.copilotResponse.epistemic_classification.strategic_interpretations_count} Strategic Syntheses
                                </span>
                              </div>
                            )}

                            {/* Copy Button */}
                            <div className="flex justify-end pt-1">
                              <button
                                onClick={() => handleCopy(m.text, m.id)}
                                className="flex items-center gap-1.5 text-[11px] text-slate-500 hover:text-blue-600 transition-colors"
                              >
                                {copiedId === m.id ? (
                                  <>
                                    <Check className="w-3.5 h-3.5 text-green-600" /> Copied to clipboard
                                  </>
                                ) : (
                                  <>
                                    <Copy className="w-3.5 h-3.5" /> Copy Answer
                                  </>
                                )}
                              </button>
                            </div>
                          </div>
                        )}
                      </div>
                    )}
                  </div>
                </div>
              ))}
              <div ref={messagesEndRef} />
            </div>

            {/* Input Bar */}
            <div className="pt-3 border-t border-slate-200">
              <form
                onSubmit={(e) => {
                  e.preventDefault();
                  handleSendQuery();
                }}
                className="flex items-center gap-3 bg-white border border-slate-300 rounded-xl px-4 py-2.5 focus-within:border-blue-600 focus-within:ring-2 focus-within:ring-blue-500/20 shadow-xs"
              >
                <input
                  type="text"
                  value={inputQuery}
                  onChange={(e) => setInputQuery(e.target.value)}
                  placeholder="Ask a strategic, financial, operational, or customer question..."
                  className="flex-1 bg-transparent text-sm text-slate-800 placeholder-slate-400 focus:outline-none"
                  disabled={isQuerying}
                />
                <button
                  type="submit"
                  disabled={!inputQuery.trim() || isQuerying}
                  className="p-2 rounded-lg bg-orange-500 hover:bg-orange-600 text-white disabled:opacity-40 disabled:hover:bg-orange-500 transition-colors shadow-xs"
                  title="Send inquiry"
                  aria-label="Send inquiry"
                >
                  <Send className="w-4 h-4" />
                </button>
              </form>
            </div>
          </div>
        )}

        {/* ========================================================= */}
        {/* TAB 2: EXECUTIVE SUMMARIES */}
        {/* ========================================================= */}
        {activeSubTab === 'summaries' && (
          <div className="space-y-6">
            {/* Summary Type Filter Pills */}
            <div className="flex flex-wrap items-center gap-2 pb-2 border-b border-slate-200">
              {[
                { id: 'daily', label: 'Daily Briefing' },
                { id: 'weekly', label: 'Weekly Digest' },
                { id: 'monthly', label: 'Monthly Summary' },
                { id: 'financial_health', label: 'Financial Health' },
                { id: 'customer_health', label: 'Customer Health' },
                { id: 'restaurant_performance', label: 'Restaurant Network' },
                { id: 'operational_risk', label: 'Operational Risk' },
                { id: 'business_opportunities', label: 'Business Opportunities' },
              ].map((s) => (
                <button
                  key={s.id}
                  onClick={() => {
                    setSummaryType(s.id);
                    loadSummary(s.id);
                  }}
                  className={`px-3 py-1.5 rounded-lg text-xs font-medium transition-all ${
                    summaryType === s.id
                      ? 'bg-blue-600 text-white shadow-xs'
                      : 'bg-slate-100 text-slate-600 hover:bg-slate-200'
                  }`}
                >
                  {s.label}
                </button>
              ))}
            </div>

            {isLoadingSummary ? (
              <div className="flex items-center justify-center py-16 text-blue-600 gap-3">
                <RefreshCw className="w-5 h-5 animate-spin" />
                <span>Generating {summaryType.replace('_', ' ')} executive intelligence brief...</span>
              </div>
            ) : summaryData ? (
              <div className="space-y-6">
                <div>
                  <div className="flex items-center justify-between">
                    <h3 className="text-lg font-semibold text-slate-800">{summaryData.title}</h3>
                    <span className="text-xs text-slate-500">{summaryData.reporting_period}</span>
                  </div>
                  <p className="text-xs text-blue-600 font-mono mt-1">Scope: {summaryData.active_scope}</p>
                </div>

                {/* 1. Verified Historical Facts */}
                <div className="p-4 rounded-xl bg-white border border-slate-200 shadow-xs space-y-2">
                  <h4 className="text-xs font-semibold uppercase tracking-wider text-green-700 flex items-center gap-2">
                    <CheckCircle2 className="w-4 h-4 text-green-600" /> 1. Verified Historical Facts (Audited MySQL Records)
                  </h4>
                  <ul className="space-y-1.5 text-xs text-slate-700">
                    {summaryData.verified_historical_facts.map((fact, idx) => (
                      <li key={idx} className="flex items-start gap-2">
                        <span className="text-green-600 font-bold">•</span>
                        <span>{fact}</span>
                      </li>
                    ))}
                  </ul>
                </div>

                {/* 2. Machine Learning Predictions */}
                <div className="p-4 rounded-xl bg-white border border-slate-200 shadow-xs space-y-2">
                  <h4 className="text-xs font-semibold uppercase tracking-wider text-orange-600 flex items-center gap-2">
                    <Brain className="w-4 h-4 text-orange-500" /> 2. Machine Learning Predictions & Confidence Tiers
                  </h4>
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-3 pt-1">
                    {summaryData.model_predictions.map((p, idx) => (
                      <div key={idx} className="p-3 rounded-lg bg-slate-50 border border-slate-200 space-y-1 text-xs">
                        <div className="flex items-center justify-between">
                          <span className="font-semibold text-slate-800">{p.metric}</span>
                          <span
                            className={`px-2 py-0.5 rounded text-[10px] font-mono ${
                              p.confidence.includes('HIGH')
                                ? 'bg-green-50 text-green-700 border border-green-200'
                                : 'bg-orange-50 text-orange-700 border border-orange-200'
                            }`}
                          >
                            {p.confidence}
                          </span>
                        </div>
                        <p className="text-blue-700 font-medium">{p.value}</p>
                        <p className="text-[10px] text-slate-500">Model: {p.model}</p>
                      </div>
                    ))}
                  </div>
                </div>

                {/* 3. Strategic Interpretations */}
                <div className="p-4 rounded-xl bg-white border border-slate-200 shadow-xs space-y-2">
                  <h4 className="text-xs font-semibold uppercase tracking-wider text-blue-700 flex items-center gap-2">
                    <Sparkles className="w-4 h-4 text-blue-600" /> 3. Strategic Multi-Agent Interpretations
                  </h4>
                  <ul className="space-y-1.5 text-xs text-slate-700">
                    {summaryData.strategic_interpretations.map((interp, idx) => (
                      <li key={idx} className="flex items-start gap-2">
                        <span className="text-blue-600 font-bold">•</span>
                        <span>{interp}</span>
                      </li>
                    ))}
                  </ul>
                </div>

                {/* 4. Simulated Projections */}
                <div className="p-4 rounded-xl bg-white border border-slate-200 shadow-xs space-y-2">
                  <h4 className="text-xs font-semibold uppercase tracking-wider text-slate-800 flex items-center gap-2">
                    <Sliders className="w-4 h-4 text-slate-600" /> 4. Counterfactual Scenario Projections (is_simulation_projection=True)
                  </h4>
                  <ul className="space-y-1.5 text-xs text-slate-700">
                    {summaryData.simulated_projections.map((sim, idx) => (
                      <li key={idx} className="flex items-start gap-2">
                        <span className="text-orange-500 font-bold">•</span>
                        <span>
                          <strong className="text-slate-900">{sim.scenario}</strong>: {sim.projected_benefit}
                        </span>
                      </li>
                    ))}
                  </ul>
                </div>

                {/* Epistemic Notice */}
                <div className="p-3 rounded-lg bg-blue-50 border border-blue-200 text-xs text-blue-800 flex items-start gap-2">
                  <Info className="w-4 h-4 text-blue-600 shrink-0 mt-0.5" />
                  <span>{summaryData.epistemic_notice}</span>
                </div>
              </div>
            ) : null}
          </div>
        )}

        {/* ========================================================= */}
        {/* TAB 3: ROOT CAUSE INTELLIGENCE */}
        {/* ========================================================= */}
        {activeSubTab === 'root_cause' && (
          <div className="space-y-6">
            <div className="flex flex-wrap items-center gap-2 pb-2 border-b border-slate-200">
              {[
                { id: 'revenue_decline', label: 'Why Did Revenue / Margin Drop?' },
                { id: 'delivery_delays', label: 'Why Are Deliveries Delayed (>45m)?' },
                { id: 'cancellations', label: 'Why Are Cancellations Increasing?' },
                { id: 'customer_churn', label: 'Why Is Customer Retention Declining?' },
              ].map((t) => (
                <button
                  key={t.id}
                  onClick={() => {
                    setRcaTarget(t.id);
                    loadRca(t.id);
                  }}
                  className={`px-3 py-1.5 rounded-lg text-xs font-medium transition-all ${
                    rcaTarget === t.id
                      ? 'bg-blue-600 text-white shadow-xs'
                      : 'bg-slate-100 text-slate-600 hover:bg-slate-200'
                  }`}
                >
                  {t.label}
                </button>
              ))}
            </div>

            {isLoadingRca ? (
              <div className="flex items-center justify-center py-16 text-blue-600 gap-3">
                <RefreshCw className="w-5 h-5 animate-spin" />
                <span>Investigating causal factors across multi-table datasets...</span>
              </div>
            ) : rcaData ? (
              <div className="space-y-6">
                <div>
                  <h3 className="text-lg font-semibold text-slate-800">{rcaData.target_kpi}</h3>
                  <p className="text-xs text-slate-500 mt-1">
                    Data-grounded causal diagnosis combining operations, merchant SLAs, and financial margins.
                  </p>
                </div>

                {/* Contributing Factors */}
                <div className="space-y-3">
                  <h4 className="text-xs font-semibold uppercase tracking-wider text-slate-500">
                    Contributing Factors & Dimensional Weights
                  </h4>
                  <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
                    {rcaData.contributing_factors.map((f, idx) => (
                      <div
                        key={idx}
                        className="p-4 rounded-xl bg-white border border-slate-200 shadow-xs space-y-2 text-xs"
                      >
                        <div className="flex items-center justify-between">
                          <span className="font-semibold text-slate-800">{f.factor}</span>
                          <span className="px-2 py-0.5 rounded text-[10px] font-mono bg-blue-50 text-blue-700 border border-blue-200 font-medium">
                            Weight: {f.contribution_weight}
                          </span>
                        </div>
                        <p className="text-slate-600">{f.evidence}</p>
                      </div>
                    ))}
                  </div>
                </div>

                {/* Correlation vs Causation */}
                <div className="p-4 rounded-xl bg-orange-50 border border-orange-200 space-y-1.5 text-xs">
                  <h4 className="font-semibold text-orange-800 flex items-center gap-2">
                    <ShieldAlert className="w-4 h-4 text-orange-600" /> Correlation vs. Causation Analysis
                  </h4>
                  <p className="text-slate-700 leading-relaxed">{rcaData.correlation_vs_causation}</p>
                </div>

                {/* Recommended Investigative Actions */}
                <div className="p-4 rounded-xl bg-white border border-slate-200 shadow-xs space-y-2 text-xs">
                  <h4 className="font-semibold text-slate-800">Recommended Investigative Next Steps</h4>
                  <ul className="space-y-1.5 text-slate-600">
                    {rcaData.recommended_investigative_actions.map((act, idx) => (
                      <li key={idx} className="flex items-start gap-2">
                        <CheckCircle2 className="w-3.5 h-3.5 text-blue-600 mt-0.5 shrink-0" />
                        <span>{act}</span>
                      </li>
                    ))}
                  </ul>
                </div>
              </div>
            ) : null}
          </div>
        )}

        {/* ========================================================= */}
        {/* TAB 4: PROACTIVE BUSINESS ALERTS */}
        {/* ========================================================= */}
        {activeSubTab === 'alerts' && (
          <div className="space-y-4">
            <div className="flex items-center justify-between">
              <div>
                <h3 className="text-base font-semibold text-slate-800">AI Business Alert Center</h3>
                <p className="text-xs text-slate-500">
                  Autonomic surveillance scanning operational, financial, merchant, and customer streams.
                </p>
              </div>
              <button
                onClick={loadAlerts}
                className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs bg-white hover:bg-slate-50 text-slate-700 border border-slate-200 transition-colors shadow-xs"
              >
                <RefreshCw className="w-3.5 h-3.5" /> Refresh Alerts
              </button>
            </div>

            {isLoadingAlerts ? (
              <div className="flex items-center justify-center py-16 text-blue-600 gap-3">
                <RefreshCw className="w-5 h-5 animate-spin" />
                <span>Scanning active business streams...</span>
              </div>
            ) : (
              <div className="space-y-3">
                {alerts.map((a) => {
                  const isCrit = a.severity === 'Critical';
                  const isHigh = a.severity === 'High';
                  return (
                    <div
                      key={a.alert_id}
                      className={`p-4 rounded-xl border transition-all space-y-2 text-xs shadow-xs ${
                        isCrit
                          ? 'bg-red-50/60 border-red-200'
                          : isHigh
                          ? 'bg-orange-50/60 border-orange-200'
                          : 'bg-white border-slate-200'
                      }`}
                    >
                      <div className="flex items-center justify-between">
                        <div className="flex items-center gap-2">
                          <span
                            className={`px-2 py-0.5 rounded text-[10px] font-bold uppercase tracking-wider ${
                              isCrit
                                ? 'bg-red-100 text-red-700'
                                : isHigh
                                ? 'bg-orange-100 text-orange-700'
                                : 'bg-slate-100 text-slate-700'
                            }`}
                          >
                            {a.severity}
                          </span>
                          <span className="font-semibold text-slate-800 text-sm">{a.title}</span>
                        </div>
                        <span className="text-[10px] text-slate-400 font-mono">{a.detection_time}</span>
                      </div>

                      <p className="text-slate-600">{a.summary}</p>

                      <div className="grid grid-cols-1 md:grid-cols-2 gap-2 pt-1 text-[11px]">
                        <div className="p-2 rounded bg-white border border-slate-200">
                          <span className="text-slate-500 font-medium">Evidence: </span>
                          <span className="text-slate-700">{a.supporting_evidence}</span>
                        </div>
                        <div className="p-2 rounded bg-white border border-slate-200">
                          <span className="text-slate-500 font-medium">Action: </span>
                          <span className="text-orange-600 font-medium">{a.recommended_action}</span>
                        </div>
                      </div>
                    </div>
                  );
                })}
              </div>
            )}
          </div>
        )}

        {/* ========================================================= */}
        {/* TAB 5: WHAT-IF SCENARIO SIMULATOR */}
        {/* ========================================================= */}
        {activeSubTab === 'simulator' && (
          <div className="space-y-6">
            <div className="flex flex-wrap items-center gap-2 pb-2 border-b border-slate-200">
              {[
                { id: 'promotion_optimization', label: 'Promotions (20% Cap)' },
                { id: 'delivery_fee_restructuring', label: 'Delivery Fee (+₹10 >5km)' },
                { id: 'rider_capacity_expansion', label: 'Rider Capacity (+15% Peak)' },
                { id: 'restaurant_capacity_acceleration', label: 'Kitchen Prep (-5m Buffer)' },
                { id: 'customer_retention_campaign', label: 'VIP Retention Campaign' },
                { id: 'order_demand_fluctuation', label: 'Macro Demand (+10% Surge)' },
              ].map((s) => (
                <button
                  key={s.id}
                  onClick={() => {
                    setSimScenario(s.id);
                    loadSimulation(s.id);
                  }}
                  className={`px-3 py-1.5 rounded-lg text-xs font-medium transition-all ${
                    simScenario === s.id
                      ? 'bg-blue-600 text-white shadow-xs'
                      : 'bg-slate-100 text-slate-600 hover:bg-slate-200'
                  }`}
                >
                  {s.label}
                </button>
              ))}
            </div>

            {isLoadingSim ? (
              <div className="flex items-center justify-center py-16 text-blue-600 gap-3">
                <RefreshCw className="w-5 h-5 animate-spin" />
                <span>Running Digital Twin counterfactual scenario simulation...</span>
              </div>
            ) : simData ? (
              <div className="space-y-6">
                <div>
                  <div className="flex items-center justify-between">
                    <h3 className="text-lg font-semibold text-slate-800">{simData.scenario_title}</h3>
                    <span className="px-2.5 py-0.5 rounded text-[10px] font-mono uppercase tracking-wider bg-orange-50 text-orange-700 border border-orange-200">
                      Simulated Estimate
                    </span>
                  </div>
                  <p className="text-xs text-slate-500 mt-1">{simData.disclaimer}</p>
                </div>

                {/* Comparison Table */}
                <div className="rounded-xl border border-slate-200 overflow-hidden text-xs shadow-xs bg-white">
                  <table className="w-full text-left">
                    <thead className="bg-slate-50 text-slate-600 font-mono uppercase text-[10px] border-b border-slate-200">
                      <tr>
                        <th className="p-3">Key Metric</th>
                        <th className="p-3">Baseline Scenario</th>
                        <th className="p-3">Projected Outcome</th>
                        <th className="p-3 text-right">Variance Delta</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-slate-100 text-slate-700">
                      <tr>
                        <td className="p-3 font-semibold text-slate-900">Delivered Orders</td>
                        <td className="p-3">{simData.baseline.delivered_orders.toLocaleString()}</td>
                        <td className="p-3 text-blue-600 font-medium">{simData.projected_outcomes.projected_delivered_orders.toLocaleString()}</td>
                        <td className="p-3 text-right font-mono font-medium text-green-600">
                          {simData.variance_deltas.orders_delta > 0 ? '+' : ''}
                          {simData.variance_deltas.orders_delta.toLocaleString()}
                        </td>
                      </tr>
                      <tr>
                        <td className="p-3 font-semibold text-slate-900">Gross Merchandise Value (GMV)</td>
                        <td className="p-3">₹{simData.baseline.realized_gross_gmv.toLocaleString(undefined, { minimumFractionDigits: 2 })}</td>
                        <td className="p-3 text-blue-600 font-medium">₹{simData.projected_outcomes.projected_gross_gmv.toLocaleString(undefined, { minimumFractionDigits: 2 })}</td>
                        <td className="p-3 text-right font-mono font-medium text-green-600">
                          {simData.variance_deltas.gmv_delta > 0 ? '+' : ''}₹{simData.variance_deltas.gmv_delta.toLocaleString(undefined, { minimumFractionDigits: 2 })}
                        </td>
                      </tr>
                      <tr>
                        <td className="p-3 font-semibold text-slate-900">Net Contribution Margin</td>
                        <td className="p-3">₹{simData.baseline.net_contribution_margin.toLocaleString(undefined, { minimumFractionDigits: 2 })}</td>
                        <td className="p-3 text-blue-600 font-medium">₹{simData.projected_outcomes.projected_contribution_margin.toLocaleString(undefined, { minimumFractionDigits: 2 })}</td>
                        <td className="p-3 text-right font-mono font-bold text-green-600">
                          {simData.variance_deltas.margin_delta_rupees > 0 ? '+' : ''}₹{simData.variance_deltas.margin_delta_rupees.toLocaleString(undefined, { minimumFractionDigits: 2 })}
                        </td>
                      </tr>
                      <tr>
                        <td className="p-3 font-semibold text-slate-900">SLA Breaches (&gt;45 min)</td>
                        <td className="p-3">{simData.baseline.sla_breach_count.toLocaleString()} ({simData.baseline.sla_breach_rate_pct}%)</td>
                        <td className="p-3 text-blue-600 font-medium">{simData.projected_outcomes.projected_sla_breaches.toLocaleString()} ({simData.projected_outcomes.projected_sla_breach_rate_pct}%)</td>
                        <td className="p-3 text-right font-mono font-medium text-blue-600">
                          {simData.variance_deltas.sla_breaches_prevented > 0 ? '+' : ''}{simData.variance_deltas.sla_breaches_prevented.toLocaleString()} prevented
                        </td>
                      </tr>
                    </tbody>
                  </table>
                </div>

                {/* Assumptions */}
                <div className="p-4 rounded-xl bg-white border border-slate-200 shadow-xs space-y-2 text-xs">
                  <h4 className="font-semibold text-slate-800">Mathematical Model Assumptions</h4>
                  <ul className="space-y-1.5 text-slate-600">
                    {simData.scenario_assumptions.map((assump: string, idx: number) => (
                      <li key={idx} className="flex items-start gap-2">
                        <span className="text-blue-600 font-bold">•</span>
                        <span>{assump}</span>
                      </li>
                    ))}
                  </ul>
                </div>
              </div>
            ) : null}
          </div>
        )}
      </div>
    </div>
  );
}
