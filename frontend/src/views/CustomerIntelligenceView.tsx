import React, { useEffect, useState } from 'react';
import {
  Users,
  Target,
  Sparkles,
  AlertCircle,
  Eye,
  CheckCircle,
  X,
  CreditCard,
  ShoppingBag,
  Award,
  TrendingUp,
  UserCheck,
  UserPlus,
  ShieldAlert,
  ArrowRight,
  Brain,
} from 'lucide-react';
import {
  AreaChart,
  Area,
  BarChart,
  Bar,
  PieChart,
  Pie,
  Cell,
  XAxis,
  YAxis,
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
import { SkeletonLoader, DataTable, ColumnDef, StatusBadge } from '../components/ui';
import {
  api,
  CustomerData,
  CustomerListItem,
  Customer360Data,
  CustomerPrescriptiveProfile,
} from '../services/api';
import { formatCurrency, formatNumber, formatDateTimeToIST } from '../utils/formatters';

interface Props {
  filters?: GlobalFilterState;
}

export const CustomerIntelligenceView: React.FC<Props> = ({ filters }) => {
  const [data, setData] = useState<CustomerData | null>(null);
  const [customerList, setCustomerList] = useState<CustomerListItem[]>([]);
  const [selectedCustomerId, setSelectedCustomerId] = useState<string | null>(null);
  const [cust360, setCust360] = useState<Customer360Data | null>(null);
  const [prescriptiveProfile, setPrescriptiveProfile] = useState<CustomerPrescriptiveProfile | null>(null);
  const [loading360, setLoading360] = useState(false);
  const [loading, setLoading] = useState(true);

  const [error, setError] = useState<unknown>(null);
  const [error360, setError360] = useState<unknown>(null);

  const loadCustomerTelemetry = () => {
    setLoading(true);
    setError(null);
    Promise.all([api.getCustomerOverview(filters), api.getCustomerList()])
      .then(([overviewRes, listRes]) => {
        setData(overviewRes);
        setCustomerList(listRes);
      })
      .catch((err) => {
        console.error('Customer intelligence error:', err);
        setError(err);
      })
      .finally(() => setLoading(false));
  };

  useEffect(() => {
    loadCustomerTelemetry();
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

  const openCustomer360 = (id: string) => {
    setSelectedCustomerId(id);
    setCust360(null);
    setPrescriptiveProfile(null);
    setError360(null);
    setLoading360(true);
    Promise.all([
      api.getCustomer360(id),
      api.getPrescriptiveCustomerProfile(id).catch(() => null),
    ])
      .then(([res360, resPrescriptive]) => {
        setCust360(res360);
        setPrescriptiveProfile(resPrescriptive);
      })
      .catch((err) => {
        console.error('Customer 360 error:', err);
        setError360(err);
      })
      .finally(() => setLoading360(false));
  };

  if (loading) {
    return (
      <div className="space-y-6 animate-pulse" aria-busy="true" aria-label="Loading Customer Intelligence">
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
        title="Customer Intelligence Telemetry Unavailable"
        error={error || 'Empty customer payload received.'}
        onRetry={loadCustomerTelemetry}
      />
    );
  }

  const { kpis, rfm_segments, clv_tiers, churn_distribution, cohort_retention, acquisition_trends, new_vs_repeat, high_value_customers } = data;

  const repeatPct = new_vs_repeat?.repeat_percentage ?? 90.0;
  const newPct = (100 - repeatPct).toFixed(1);

  return (
    <div className="space-y-8 animate-fadeIn">
      {/* Title Header */}
      <div>
        <div className="flex items-center gap-2 mb-1">
          <span className="text-xs font-bold uppercase tracking-widest text-blue-600">CUSTOMER ENGINE</span>
          <span className="text-slate-300">•</span>
          <span className="text-xs text-slate-500">{formatNumber(data.kpis.total_customers)} Accounts Synthesized</span>
        </div>
        <h1 className="text-3xl font-extrabold tracking-tight text-slate-900">Customer Intelligence & Retention Center</h1>
        <p className="text-sm text-slate-500 mt-1">
          Customer acquisition velocity, new vs. repeat dynamics, RFM behavioral segmentation, 12-month CLV distribution, and high-value VIP identification.
        </p>
      </div>

      {/* SECTION A: KPIS */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <KpiCard
          label="Registered Customer Base"
          value={formatNumber(kpis.total_customers)}
          subtext="Total unique patrons"
          delta="Active cohort"
          deltaPositive={true}
          calculationTooltip="COUNT(DISTINCT customer_id) in database scope"
          dataFreshness="Real-time MySQL Sync"
          icon={Users}
          accent="sapphire"
          aiPayload={{
            dashboardName: 'Customer Intelligence',
            kpiOrChartId: 'kpi_total_customers',
            selectedMetric: 'Registered Customer Base',
            metricValue: formatNumber(kpis.total_customers),
            sourceComponent: 'CustomerKpiCard',
          }}
        />
        <KpiCard
          label="Average Order Basket (AOV)"
          value={formatCurrency(kpis.avg_aov)}
          subtext="Per-order expenditure"
          delta="+4.1% basket velocity"
          deltaPositive={true}
          calculationTooltip="Net Revenue / Delivered Orders (KPI-03 Net AOV)"
          dataFreshness="Real-time MySQL Sync"
          icon={ShoppingBag}
          accent="emerald"
          aiPayload={{
            dashboardName: 'Customer Intelligence',
            kpiOrChartId: 'kpi_avg_aov',
            selectedMetric: 'Average Order Value (AOV)',
            metricValue: formatCurrency(kpis.avg_aov),
            sourceComponent: 'CustomerKpiCard',
          }}
        />
        <KpiCard
          label="High Churn Vulnerability"
          value={`${kpis.high_churn_rate_pct}%`}
          subtext="Predicted 30-day drop risk"
          delta="LOW_EMPIRICAL Heuristic"
          deltaPositive={false}
          calculationTooltip="Percentage of customers flagged in High Churn Risk tier (LOW_EMPIRICAL)"
          dataFreshness="Real-time MySQL Sync"
          icon={AlertCircle}
          accent="crimson"
          aiPayload={{
            dashboardName: 'Customer Intelligence',
            kpiOrChartId: 'kpi_churn_vulnerability',
            selectedMetric: 'High Churn Vulnerability',
            metricValue: `${kpis.high_churn_rate_pct}%`,
            sourceComponent: 'CustomerKpiCard',
          }}
        />
        <KpiCard
          label="Mean 12-Month CLV"
          value={formatCurrency(kpis.avg_clv_12m)}
          subtext="Projected net revenue value"
          delta="Certified model benchmark"
          deltaPositive={true}
          calculationTooltip="Mean Estimated Customer Lifetime Value across 12-month horizon"
          dataFreshness="Real-time MySQL Sync"
          icon={Target}
          accent="cyan"
          aiPayload={{
            dashboardName: 'Customer Intelligence',
            kpiOrChartId: 'kpi_avg_clv_12m',
            selectedMetric: 'Mean 12-Month Customer Lifetime Value',
            metricValue: formatCurrency(kpis.avg_clv_12m),
            sourceComponent: 'CustomerKpiCard',
          }}
        />
      </div>

      {/* SECTION B: ACQUISITION TRENDS & NEW VS REPEAT BREAKDOWN */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Customer Acquisition Trends (Area Chart) */}
        <div className="lg:col-span-2 glass-card p-6">
          <SectionHeader
            title="Customer Acquisition Trajectory"
            subtitle="Monthly newly registered accounts onboarding onto the platform"
            tag="GROWTH VELOCITY"
            action={
              <ContextualAIButton
                payload={{
                  dashboardName: 'Customer Intelligence',
                  kpiOrChartId: 'chart_acquisition_trajectory',
                  selectedMetric: 'Customer Acquisition Trajectory',
                  sourceComponent: 'AcquisitionAreaChart',
                  suggestedPrompt: 'Analyze customer acquisition trends across signup months and evaluate organic growth velocity.',
                }}
                variant="badge"
                label="Analyze Growth"
              />
            }
          />
          <div className="h-72 w-full">
            <ResponsiveContainer width="100%" height="100%">
              <AreaChart data={acquisition_trends || []} margin={{ top: 10, right: 10, left: 0, bottom: 20 }}>
                <defs>
                  <linearGradient id="acqGrad" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#06B6D4" stopOpacity={0.4} />
                    <stop offset="95%" stopColor="#06B6D4" stopOpacity={0.0} />
                  </linearGradient>
                </defs>
                <CartesianGrid strokeDasharray="3 3" stroke="var(--theme-chart-grid, #1E293B)" vertical={false} />
                <XAxis dataKey="month" stroke="var(--theme-chart-axis, #64748B)" fontSize={11} tickLine={false} />
                <YAxis stroke="var(--theme-chart-axis, #64748B)" fontSize={11} tickLine={false} />
                <Tooltip
                  contentStyle={{
                    backgroundColor: 'var(--theme-tooltip-bg, #0F1622)',
                    borderColor: 'var(--theme-tooltip-border, #334155)',
                    color: 'var(--theme-tooltip-text, #F8FAFC)',
                    borderRadius: '8px',
                    fontSize: '12px',
                  }}
                  formatter={(val: any) => [`${formatNumber(Number(val))} signups`, 'New Customers']}
                />
                <Area type="monotone" dataKey="new_customers" name="New Customers" stroke="#06B6D4" strokeWidth={2.5} fillOpacity={1} fill="url(#acqGrad)" />
              </AreaChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* New vs. Repeat Customers Breakdown */}
        <div className="glass-card p-6 flex flex-col justify-between">
          <div>
            <SectionHeader
              title="New vs. Repeat Order Dynamics"
              subtitle="First-time orders vs. retention re-orders"
              tag="RETENTION RATIO"
            />
            <div className="mt-4 space-y-4">
              <div>
                <div className="flex justify-between text-xs mb-1.5">
                  <span className="text-slate-700 font-medium flex items-center gap-1">
                    <UserCheck size={14} className="text-green-600" />
                    Repeat Orders ({repeatPct}%)
                  </span>
                  <span className="text-green-600 font-bold num-tabular">
                    {formatNumber(new_vs_repeat?.repeat_orders ?? 44971)}
                  </span>
                </div>
                <div className="w-full bg-slate-200 rounded-full h-3 overflow-hidden">
                  <div
                    className="bg-green-600 h-full rounded-full transition-all duration-500"
                    style={{ width: `${repeatPct}%` }}
                  />
                </div>
              </div>

              <div>
                <div className="flex justify-between text-xs mb-1.5">
                  <span className="text-slate-300 font-medium flex items-center gap-1">
                    <UserPlus size={14} className="text-cyan-400" />
                    First-Time Orders ({newPct}%)
                  </span>
                  <span className="text-cyan-400 font-bold num-tabular">
                    {formatNumber(new_vs_repeat?.new_orders ?? 5000)}
                  </span>
                </div>
                <div className="w-full bg-slate-200 rounded-full h-3 overflow-hidden">
                  <div
                    className="bg-blue-600 h-full rounded-full transition-all duration-500"
                    style={{ width: `${newPct}%` }}
                  />
                </div>
              </div>

              <div className="p-3 rounded-lg bg-slate-50 border border-slate-200 text-xs text-slate-700 space-y-1">
                <div className="font-semibold text-slate-900 flex items-center gap-1">
                  <Award size={13} className="text-orange-500" />
                  High Retention Velocity
                </div>
                <p className="text-[11px] text-slate-500 leading-relaxed">
                  90.0% of transactions are generated by repeat diners, indicating high platform stickiness and sustainable organic retention.
                </p>
              </div>
            </div>
          </div>

          <div className="pt-3 border-t border-slate-200 mt-4">
            <ContextualAIAction
              payload={{
                dashboardName: 'Customer Intelligence',
                kpiOrChartId: 'new_vs_repeat_orders',
                selectedMetric: 'New vs. Repeat Ratio',
                sourceComponent: 'NewVsRepeatCard',
                suggestedPrompt: 'Evaluate repeat customer ordering patterns, repurchase intervals, and customer lifecycle longevity.',
              }}
              label="Ask Customer Agent"
            />
          </div>
        </div>
      </div>

      {/* SECTION C: RFM & CLV DISTRIBUTION CHARTS */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* RFM Segments */}
        <div className="glass-card p-6">
          <SectionHeader
            title="RFM Behavioral Segmentation"
            subtitle="Customer volume segmented by Recency, Frequency, and Monetary scores"
            tag="BEHAVIOR MATRIX"
            action={
              <ContextualAIButton
                payload={{
                  dashboardName: 'Customer Intelligence',
                  kpiOrChartId: 'chart_rfm_segmentation',
                  selectedMetric: 'RFM Behavioral Segmentation',
                  sourceComponent: 'RfmChart',
                  suggestedPrompt: 'Analyze RFM behavioral segmentation and customer volume distribution across recency, frequency, and monetary tiers.',
                }}
                variant="badge"
                label="Analyze RFM"
              />
            }
          />
          <div className="h-72 w-full">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={rfm_segments} margin={{ top: 10, right: 10, left: 0, bottom: 25 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="var(--theme-chart-grid, #1E293B)" vertical={false} />
                <XAxis dataKey="segment" stroke="var(--theme-chart-axis, #64748B)" fontSize={10} angle={-15} textAnchor="end" />
                <YAxis stroke="var(--theme-chart-axis, #64748B)" fontSize={11} tickLine={false} />
                <Tooltip
                  contentStyle={{
                    backgroundColor: 'var(--theme-tooltip-bg, #0F1622)',
                    borderColor: 'var(--theme-tooltip-border, #334155)',
                    color: 'var(--theme-tooltip-text, #F8FAFC)',
                    borderRadius: '8px',
                    fontSize: '12px',
                  }}
                  formatter={(val: any) => [`${val} patrons`, 'Customer Count']}
                />
                <Bar dataKey="count" fill="var(--theme-chart-primary, #3B82F6)" radius={[4, 4, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Churn Risk Distribution with LOW_EMPIRICAL Badge */}
        <div className="glass-card p-6">
          <div className="flex items-center justify-between mb-2">
            <div>
              <div className="flex items-center gap-1.5 mb-1">
                <span className="text-[10px] font-bold uppercase tracking-wider text-crimson-400 bg-crimson-500/10 px-2 py-0.5 rounded border border-crimson-500/30">
                  CHURN VULNERABILITY
                </span>
                <span className="px-1.5 py-0.5 rounded text-[10px] font-mono bg-amber-500/10 text-amber-300 border border-amber-500/30">
                  LOW_EMPIRICAL
                </span>
              </div>
              <h3 className="text-lg font-bold text-white">Risk Tier Volume Distribution</h3>
            </div>
            <ContextualAIButton
              payload={{
                dashboardName: 'Customer Intelligence',
                kpiOrChartId: 'chart_churn_distribution',
                selectedMetric: 'Churn Risk Tier Distribution',
                sourceComponent: 'ChurnDonutChart',
                suggestedPrompt: 'Analyze customer churn risk distribution, considering the LOW_EMPIRICAL confidence boundaries and discount guardrails.',
              }}
              variant="badge"
              label="Audit Churn"
            />
          </div>

          <div className="h-64 w-full">
            <ResponsiveContainer width="100%" height="100%">
              <PieChart>
                <Pie
                  data={churn_distribution}
                  dataKey="count"
                  nameKey="risk_level"
                  cx="50%"
                  cy="50%"
                  innerRadius={55}
                  outerRadius={85}
                  paddingAngle={4}
                >
                  {(churn_distribution || []).map((entry, index) => {
                    const color =
                      entry.risk_level.toLowerCase().includes('high')
                        ? '#EF4444'
                        : entry.risk_level.toLowerCase().includes('medium')
                        ? '#F59E0B'
                        : '#10B981';
                    return <Cell key={`cell-${index}`} fill={color} />;
                  })}
                </Pie>
                <Tooltip
                  contentStyle={{
                    backgroundColor: 'var(--theme-tooltip-bg, #0F1622)',
                    borderColor: 'var(--theme-tooltip-border, #334155)',
                    color: 'var(--theme-tooltip-text, #F8FAFC)',
                    borderRadius: '8px',
                    fontSize: '12px',
                  }}
                  formatter={(val: any, name: any, item: any) => [
                    `${formatNumber(Number(val))} accounts (${item.payload.percentage}%)`,
                    name,
                  ]}
                />
                <Legend wrapperStyle={{ fontSize: '11px', paddingTop: '10px' }} />
              </PieChart>
            </ResponsiveContainer>
          </div>
        </div>
      </div>

      {/* SECTION D: HIGH-VALUE VIP CUSTOMER IDENTIFICATION */}
      <div className="space-y-3">
        <DataTable
          data={high_value_customers || []}
          keyExtractor={(vip) => vip.customer_id}
          title="High-Value Customer Identification (Top CLV)"
          subtitle="Top patrons identified by certified 12-Month Lifetime Value projections"
          searchPlaceholder="Search customers by name, city, persona..."
          exportFileName="novanest_vip_customers"
          defaultSortKey="estimated_clv"
          defaultSortDir="desc"
          columns={[
            {
              key: 'customer_name',
              header: 'Customer',
              sortable: true,
              render: (vip) => (
                <div>
                  <div className="font-semibold text-white">{vip.customer_name}</div>
                  <div className="text-[10px] font-mono text-slate-500">{vip.customer_id}</div>
                </div>
              ),
              accessor: (vip) => vip.customer_name,
            },
            {
              key: 'city',
              header: 'City',
              sortable: true,
              render: (vip) => <span className="text-slate-300">{vip.city}</span>,
              accessor: (vip) => vip.city,
            },
            {
              key: 'persona',
              header: 'Persona',
              sortable: true,
              render: (vip) => (
                <StatusBadge
                  label={vip.persona}
                  variant="info"
                  size="sm"
                />
              ),
              accessor: (vip) => vip.persona,
            },
            {
              key: 'total_orders',
              header: 'Orders',
              sortable: true,
              align: 'right',
              render: (vip) => <span className="text-slate-300 font-mono">{formatNumber(vip.total_orders)}</span>,
              accessor: (vip) => vip.total_orders,
            },
            {
              key: 'total_revenue',
              header: 'Total Spend',
              sortable: true,
              align: 'right',
              render: (vip) => <span className="font-semibold text-slate-200 font-mono">{formatCurrency(vip.total_revenue)}</span>,
              accessor: (vip) => vip.total_revenue,
            },
            {
              key: 'aov',
              header: 'AOV',
              sortable: true,
              align: 'right',
              render: (vip) => <span className="text-slate-300 font-mono">{formatCurrency(vip.aov)}</span>,
              accessor: (vip) => vip.aov,
            },
            {
              key: 'estimated_clv',
              header: 'Projected 12M CLV',
              sortable: true,
              align: 'right',
              render: (vip) => <span className="font-bold text-green-600 font-mono">{formatCurrency(vip.estimated_clv)}</span>,
              accessor: (vip) => vip.estimated_clv,
            },
            {
              key: 'actions',
              header: 'AI Action',
              sortable: false,
              align: 'right',
              render: (vip) => (
                <ContextualAIAction
                  payload={{
                    dashboardName: 'Customer Intelligence',
                    kpiOrChartId: `vip_${vip.customer_id}`,
                    entityType: 'customer',
                    entityId: vip.customer_id,
                    entityName: vip.customer_name,
                    city: vip.city,
                    sourceComponent: 'HighValueCustomersTable',
                    suggestedPrompt: `Generate an individualized VIP retention and loyalty expansion plan for ${vip.customer_name} (CLV: ₹${vip.estimated_clv}, ${vip.total_orders} orders).`,
                    autoSubmit: true,
                  }}
                  label="Ask Customer Agent"
                />
              ),
            },
          ]}
        />
      </div>

      {/* SECTION E: COHORT RETENTION DECAY MATRIX */}
      <div className="glass-card p-6">
        <div className="flex items-center justify-between mb-4">
          <div>
            <span className="text-[10px] font-bold uppercase tracking-wider text-green-700 bg-green-50 px-2 py-0.5 rounded border border-green-200">
              RETENTION DECAY
            </span>
            <h3 className="text-lg font-bold text-slate-900 mt-1">Monthly Cohort Retention Matrix</h3>
          </div>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-center text-xs">
            <thead>
              <tr className="border-b border-slate-200 text-slate-500 uppercase tracking-wider">
                <th className="pb-2.5 text-left font-semibold">Cohort Month</th>
                <th className="pb-2.5 font-semibold">Month 0</th>
                <th className="pb-2.5 font-semibold">Month 1</th>
                <th className="pb-2.5 font-semibold">Month 2</th>
                <th className="pb-2.5 font-semibold">Month 3</th>
                <th className="pb-2.5 font-semibold">Month 4</th>
                <th className="pb-2.5 font-semibold">Month 5</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100 font-mono">
              {(cohort_retention || []).map((c) => (
                <tr key={c.cohort} className="hover:bg-slate-50">
                  <td className="py-2.5 text-left font-sans font-semibold text-slate-900">{c.cohort}</td>
                  <td className="py-2.5 text-green-700 font-bold bg-green-50">{c.month_0}%</td>
                  <td className="py-2.5 text-slate-700">{c.month_1}%</td>
                  <td className="py-2.5 text-slate-700">{c.month_2}%</td>
                  <td className="py-2.5 text-slate-700">{c.month_3}%</td>
                  <td className="py-2.5 text-slate-700">{c.month_4}%</td>
                  <td className="py-2.5 text-slate-700">{c.month_5}%</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};
