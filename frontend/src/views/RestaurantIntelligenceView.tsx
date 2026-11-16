import React, { useEffect, useState } from 'react';
import {
  Store,
  ShieldAlert,
  AlertTriangle,
  Award,
  Sparkles,
  Search,
  Activity,
  ArrowUpRight,
  X,
  CheckCircle2,
  Clock,
  TrendingUp,
  Percent,
  ChefHat,
  Compass,
} from 'lucide-react';
import {
  BarChart,
  Bar,
  ScatterChart,
  Scatter,
  XAxis,
  YAxis,
  ZAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Legend,
} from 'recharts';
import { KpiCard } from '../components/KpiCard';
import { SectionHeader } from '../components/SectionHeader';
import { ApiErrorState, EmptyStateCard } from '../components/ApiStatePanel';
import { ContextualAIButton } from '../components/ContextualAIButton';
import { ContextualAIAction } from '../components/ContextualAIAction';
import { GlobalFilterState } from '../components/GlobalFilterBar';
import { SkeletonLoader, DataTable, StatusBadge } from '../components/ui';
import { api, RestaurantData, RestaurantPrescriptiveProfile } from '../services/api';
import { formatCurrency, formatNumber } from '../utils/formatters';

interface Props {
  filters?: GlobalFilterState;
}

export const RestaurantIntelligenceView: React.FC<Props> = ({ filters }) => {
  const [data, setData] = useState<RestaurantData | null>(null);
  const [searchQuery, setSearchQuery] = useState('');
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<unknown>(null);

  // Restaurant 360 Prescriptive State
  const [selectedRestaurantId, setSelectedRestaurantId] = useState<string | null>(null);
  const [prescriptiveProfile, setPrescriptiveProfile] = useState<RestaurantPrescriptiveProfile | null>(null);
  const [loadingProfile, setLoadingProfile] = useState(false);

  const openRestaurantProfile = (restaurantId: string) => {
    setSelectedRestaurantId(restaurantId);
    setPrescriptiveProfile(null);
    setLoadingProfile(true);
    api
      .getPrescriptiveRestaurantProfile(restaurantId)
      .then((res) => setPrescriptiveProfile(res))
      .catch((err) => console.error('Restaurant profile error:', err))
      .finally(() => setLoadingProfile(false));
  };

  const loadOverview = () => {
    setLoading(true);
    setError(null);
    api
      .getRestaurantOverview(filters)
      .then((res) => setData(res))
      .catch((err) => {
        console.error('Restaurant overview error:', err);
        setError(err);
      })
      .finally(() => setLoading(false));
  };

  useEffect(() => {
    loadOverview();
  }, [
    filters?.city,
    filters?.dateRange,
    filters?.startDate,
    filters?.endDate,
    filters?.restaurantId,
    filters?.customerSegment,
    filters?.orderStatus,
    filters?.paymentMethod,
  ]);

  if (loading) {
    return (
      <div className="space-y-6 animate-pulse" aria-busy="true" aria-label="Loading Restaurant Intelligence">
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
          <SkeletonLoader variant="kpi" count={4} />
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
        title="Restaurant Intelligence Telemetry Unavailable"
        error={error || 'Empty restaurant telemetry payload received.'}
        onRetry={loadOverview}
      />
    );
  }

  const {
    kpis,
    health_distribution,
    risk_distribution,
    cuisine_benchmarks,
    performance_matrix,
    early_warnings,
    restaurant_ranking,
    underperforming_restaurants,
  } = data;

  const filteredRanking = (restaurant_ranking || []).filter(
    (r) =>
      r.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
      r.city.toLowerCase().includes(searchQuery.toLowerCase()) ||
      r.cuisine.toLowerCase().includes(searchQuery.toLowerCase())
  );

  return (
    <div className="space-y-8 animate-fadeIn">
      {/* Title */}
      <div>
        <div className="flex items-center gap-2 mb-1">
          <span className="text-xs font-bold uppercase tracking-widest text-blue-600">MERCHANT NETWORK</span>
          <span className="text-slate-300">•</span>
          <span className="text-xs text-slate-500">{formatNumber(data.kpis.total_restaurants)} Kitchens Under Active Telemetry</span>
        </div>
        <h1 className="text-3xl font-extrabold tracking-tight text-slate-900">Restaurant Intelligence & Risk Engine</h1>
        <p className="text-sm text-slate-500 mt-1">
          Composite Merchant Health Scores (0-100), partner revenue rankings, prep duration SLAs, cancellation rates, and proactive remediation.
        </p>
      </div>

      {/* SECTION A: KPIS */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <KpiCard
          label="Partner Network Size"
          value={formatNumber(kpis.total_restaurants)}
          subtext="Licensed merchants"
          delta="Full coverage"
          deltaPositive={true}
          calculationTooltip="COUNT(DISTINCT restaurant_id) in database scope"
          dataFreshness="Real-time MySQL Sync"
          icon={Store}
          accent="sapphire"
          aiPayload={{
            dashboardName: 'Restaurant Intelligence',
            kpiOrChartId: 'kpi_partner_network_size',
            selectedMetric: 'total_restaurants',
            metricValue: formatNumber(kpis.total_restaurants),
            sourceComponent: 'RestaurantKpiCard',
          }}
        />
        <KpiCard
          label="Mean Merchant Health"
          value={`${kpis.avg_health_score}/100`}
          subtext="Composite multi-factor index"
          delta={kpis.avg_health_score >= 70 ? 'Nominal partner SLA' : 'Watch status'}
          deltaPositive={kpis.avg_health_score >= 70}
          calculationTooltip="Weighted score of prep latency, customer rating, volume, and order completion"
          dataFreshness="Real-time MySQL Sync"
          icon={Activity}
          accent={kpis.avg_health_score >= 70 ? 'emerald' : 'amber'}
          aiPayload={{
            dashboardName: 'Restaurant Intelligence',
            kpiOrChartId: 'kpi_mean_merchant_health',
            selectedMetric: 'avg_health_score',
            metricValue: `${kpis.avg_health_score}/100`,
            sourceComponent: 'RestaurantKpiCard',
          }}
        />
        <KpiCard
          label="Critical Risk Merchants"
          value={formatNumber(kpis.critical_risk_count)}
          subtext="Health < 50 or severe churn"
          delta="Remediation candidate"
          deltaPositive={false}
          calculationTooltip="Count of restaurant partners flagged with Health Score < 50 or severe churn indicators"
          dataFreshness="Real-time MySQL Sync"
          icon={ShieldAlert}
          accent="crimson"
          aiPayload={{
            dashboardName: 'Restaurant Intelligence',
            kpiOrChartId: 'kpi_critical_risk_merchants',
            selectedMetric: 'critical_risk_count',
            metricValue: formatNumber(kpis.critical_risk_count),
            sourceComponent: 'RestaurantKpiCard',
          }}
        />
        <KpiCard
          label="Active Early Warnings"
          value={formatNumber(kpis.active_early_warnings)}
          subtext="Operational threshold breaches"
          delta="Partner alerts"
          deltaPositive={false}
          calculationTooltip="Active automated anomaly flags (rating drop, cancellation surge, prep latency)"
          dataFreshness="Real-time MySQL Sync"
          icon={AlertTriangle}
          accent="amber"
          aiPayload={{
            dashboardName: 'Restaurant Intelligence',
            kpiOrChartId: 'kpi_active_early_warnings',
            selectedMetric: 'active_early_warnings',
            metricValue: formatNumber(kpis.active_early_warnings),
            sourceComponent: 'RestaurantKpiCard',
          }}
        />
      </div>

      {/* SECTION B: RESTAURANT PERFORMANCE RANKINGS TABLE */}
      <div className="glass-card p-6">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-3 mb-4">
          <div>
            <span className="text-[10px] font-bold uppercase tracking-wider text-green-700 bg-green-50 px-2 py-0.5 rounded border border-green-200">
              MERCHANT RANKINGS
            </span>
            <h3 className="text-lg font-bold text-slate-900 mt-1">Partner Performance & Revenue Contribution</h3>
            <p className="text-xs text-slate-500 mt-0.5">
              Ranked by total Gross Merchandise Value, prep duration SLAs, and order cancellation rates.
            </p>
          </div>

          <div className="flex items-center gap-2">
            <div className="relative">
              <Search size={14} className="absolute left-2.5 top-1/2 -translate-y-1/2 text-slate-400" />
              <input
                type="text"
                placeholder="Search merchant, city, cuisine..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="bg-white border border-slate-300 text-slate-800 text-xs rounded-lg pl-8 pr-3 py-1.5 focus:outline-none focus:border-blue-600 focus:ring-1 focus:ring-blue-600/20 w-64 shadow-2xs"
              />
            </div>
          </div>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left text-sm">
            <thead>
              <tr className="border-b border-slate-200 text-slate-500 text-xs uppercase tracking-wider">
                <th className="pb-3 font-semibold">Restaurant</th>
                <th className="pb-3 font-semibold">City</th>
                <th className="pb-3 font-semibold">Cuisine</th>
                <th className="pb-3 font-semibold text-right">Orders</th>
                <th className="pb-3 font-semibold text-right">Revenue</th>
                <th className="pb-3 font-semibold text-right">Share %</th>
                <th className="pb-3 font-semibold text-right">Avg Prep</th>
                <th className="pb-3 font-semibold text-right">Cancel %</th>
                <th className="pb-3 font-semibold text-center">Health</th>
                <th className="pb-3 font-semibold text-right">AI Action</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {filteredRanking.slice(0, 15).map((r) => (
                <tr key={r.restaurant_id} className="hover:bg-slate-50 transition-colors">
                  <td className="py-3 font-medium text-slate-900">
                    <div>{r.name}</div>
                    <span className="text-[10px] font-mono text-slate-400">{r.restaurant_id}</span>
                  </td>
                  <td className="py-3 text-slate-600">{r.city}</td>
                  <td className="py-3 text-slate-600">{r.cuisine}</td>
                  <td className="py-3 text-right text-slate-700 num-tabular">{r.orders}</td>
                  <td className="py-3 text-right font-semibold text-green-600 num-tabular">{formatCurrency(r.revenue)}</td>
                  <td className="py-3 text-right text-slate-700 num-tabular">{r.revenue_share_pct}%</td>
                  <td className="py-3 text-right text-slate-700 num-tabular">{r.avg_prep_duration_mins}m</td>
                  <td className="py-3 text-right text-slate-700 num-tabular">{r.cancellation_rate_pct}%</td>
                  <td className="py-3 text-center">
                    <span
                      className={`px-2 py-0.5 rounded text-xs font-semibold ${
                        r.health_score >= 80
                          ? 'bg-green-50 text-green-700 border border-green-200'
                          : r.health_score >= 65
                          ? 'bg-orange-50 text-orange-700 border border-orange-200'
                          : 'bg-red-50 text-red-700 border border-red-200'
                      }`}
                    >
                      {r.health_score}
                    </span>
                  </td>
                  <td className="py-3 text-right">
                    <div className="flex items-center justify-end gap-1.5">
                      <ContextualAIAction
                        payload={{
                          dashboardName: 'Restaurant Intelligence',
                          kpiOrChartId: `rest_${r.restaurant_id}`,
                          entityType: 'restaurant',
                          entityId: r.restaurant_id,
                          entityName: r.name,
                          city: r.city,
                          sourceComponent: 'RestaurantRankingTable',
                          suggestedPrompt: `Analyze partner performance, prep duration bottlenecks, and cancellation root causes for ${r.name} (${r.restaurant_id}).`,
                          autoSubmit: true,
                        }}
                        label="Ask Agent"
                      />
                      <button
                        type="button"
                        onClick={() => openRestaurantProfile(r.restaurant_id)}
                        className="p-1 rounded hover:bg-slate-100 text-slate-500 hover:text-slate-900"
                        title="Inspect 360"
                      >
                        <ArrowUpRight size={14} />
                      </button>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* SECTION C: UNDERPERFORMING PARTNERS REMEDIATION */}
      <div className="space-y-3">
        <DataTable
          data={underperforming_restaurants || []}
          keyExtractor={(u) => u.restaurant_id}
          title="Underperforming Merchants Requiring Operational Support"
          subtitle="Partners with Health Score < 65 or elevated prep latency flagged for partner coaching"
          searchPlaceholder="Search merchants by name, city, cuisine, issue..."
          exportFileName="novanest_underperforming_merchants"
          defaultSortKey="health_score"
          defaultSortDir="asc"
          columns={[
            {
              key: 'name',
              header: 'Restaurant Partner',
              sortable: true,
              render: (u) => (
                <div>
                  <div className="font-semibold text-white">{u.name}</div>
                  <div className="text-[10px] font-mono text-slate-500">{u.restaurant_id}</div>
                </div>
              ),
              accessor: (u) => u.name,
            },
            {
              key: 'city',
              header: 'City',
              sortable: true,
              render: (u) => <span className="text-slate-300">{u.city}</span>,
              accessor: (u) => u.city,
            },
            {
              key: 'cuisine',
              header: 'Cuisine',
              sortable: true,
              render: (u) => <span className="text-slate-400">{u.cuisine}</span>,
              accessor: (u) => u.cuisine,
            },
            {
              key: 'health_score',
              header: 'Health Score',
              sortable: true,
              align: 'center',
              render: (u) => (
                <StatusBadge
                  label={String(u.health_score)}
                  variant={u.health_score < 50 ? 'danger' : 'warning'}
                  icon="warning"
                  size="sm"
                />
              ),
              accessor: (u) => u.health_score,
            },
            {
              key: 'issue',
              header: 'Diagnosed Issue',
              sortable: true,
              render: (u) => <span className="text-amber-300 text-xs">{u.issue}</span>,
              accessor: (u) => u.issue,
            },
            {
              key: 'recommended_action',
              header: 'Recommended Remediation',
              sortable: false,
              render: (u) => <span className="text-slate-300 text-xs">{u.recommended_action}</span>,
            },
            {
              key: 'actions',
              header: 'Action',
              sortable: false,
              align: 'right',
              render: (u) => (
                <ContextualAIAction
                  payload={{
                    dashboardName: 'Restaurant Intelligence',
                    kpiOrChartId: `remediate_${u.restaurant_id}`,
                    entityType: 'restaurant',
                    entityId: u.restaurant_id,
                    entityName: u.name,
                    city: u.city,
                    sourceComponent: 'UnderperformingRestaurantsTable',
                    suggestedPrompt: `Generate partner consultation checklist and kitchen prep SLA remediation playbook for ${u.name} (${u.issue}).`,
                    autoSubmit: true,
                  }}
                  label="Deploy Consultation"
                />
              ),
            },
          ]}
        />
      </div>

      {/* SECTION D: CUISINE BENCHMARKS & HEALTH DISTRIBUTION */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Health Distribution */}
        <div className="glass-card p-6">
          <SectionHeader
            title="Merchant Health Score Distribution"
            subtitle="Partners categorized across composite vitality tiers"
            tag="HEALTH BINS"
          />
          <div className="h-64 w-full mt-3">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={health_distribution} margin={{ top: 10, right: 10, left: 0, bottom: 20 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="var(--theme-chart-grid, #1E293B)" vertical={false} />
                <XAxis dataKey="tier" stroke="var(--theme-chart-axis, #64748B)" fontSize={10} />
                <YAxis stroke="var(--theme-chart-axis, #64748B)" fontSize={11} tickLine={false} />
                <Tooltip
                  contentStyle={{
                    backgroundColor: 'var(--theme-tooltip-bg, #0F1622)',
                    borderColor: 'var(--theme-tooltip-border, #334155)',
                    color: 'var(--theme-tooltip-text, #F8FAFC)',
                    borderRadius: '8px',
                    fontSize: '12px',
                  }}
                  formatter={(val: any) => [`${val} restaurants`, 'Count']}
                />
                <Bar dataKey="count" fill="#3B82F6" radius={[4, 4, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Cuisine Benchmarks */}
        <div className="glass-card p-6">
          <SectionHeader
            title="Cuisine Category Benchmarks"
            subtitle="Average revenue contribution and volume per cuisine type"
            tag="CUISINE SHARE"
          />
          <div className="h-64 w-full mt-3">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={cuisine_benchmarks} margin={{ top: 10, right: 10, left: 10, bottom: 20 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#E2E8F0" vertical={false} />
                <XAxis dataKey="cuisine" stroke="#64748B" fontSize={10} />
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
                  formatter={(val: any) => [formatCurrency(Number(val)), 'Avg Revenue']}
                />
                <Bar dataKey="avg_revenue" fill="#2563EB" radius={[4, 4, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>
      </div>
    </div>
  );
};
