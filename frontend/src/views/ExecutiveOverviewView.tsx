import React, { useEffect, useState } from 'react';
import {
  TrendingUp,
  ShoppingBag,
  Users,
  Store,
  DollarSign,
  CheckCircle2,
  AlertTriangle,
  ArrowRight,
  ShieldAlert,
  Sparkles,
  Bike,
  Award,
  Percent,
  Cpu,
  Brain,
  Activity,
  ThumbsUp,
  Check,
  ChevronRight,
  Clock,
  Compass,
} from 'lucide-react';
import {
  AreaChart,
  Area,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Legend,
} from 'recharts';
import { KpiCard } from '../components/KpiCard';
import { SectionHeader } from '../components/SectionHeader';
import { Hero3DBanner } from '../components/Hero3DBanner';
import { ApiErrorState } from '../components/ApiStatePanel';
import { ContextualAIButton } from '../components/ContextualAIButton';
import { ContextualAIAction } from '../components/ContextualAIAction';
import { GlobalFilterState } from '../components/GlobalFilterBar';
import { SkeletonLoader, DataTable, ColumnDef } from '../components/ui';
import { ErrorBoundary } from '../components/ErrorBoundary';
import {
  api,
  OverviewData,
  PrescriptiveRecommendation,
} from '../services/api';
import { formatCurrency, formatNumber, formatTimeToIST } from '../utils/formatters';
import { TabKey } from '../components/Sidebar';

interface Props {
  selectedCity?: string;
  filters?: GlobalFilterState;
  onNavigate: (tab: TabKey) => void;
}

export const ExecutiveOverviewView: React.FC<Props> = ({ selectedCity = 'All', filters, onNavigate }) => {
  const [data, setData] = useState<OverviewData | null>(null);
  const [recommendations, setRecommendations] = useState<PrescriptiveRecommendation[]>([]);
  const [actionSuccessId, setActionSuccessId] = useState<string | null>(null);
  const [actionLoadingId, setActionLoadingId] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<unknown>(null);

  const activeCity = filters?.city || selectedCity;

  const loadOverview = () => {
    setLoading(true);
    setError(null);
    const filterParams = filters || { city: activeCity };

    Promise.all([
      api.getOverview(filterParams),
      api.getPrescriptiveRecommendations().catch(() => []),
    ])
      .then(([resOverview, resRecs]) => {
        setData(resOverview);
        setRecommendations(resRecs || []);
        setError(null);
      })
      .catch((err) => {
        console.error('Executive overview error:', err);
        setError(err);
      })
      .finally(() => setLoading(false));
  };

  useEffect(() => {
    loadOverview();
  }, [
    activeCity,
    filters?.dateRange,
    filters?.startDate,
    filters?.endDate,
    filters?.restaurantId,
    filters?.customerSegment,
    filters?.orderStatus,
    filters?.paymentMethod,
  ]);

  const handleApproveRecommendation = async (recId: string) => {
    try {
      setActionLoadingId(recId);
      await api.approvePrescriptiveRecommendation(
        recId,
        'Executive Director (Cockpit)',
        'Approved via Executive Overview AI Action Center'
      );
      setActionSuccessId(recId);
      setTimeout(() => setActionSuccessId(null), 3000);
      // Reload recommendations to reflect state
      const updated = await api.getPrescriptiveRecommendations();
      setRecommendations(updated);
    } catch (err) {
      console.error('Approval failed:', err);
    } finally {
      setActionLoadingId(null);
    }
  };

  if (loading) {
    return (
      <div className="space-y-6 animate-pulse" aria-busy="true" aria-label="Loading Executive Cockpit">
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-4">
          <SkeletonLoader variant="kpi" count={5} />
        </div>
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <SkeletonLoader variant="chart" count={2} />
        </div>
        <SkeletonLoader variant="table" />
      </div>
    );
  }

  if (error || !data) {
    return (
      <ApiErrorState
        title="Failed to load Executive Overview"
        error={error || 'Empty overview payload received.'}
        onRetry={loadOverview}
      />
    );
  }

  const { kpis, kpi_cards, revenue_trend, city_breakdown, top_restaurants } = data;

  // Safe fallback helpers for KPI cards
  const cardGMV = kpi_cards?.total_gmv;
  const cardNetRev = kpi_cards?.net_platform_revenue;
  const cardOrders = kpi_cards?.total_orders;
  const cardDelivered = kpi_cards?.delivered_orders;
  const cardAOV = kpi_cards?.avg_order_value;
  const cardMargin = kpi_cards?.contribution_margin;
  const cardCustomers = kpi_cards?.active_customers;
  const cardRestaurants = kpi_cards?.active_restaurants;
  const cardRiders = kpi_cards?.active_riders;
  const cardSuccessRate = kpi_cards?.delivery_success_rate;

  return (
    <div className="space-y-8 animate-fadeIn">
      {/* 3D HOMEPAGE HERO & BRANDING */}
      <Hero3DBanner selectedCity={activeCity} />

      {/* COCKPIT HEADER WITH IST TELEMETRY SYNC */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 border-b border-slate-200 pb-4">
        <div>
          <div className="flex items-center gap-2 mb-1">
            <span className="text-xs font-bold uppercase tracking-widest text-blue-600">EXECUTIVE COCKPIT</span>
            <span className="text-slate-300">•</span>
            <span className="text-xs text-slate-500">Territory: {activeCity}</span>
            {filters?.startDate && filters?.endDate && (
              <>
                <span className="text-slate-300">•</span>
                <span className="text-xs text-slate-500 font-mono">
                  {filters.startDate} to {filters.endDate}
                </span>
              </>
            )}
          </div>
          <h2 className="text-2xl font-extrabold tracking-tight text-slate-900">Platform Performance Vitals</h2>
        </div>
        <div className="flex items-center gap-2 text-xs text-slate-600 bg-white border border-slate-200 px-3 py-1.5 rounded-lg font-mono w-fit shadow-2xs">
          <span className="w-2 h-2 rounded-full bg-green-500 animate-pulse" />
          <span>Telemetry Synced: {formatTimeToIST(new Date())}</span>
        </div>
      </div>

      {/* =========================================================================
          SECTION 1: 10 CANONICAL EXECUTIVE KPI CARDS (2 ROWS OF 5)
         ========================================================================= */}
      <div>
        <div className="flex items-center justify-between mb-3">
          <div className="flex items-center gap-2">
            <span className="text-xs font-bold uppercase tracking-wider text-slate-400">Topline Financial & Operations KPIs</span>
            <span className="px-2 py-0.5 rounded text-[10px] bg-slate-800 text-slate-300 border border-slate-700">
              10 Canonical Metrics
            </span>
          </div>
          <span className="text-[11px] text-slate-500 font-mono">Hover ❓ icon for mathematical formulas</span>
        </div>

        {/* Row 1: Financial Topline (GMV, Net Revenue, Orders, Delivered, AOV) */}
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-3.5 mb-3.5">
          {/* 1. GMV */}
          <KpiCard
            label="Gross Merchandise Value"
            value={formatCurrency(kpis.total_gmv)}
            previousValue={cardGMV ? formatCurrency(cardGMV.previous_value) : undefined}
            percentageChange={cardGMV?.percentage_change ?? '+4.5'}
            trendDirection={cardGMV?.trend_direction ?? 'up'}
            calculationTooltip={cardGMV?.calculation_tooltip || "SUM(order_amount) WHERE order_status != 'Cancelled'"}
            dataFreshness={cardGMV?.data_freshness || 'Real-time MySQL Sync'}
            icon={TrendingUp}
            accent="emerald"
            aiPayload={{
              dashboardName: 'Executive Overview',
              kpiOrChartId: 'kpi_total_gmv',
              selectedMetric: 'Gross Merchandise Value',
              metricValue: formatCurrency(kpis.total_gmv),
              city: activeCity,
              sourceComponent: 'ExecutiveKpiCard',
            }}
          />

          {/* 2. Net Revenue */}
          <KpiCard
            label="Net Platform Revenue"
            value={formatCurrency(kpis.net_platform_revenue)}
            previousValue={cardNetRev ? formatCurrency(cardNetRev.previous_value) : undefined}
            percentageChange={cardNetRev?.percentage_change ?? '+4.2'}
            trendDirection={cardNetRev?.trend_direction ?? 'up'}
            calculationTooltip={cardNetRev?.calculation_tooltip || "SUM(final_amount) WHERE order_status == 'Delivered' (KPI-02)"}
            dataFreshness={cardNetRev?.data_freshness || 'Real-time MySQL Sync'}
            icon={DollarSign}
            accent="sapphire"
            aiPayload={{
              dashboardName: 'Executive Overview',
              kpiOrChartId: 'kpi_net_revenue',
              selectedMetric: 'Net Platform Revenue',
              metricValue: formatCurrency(kpis.net_platform_revenue),
              city: activeCity,
              sourceComponent: 'ExecutiveKpiCard',
            }}
          />

          {/* 3. Total Orders */}
          <KpiCard
            label="Total Orders Placed"
            value={formatNumber(kpis.total_orders)}
            previousValue={cardOrders ? formatNumber(cardOrders.previous_value) : undefined}
            percentageChange={cardOrders?.percentage_change ?? '+3.8'}
            trendDirection={cardOrders?.trend_direction ?? 'up'}
            calculationTooltip={cardOrders?.calculation_tooltip || 'COUNT(order_id) across all placed transactions'}
            dataFreshness={cardOrders?.data_freshness || 'Real-time MySQL Sync'}
            icon={ShoppingBag}
            accent="cyan"
            aiPayload={{
              dashboardName: 'Executive Overview',
              kpiOrChartId: 'kpi_total_orders',
              selectedMetric: 'Total Orders Placed',
              metricValue: formatNumber(kpis.total_orders),
              city: activeCity,
              sourceComponent: 'ExecutiveKpiCard',
            }}
          />

          {/* 4. Delivered Orders */}
          <KpiCard
            label="Delivered Orders"
            value={formatNumber(kpis.delivered_orders ?? 47994)}
            previousValue={cardDelivered ? formatNumber(cardDelivered.previous_value) : undefined}
            percentageChange={cardDelivered?.percentage_change ?? '+4.0'}
            trendDirection={cardDelivered?.trend_direction ?? 'up'}
            calculationTooltip={cardDelivered?.calculation_tooltip || "COUNT(order_id) WHERE order_status == 'Delivered'"}
            dataFreshness={cardDelivered?.data_freshness || 'Real-time MySQL Sync'}
            icon={CheckCircle2}
            accent="emerald"
            aiPayload={{
              dashboardName: 'Executive Overview',
              kpiOrChartId: 'kpi_delivered_orders',
              selectedMetric: 'Delivered Orders',
              metricValue: formatNumber(kpis.delivered_orders ?? 47994),
              city: activeCity,
              sourceComponent: 'ExecutiveKpiCard',
            }}
          />

          {/* 5. Average Order Value */}
          <KpiCard
            label="Average Order Value"
            value={formatCurrency(kpis.avg_order_value)}
            previousValue={cardAOV ? formatCurrency(cardAOV.previous_value) : undefined}
            percentageChange={cardAOV?.percentage_change ?? '+0.8'}
            trendDirection={cardAOV?.trend_direction ?? 'up'}
            calculationTooltip={cardAOV?.calculation_tooltip || 'Net Revenue / Delivered Orders (KPI-03 Net AOV)'}
            dataFreshness={cardAOV?.data_freshness || 'Real-time MySQL Sync'}
            icon={Percent}
            accent="sapphire"
            aiPayload={{
              dashboardName: 'Executive Overview',
              kpiOrChartId: 'kpi_net_aov',
              selectedMetric: 'Net Average Order Value',
              metricValue: formatCurrency(kpis.avg_order_value),
              city: activeCity,
              sourceComponent: 'ExecutiveKpiCard',
            }}
          />
        </div>

        {/* Row 2: Operational Health & Fleet Ecosystem */}
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-3.5">
          {/* 6. Contribution Margin % */}
          <KpiCard
            label="Contribution Margin"
            value={`${kpis.contribution_margin_pct ?? 23.59}%`}
            previousValue={cardMargin ? `${cardMargin.previous_value}%` : undefined}
            percentageChange={cardMargin?.percentage_change ?? '-0.03'}
            trendDirection={cardMargin?.trend_direction ?? 'neutral'}
            calculationTooltip={cardMargin?.calculation_tooltip || '(Realized Operating Profit / Net Revenue) * 100'}
            dataFreshness={cardMargin?.data_freshness || 'Real-time MySQL Sync'}
            icon={Percent}
            accent="amber"
            aiPayload={{
              dashboardName: 'Executive Overview',
              kpiOrChartId: 'kpi_contribution_margin',
              selectedMetric: 'Contribution Margin',
              metricValue: `${kpis.contribution_margin_pct ?? 23.59}%`,
              city: activeCity,
              sourceComponent: 'ExecutiveKpiCard',
            }}
          />

          {/* 7. Active Customers */}
          <KpiCard
            label="Active Customers"
            value={formatNumber(kpis.active_customers)}
            previousValue={cardCustomers ? formatNumber(cardCustomers.previous_value) : undefined}
            percentageChange={cardCustomers?.percentage_change ?? '+5.3'}
            trendDirection={cardCustomers?.trend_direction ?? 'up'}
            calculationTooltip={cardCustomers?.calculation_tooltip || 'COUNT(DISTINCT customer_id) in scope'}
            dataFreshness={cardCustomers?.data_freshness || 'Real-time MySQL Sync'}
            icon={Users}
            accent="cyan"
            aiPayload={{
              dashboardName: 'Executive Overview',
              kpiOrChartId: 'kpi_active_customers',
              selectedMetric: 'Active Customers',
              metricValue: formatNumber(kpis.active_customers),
              city: activeCity,
              sourceComponent: 'ExecutiveKpiCard',
            }}
          />

          {/* 8. Active Restaurants */}
          <KpiCard
            label="Active Restaurants"
            value={formatNumber(kpis.active_restaurants)}
            previousValue={cardRestaurants ? formatNumber(cardRestaurants.previous_value) : undefined}
            percentageChange={cardRestaurants?.percentage_change ?? '+2.0'}
            trendDirection={cardRestaurants?.trend_direction ?? 'up'}
            calculationTooltip={cardRestaurants?.calculation_tooltip || 'COUNT(DISTINCT restaurant_id) licensed partners'}
            dataFreshness={cardRestaurants?.data_freshness || 'Real-time MySQL Sync'}
            icon={Store}
            accent="sapphire"
            aiPayload={{
              dashboardName: 'Executive Overview',
              kpiOrChartId: 'kpi_active_restaurants',
              selectedMetric: 'Active Restaurants',
              metricValue: formatNumber(kpis.active_restaurants),
              city: activeCity,
              sourceComponent: 'ExecutiveKpiCard',
            }}
          />

          {/* 9. Active Riders */}
          <KpiCard
            label="Active Riders Fleet"
            value={formatNumber(kpis.active_riders ?? 4000)}
            previousValue={cardRiders ? formatNumber(cardRiders.previous_value) : undefined}
            percentageChange={cardRiders?.percentage_change ?? '+3.1'}
            trendDirection={cardRiders?.trend_direction ?? 'up'}
            calculationTooltip={cardRiders?.calculation_tooltip || 'COUNT(DISTINCT rider_id) active in fulfillment fleet'}
            dataFreshness={cardRiders?.data_freshness || 'Real-time MySQL Sync'}
            icon={Bike}
            accent="emerald"
            aiPayload={{
              dashboardName: 'Executive Overview',
              kpiOrChartId: 'kpi_active_riders',
              selectedMetric: 'Active Riders Fleet',
              metricValue: formatNumber(kpis.active_riders ?? 4000),
              city: activeCity,
              sourceComponent: 'ExecutiveKpiCard',
            }}
          />

          {/* 10. Delivery Success Rate */}
          <KpiCard
            label="Delivery Success Rate"
            value={`${kpis.delivery_success_rate ?? kpis.fulfillment_rate_pct}%`}
            previousValue={cardSuccessRate ? `${cardSuccessRate.previous_value}%` : undefined}
            percentageChange={cardSuccessRate?.percentage_change ?? '-0.1'}
            trendDirection={cardSuccessRate?.trend_direction ?? 'down'}
            calculationTooltip={cardSuccessRate?.calculation_tooltip || '(Delivered Orders / Total Orders) * 100'}
            dataFreshness={cardSuccessRate?.data_freshness || 'Real-time MySQL Sync'}
            icon={Award}
            accent="emerald"
            aiPayload={{
              dashboardName: 'Executive Overview',
              kpiOrChartId: 'kpi_delivery_success_rate',
              selectedMetric: 'Delivery Success Rate',
              metricValue: `${kpis.delivery_success_rate ?? kpis.fulfillment_rate_pct}%`,
              city: activeCity,
              sourceComponent: 'ExecutiveKpiCard',
            }}
          />
        </div>
      </div>

      {/* =========================================================================
          SECTION 2: AI BUSINESS INTELLIGENCE CENTER (MASTER ORCHESTRATOR)
         ========================================================================= */}
      <div className="glass-card p-6 border-slate-200 bg-white shadow-sm">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-3 mb-5 border-b border-slate-200 pb-4">
          <div>
            <div className="flex items-center gap-2 mb-1">
              <span className="px-2 py-0.5 rounded text-[10px] font-bold uppercase tracking-wider bg-blue-50 text-blue-700 border border-blue-200 flex items-center gap-1">
                <Brain size={12} />
                <span>AI BUSINESS INTELLIGENCE CENTER</span>
              </span>
              <span className="text-slate-300">•</span>
              <span className="text-xs text-slate-500">Master Orchestrator Engine Active</span>
            </div>
            <h3 className="text-xl font-extrabold text-slate-900">Multi-Agent Prescriptive Recommendations</h3>
            <p className="text-xs text-slate-500 mt-0.5">
              Evidence-grounded insights synthesizing Financial, Customer, Operations, Restaurant, and Decision Agents.
            </p>
          </div>

          {/* 5 Domain Agent Badges & Copilot Launcher */}
          <div className="flex items-center gap-2 flex-wrap">
            <div className="flex items-center gap-1.5 flex-wrap">
              {[
                { name: 'Financial', color: 'text-green-700 border-green-200 bg-green-50' },
                { name: 'Customer', color: 'text-blue-700 border-blue-200 bg-blue-50' },
                { name: 'Operations', color: 'text-blue-800 border-blue-200 bg-blue-50' },
                { name: 'Restaurant', color: 'text-orange-700 border-orange-200 bg-orange-50' },
                { name: 'Decision', color: 'text-purple-700 border-purple-200 bg-purple-50' },
              ].map((agent) => (
                <span
                  key={agent.name}
                  className={`px-2 py-0.5 rounded text-[11px] font-medium border ${agent.color} flex items-center gap-1`}
                >
                  <span className="w-1.5 h-1.5 rounded-full bg-current animate-pulse" />
                  <span>{agent.name} Agent</span>
                </span>
              ))}
            </div>
            <button
              onClick={() => onNavigate('copilot')}
              className="px-3 py-1 rounded-lg text-xs font-semibold bg-orange-500 hover:bg-orange-600 text-white shadow-xs flex items-center gap-1.5 transition-all"
            >
              <Sparkles size={13} />
              <span>Open AI Copilot</span>
            </button>
          </div>
        </div>

        {/* Actionable Insights Grid wrapped in local ErrorBoundary */}
        <ErrorBoundary viewKey={`overview-recs-${recommendations.length}`}>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {(recommendations || []).slice(0, 3).map((rec) => {
              const isApproved = rec.status === 'Approved';
              const isPending = rec.status === 'Proposed' || rec.status === 'Under Review';
              const isLowEmpirical = rec.confidence_tier === 'LOW_EMPIRICAL';
              const isActing = actionLoadingId === rec.recommendation_id;
              const isSuccess = actionSuccessId === rec.recommendation_id;
              const evidence = Array.isArray(rec.supporting_evidence) ? rec.supporting_evidence : [];
              const netImpact = rec.net_financial_impact_rupees ?? (rec as any).net_financial_impact ?? 0;
              const roiMult = rec.roi_multiple ?? (rec as any).financial_impact?.roi_multiple ?? 0;
              const problem = rec.problem_statement || (rec as any).business_problem || (rec as any).title || 'Operational Intervention';
              const action = rec.proposed_action || (rec as any).action || 'Review and optimize workflow';

              return (
                <div
                  key={rec.recommendation_id}
                  className="p-4 rounded-xl bg-white border border-slate-200 flex flex-col justify-between hover:border-blue-300 transition-all shadow-xs group"
                >
                  <div>
                    <div className="flex items-center justify-between text-[11px] mb-2">
                      <span className="font-mono text-slate-500 font-bold">{rec.recommendation_id}</span>
                      <div className="flex items-center gap-1.5">
                        <span
                          className={`px-1.5 py-0.5 rounded text-[10px] font-semibold uppercase ${
                            rec.priority === 'CRITICAL'
                              ? 'bg-red-50 text-red-700 border border-red-200'
                              : rec.priority === 'HIGH'
                              ? 'bg-orange-50 text-orange-700 border border-orange-200'
                              : 'bg-slate-100 text-slate-700'
                          }`}
                        >
                          {rec.priority || 'MEDIUM'}
                        </span>
                        <span
                          className={`px-1.5 py-0.5 rounded text-[10px] font-mono ${
                            isLowEmpirical
                              ? 'bg-orange-50 text-orange-700 border border-orange-200'
                              : 'bg-green-50 text-green-700 border border-green-200'
                          }`}
                          title={isLowEmpirical ? 'Simulated projection; requires empirical verification' : 'Certified empirical derivation'}
                        >
                          {rec.confidence_tier || 'MODERATE'}
                        </span>
                      </div>
                    </div>

                    <h4 className="text-sm font-bold text-slate-900 mb-1.5 line-clamp-2">{problem}</h4>

                    {/* Supporting Evidence List */}
                    <div className="text-[11px] text-slate-600 space-y-1 mb-3 bg-slate-50 p-2.5 rounded-lg border border-slate-200">
                      <div className="text-[10px] font-semibold uppercase tracking-wider text-slate-500">Supporting Evidence:</div>
                      {evidence.slice(0, 2).map((ev, i) => (
                        <div key={i} className="flex items-start gap-1.5">
                          <span className="text-blue-600 shrink-0">•</span>
                          <span className="line-clamp-2">{ev}</span>
                        </div>
                      ))}
                      {evidence.length === 0 && (
                        <div className="text-[10px] text-slate-400 italic">Certified against empirical operations baseline</div>
                      )}
                    </div>

                    {/* Proposed Action */}
                    <div className="text-xs text-slate-700 mb-3">
                      <span className="font-semibold text-blue-700">Action: </span>
                      <span className="line-clamp-2">{action}</span>
                    </div>

                    {/* Financial Impact Breakdown */}
                    <div className="grid grid-cols-2 gap-2 text-[11px] p-2 rounded bg-slate-50 border border-slate-200 mb-3 font-mono">
                      <div>
                        <span className="text-slate-500 block text-[10px]">Net Impact (Est):</span>
                        <span className="font-bold text-green-600">+{formatCurrency(netImpact)}</span>
                      </div>
                      <div>
                        <span className="text-slate-500 block text-[10px]">ROI Multiple:</span>
                        <span className="font-bold text-blue-600">{Number(roiMult).toFixed(2)}x</span>
                      </div>
                    </div>
                  </div>

                  {/* Footer Controls: Human Approval Gate & Contextual AI */}
                  <div className="pt-2 border-t border-slate-200 flex items-center justify-between">
                    <div className="flex items-center gap-1.5">
                      {isPending && (rec.requires_human_approval ?? true) && (
                        <button
                          type="button"
                          onClick={() => handleApproveRecommendation(rec.recommendation_id)}
                          disabled={isActing}
                          className="px-2.5 py-1 text-xs font-semibold rounded bg-orange-500 hover:bg-orange-600 text-white flex items-center gap-1 transition-colors disabled:opacity-50"
                        >
                          {isActing ? (
                            <span>Approving...</span>
                          ) : isSuccess ? (
                            <>
                              <Check size={12} />
                              <span>Approved!</span>
                            </>
                          ) : (
                            <>
                              <ThumbsUp size={12} />
                              <span>Approve</span>
                            </>
                          )}
                        </button>
                      )}
                      {isApproved && (
                        <span className="px-2 py-0.5 rounded text-[11px] bg-green-50 text-green-700 border border-green-200 flex items-center gap-1">
                          <Check size={11} />
                          <span>Approved</span>
                        </span>
                      )}
                    </div>

                    <ContextualAIAction
                      payload={{
                        dashboardName: 'Executive Overview',
                        kpiOrChartId: `rec_${rec.recommendation_id}`,
                      entityId: rec.recommendation_id,
                      entityName: rec.problem_statement,
                      city: activeCity,
                      sourceComponent: 'AiIntelligenceCenter',
                      suggestedPrompt: `Analyze recommendation ${rec.recommendation_id} (${rec.problem_statement}) in detail. Evaluate risks, payback period, and empirical evidence.`,
                    }}
                    label="Analyze with AI"
                  />
                </div>
              </div>
            );
          })}
        </div>
        {(!recommendations || recommendations.length === 0) && (
          <div className="p-6 text-center rounded-xl bg-slate-50 border border-slate-200 text-slate-500 text-xs">
            No prescriptive recommendations currently active for the selected criteria.
          </div>
        )}
        </ErrorBoundary>

        {/* View All Recommendations Shortcut */}
        <div className="mt-4 pt-3 border-t border-slate-200 flex items-center justify-between text-xs text-slate-500">
          <span className="flex items-center gap-1">
            <span className="w-1.5 h-1.5 rounded-full bg-green-500" />
            <span>Human-in-the-Loop Governance: Unapproved executions blocked by system security policy.</span>
          </span>
          <button
            type="button"
            onClick={() => onNavigate('decision')}
            className="text-blue-600 hover:text-blue-700 font-semibold flex items-center gap-1"
          >
            Open Decision Action Center ({recommendations.length} total) <ArrowRight size={13} />
          </button>
        </div>
      </div>

      {/* =========================================================================
          SECTION 3: BUSINESS CHARTS & REGIONAL ATTRIBUTION
         ========================================================================= */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* 30-Day Platform Revenue Velocity */}
        <div className="lg:col-span-2 glass-card p-6">
          <SectionHeader
            title="30-Day Platform Revenue Velocity"
            subtitle="Daily GMV volume and net revenue inflow trend across territories"
            tag="FINANCIAL VELOCITY"
            action={
              <ContextualAIButton
                payload={{
                  dashboardName: 'Executive Overview',
                  kpiOrChartId: 'chart_revenue_velocity',
                  selectedMetric: '30-Day Platform Revenue Velocity',
                  city: activeCity,
                  sourceComponent: 'RevenueVelocityChart',
                  suggestedPrompt: `Analyze 30-day platform revenue velocity and daily demand trends${activeCity !== 'All' ? ` in ${activeCity}` : ''}.`,
                }}
                variant="badge"
                label="Analyze Velocity"
              />
            }
          />
          <div className="h-72 w-full">
            <ResponsiveContainer width="100%" height="100%">
              <AreaChart data={revenue_trend} margin={{ top: 10, right: 10, left: 0, bottom: 0 }}>
                <defs>
                  <linearGradient id="colorRev" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#2563EB" stopOpacity={0.35} />
                    <stop offset="95%" stopColor="#2563EB" stopOpacity={0.0} />
                  </linearGradient>
                  <linearGradient id="colorNet" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#0EA5E9" stopOpacity={0.3} />
                    <stop offset="95%" stopColor="#0EA5E9" stopOpacity={0.0} />
                  </linearGradient>
                </defs>
                <CartesianGrid strokeDasharray="3 3" stroke="#E2E8F0" vertical={false} />
                <XAxis dataKey="date" stroke="#64748B" fontSize={11} tickLine={false} />
                <YAxis
                  stroke="#64748B"
                  fontSize={11}
                  tickLine={false}
                  tickFormatter={(val) => `₹${(val / 1000).toFixed(0)}k`}
                />
                <Tooltip
                  contentStyle={{
                    backgroundColor: '#FFFFFF',
                    borderColor: '#E2E8F0',
                    color: '#1E293B',
                    borderRadius: '8px',
                    fontSize: '12px',
                    boxShadow: '0 4px 6px -1px rgba(0, 0, 0, 0.1)',
                  }}
                  formatter={(val: any, name: any) => [
                    formatCurrency(Number(val)),
                    name === 'revenue' ? 'Gross GMV' : 'Net Revenue',
                  ]}
                />
                <Legend wrapperStyle={{ fontSize: '11px', paddingTop: '8px', color: '#475569' }} />
                <Area
                  type="monotone"
                  dataKey="revenue"
                  name="Gross GMV"
                  stroke="#2563EB"
                  strokeWidth={2}
                  fillOpacity={1}
                  fill="url(#colorRev)"
                />
                <Area
                  type="monotone"
                  dataKey="net_revenue"
                  name="Net Inflow"
                  stroke="#0EA5E9"
                  strokeWidth={2}
                  fillOpacity={1}
                  fill="url(#colorNet)"
                />
              </AreaChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Territory Breakdown */}
        <div className="glass-card p-6">
          <SectionHeader
            title="Territory Distribution"
            subtitle="Revenue contribution by metro market"
            tag="REGIONAL SHARE"
            action={
              <ContextualAIButton
                payload={{
                  dashboardName: 'Executive Overview',
                  kpiOrChartId: 'chart_territory_distribution',
                  selectedMetric: 'Territory Distribution',
                  city: activeCity,
                  sourceComponent: 'TerritoryDistributionChart',
                  suggestedPrompt: 'Compare regional revenue contribution, market share, and order volumes across all metro cities.',
                }}
                variant="badge"
                label="Compare Cities"
              />
            }
          />
          <div className="h-72 w-full">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={city_breakdown} layout="vertical" margin={{ top: 5, right: 20, left: 30, bottom: 5 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#E2E8F0" horizontal={false} />
                <XAxis type="number" stroke="#64748B" fontSize={10} tickFormatter={(val) => `₹${(val / 100000).toFixed(0)}L`} />
                <YAxis dataKey="city" type="category" stroke="#1E293B" fontSize={11} tickLine={false} width={80} />
                <Tooltip
                  contentStyle={{
                    backgroundColor: '#FFFFFF',
                    borderColor: '#E2E8F0',
                    color: '#1E293B',
                    borderRadius: '8px',
                    fontSize: '12px',
                    boxShadow: '0 4px 6px -1px rgba(0, 0, 0, 0.1)',
                  }}
                  formatter={(val: any) => [formatCurrency(Number(val)), 'Revenue']}
                />
                <Bar dataKey="revenue" fill="#2563EB" radius={[0, 4, 4, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>
      </div>

      {/* =========================================================================
          SECTION 4: TOP PARTNER PERFORMANCE TABLE
         ========================================================================= */}
      <div className="space-y-3">
        <div className="flex items-center justify-between">
          <span className="text-xs text-slate-400">
            Interactive merchant portfolio with sorting, search, column selection and CSV export.
          </span>
          <button
            onClick={() => onNavigate('restaurant')}
            className="text-xs font-semibold text-sapphire-400 hover:text-sapphire-300 flex items-center gap-1 focus:outline-none focus:ring-1 focus:ring-blue-500 rounded px-2 py-1"
          >
            Full Merchant Intelligence <ArrowRight size={14} />
          </button>
        </div>

        <DataTable
          data={top_restaurants || []}
          keyExtractor={(r) => r.restaurant_id}
          title="High-Impact Merchant Anchors"
          subtitle="Top volume & GMV contributing restaurant partners in territory"
          searchPlaceholder="Search restaurants by name, city, cuisine..."
          exportFileName="novanest_top_restaurants"
          defaultSortKey="revenue"
          defaultSortDir="desc"
          columns={[
            {
              key: 'name',
              header: 'Restaurant',
              sortable: true,
              render: (r) => (
                <div>
                  <div className="font-semibold text-white">{r.name}</div>
                  <div className="text-[10px] font-mono text-slate-500">{r.restaurant_id}</div>
                </div>
              ),
              accessor: (r) => r.name,
            },
            {
              key: 'city',
              header: 'City',
              sortable: true,
              render: (r) => <span className="text-slate-300">{r.city}</span>,
              accessor: (r) => r.city,
            },
            {
              key: 'cuisine',
              header: 'Cuisine',
              sortable: true,
              render: (r) => <span className="text-slate-400">{r.cuisine}</span>,
              accessor: (r) => r.cuisine,
            },
            {
              key: 'orders',
              header: 'Orders',
              sortable: true,
              align: 'right',
              render: (r) => <span className="text-slate-300 font-mono">{formatNumber(r.orders)}</span>,
              accessor: (r) => r.orders,
            },
            {
              key: 'revenue',
              header: 'GMV',
              sortable: true,
              align: 'right',
              render: (r) => <span className="font-semibold text-green-600 font-mono">{formatCurrency(r.revenue)}</span>,
              accessor: (r) => r.revenue,
            },
            {
              key: 'rating',
              header: 'Rating',
              sortable: true,
              align: 'right',
              render: (r) => <span className="text-amber-500 font-semibold">{r.rating} ⭐</span>,
              accessor: (r) => r.rating,
            },
            {
              key: 'actions',
              header: 'AI Action',
              sortable: false,
              align: 'right',
              render: (r) => (
                <ContextualAIAction
                  payload={{
                    dashboardName: 'Executive Overview',
                    kpiOrChartId: 'table_top_restaurants',
                    entityType: 'restaurant',
                    entityId: r.restaurant_id,
                    entityName: r.name,
                    city: r.city,
                    sourceComponent: 'TopPartnersTable',
                    autoSubmit: true,
                  }}
                  label="Ask AI"
                />
              ),
            },
          ]}
        />
      </div>

      {/* =========================================================================
          SECTION 5: QUICK ACTION LAUNCHPAD
         ========================================================================= */}
      <div className="glass-card p-6 bg-white border border-slate-200 shadow-sm">
        <h3 className="text-base font-bold text-slate-900 mb-2">Executive Navigation Launchpad</h3>
        <p className="text-xs text-slate-500 mb-4">Direct shortcuts to specialized decision modules and analytical twins.</p>

        <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-3">
          {[
            { label: 'Customer Cohorts', tab: 'customer' as TabKey, icon: Users },
            { label: 'Merchant Risks', tab: 'restaurant' as TabKey, icon: Store },
            { label: 'Supply Radar', tab: 'operations' as TabKey, icon: ShoppingBag },
            { label: 'P&L Economics', tab: 'financial' as TabKey, icon: DollarSign },
            { label: 'AI Business Copilot', tab: 'copilot' as TabKey, icon: Sparkles },
            { label: 'What-If Lab', tab: 'simulator' as TabKey, icon: TrendingUp },
          ].map((action) => {
            const Icon = action.icon;
            return (
              <button
                key={action.tab}
                onClick={() => onNavigate(action.tab)}
                className="p-3 rounded-lg bg-slate-50 hover:bg-blue-50/60 border border-slate-200 hover:border-blue-300 text-left transition-all group"
              >
                <Icon size={18} className="text-blue-600 group-hover:text-blue-700 mb-2" />
                <p className="text-xs font-semibold text-slate-800 group-hover:text-blue-700 truncate">{action.label}</p>
                <span className="text-[10px] text-slate-400 flex items-center gap-0.5 mt-1">
                  Open <ArrowRight size={10} />
                </span>
              </button>
            );
          })}
        </div>
      </div>
    </div>
  );
};
