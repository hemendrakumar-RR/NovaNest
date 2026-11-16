import React, { useEffect, useState, useMemo } from 'react';
import {
  BrainCircuit,
  ShieldCheck,
  CheckCircle2,
  AlertTriangle,
  ArrowRight,
  TrendingUp,
  Sliders,
  Sparkles,
  Users,
  Store,
  Truck,
  Filter,
  Search,
  DollarSign,
  Clock,
  FileText,
  Check,
  X,
  BarChart3,
  AlertCircle,
  RotateCcw,
  ChevronRight,
  Activity,
  ShieldAlert,
  Percent,
} from 'lucide-react';
import {
  ResponsiveContainer,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  CartesianGrid,
  Legend,
  Cell,
} from 'recharts';
import { SectionHeader } from '../components/SectionHeader';
import { ApiErrorState, EmptyStateCard } from '../components/ApiStatePanel';
import { ErrorBoundary } from '../components/ErrorBoundary';
import {
  api,
  PrescriptiveRecommendation,
  PrescriptiveSummary,
  PrescriptiveFinancialCharts,
} from '../services/api';
import { TabKey } from '../components/Sidebar';
import { formatCurrency, formatNumber } from '../utils/formatters';

interface Props {
  onNavigate: (tab: TabKey) => void;
}

export const DecisionIntelligenceView: React.FC<Props> = ({ onNavigate }) => {
  const [recommendations, setRecommendations] = useState<PrescriptiveRecommendation[]>([]);
  const [summary, setSummary] = useState<PrescriptiveSummary | null>(null);
  const [financialCharts, setFinancialCharts] = useState<PrescriptiveFinancialCharts | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<unknown>(null);

  // View mode
  const [viewMode, setViewMode] = useState<'cards' | 'financials'>('cards');

  // Filters
  const [searchQuery, setSearchQuery] = useState('');
  const [domainFilter, setDomainFilter] = useState('ALL');
  const [priorityFilter, setPriorityFilter] = useState('ALL');
  const [confidenceFilter, setConfidenceFilter] = useState('ALL');
  const [statusFilter, setStatusFilter] = useState('ALL');

  // Modals & Action States
  const [selectedRec, setSelectedRec] = useState<PrescriptiveRecommendation | null>(null);
  const [actionModalType, setActionModalType] = useState<
    'details' | 'approve' | 'reject' | 'record_outcome' | null
  >(null);
  const [operatorName, setOperatorName] = useState('Operations Executive');
  const [actionNotes, setActionNotes] = useState('');
  const [actionSubmitting, setActionSubmitting] = useState(false);
  const [actionFeedback, setActionFeedback] = useState<{ type: 'success' | 'error'; message: string } | null>(null);

  // Outcome recording state
  const [outcomeRealizedBenefit, setOutcomeRealizedBenefit] = useState<number>(0);
  const [outcomeActualCost, setOutcomeActualCost] = useState<number>(0);
  const [outcomeNotes, setOutcomeNotes] = useState('Audited realized financial outcome post-implementation');

  const loadData = () => {
    setLoading(true);
    setError(null);
    Promise.all([
      api.getPrescriptiveRecommendations(),
      api.getPrescriptiveSummary(),
      api.getPrescriptiveFinancialCharts(),
    ])
      .then(([recsRes, summaryRes, chartsRes]) => {
        setRecommendations(Array.isArray(recsRes) ? recsRes : []);
        setSummary(summaryRes);
        setFinancialCharts(chartsRes);
      })
      .catch((err) => {
        console.error('Prescriptive intelligence error:', err);
        setError(err);
      })
      .finally(() => setLoading(false));
  };

  useEffect(() => {
    loadData();
  }, []);

  // Filtered recommendations
  const filteredRecs = useMemo(() => {
    return recommendations.filter((rec) => {
      if (domainFilter !== 'ALL' && rec.domain !== domainFilter) return false;
      if (priorityFilter !== 'ALL' && rec.priority !== priorityFilter) return false;
      if (confidenceFilter !== 'ALL' && rec.confidence_tier !== confidenceFilter) return false;
      if (statusFilter !== 'ALL' && rec.status !== statusFilter) return false;
      if (searchQuery.trim()) {
        const q = searchQuery.toLowerCase();
        const matchId = rec.recommendation_id.toLowerCase().includes(q);
        const matchProb = rec.problem_statement.toLowerCase().includes(q);
        const matchAct = rec.proposed_action.toLowerCase().includes(q);
        const matchDom = rec.domain.toLowerCase().includes(q);
        if (!matchId && !matchProb && !matchAct && !matchDom) return false;
      }
      return true;
    });
  }, [recommendations, domainFilter, priorityFilter, confidenceFilter, statusFilter, searchQuery]);

  // Lifecycle action handlers
  const handleOpenApprove = (rec: PrescriptiveRecommendation) => {
    setSelectedRec(rec);
    setActionModalType('approve');
    setActionNotes(`Approved for operational rollout by ${operatorName}`);
    setActionFeedback(null);
  };

  const handleOpenReject = (rec: PrescriptiveRecommendation) => {
    setSelectedRec(rec);
    setActionModalType('reject');
    setActionNotes('');
    setActionFeedback(null);
  };

  const handleOpenDetails = (rec: PrescriptiveRecommendation) => {
    setSelectedRec(rec);
    setActionModalType('details');
    setActionFeedback(null);
  };

  const handleOpenRecordOutcome = (rec: PrescriptiveRecommendation) => {
    setSelectedRec(rec);
    setActionModalType('record_outcome');
    setOutcomeRealizedBenefit(rec.expected_gross_benefit_rupees);
    setOutcomeActualCost(rec.implementation_cost_rupees);
    setOutcomeNotes(`Audited 30-day post-rollout performance for ${rec.recommendation_id}`);
    setActionFeedback(null);
  };

  const handleApproveSubmit = async () => {
    if (!selectedRec) return;
    setActionSubmitting(true);
    setActionFeedback(null);
    try {
      const res = await api.approvePrescriptiveRecommendation(
        selectedRec.recommendation_id,
        operatorName,
        actionNotes
      );
      setRecommendations((prev) =>
        prev.map((r) => (r.recommendation_id === res.recommendation.recommendation_id ? res.recommendation : r))
      );
      setActionFeedback({ type: 'success', message: `${res.recommendation.recommendation_id} successfully approved.` });
      setTimeout(() => {
        setActionModalType(null);
        loadData();
      }, 1000);
    } catch (err: any) {
      setActionFeedback({ type: 'error', message: err?.detail || err?.message || 'Approval failed' });
    } finally {
      setActionSubmitting(false);
    }
  };

  const handleRejectSubmit = async () => {
    if (!selectedRec) return;
    if (!actionNotes.trim()) {
      setActionFeedback({ type: 'error', message: 'Rejection reason is mandatory.' });
      return;
    }
    setActionSubmitting(true);
    setActionFeedback(null);
    try {
      const res = await api.rejectPrescriptiveRecommendation(
        selectedRec.recommendation_id,
        operatorName,
        actionNotes
      );
      setRecommendations((prev) =>
        prev.map((r) => (r.recommendation_id === res.recommendation.recommendation_id ? res.recommendation : r))
      );
      setActionFeedback({ type: 'success', message: `${res.recommendation.recommendation_id} rejected.` });
      setTimeout(() => {
        setActionModalType(null);
        loadData();
      }, 1000);
    } catch (err: any) {
      setActionFeedback({ type: 'error', message: err?.detail || err?.message || 'Rejection failed' });
    } finally {
      setActionSubmitting(false);
    }
  };

  const handleStartProgress = async (rec: PrescriptiveRecommendation) => {
    setActionSubmitting(true);
    try {
      const res = await api.startPrescriptiveProgress(rec.recommendation_id, operatorName);
      setRecommendations((prev) =>
        prev.map((r) => (r.recommendation_id === res.recommendation.recommendation_id ? res.recommendation : r))
      );
      loadData();
    } catch (err: any) {
      alert(`Cannot start progress: ${err?.detail || err?.message}`);
    } finally {
      setActionSubmitting(false);
    }
  };

  const handleMarkImplemented = async (rec: PrescriptiveRecommendation) => {
    setActionSubmitting(true);
    try {
      const res = await api.markPrescriptiveImplemented(rec.recommendation_id, operatorName);
      setRecommendations((prev) =>
        prev.map((r) => (r.recommendation_id === res.recommendation.recommendation_id ? res.recommendation : r))
      );
      loadData();
    } catch (err: any) {
      alert(`Cannot mark implemented: ${err?.detail || err?.message}`);
    } finally {
      setActionSubmitting(false);
    }
  };

  const handleRecordOutcomeSubmit = async () => {
    if (!selectedRec) return;
    setActionSubmitting(true);
    setActionFeedback(null);
    try {
      const res = await api.recordPrescriptiveOutcome(selectedRec.recommendation_id, {
        realized_gross_benefit: Number(outcomeRealizedBenefit),
        actual_cost: Number(outcomeActualCost),
        measured_by: operatorName,
        audit_notes: outcomeNotes,
      });
      setRecommendations((prev) =>
        prev.map((r) => (r.recommendation_id === res.recommendation.recommendation_id ? res.recommendation : r))
      );
      setActionFeedback({ type: 'success', message: `Audited outcome recorded for ${res.recommendation.recommendation_id}.` });
      setTimeout(() => {
        setActionModalType(null);
        loadData();
      }, 1000);
    } catch (err: any) {
      setActionFeedback({ type: 'error', message: err?.detail || err?.message || 'Recording outcome failed' });
    } finally {
      setActionSubmitting(false);
    }
  };

  const domainIcons: Record<string, any> = {
    customer_retention: Users,
    revenue_optimization: DollarSign,
    restaurant_optimization: Store,
    rider_logistics: Truck,
  };

  const domainLabels: Record<string, string> = {
    customer_retention: 'Customer Retention',
    revenue_optimization: 'Revenue Optimization',
    restaurant_optimization: 'Restaurant Optimization',
    rider_logistics: 'Rider Logistics',
  };

  const getStatusBadge = (status: string) => {
    switch (status) {
      case 'Approved':
        return 'bg-emerald-500/20 text-emerald-400 border-emerald-500/30';
      case 'In Progress':
        return 'bg-cyan-500/20 text-cyan-400 border-cyan-500/30';
      case 'Implemented':
        return 'bg-indigo-500/20 text-indigo-400 border-indigo-500/30';
      case 'Outcome Recorded':
        return 'bg-purple-500/20 text-purple-400 border-purple-500/30';
      case 'Rejected':
        return 'bg-rose-500/20 text-rose-400 border-rose-500/30';
      case 'Under Review':
        return 'bg-amber-500/20 text-amber-400 border-amber-500/30';
      default:
        return 'bg-sapphire-500/20 text-sapphire-400 border-sapphire-500/30';
    }
  };

  const getConfidenceBadge = (tier: string) => {
    switch (tier) {
      case 'HIGH':
        return 'bg-emerald-500/20 text-emerald-300 border-emerald-500/40';
      case 'MODERATE':
        return 'bg-sky-500/20 text-sky-300 border-sky-500/40';
      case 'OPERATIONAL_GATED':
        return 'bg-amber-500/20 text-amber-300 border-amber-500/40';
      case 'LOW_EMPIRICAL':
        return 'bg-rose-500/20 text-rose-300 border-rose-500/40';
      default:
        return 'bg-slate-700 text-slate-300 border-slate-600';
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-96">
        <div className="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-sapphire-500" />
      </div>
    );
  }

  if (error) {
    return (
      <ApiErrorState
        title="Executive Recommendation Center Unavailable"
        error={error}
        onRetry={loadData}
      />
    );
  }

  return (
    <div className="space-y-8 animate-fadeIn">
      {/* Top Header */}
      <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2 mb-1">
            <span className="text-xs font-bold uppercase tracking-widest text-sapphire-400">
              PHASE 09 EXECUTIVE SUITE
            </span>
            <span className="text-slate-600">•</span>
            <span className="text-xs text-slate-400">Prescriptive Decision Action Center</span>
          </div>
          <h1 className="text-3xl font-extrabold tracking-tight text-white flex items-center gap-3">
            <BrainCircuit className="text-sapphire-400" size={32} />
            Executive Recommendation Center
          </h1>
          <p className="text-sm text-slate-400 mt-1 max-w-3xl">
            Human-in-the-loop decision intelligence platform. Review, approve, deploy, and audit evidence-grounded
            prescriptive interventions across customer retention, pricing & margins, restaurant capacity, and rider fleet.
          </p>
        </div>

        {/* View Mode Toggle & Actions */}
        <div className="flex items-center gap-3">
          <div className="flex rounded-lg bg-obsidian-900 p-1 border border-slate-800">
            <button
              onClick={() => setViewMode('cards')}
              className={`px-3 py-1.5 text-xs font-semibold rounded-md transition-all flex items-center gap-1.5 ${
                viewMode === 'cards'
                  ? 'bg-sapphire-600 text-white shadow-sm'
                  : 'text-slate-400 hover:text-white'
              }`}
            >
              <FileText size={14} /> Action Center
            </button>
            <button
              onClick={() => setViewMode('financials')}
              className={`px-3 py-1.5 text-xs font-semibold rounded-md transition-all flex items-center gap-1.5 ${
                viewMode === 'financials'
                  ? 'bg-sapphire-600 text-white shadow-sm'
                  : 'text-slate-400 hover:text-white'
              }`}
            >
              <BarChart3 size={14} /> Financial Waterfall
            </button>
          </div>

          <button
            onClick={() => onNavigate('simulator')}
            className="px-4 py-2 rounded-lg bg-obsidian-900 hover:bg-obsidian-800 text-slate-200 border border-slate-700 text-xs font-semibold flex items-center gap-2 transition-all shadow-sm"
          >
            <Sliders size={14} className="text-sapphire-400" />
            What-If Simulator
          </button>
        </div>
      </div>

      {/* EXECUTIVE KPI SUMMARY BAR */}
      {summary && (
        <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
          <div className="glass-card p-4 rounded-xl border border-slate-800/80 bg-obsidian-900/60">
            <span className="text-[11px] font-bold uppercase tracking-wider text-slate-400">
              Active Interventions
            </span>
            <div className="mt-1 flex items-baseline gap-2">
              <span className="text-2xl font-black text-white">{summary.total_recommendations}</span>
              <span className="text-xs text-slate-500 font-mono">Canonical IDs</span>
            </div>
            <div className="mt-2 text-[11px] text-slate-400 flex items-center gap-1">
              <ShieldCheck size={13} className="text-emerald-400" /> 100% Deterministic
            </div>
          </div>

          <div className="glass-card p-4 rounded-xl border border-slate-800/80 bg-obsidian-900/60">
            <span className="text-[11px] font-bold uppercase tracking-wider text-slate-400">
              Gross Projected Benefit
            </span>
            <div className="mt-1 flex items-baseline gap-2">
              <span className="text-2xl font-black text-emerald-400">
                {formatCurrency(summary.total_gross_benefit_rupees)}
              </span>
            </div>
            <div className="mt-2 text-[11px] text-slate-400 flex items-center gap-1">
              <TrendingUp size={13} className="text-emerald-400" /> Pre-cost Revenue & Savings
            </div>
          </div>

          <div className="glass-card p-4 rounded-xl border border-slate-800/80 bg-obsidian-900/60">
            <span className="text-[11px] font-bold uppercase tracking-wider text-slate-400">
              Implementation Cost
            </span>
            <div className="mt-1 flex items-baseline gap-2">
              <span className="text-2xl font-black text-rose-400">
                {formatCurrency(summary.total_implementation_cost_rupees)}
              </span>
            </div>
            <div className="mt-2 text-[11px] text-slate-400 flex items-center gap-1">
              <DollarSign size={13} className="text-rose-400" /> Subsidies & Operational Pools
            </div>
          </div>

          <div className="glass-card p-4 rounded-xl border border-slate-800/80 bg-obsidian-900/60">
            <span className="text-[11px] font-bold uppercase tracking-wider text-slate-400">
              Net Financial Impact
            </span>
            <div className="mt-1 flex items-baseline gap-2">
              <span className="text-2xl font-black text-cyan-400">
                {formatCurrency(summary.total_net_financial_impact_rupees)}
              </span>
            </div>
            <div className="mt-2 text-[11px] text-slate-400 flex items-center gap-1">
              <Sparkles size={13} className="text-cyan-400" /> Net Bottom-line Uplift
            </div>
          </div>

          <div className="glass-card p-4 rounded-xl border border-slate-800/80 bg-obsidian-900/60">
            <span className="text-[11px] font-bold uppercase tracking-wider text-slate-400">
              Portfolio ROI Multiple
            </span>
            <div className="mt-1 flex items-baseline gap-2">
              <span className="text-2xl font-black text-amber-300">
                {summary.overall_roi_multiple.toFixed(2)}x
              </span>
              <span className="text-xs text-amber-400/80 font-mono">Net/Cost</span>
            </div>
            <div className="mt-2 text-[11px] text-slate-400 flex items-center gap-1">
              <Activity size={13} className="text-amber-400" /> Blended Platform Return
            </div>
          </div>
        </div>
      )}

      {/* VIEW MODE 1: ACTION CENTER CARDS */}
      {viewMode === 'cards' && (
        <div className="space-y-6">
          {/* SEARCH & MULTI-CRITERIA FILTERS */}
          <div className="glass-card p-4 rounded-xl border border-slate-800 space-y-3">
            <div className="flex flex-col md:flex-row items-center gap-3">
              <div className="relative flex-1 w-full">
                <Search className="absolute left-3 top-2.5 text-slate-500" size={16} />
                <input
                  type="text"
                  placeholder="Search by ID (e.g. REC-RET-VIP-001), domain, problem, or action..."
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  className="w-full pl-9 pr-4 py-2 bg-obsidian-950/80 border border-slate-800 rounded-lg text-xs text-white placeholder-slate-500 focus:outline-none focus:border-sapphire-500 transition-colors"
                />
              </div>

              <div className="flex items-center gap-2 w-full md:w-auto">
                {/* Domain Filter */}
                <select
                  value={domainFilter}
                  onChange={(e) => setDomainFilter(e.target.value)}
                  aria-label="Filter by Business Domain"
                  className="bg-obsidian-950 border border-slate-800 rounded-lg text-xs text-slate-300 py-2 px-3 focus:outline-none focus:border-sapphire-500"
                >
                  <option value="ALL">All Domains</option>
                  <option value="customer_retention">Customer Retention</option>
                  <option value="revenue_optimization">Revenue Optimization</option>
                  <option value="restaurant_optimization">Restaurant Optimization</option>
                  <option value="rider_logistics">Rider Logistics</option>
                </select>

                {/* Priority Filter */}
                <select
                  value={priorityFilter}
                  onChange={(e) => setPriorityFilter(e.target.value)}
                  aria-label="Filter by Priority"
                  className="bg-obsidian-950 border border-slate-800 rounded-lg text-xs text-slate-300 py-2 px-3 focus:outline-none focus:border-sapphire-500"
                >
                  <option value="ALL">All Priorities</option>
                  <option value="CRITICAL">Critical</option>
                  <option value="HIGH">High</option>
                  <option value="MEDIUM">Medium</option>
                  <option value="LOW">Low</option>
                </select>

                {/* Confidence Tier Filter */}
                <select
                  value={confidenceFilter}
                  onChange={(e) => setConfidenceFilter(e.target.value)}
                  aria-label="Filter by Confidence Tier"
                  className="bg-obsidian-950 border border-slate-800 rounded-lg text-xs text-slate-300 py-2 px-3 focus:outline-none focus:border-sapphire-500"
                >
                  <option value="ALL">All Confidence Tiers</option>
                  <option value="HIGH">HIGH (Deterministic Empirical)</option>
                  <option value="MODERATE">MODERATE (Statistical Model)</option>
                  <option value="OPERATIONAL_GATED">OPERATIONAL_GATED (Batch Telemetry)</option>
                  <option value="LOW_EMPIRICAL">LOW_EMPIRICAL (Exploratory Only)</option>
                </select>

                {/* Status Filter */}
                <select
                  value={statusFilter}
                  onChange={(e) => setStatusFilter(e.target.value)}
                  aria-label="Filter by Lifecycle Status"
                  className="bg-obsidian-950 border border-slate-800 rounded-lg text-xs text-slate-300 py-2 px-3 focus:outline-none focus:border-sapphire-500"
                >
                  <option value="ALL">All Lifecycle Statuses</option>
                  <option value="Proposed">Proposed</option>
                  <option value="Under Review">Under Review</option>
                  <option value="Approved">Approved</option>
                  <option value="In Progress">In Progress</option>
                  <option value="Implemented">Implemented</option>
                  <option value="Outcome Recorded">Outcome Recorded</option>
                  <option value="Rejected">Rejected</option>
                </select>
              </div>
            </div>

            <div className="flex items-center justify-between text-xs text-slate-400 pt-1 border-t border-slate-800/60">
              <span className="flex items-center gap-1.5">
                <ShieldAlert size={14} className="text-amber-400" />
                <span className="font-semibold text-slate-300">Governance Policy:</span> Autonomous fund execution is
                strictly disabled. Human executive authorization required before deployment.
              </span>
              <span className="font-mono text-slate-500">
                Showing {filteredRecs.length} of {recommendations.length} recommendations
              </span>
            </div>
          </div>

          {/* RECOMMENDATION CARDS GRID */}
          {filteredRecs.length === 0 ? (
            <EmptyStateCard
              title="No Matching Prescriptive Recommendations"
              description="Adjust your search query or filter parameters to display queued interventions."
              actionLabel="Reset Filters"
              onAction={() => {
                setSearchQuery('');
                setDomainFilter('ALL');
                setPriorityFilter('ALL');
                setConfidenceFilter('ALL');
                setStatusFilter('ALL');
              }}
            />
          ) : (
            <ErrorBoundary viewKey={`decision-recs-${filteredRecs.length}`}>
              <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                {(filteredRecs || []).map((rec) => {
                const Icon = domainIcons[rec.domain] || Sparkles;
                const isApproved = rec.status === 'Approved';
                const isInProgress = rec.status === 'In Progress';
                const isImplemented = rec.status === 'Implemented';
                const isOutcomeRecorded = rec.status === 'Outcome Recorded';
                const isRejected = rec.status === 'Rejected';
                const isActionable = rec.status === 'Proposed' || rec.status === 'Under Review';

                return (
                  <div
                    key={rec.recommendation_id}
                    className="glass-card p-6 flex flex-col justify-between rounded-xl border border-slate-800 hover:border-slate-700 transition-all bg-obsidian-900/90 shadow-lg relative overflow-hidden"
                  >
                    {/* Top Stripe Color */}
                    <div
                      className={`absolute top-0 left-0 right-0 h-1 ${
                        rec.priority === 'CRITICAL'
                          ? 'bg-rose-500'
                          : rec.priority === 'HIGH'
                          ? 'bg-amber-500'
                          : 'bg-sapphire-500'
                      }`}
                    />

                    <div>
                      {/* Domain, ID & Badges */}
                      <div className="flex items-start justify-between gap-3 mb-3">
                        <div className="flex items-center gap-2">
                          <div className="p-2 rounded-lg bg-obsidian-950 border border-slate-800 text-sapphire-400">
                            <Icon size={18} />
                          </div>
                          <div>
                            <span className="font-mono text-xs font-black text-white tracking-wide">
                              {rec.recommendation_id}
                            </span>
                            <p className="text-[11px] text-slate-400">
                              {domainLabels[rec.domain] || rec.domain}
                            </p>
                          </div>
                        </div>

                        <div className="flex items-center gap-1.5 flex-wrap justify-end">
                          {/* Priority */}
                          <span
                            className={`text-[10px] font-bold px-2 py-0.5 rounded border uppercase tracking-wider ${
                              rec.priority === 'CRITICAL'
                                ? 'bg-rose-500/20 text-rose-300 border-rose-500/30'
                                : rec.priority === 'HIGH'
                                ? 'bg-amber-500/20 text-amber-300 border-amber-500/30'
                                : 'bg-slate-800 text-slate-300 border-slate-700'
                            }`}
                          >
                            {rec.priority}
                          </span>

                          {/* Confidence Tier */}
                          <span
                            className={`text-[10px] font-bold px-2 py-0.5 rounded border uppercase tracking-wider ${getConfidenceBadge(
                              rec.confidence_tier
                            )}`}
                          >
                            {rec.confidence_tier}
                          </span>

                          {/* Lifecycle Status */}
                          <span
                            className={`text-[10px] font-bold px-2 py-0.5 rounded border uppercase tracking-wider ${getStatusBadge(
                              rec.status
                            )}`}
                          >
                            {rec.status}
                          </span>
                        </div>
                      </div>

                      {/* Business Problem Statement */}
                      <div className="mb-3">
                        <h3 className="text-base font-bold text-white leading-snug mb-1">
                          {rec.problem_statement || (rec as any).business_problem || rec.title}
                        </h3>
                        <p className="text-xs text-slate-300 font-medium">
                          <span className="text-sapphire-400 font-semibold">Prescriptive Action: </span>
                          {rec.proposed_action || (rec as any).action}
                        </p>
                      </div>

                      {/* Supporting Evidence */}
                      <div className="p-3 rounded-lg bg-obsidian-950/90 border border-slate-800/80 mb-4 space-y-1.5 text-xs">
                        <span className="text-[10px] font-bold uppercase tracking-wider text-slate-400 flex items-center gap-1">
                          <ShieldCheck size={12} className="text-emerald-400" /> Supporting Audited Evidence
                        </span>
                        <ul className="space-y-1 pl-1">
                          {((rec.supporting_evidence && Array.isArray(rec.supporting_evidence)) ? rec.supporting_evidence : []).map((ev, idx) => (
                            <li key={idx} className="text-slate-300 text-[11px] flex items-start gap-1.5">
                              <span className="text-sapphire-400 font-bold">•</span>
                              <span>{ev}</span>
                            </li>
                          ))}
                          {(!rec.supporting_evidence || rec.supporting_evidence.length === 0) && (
                            <li className="text-slate-500 text-[11px] italic">Audited empirical baseline evidence</li>
                          )}
                        </ul>
                      </div>

                      {/* Financial Metrics Strip */}
                      <div className="grid grid-cols-2 sm:grid-cols-5 gap-2 p-3 rounded-lg bg-obsidian-950/60 border border-slate-800/60 mb-4 text-center">
                        <div>
                          <span className="text-[10px] text-slate-400 uppercase font-semibold">Gross Benefit</span>
                          <p className="text-xs font-black text-emerald-400 mt-0.5">
                            {formatCurrency(rec.expected_gross_benefit_rupees ?? (rec as any).financial_impact?.gross_benefit ?? 0)}
                          </p>
                        </div>
                        <div>
                          <span className="text-[10px] text-slate-400 uppercase font-semibold">Impl. Cost</span>
                          <p className="text-xs font-black text-rose-400 mt-0.5">
                            {formatCurrency(rec.implementation_cost_rupees ?? (rec as any).financial_impact?.implementation_cost ?? 0)}
                          </p>
                        </div>
                        <div>
                          <span className="text-[10px] text-slate-400 uppercase font-semibold">Net Impact</span>
                          <p className="text-xs font-black text-cyan-400 mt-0.5">
                            {formatCurrency(rec.net_financial_impact_rupees ?? (rec as any).financial_impact?.net_financial_impact ?? 0)}
                          </p>
                        </div>
                        <div>
                          <span className="text-[10px] text-slate-400 uppercase font-semibold">Projected ROI</span>
                          <p className="text-xs font-black text-amber-300 mt-0.5">
                            {Number(rec.roi_multiple || (rec as any).financial_impact?.roi_multiple || 0).toFixed(2)}x
                          </p>
                        </div>
                        <div>
                          <span className="text-[10px] text-slate-400 uppercase font-semibold">Payback</span>
                          <p className="text-xs font-black text-slate-300 mt-0.5">
                            {rec.payback_period_days ?? 30}d
                          </p>
                        </div>
                      </div>

                      {/* Audit / Operator Meta Trail */}
                      {(rec.approved_by || rec.rejected_by || rec.outcome_record) && (
                        <div className="p-2.5 rounded bg-slate-900/60 border border-slate-800 text-[11px] text-slate-300 mb-4 space-y-1">
                          {rec.approved_by && (
                            <p className="flex items-center gap-1.5 text-emerald-400">
                              <CheckCircle2 size={12} /> Approved by: {rec.approved_by}
                              {rec.approval_notes && <span className="text-slate-400">({rec.approval_notes})</span>}
                            </p>
                          )}
                          {rec.rejected_by && (
                            <p className="flex items-center gap-1.5 text-rose-400">
                              <X size={12} /> Rejected by: {rec.rejected_by}
                              {rec.rejection_reason && <span className="text-slate-400">({rec.rejection_reason})</span>}
                            </p>
                          )}
                          {rec.outcome_record && (
                            <p className="flex items-center gap-1.5 text-purple-400 font-semibold">
                              <Activity size={12} /> Audited Realized Benefit: {formatCurrency(rec.outcome_record.realized_gross_benefit_rupees)}
                              <span className="text-slate-400 font-normal">
                                (Variance: {rec.outcome_record.variance_vs_projected_pct > 0 ? '+' : ''}
                                {rec.outcome_record.variance_vs_projected_pct.toFixed(1)}%)
                              </span>
                            </p>
                          )}
                        </div>
                      )}
                    </div>

                    {/* ACTION BUTTONS TOOLBAR */}
                    <div className="pt-3 border-t border-slate-800 flex flex-wrap items-center justify-between gap-2">
                      <button
                        onClick={() => handleOpenDetails(rec)}
                        className="px-3 py-1.5 rounded-lg bg-obsidian-950 hover:bg-slate-800 text-slate-300 text-xs font-semibold border border-slate-800 flex items-center gap-1.5 transition-colors"
                      >
                        <FileText size={13} /> Details & History
                      </button>

                      <div className="flex items-center gap-2">
                        {isActionable && (
                          <>
                            <button
                              onClick={() => handleOpenReject(rec)}
                              className="px-3 py-1.5 rounded-lg bg-rose-500/10 hover:bg-rose-500/20 text-rose-400 border border-rose-500/30 text-xs font-semibold flex items-center gap-1 transition-colors"
                            >
                              <X size={13} /> Reject
                            </button>
                            <button
                              onClick={() => handleOpenApprove(rec)}
                              className="px-3 py-1.5 rounded-lg bg-emerald-600 hover:bg-emerald-500 text-white text-xs font-semibold flex items-center gap-1.5 shadow-md shadow-emerald-500/20 transition-all"
                            >
                              <Check size={13} /> Approve Action
                            </button>
                          </>
                        )}

                        {isApproved && (
                          <button
                            onClick={() => handleStartProgress(rec)}
                            disabled={actionSubmitting}
                            className="px-3 py-1.5 rounded-lg bg-cyan-600 hover:bg-cyan-500 text-white text-xs font-semibold flex items-center gap-1.5 shadow-md shadow-cyan-500/20 transition-all"
                          >
                            <Activity size={13} /> Start Deployment
                          </button>
                        )}

                        {isInProgress && (
                          <button
                            onClick={() => handleMarkImplemented(rec)}
                            disabled={actionSubmitting}
                            className="px-3 py-1.5 rounded-lg bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-semibold flex items-center gap-1.5 shadow-md shadow-indigo-500/20 transition-all"
                          >
                            <CheckCircle2 size={13} /> Mark Implemented
                          </button>
                        )}

                        {isImplemented && (
                          <button
                            onClick={() => handleOpenRecordOutcome(rec)}
                            className="px-3 py-1.5 rounded-lg bg-purple-600 hover:bg-purple-500 text-white text-xs font-semibold flex items-center gap-1.5 shadow-md shadow-purple-500/20 transition-all"
                          >
                            <Activity size={13} /> Record Audited Outcome
                          </button>
                        )}

                        {isOutcomeRecorded && (
                          <span className="px-3 py-1.5 rounded-lg bg-purple-500/10 text-purple-300 border border-purple-500/30 text-xs font-semibold flex items-center gap-1.5">
                            <CheckCircle2 size={13} /> Outcome Certified
                          </span>
                        )}

                        <button
                          onClick={() => onNavigate('simulator')}
                          title="Simulate Scenario"
                          className="p-1.5 rounded-lg bg-obsidian-950 hover:bg-slate-800 text-slate-400 hover:text-white border border-slate-800 transition-colors"
                        >
                          <Sliders size={14} />
                        </button>
                      </div>
                    </div>
                  </div>
                );
              })}
              </div>
            </ErrorBoundary>
          )}
        </div>
      )}

      {/* VIEW MODE 2: FINANCIAL WATERFALL & COST CHARTS */}
      {viewMode === 'financials' && financialCharts && (
        <ErrorBoundary viewKey="decision-financials">
          <div className="space-y-6">
          <div className="glass-card p-6 rounded-xl border border-slate-800">
            <div className="flex items-center justify-between mb-4">
              <div>
                <h3 className="text-lg font-bold text-white flex items-center gap-2">
                  <BarChart3 className="text-sapphire-400" size={20} />
                  Audited Platform Contribution Margin Waterfall
                </h3>
                <p className="text-xs text-slate-400 mt-0.5">
                  Gross GMV inflow vs platform commissions, delivery fees collected, coupon subsidies, and rider logistics fulfillment.
                </p>
              </div>
              <span className="text-xs font-mono px-2.5 py-1 rounded bg-obsidian-950 border border-slate-800 text-emerald-400">
                Net Margin: {financialCharts.summary?.financial_breakdown?.contribution_margin_percentage ?? 0}%
              </span>
            </div>

            <div className="h-80 w-full">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={financialCharts.contribution_margin_waterfall || []}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
                  <XAxis dataKey="name" stroke="#64748b" tick={{ fontSize: 11 }} />
                  <YAxis
                    stroke="#64748b"
                    tick={{ fontSize: 11 }}
                    tickFormatter={(val) => `₹${(val / 100000).toFixed(0)}L`}
                  />
                  <Tooltip
                    contentStyle={{ backgroundColor: '#0f172a', borderColor: '#334155', borderRadius: '8px' }}
                    formatter={(val: any) => [formatCurrency(val), 'Amount (INR)']}
                  />
                  <Bar dataKey="amount" radius={[4, 4, 0, 0]}>
                    {(financialCharts.contribution_margin_waterfall || []).map((entry, index) => {
                      let color = '#3b82f6';
                      if (entry.type === 'total') color = '#6366f1';
                      if (entry.type === 'positive') color = '#10b981';
                      if (entry.type === 'negative') color = '#ef4444';
                      if (entry.type === 'subtotal') color = '#06b6d4';
                      return <Cell key={`cell-${index}`} fill={color} />;
                    })}
                  </Bar>
                </BarChart>
              </ResponsiveContainer>
            </div>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {/* Revenue Inflow vs Outflow */}
            <div className="glass-card p-6 rounded-xl border border-slate-800">
              <h4 className="text-sm font-bold text-white mb-2">Platform Revenue Inflow vs Outflow</h4>
              <p className="text-xs text-slate-400 mb-4">
                Total commissions & delivery fees collected vs platform promotional subsidies and logistics costs.
              </p>
              <div className="space-y-3">
                {(financialCharts.revenue_vs_cost_comparison || []).map((item, idx) => (
                  <div key={idx} className="p-3 rounded-lg bg-obsidian-950 border border-slate-800/80 flex items-center justify-between">
                    <span className="text-xs text-slate-300 font-medium">{item.category}</span>
                    <span
                      className={`text-sm font-black font-mono ${
                        item.amount > 0 ? 'text-emerald-400' : 'text-rose-400'
                      }`}
                    >
                      {formatCurrency(item.amount)}
                    </span>
                  </div>
                ))}
              </div>
            </div>

            {/* Promotional Subsidy Reconciliation */}
            <div className="glass-card p-6 rounded-xl border border-slate-800">
              <h4 className="text-sm font-bold text-white mb-2">Promotional Subsidy & Leakage Reconciliation</h4>
              <p className="text-xs text-slate-400 mb-4">
                Audited order-level breakdown of heavy discounts (&gt;25%) and sub-MOV small baskets.
              </p>
              <div className="space-y-3 text-xs">
                <div className="p-3 rounded-lg bg-obsidian-950 border border-slate-800 flex justify-between">
                  <span className="text-slate-400">Total Delivered Discounts (All Orders):</span>
                  <span className="font-bold text-white">
                    {formatCurrency(financialCharts.summary?.financial_breakdown?.total_discounts_applied ?? 0)}
                  </span>
                </div>
                <div className="p-3 rounded-lg bg-obsidian-950 border border-slate-800 flex justify-between">
                  <span className="text-slate-400">Platform 60% Subsidized Share:</span>
                  <span className="font-bold text-rose-400">
                    {formatCurrency(financialCharts.summary?.financial_breakdown?.platform_subsidized_discount_share_60pct ?? 0)}
                  </span>
                </div>
                <div className="p-3 rounded-lg bg-obsidian-950 border border-slate-800 flex justify-between">
                  <span className="text-slate-400">Heavy Discount Orders (&gt;25%):</span>
                  <span className="font-bold text-amber-300">
                    {financialCharts.summary?.revenue_leakage_diagnosis?.heavy_discount_orders_count ?? 0} orders (
                    {formatCurrency(financialCharts.summary?.revenue_leakage_diagnosis?.heavy_discount_total_value ?? 0)})
                  </span>
                </div>
                <div className="p-3 rounded-lg bg-obsidian-950 border border-slate-800 flex justify-between">
                  <span className="text-slate-400">Small Basket Orders (&lt;₹350):</span>
                  <span className="font-bold text-amber-300">
                    {financialCharts.summary?.revenue_leakage_diagnosis?.small_basket_orders_count ?? 0} orders (
                    {financialCharts.summary?.revenue_leakage_diagnosis?.small_basket_orders_pct ?? 0}%)
                  </span>
                </div>
              </div>
            </div>
          </div>
        </div>
        </ErrorBoundary>
      )}

      {/* MODAL 1: DETAILS & AUDIT TRAIL */}
      {actionModalType === 'details' && selectedRec && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 backdrop-blur-sm p-4">
          <div className="w-full max-w-2xl max-h-[90vh] overflow-y-auto rounded-2xl border border-slate-200 bg-white p-6 shadow-2xl space-y-5">
            <div className="flex items-center justify-between border-b border-slate-200 pb-4">
              <div>
                <span className="text-xs font-mono font-bold text-blue-600 uppercase">
                  {selectedRec.recommendation_id} • AUDIT TRAIL
                </span>
                <h3 className="text-lg font-bold text-slate-800 mt-0.5">{selectedRec.problem_statement}</h3>
              </div>
              <button
                onClick={() => setActionModalType(null)}
                className="p-1 rounded-lg text-slate-400 hover:text-slate-700 hover:bg-slate-100"
              >
                <X size={18} />
              </button>
            </div>

            <div className="space-y-4 text-xs">
              <div>
                <span className="font-bold text-slate-500 uppercase tracking-wider">Prescriptive Action:</span>
                <p className="text-slate-800 mt-1 p-3 rounded-lg bg-slate-50 border border-slate-200">
                  {selectedRec.proposed_action}
                </p>
              </div>

              <div>
                <span className="font-bold text-slate-500 uppercase tracking-wider">Lifecycle Status History:</span>
                <div className="mt-2 space-y-2">
                  {(selectedRec.status_history || []).map((h, i) => (
                    <div
                      key={i}
                      className="p-3 rounded-lg bg-slate-50 border border-slate-200 flex items-start justify-between"
                    >
                      <div>
                        <span className="font-bold text-slate-800">{h.status}</span>
                        <p className="text-[11px] text-slate-500 mt-0.5">
                          Actor: <span className="text-slate-700 font-medium">{h.actor || (h as any).changed_by || 'Operations'}</span>
                          {(h.reason_or_notes || (h as any).notes) && ` • Notes: ${h.reason_or_notes || (h as any).notes}`}
                        </p>
                      </div>
                      <span className="text-[10px] font-mono text-slate-500">{h.timestamp || (h as any).changed_at}</span>
                    </div>
                  ))}
                  {(!selectedRec.status_history || selectedRec.status_history.length === 0) && (
                    <p className="text-[11px] text-slate-500 italic p-2 rounded bg-slate-50">No historical status transitions recorded.</p>
                  )}
                </div>
              </div>

              {selectedRec.outcome_record && (
                <div className="p-3 rounded-lg bg-purple-50 border border-purple-200">
                  <span className="font-bold text-purple-700 uppercase tracking-wider flex items-center gap-1.5">
                    <Activity size={14} /> Realized Financial Outcome Audit
                  </span>
                  <div className="grid grid-cols-2 gap-2 mt-2">
                    <div>
                      <span className="text-slate-500">Audited Gross Benefit:</span>
                      <p className="font-bold text-green-600">
                        {formatCurrency(selectedRec.outcome_record.realized_gross_benefit_rupees)}
                      </p>
                    </div>
                    <div>
                      <span className="text-slate-500">Actual Realized Cost:</span>
                      <p className="font-bold text-red-600">
                        {formatCurrency(selectedRec.outcome_record.actual_cost_rupees)}
                      </p>
                    </div>
                    <div>
                      <span className="text-slate-500">Measured By:</span>
                      <p className="text-slate-700">{selectedRec.outcome_record.measured_by}</p>
                    </div>
                    <div>
                      <span className="text-slate-500">Variance vs Projected:</span>
                      <p className="font-bold text-blue-600">
                        {selectedRec.outcome_record.variance_vs_projected_pct > 0 ? '+' : ''}
                        {selectedRec.outcome_record.variance_vs_projected_pct.toFixed(1)}%
                      </p>
                    </div>
                  </div>
                  <p className="text-[11px] text-slate-600 mt-2 italic">
                    Audit Notes: {selectedRec.outcome_record.audit_notes}
                  </p>
                </div>
              )}
            </div>

            <div className="pt-3 border-t border-slate-200 flex justify-end">
              <button
                onClick={() => setActionModalType(null)}
                className="px-4 py-2 rounded-lg bg-slate-100 hover:bg-slate-200 text-slate-700 text-xs font-semibold border border-slate-200"
              >
                Close Audit Record
              </button>
            </div>
          </div>
        </div>
      )}

      {/* MODAL 2: APPROVE DIALOG */}
      {actionModalType === 'approve' && selectedRec && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 backdrop-blur-sm p-4">
          <div className="w-full max-w-lg rounded-2xl border border-slate-200 bg-white p-6 shadow-2xl space-y-4">
            <div className="flex items-center justify-between border-b border-slate-200 pb-3">
              <h3 className="text-base font-bold text-slate-800 flex items-center gap-2">
                <CheckCircle2 className="text-blue-600" size={18} />
                Approve Prescriptive Recommendation
              </h3>
              <button
                onClick={() => setActionModalType(null)}
                className="p-1 rounded-lg text-slate-400 hover:text-slate-700 hover:bg-slate-100"
              >
                <X size={18} />
              </button>
            </div>

            <div className="p-3 rounded-lg bg-blue-50 border border-blue-200 text-xs text-slate-700">
              <p className="font-bold text-blue-700 mb-1">Human Executive Authorization Required</p>
              Approving recommendation <span className="font-mono text-slate-800 font-semibold">{selectedRec.recommendation_id}</span> will
              transition it to <span className="font-semibold text-blue-600">Approved</span> state and record your credentials
              in the compliance audit ledger.
            </div>

            <div className="space-y-3 text-xs">
              <div>
                <label className="block text-slate-600 font-semibold mb-1">Approving Operator / Executive ID</label>
                <input
                  type="text"
                  value={operatorName}
                  onChange={(e) => setOperatorName(e.target.value)}
                  className="w-full p-2.5 rounded-lg bg-white border border-slate-300 text-slate-800 focus:outline-none focus:border-blue-600 focus:ring-1 focus:ring-blue-600"
                />
              </div>

              <div>
                <label className="block text-slate-600 font-semibold mb-1">Approval Notes / Operational Directives</label>
                <textarea
                  rows={3}
                  value={actionNotes}
                  onChange={(e) => setActionNotes(e.target.value)}
                  placeholder="e.g. Approved rollout for Chennai and Hyderabad regions with 30-day checkpoint."
                  className="w-full p-2.5 rounded-lg bg-white border border-slate-300 text-slate-800 focus:outline-none focus:border-blue-600 focus:ring-1 focus:ring-blue-600"
                />
              </div>
            </div>

            {actionFeedback && (
              <div
                className={`p-3 rounded-lg text-xs font-semibold ${
                  actionFeedback.type === 'success'
                    ? 'bg-green-50 text-green-700 border border-green-200'
                    : 'bg-red-50 text-red-700 border border-red-200'
                }`}
              >
                {actionFeedback.message}
              </div>
            )}

            <div className="pt-3 border-t border-slate-200 flex items-center justify-end gap-2">
              <button
                onClick={() => setActionModalType(null)}
                disabled={actionSubmitting}
                className="px-3 py-1.5 rounded-lg bg-slate-100 hover:bg-slate-200 text-slate-700 text-xs font-semibold border border-slate-200"
              >
                Cancel
              </button>
              <button
                onClick={handleApproveSubmit}
                disabled={actionSubmitting || !operatorName.trim()}
                className="px-4 py-2 rounded-lg bg-orange-500 hover:bg-orange-600 text-white text-xs font-semibold flex items-center gap-1.5 shadow-md shadow-orange-500/20"
              >
                {actionSubmitting ? 'Recording Approval...' : 'Confirm Executive Approval'}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* MODAL 3: REJECT DIALOG */}
      {actionModalType === 'reject' && selectedRec && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 backdrop-blur-sm p-4">
          <div className="w-full max-w-lg rounded-2xl border border-slate-200 bg-white p-6 shadow-2xl space-y-4">
            <div className="flex items-center justify-between border-b border-slate-200 pb-3">
              <h3 className="text-base font-bold text-slate-800 flex items-center gap-2">
                <ShieldAlert className="text-red-600" size={18} />
                Reject Prescriptive Recommendation
              </h3>
              <button
                onClick={() => setActionModalType(null)}
                className="p-1 rounded-lg text-slate-400 hover:text-slate-700 hover:bg-slate-100"
              >
                <X size={18} />
              </button>
            </div>

            <div className="p-3 rounded-lg bg-red-50 border border-red-200 text-xs text-slate-700">
              <p className="font-bold text-red-700 mb-1">Mandatory Rejection Justification</p>
              Rejecting <span className="font-mono text-slate-800 font-semibold">{selectedRec.recommendation_id}</span> requires a formal
              governance justification recorded for compliance auditing.
            </div>

            <div className="space-y-3 text-xs">
              <div>
                <label className="block text-slate-600 font-semibold mb-1">Rejecting Operator / Auditor ID</label>
                <input
                  type="text"
                  value={operatorName}
                  onChange={(e) => setOperatorName(e.target.value)}
                  className="w-full p-2.5 rounded-lg bg-white border border-slate-300 text-slate-800 focus:outline-none focus:border-red-600 focus:ring-1 focus:ring-red-600"
                />
              </div>

              <div>
                <label className="block text-slate-600 font-semibold mb-1">Reason for Rejection *</label>
                <textarea
                  rows={3}
                  value={actionNotes}
                  onChange={(e) => setActionNotes(e.target.value)}
                  placeholder="Explain why this prescriptive action is rejected (e.g. Budget reallocation, vendor contract conflict)..."
                  className="w-full p-2.5 rounded-lg bg-white border border-slate-300 text-slate-800 focus:outline-none focus:border-red-600 focus:ring-1 focus:ring-red-600"
                />
              </div>
            </div>

            {actionFeedback && (
              <div
                className={`p-3 rounded-lg text-xs font-semibold ${
                  actionFeedback.type === 'success'
                    ? 'bg-green-50 text-green-700 border border-green-200'
                    : 'bg-red-50 text-red-700 border border-red-200'
                }`}
              >
                {actionFeedback.message}
              </div>
            )}

            <div className="pt-3 border-t border-slate-200 flex items-center justify-end gap-2">
              <button
                onClick={() => setActionModalType(null)}
                disabled={actionSubmitting}
                className="px-3 py-1.5 rounded-lg bg-slate-100 hover:bg-slate-200 text-slate-700 text-xs font-semibold border border-slate-200"
              >
                Cancel
              </button>
              <button
                onClick={handleRejectSubmit}
                disabled={actionSubmitting || !actionNotes.trim()}
                className="px-4 py-2 rounded-lg bg-red-600 hover:bg-red-700 text-white text-xs font-semibold flex items-center gap-1.5 shadow-md shadow-red-600/20"
              >
                {actionSubmitting ? 'Recording Rejection...' : 'Confirm Rejection'}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* MODAL 4: RECORD AUDITED OUTCOME */}
      {actionModalType === 'record_outcome' && selectedRec && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 backdrop-blur-sm p-4">
          <div className="w-full max-w-lg rounded-2xl border border-slate-200 bg-white p-6 shadow-2xl space-y-4">
            <div className="flex items-center justify-between border-b border-slate-200 pb-3">
              <h3 className="text-base font-bold text-slate-800 flex items-center gap-2">
                <Activity className="text-blue-600" size={18} />
                Record Realized Financial Outcome
              </h3>
              <button
                onClick={() => setActionModalType(null)}
                className="p-1 rounded-lg text-slate-400 hover:text-slate-700 hover:bg-slate-100"
              >
                <X size={18} />
              </button>
            </div>

            <div className="p-3 rounded-lg bg-purple-50 border border-purple-200 text-xs text-slate-700">
              <p className="font-bold text-purple-700 mb-1">Post-Rollout Measurement & Variance Tracking</p>
              Compare audited empirical performance against the initial projection of{' '}
              <span className="font-bold text-slate-800">{formatCurrency(selectedRec.expected_gross_benefit_rupees)}</span> gross
              benefit.
            </div>

            <div className="space-y-3 text-xs">
              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-slate-600 font-semibold mb-1">Realized Gross Benefit (₹)</label>
                  <input
                    type="number"
                    value={outcomeRealizedBenefit}
                    onChange={(e) => setOutcomeRealizedBenefit(parseFloat(e.target.value) || 0)}
                    className="w-full p-2.5 rounded-lg bg-white border border-slate-300 text-slate-800 focus:outline-none focus:border-blue-600 focus:ring-1 focus:ring-blue-600"
                  />
                </div>
                <div>
                  <label className="block text-slate-600 font-semibold mb-1">Actual Realized Cost (₹)</label>
                  <input
                    type="number"
                    value={outcomeActualCost}
                    onChange={(e) => setOutcomeActualCost(parseFloat(e.target.value) || 0)}
                    className="w-full p-2.5 rounded-lg bg-white border border-slate-300 text-slate-800 focus:outline-none focus:border-blue-600 focus:ring-1 focus:ring-blue-600"
                  />
                </div>
              </div>

              {/* Calculated Realized Net & Variance */}
              <div className="p-3 rounded-lg bg-slate-50 border border-slate-200 flex justify-between text-xs font-mono">
                <div>
                  <span className="text-slate-500">Net Realized: </span>
                  <span className="font-bold text-blue-600">
                    {formatCurrency(outcomeRealizedBenefit - outcomeActualCost)}
                  </span>
                </div>
                <div>
                  <span className="text-slate-500">Variance: </span>
                  <span
                    className={`font-bold ${
                      outcomeRealizedBenefit >= selectedRec.expected_gross_benefit_rupees
                        ? 'text-green-600'
                        : 'text-orange-500'
                    }`}
                  >
                    {(
                      ((outcomeRealizedBenefit - selectedRec.expected_gross_benefit_rupees) /
                        (selectedRec.expected_gross_benefit_rupees || 1)) *
                      100
                    ).toFixed(1)}
                    %
                  </span>
                </div>
              </div>

              <div>
                <label className="block text-slate-600 font-semibold mb-1">Auditing Financial Analyst ID</label>
                <input
                  type="text"
                  value={operatorName}
                  onChange={(e) => setOperatorName(e.target.value)}
                  className="w-full p-2.5 rounded-lg bg-white border border-slate-300 text-slate-800 focus:outline-none focus:border-blue-600 focus:ring-1 focus:ring-blue-600"
                />
              </div>

              <div>
                <label className="block text-slate-600 font-semibold mb-1">Audited Findings & Documentation</label>
                <textarea
                  rows={2}
                  value={outcomeNotes}
                  onChange={(e) => setOutcomeNotes(e.target.value)}
                  className="w-full p-2.5 rounded-lg bg-white border border-slate-300 text-slate-800 focus:outline-none focus:border-blue-600 focus:ring-1 focus:ring-blue-600"
                />
              </div>
            </div>

            {actionFeedback && (
              <div
                className={`p-3 rounded-lg text-xs font-semibold ${
                  actionFeedback.type === 'success'
                    ? 'bg-green-50 text-green-700 border border-green-200'
                    : 'bg-red-50 text-red-700 border border-red-200'
                }`}
              >
                {actionFeedback.message}
              </div>
            )}

            <div className="pt-3 border-t border-slate-200 flex items-center justify-end gap-2">
              <button
                onClick={() => setActionModalType(null)}
                disabled={actionSubmitting}
                className="px-3 py-1.5 rounded-lg bg-slate-100 hover:bg-slate-200 text-slate-700 text-xs font-semibold border border-slate-200"
              >
                Cancel
              </button>
              <button
                onClick={handleRecordOutcomeSubmit}
                disabled={actionSubmitting}
                className="px-4 py-2 rounded-lg bg-blue-600 hover:bg-blue-700 text-white text-xs font-semibold flex items-center gap-1.5 shadow-md shadow-blue-600/20"
              >
                {actionSubmitting ? 'Recording Outcome...' : 'Certify Audited Outcome'}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
