import React, { useEffect, useState } from 'react';
import {
  IndianRupee,
  TrendingUp,
  Percent,
  AlertTriangle,
  ArrowDownRight,
  ShieldAlert,
  Tag,
  PieChart as PieIcon,
  CheckCircle2,
  Calendar,
  CreditCard,
  Building2,
  BarChart3,
  Layers,
  ArrowRight,
} from 'lucide-react';
import {
  AreaChart,
  Area,
  BarChart,
  Bar,
  LineChart,
  Line,
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
import { SkeletonLoader, DataTable, StatusBadge } from '../components/ui';
import { api, FinancialData } from '../services/api';
import { formatCurrency, formatNumber, formatPercent } from '../utils/formatters';

const PIE_COLORS = ['#2563EB', '#F97316', '#0EA5E9', '#16A34A', '#F59E0B', '#DC2626'];

interface Props {
  filters?: GlobalFilterState;
}

export const FinancialIntelligenceView: React.FC<Props> = ({ filters }) => {
  const [data, setData] = useState<FinancialData | null>(null);
  const [trendGranularity, setTrendGranularity] = useState<'daily' | 'weekly' | 'monthly'>('daily');
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<unknown>(null);

  const loadFinancials = () => {
    setLoading(true);
    setError(null);
    api
      .getFinancialOverview(filters)
      .then((res) => setData(res))
      .catch((err) => {
        console.error('Financial overview error:', err);
        setError(err);
      })
      .finally(() => setLoading(false));
  };

  useEffect(() => {
    loadFinancials();
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
      <div className="space-y-6 animate-pulse" aria-busy="true" aria-label="Loading Financial Intelligence">
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
        title="Financial Intelligence Telemetry Unavailable"
        error={error || 'Empty financial payload received.'}
        onRetry={loadFinancials}
      />
    );
  }

  const { kpis, unit_economics, revenue_leakage, promotions, revenue_trends, payment_methods, city_financials, aov_trend } = data;

  const revenuePillars = [
    { name: 'Commission Rev (20%)', amount: kpis.commission_revenue, fill: '#2563EB' },
    { name: 'Delivery Fee Rev', amount: kpis.delivery_fee_revenue, fill: '#0EA5E9' },
    { name: 'Promo Subsidies', amount: -kpis.discount_subsidies, fill: '#DC2626' },
    { name: 'Realized Profit', amount: kpis.realized_operating_profit ?? kpis.net_platform_revenue, fill: '#16A34A' },
  ];

  // Active trend dataset normalized with consistent 'label' key
  const rawTrend =
    trendGranularity === 'weekly'
      ? revenue_trends?.weekly || []
      : trendGranularity === 'monthly'
      ? revenue_trends?.monthly || []
      : revenue_trends?.daily || [];

  const activeTrendData = rawTrend.map((item: any) => ({
    label: String(item.date || item.week || item.month || ''),
    gmv: item.gmv ?? 0,
    net_revenue: item.net_revenue ?? 0,
    orders: item.orders ?? 0,
  }));

  return (
    <div className="space-y-8 animate-fadeIn">
      {/* Title Header */}
      <div>
        <div className="flex items-center gap-2 mb-1">
          <span className="text-xs font-bold uppercase tracking-widest text-blue-600">FINANCIAL ENGINE</span>
          <span className="text-slate-300">•</span>
          <span className="text-xs text-slate-500">Platform P&L & Take Rate Economics</span>
        </div>
        <h1 className="text-3xl font-extrabold tracking-tight text-slate-900">Financial Intelligence & Unit Economics</h1>
        <p className="text-sm text-slate-500 mt-1">
          Gross Merchandise Value reconciliation, take rate velocity, multi-granularity revenue trends, payment distributions, and leakage audits.
        </p>
      </div>

      {/* SECTION A: FINANCIAL KPIS */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <KpiCard
          label="Gross Merchandise Value (GMV)"
          value={formatCurrency(kpis.gross_merchandise_value)}
          subtext="Total transaction volume"
          delta="Topline GMV"
          deltaPositive={true}
          calculationTooltip="SUM(order_amount) WHERE order_status != 'Cancelled'"
          dataFreshness="Real-time MySQL Sync"
          icon={IndianRupee}
          accent="emerald"
          aiPayload={{
            dashboardName: 'Financial Intelligence',
            kpiOrChartId: 'kpi_gross_merchandise_value',
            selectedMetric: 'Gross Merchandise Value',
            metricValue: formatCurrency(kpis.gross_merchandise_value),
            sourceComponent: 'FinancialKpiCard',
          }}
        />
        <KpiCard
          label="Net Revenue (Platform Inflow)"
          value={formatCurrency(kpis.net_platform_revenue)}
          subtext="Delivered order cash inflow (KPI-02)"
          delta={`${kpis.profit_margin_pct}% realized margin`}
          deltaPositive={true}
          calculationTooltip="SUM(final_amount) WHERE order_status == 'Delivered'"
          dataFreshness="Real-time MySQL Sync"
          icon={TrendingUp}
          accent="sapphire"
          aiPayload={{
            dashboardName: 'Financial Intelligence',
            kpiOrChartId: 'kpi_net_platform_revenue',
            selectedMetric: 'Net Platform Revenue',
            metricValue: formatCurrency(kpis.net_platform_revenue),
            sourceComponent: 'FinancialKpiCard',
          }}
        />
        <KpiCard
          label="Discount & Fee Subsidies"
          value={formatCurrency(kpis.discount_subsidies)}
          subtext="Delivered order discounts"
          delta="Platform funded promotions"
          deltaPositive={false}
          calculationTooltip="SUM(discount_amount) on delivered platform transactions"
          dataFreshness="Real-time MySQL Sync"
          icon={ArrowDownRight}
          accent="amber"
          aiPayload={{
            dashboardName: 'Financial Intelligence',
            kpiOrChartId: 'kpi_discount_subsidies',
            selectedMetric: 'Discount & Fee Subsidies',
            metricValue: formatCurrency(kpis.discount_subsidies),
            sourceComponent: 'FinancialKpiCard',
          }}
        />
        <KpiCard
          label="Potential Risk Exposure"
          value={formatCurrency(kpis.total_potential_risk_exposure ?? kpis.total_revenue_leakage)}
          subtext="Unverified screening candidates"
          delta="Statistical outlier screening"
          deltaPositive={false}
          calculationTooltip="Aggregated potential exposure from statistical leakage candidates"
          dataFreshness="Real-time MySQL Sync"
          icon={ShieldAlert}
          accent="crimson"
          aiPayload={{
            dashboardName: 'Financial Intelligence',
            kpiOrChartId: 'kpi_potential_risk_exposure',
            selectedMetric: 'Potential Risk Exposure',
            metricValue: formatCurrency(kpis.total_potential_risk_exposure ?? kpis.total_revenue_leakage),
            sourceComponent: 'FinancialKpiCard',
          }}
        />
      </div>

      {/* SECTION B: MULTI-GRANULARITY REVENUE TRENDS (GROSS VS NET) */}
      <div className="glass-card p-6">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 mb-4">
          <div>
            <div className="flex items-center gap-2 mb-1">
              <span className="text-[10px] font-bold uppercase tracking-wider text-sapphire-400 bg-sapphire-500/10 px-2 py-0.5 rounded border border-sapphire-500/30">
                REVENUE DYNAMICS
              </span>
              <span className="text-xs text-slate-500">Gross GMV vs. Net Cash Inflow</span>
            </div>
            <h3 className="text-lg font-bold text-slate-900">Comparative Revenue Velocity</h3>
          </div>

          {/* Granularity Toggle Buttons */}
          <div className="flex items-center gap-1 bg-slate-100 border border-slate-200 p-1 rounded-lg">
            {(['daily', 'weekly', 'monthly'] as const).map((gran) => (
              <button
                key={gran}
                type="button"
                onClick={() => setTrendGranularity(gran)}
                className={`px-3 py-1 text-xs font-semibold rounded-md capitalize transition-colors ${
                  trendGranularity === gran
                    ? 'bg-blue-600 text-white shadow-xs'
                    : 'text-slate-600 hover:text-slate-900 hover:bg-white/60'
                }`}
              >
                {gran}
              </button>
            ))}
          </div>
        </div>

        <div className="h-80 w-full">
          <ResponsiveContainer width="100%" height="100%">
            <AreaChart data={activeTrendData} margin={{ top: 10, right: 10, left: 10, bottom: 10 }}>
              <defs>
                <linearGradient id="gmvGrad" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="#2563EB" stopOpacity={0.35} />
                  <stop offset="95%" stopColor="#2563EB" stopOpacity={0.0} />
                </linearGradient>
                <linearGradient id="netGrad" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="#0EA5E9" stopOpacity={0.3} />
                  <stop offset="95%" stopColor="#0EA5E9" stopOpacity={0.0} />
                </linearGradient>
              </defs>
              <CartesianGrid strokeDasharray="3 3" stroke="#E2E8F0" vertical={false} />
              <XAxis dataKey="label" stroke="#64748B" fontSize={11} tickLine={false} />
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
                  name === 'gmv' ? 'Gross Merchandise Value' : 'Net Revenue (Delivered)',
                ]}
              />
              <Legend wrapperStyle={{ fontSize: '11px', paddingTop: '10px', color: '#475569' }} />
              <Area
                type="monotone"
                dataKey="gmv"
                name="Gross GMV"
                stroke="#2563EB"
                strokeWidth={2}
                fillOpacity={1}
                fill="url(#gmvGrad)"
              />
              <Area
                type="monotone"
                dataKey="net_revenue"
                name="Net Revenue"
                stroke="#0EA5E9"
                strokeWidth={2}
                fillOpacity={1}
                fill="url(#netGrad)"
              />
            </AreaChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* SECTION C: PAYMENT METHODS & AOV DYNAMICS */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Payment Method Distribution */}
        <div className="glass-card p-6">
          <SectionHeader
            title="Payment Method Distribution"
            subtitle="Order volume and settlement share across payment instruments"
            tag="PAYMENT RAILS"
            action={
              <ContextualAIButton
                payload={{
                  dashboardName: 'Financial Intelligence',
                  kpiOrChartId: 'chart_payment_methods',
                  selectedMetric: 'Payment Method Distribution',
                  sourceComponent: 'PaymentMethodsDonut',
                  suggestedPrompt: 'Analyze payment method distribution and gateway conversion trends.',
                }}
                variant="badge"
                label="Analyze Rails"
              />
            }
          />
          <div className="h-64 w-full">
            <ResponsiveContainer width="100%" height="100%">
              <PieChart>
                <Pie
                  data={payment_methods || []}
                  dataKey="order_count"
                  nameKey="payment_method"
                  cx="50%"
                  cy="50%"
                  innerRadius={60}
                  outerRadius={90}
                  paddingAngle={3}
                >
                  {(payment_methods || []).map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={PIE_COLORS[index % PIE_COLORS.length]} />
                  ))}
                </Pie>
                <Tooltip
                  contentStyle={{
                    backgroundColor: '#FFFFFF',
                    borderColor: '#E2E8F0',
                    color: '#1E293B',
                    borderRadius: '8px',
                    fontSize: '12px',
                    boxShadow: '0 4px 6px -1px rgba(0, 0, 0, 0.1)',
                  }}
                  formatter={(val: any, name: any, item: any) => [
                    `${formatNumber(Number(val))} orders (${item.payload.percentage}%) • ${formatCurrency(item.payload.gmv)}`,
                    name,
                  ]}
                />
                <Legend wrapperStyle={{ fontSize: '11px', paddingTop: '10px', color: '#475569' }} />
              </PieChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Monthly AOV Trends */}
        <div className="glass-card p-6">
          <SectionHeader
            title="Average Order Value (AOV) Trend"
            subtitle="Gross basket vs. Net platform inflow per order across months"
            tag="BASKET EXPANSION"
            action={
              <ContextualAIButton
                payload={{
                  dashboardName: 'Financial Intelligence',
                  kpiOrChartId: 'chart_aov_trend',
                  selectedMetric: 'AOV Trend',
                  sourceComponent: 'AovTrendLineChart',
                  suggestedPrompt: 'Analyze monthly AOV basket expansion and discount erosion over time.',
                }}
                variant="badge"
                label="Analyze Basket"
              />
            }
          />
          <div className="h-64 w-full">
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={aov_trend || []} margin={{ top: 10, right: 10, left: 10, bottom: 10 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#E2E8F0" vertical={false} />
                <XAxis dataKey="month" stroke="#64748B" fontSize={11} tickLine={false} />
                <YAxis
                  stroke="#64748B"
                  fontSize={11}
                  tickLine={false}
                  tickFormatter={(val) => `₹${val}`}
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
                    name === 'net_aov' ? 'Net Delivered AOV' : 'Gross AOV',
                  ]}
                />
                <Legend wrapperStyle={{ fontSize: '11px', paddingTop: '10px', color: '#475569' }} />
                <Line type="monotone" dataKey="gross_aov" name="Gross AOV" stroke="#2563EB" strokeWidth={2} dot={{ r: 3 }} />
                <Line type="monotone" dataKey="net_aov" name="Net AOV" stroke="#0EA5E9" strokeWidth={2} dot={{ r: 3 }} />
              </LineChart>
            </ResponsiveContainer>
          </div>
        </div>
      </div>

      {/* SECTION D: CITY FINANCIAL PERFORMANCE & UNIT ECONOMICS */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* City Financial Performance Table */}
        <div className="lg:col-span-2">
          <DataTable
            data={city_financials || []}
            keyExtractor={(cf) => cf.city}
            title="City-Wise Financial Performance"
            subtitle="Revenue contribution, transaction volume, and estimated take rate yield by territory"
            searchPlaceholder="Search cities..."
            exportFileName="novanest_city_financials"
            defaultSortKey="net_revenue"
            defaultSortDir="desc"
            columns={[
              {
                key: 'city',
                header: 'City Territory',
                sortable: true,
                render: (cf) => <span className="font-semibold text-white">{cf.city}</span>,
                accessor: (cf) => cf.city,
              },
              {
                key: 'orders',
                header: 'Orders',
                sortable: true,
                align: 'right',
                render: (cf) => <span className="text-slate-300 font-mono">{formatNumber(cf.orders)}</span>,
                accessor: (cf) => cf.orders,
              },
              {
                key: 'gmv',
                header: 'Gross GMV',
                sortable: true,
                align: 'right',
                render: (cf) => <span className="font-semibold text-slate-100 font-mono">{formatCurrency(cf.gmv)}</span>,
                accessor: (cf) => cf.gmv,
              },
              {
                key: 'net_revenue',
                header: 'Net Revenue',
                sortable: true,
                align: 'right',
                render: (cf) => <span className="font-semibold text-green-600 font-mono">{formatCurrency(cf.net_revenue)}</span>,
                accessor: (cf) => cf.net_revenue,
              },
              {
                key: 'estimated_commission',
                header: 'Est Commission',
                sortable: true,
                align: 'right',
                render: (cf) => <span className="text-cyan-300 font-mono">{formatCurrency(cf.estimated_commission)}</span>,
                accessor: (cf) => cf.estimated_commission,
              },
              {
                key: 'actions',
                header: 'AI Action',
                sortable: false,
                align: 'right',
                render: (cf) => (
                  <ContextualAIAction
                    payload={{
                      dashboardName: 'Financial Intelligence',
                      kpiOrChartId: `city_${cf.city}`,
                      entityName: cf.city,
                      city: cf.city,
                      sourceComponent: 'CityFinancialsTable',
                      suggestedPrompt: `Analyze financial performance, take rate realization, and margin potential for ${cf.city}.`,
                    }}
                    label="Ask AI"
                  />
                ),
              },
            ]}
          />
        </div>

        {/* Per-Order Unit Economics Snapshot */}
        <div className="glass-card p-6 flex flex-col justify-between">
          <div>
            <SectionHeader
              title="Per-Order Unit Economics"
              subtitle="Completed (Delivered) order economics"
              tag="UNIT ECONOMICS"
            />
            <div className="space-y-3 mt-3">
              <div className="flex items-center justify-between p-2.5 rounded-lg bg-slate-50 border border-slate-200 text-xs">
                <span className="text-slate-500">Average Basket (Net AOV)</span>
                <span className="font-bold text-slate-900 num-tabular">{formatCurrency(unit_economics.aov)}</span>
              </div>
              <div className="flex items-center justify-between p-2.5 rounded-lg bg-slate-50 border border-slate-200 text-xs">
                <span className="text-slate-500">Commission Take Rate</span>
                <span className="font-bold text-blue-600 num-tabular">{unit_economics.commission_take_rate}%</span>
              </div>
              <div className="flex items-center justify-between p-2.5 rounded-lg bg-slate-50 border border-slate-200 text-xs">
                <span className="text-slate-500">Avg Delivery Fee Collected</span>
                <span className="font-bold text-blue-700 num-tabular">{formatCurrency(unit_economics.avg_delivery_fee)}</span>
              </div>
              <div className="flex items-center justify-between p-2.5 rounded-lg bg-slate-50 border border-slate-200 text-xs">
                <span className="text-slate-500">Avg Discount Subsidy Burn</span>
                <span className="font-bold text-red-600 num-tabular">-{formatCurrency(unit_economics.avg_discount_subsidy)}</span>
              </div>
            </div>
          </div>

          <div className="pt-4 border-t border-slate-200 mt-4 flex items-center justify-between">
            <div>
              <span className="text-xs text-slate-500 block">Net Unit Contribution</span>
              <span className="text-lg font-bold text-green-600 num-tabular">
                {formatCurrency(unit_economics.net_unit_contribution)}
              </span>
            </div>
            <ContextualAIAction
              payload={{
                dashboardName: 'Financial Intelligence',
                kpiOrChartId: 'unit_economics_summary',
                selectedMetric: 'Unit Economics Summary',
                sourceComponent: 'UnitEconomicsSnapshot',
                suggestedPrompt: 'Provide deep dive analysis of unit economics contribution margin drivers and subsidy efficiency.',
              }}
              label="Analyze Margin"
            />
          </div>
        </div>
      </div>

      {/* SECTION E: REVENUE LEAKAGE CANDIDATES */}
      <div className="space-y-3">
        <DataTable
          data={revenue_leakage || []}
          keyExtractor={(l, i) => `${l.category}-${i}`}
          title="Revenue Leakage Investigation Candidates"
          subtitle="Empirical rule/statistical screening candidates (not confirmed losses) awaiting partner ledger reconciliation"
          searchPlaceholder="Search leakage categories, actions..."
          exportFileName="novanest_revenue_leakage"
          defaultSortKey="amount"
          defaultSortDir="desc"
          columns={[
            {
              key: 'category',
              header: 'Anomaly Category',
              sortable: true,
              render: (l) => <span className="font-semibold text-white">{l.category}</span>,
              accessor: (l) => l.category,
            },
            {
              key: 'flagged_order_count',
              header: 'Flagged Orders',
              sortable: true,
              align: 'right',
              render: (l) => <span className="text-slate-300 font-mono">{formatNumber(l.flagged_order_count ?? 0)}</span>,
              accessor: (l) => l.flagged_order_count ?? 0,
            },
            {
              key: 'amount',
              header: 'Potential Exposure',
              sortable: true,
              align: 'right',
              render: (l) => <span className="font-bold text-crimson-400 font-mono">{formatCurrency(l.amount)}</span>,
              accessor: (l) => l.amount,
            },
            {
              key: 'detection_category',
              header: 'Detection Category',
              sortable: true,
              render: (l) => (
                <StatusBadge
                  label={l.detection_category || 'Statistical Screening'}
                  variant="warning"
                  icon="warning"
                  size="sm"
                />
              ),
              accessor: (l) => l.detection_category || 'Statistical Screening',
            },
            {
              key: 'recommended_action',
              header: 'Recommended Action',
              sortable: false,
              render: (l) => <span className="text-slate-300 text-xs">{l.recommended_action}</span>,
            },
          ]}
        />
      </div>
    </div>
  );
};
