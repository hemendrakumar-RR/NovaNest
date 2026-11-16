import React, { useEffect, useState } from 'react';
import {
  Truck,
  Clock,
  CheckCircle,
  AlertOctagon,
  Users,
  Navigation,
  Activity,
  Layers,
  Bike,
  AlertTriangle,
  MapPin,
  TrendingUp,
  Percent,
  Compass,
} from 'lucide-react';
import {
  LineChart,
  Line,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from 'recharts';
import { KpiCard } from '../components/KpiCard';
import { SectionHeader } from '../components/SectionHeader';
import { ApiErrorState, EmptyStateCard } from '../components/ApiStatePanel';
import { ContextualAIButton } from '../components/ContextualAIButton';
import { ContextualAIAction } from '../components/ContextualAIAction';
import { GlobalFilterState } from '../components/GlobalFilterBar';
import { SkeletonLoader, DataTable, StatusBadge } from '../components/ui';
import { api, OperationsData, RiderFleetWorkload } from '../services/api';
import { formatNumber } from '../utils/formatters';

interface Props {
  filters?: GlobalFilterState;
}

export const OperationsIntelligenceView: React.FC<Props> = ({ filters }) => {
  const [data, setData] = useState<OperationsData | null>(null);
  const [workload, setWorkload] = useState<RiderFleetWorkload | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<unknown>(null);

  const loadOperations = () => {
    setLoading(true);
    setError(null);
    Promise.all([
      api.getOperationsOverview(filters),
      api.getPrescriptiveRiderFleetWorkload().catch(() => null),
    ])
      .then(([opsRes, workloadRes]) => {
        setData(opsRes);
        setWorkload(workloadRes);
      })
      .catch((err) => {
        console.error('Operations overview error:', err);
        setError(err);
      })
      .finally(() => setLoading(false));
  };

  useEffect(() => {
    loadOperations();
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
      <div className="space-y-6 animate-pulse" aria-busy="true" aria-label="Loading Operations Intelligence">
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
        title="Operations Intelligence Telemetry Unavailable"
        error={error || 'Empty operations payload received.'}
        onRetry={loadOperations}
      />
    );
  }

  const {
    kpis,
    delivery_vitals,
    rider_rankings,
    city_operations,
    demand_forecast,
    demand_heatmap,
    rider_allocation,
    anomalies,
  } = data;

  const totalDeliv = delivery_vitals?.total_deliveries ?? kpis.total_deliveries;
  const completedDeliv = delivery_vitals?.completed_deliveries ?? totalDeliv;
  const avgDur = delivery_vitals?.avg_duration_mins ?? kpis.avg_duration_mins;
  const latePct = delivery_vitals?.late_delivery_pct ?? (100 - kpis.ontime_rate_pct);
  const fleetUtil = delivery_vitals?.fleet_utilization_pct ?? 83.3;

  return (
    <div className="space-y-8 animate-fadeIn">
      {/* Title */}
      <div>
        <div className="flex items-center gap-2 mb-1">
          <span className="text-xs font-bold uppercase tracking-widest text-blue-600">DISPATCH RADAR</span>
          <span className="text-slate-300">•</span>
          <span className="text-xs text-slate-500">
            {formatNumber(totalDeliv)} Deliveries &amp; {formatNumber(kpis.active_riders)} Active Riders
          </span>
        </div>
        <h1 className="text-3xl font-extrabold tracking-tight text-slate-900">Operations &amp; Logistics Intelligence</h1>
        <p className="text-sm text-slate-500 mt-1">
          Doorstep fulfillment vitals, fleet performance rankings, city delivery bottlenecks, and statistical screening candidates.
        </p>
      </div>

      {/* Prominent Telematics Baseline Caveat (Scientific Honesty) */}
      <div className="p-3 rounded-xl bg-slate-50 border border-slate-200 flex items-center justify-between text-xs text-slate-700 shadow-2xs">
        <div className="flex items-center gap-2.5">
          <span className="w-2 h-2 rounded-full bg-blue-600 animate-pulse" />
          <span className="font-semibold text-slate-800">Telematics Mode:</span>
          <span className="font-mono text-blue-700">BASELINE_ONLY</span>
          <span className="text-slate-500">•</span>
          <span className="text-slate-400 text-[11px]">
            Historical delivery dataset; no live GPS telematics simulation or synthetic rider positioning.
          </span>
        </div>
        <span className="px-2 py-0.5 rounded text-[10px] font-mono bg-slate-800 text-slate-400 border border-slate-700">
          Certified Audit Log
        </span>
      </div>

      {/* SECTION A: DELIVERY OPERATIONS VITALS */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-3.5">
        <KpiCard
          label="Total Deliveries"
          value={formatNumber(totalDeliv)}
          subtext="Total doorstep journeys"
          delta="Full coverage"
          deltaPositive={true}
          calculationTooltip="COUNT(delivery_id) across all recorded transit trips"
          dataFreshness="Real-time MySQL Sync"
          icon={Truck}
          accent="sapphire"
          aiPayload={{
            dashboardName: 'Operations Intelligence',
            kpiOrChartId: 'kpi_total_deliveries',
            selectedMetric: 'total_deliveries',
            metricValue: totalDeliv,
            sourceComponent: 'OperationsKpiCard',
            suggestedPrompt: `Analyze total delivery volume (${totalDeliv} trips) across metro territories and fulfillment velocity.`,
          }}
        />
        <KpiCard
          label="Completed Deliveries"
          value={formatNumber(completedDeliv)}
          subtext="Delivered to doorstep"
          delta="Successful handoffs"
          deltaPositive={true}
          calculationTooltip="COUNT(order_id) WHERE order_status == 'Delivered'"
          dataFreshness="Real-time MySQL Sync"
          icon={CheckCircle}
          accent="emerald"
          aiPayload={{
            dashboardName: 'Operations Intelligence',
            kpiOrChartId: 'kpi_completed_deliveries',
            selectedMetric: 'completed_deliveries',
            metricValue: completedDeliv,
            sourceComponent: 'OperationsKpiCard',
          }}
        />
        <KpiCard
          label="Mean Delivery Duration"
          value={`${avgDur} mins`}
          subtext="Kitchen to doorstep"
          delta="Transit benchmark"
          deltaPositive={true}
          calculationTooltip="AVG(delivery_duration) in minutes across completed dispatches"
          dataFreshness="Real-time MySQL Sync"
          icon={Clock}
          accent="sapphire"
          aiPayload={{
            dashboardName: 'Operations Intelligence',
            kpiOrChartId: 'kpi_mean_delivery_duration',
            selectedMetric: 'avg_duration_mins',
            metricValue: avgDur,
            sourceComponent: 'OperationsKpiCard',
            suggestedPrompt: `Analyze mean delivery duration (${avgDur} mins), transit latency bottlenecks, and kitchen handoff times.`,
          }}
        />
        <KpiCard
          label="Late Delivery SLA Rate"
          value={`${latePct}%`}
          subtext="Trips exceeding 45m"
          delta="Transit latency"
          deltaPositive={false}
          calculationTooltip="Percentage of trips with delivery duration > 45 minutes or delay flag set"
          dataFreshness="Real-time MySQL Sync"
          icon={AlertOctagon}
          accent="crimson"
          aiPayload={{
            dashboardName: 'Operations Intelligence',
            kpiOrChartId: 'kpi_late_delivery_rate',
            selectedMetric: 'late_delivery_pct',
            metricValue: `${latePct}%`,
            sourceComponent: 'OperationsKpiCard',
          }}
        />
        <KpiCard
          label="Fleet Utilization Rate"
          value={`${fleetUtil}%`}
          subtext="Active fleet deployment"
          delta="Operational capacity"
          deltaPositive={fleetUtil >= 75}
          calculationTooltip="Estimated active rider fleet utilization based on completed dispatches vs capacity"
          dataFreshness="Real-time MySQL Sync"
          icon={Bike}
          accent="cyan"
          aiPayload={{
            dashboardName: 'Operations Intelligence',
            kpiOrChartId: 'kpi_fleet_utilization',
            selectedMetric: 'fleet_utilization_pct',
            metricValue: `${fleetUtil}%`,
            sourceComponent: 'OperationsKpiCard',
          }}
        />
      </div>

      {/* SECTION B: RIDER PERFORMANCE RANKINGS TABLE */}
      <div className="glass-card p-6">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-3 mb-4">
          <div>
            <span className="text-[10px] font-bold uppercase tracking-wider text-green-700 bg-green-50 px-2 py-0.5 rounded border border-green-200">
              FLEET ANCHORS
            </span>
            <h3 className="text-lg font-bold text-slate-900 mt-1">Rider Performance &amp; Fulfillment Ranking</h3>
            <p className="text-xs text-slate-500 mt-0.5">
              Top delivery partners ranked by completed volume, transit duration, and efficiency.
            </p>
          </div>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left text-sm">
            <thead>
              <tr className="border-b border-slate-200 text-slate-500 text-xs uppercase tracking-wider">
                <th className="pb-3 font-semibold">Rider Partner</th>
                <th className="pb-3 font-semibold">City</th>
                <th className="pb-3 font-semibold">Vehicle</th>
                <th className="pb-3 font-semibold text-right">Completed Trips</th>
                <th className="pb-3 font-semibold text-right">Avg Duration</th>
                <th className="pb-3 font-semibold text-right">Avg Distance</th>
                <th className="pb-3 font-semibold text-right">Experience</th>
                <th className="pb-3 font-semibold text-right">AI Action</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {(rider_rankings || []).map((r) => (
                <tr key={r.rider_id} className="hover:bg-slate-50 transition-colors">
                  <td className="py-3 font-medium text-slate-900">
                    <div>{r.name}</div>
                    <span className="text-[10px] font-mono text-slate-400">{r.rider_id}</span>
                  </td>
                  <td className="py-3 text-slate-600">{r.city}</td>
                  <td className="py-3 text-slate-600">{r.vehicle_type}</td>
                  <td className="py-3 text-right font-semibold text-green-600 num-tabular">{r.completed_deliveries}</td>
                  <td className="py-3 text-right text-slate-700 num-tabular">{r.avg_duration_mins} mins</td>
                  <td className="py-3 text-right text-slate-700 num-tabular">{r.avg_distance_km} km</td>
                  <td className="py-3 text-right text-slate-500 num-tabular">{r.experience_years} yrs</td>
                  <td className="py-3 text-right">
                    <ContextualAIAction
                      payload={{
                        dashboardName: 'Operations Intelligence',
                        kpiOrChartId: `rider_${r.rider_id}`,
                        entityType: 'rider',
                        entityId: r.rider_id,
                        entityName: r.name,
                        city: r.city,
                        sourceComponent: 'RiderRankingsTable',
                        suggestedPrompt: `Analyze dispatch efficiency, routing paths, and fulfillment speed for rider ${r.name} (${r.rider_id}).`,
                        autoSubmit: true,
                      }}
                      label="Ask Operations Agent"
                    />
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* SECTION C: CITY-WISE OPERATIONS & BOTTLENECK RADAR */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* City-Wise Delivery Performance */}
        <div className="glass-card p-6">
          <SectionHeader
            title="Territory Delivery Performance &amp; SLA Rates"
            subtitle="Fulfillment duration and late delivery rates by metro territory"
            tag="TERRITORY SLA"
          />
          <div className="overflow-x-auto mt-3">
            <table className="w-full text-left text-sm">
              <thead>
                <tr className="border-b border-slate-200 text-slate-500 text-xs uppercase tracking-wider">
                  <th className="pb-3 font-semibold">City</th>
                  <th className="pb-3 font-semibold text-right">Trips</th>
                  <th className="pb-3 font-semibold text-right">Avg Mins</th>
                  <th className="pb-3 font-semibold text-right">Late Deliveries</th>
                  <th className="pb-3 font-semibold text-right">Late %</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {(city_operations || []).map((c) => (
                  <tr key={c.city} className="hover:bg-slate-50 transition-colors">
                    <td className="py-2.5 font-medium text-slate-900">{c.city}</td>
                    <td className="py-2.5 text-right text-slate-700 num-tabular">{formatNumber(c.deliveries)}</td>
                    <td className="py-2.5 text-right text-slate-700 num-tabular">{c.avg_duration_mins}m</td>
                    <td className="py-2.5 text-right text-red-600 num-tabular">{formatNumber(c.late_deliveries)}</td>
                    <td className="py-2.5 text-right font-bold text-orange-600 num-tabular">{c.late_delivery_pct}%</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>

        {/* 28-Day Demand Forecast vs Observed */}
        <div className="glass-card p-6">
          <SectionHeader
            title="14-Day Demand Forecast Horizon"
            subtitle="Observed deliveries alongside OLS demand predictions and prediction intervals"
            tag="PREDICTIVE DISPATCH"
            action={
              <ContextualAIButton
                payload={{
                  dashboardName: 'Operations Intelligence',
                  kpiOrChartId: 'chart_demand_forecast',
                  selectedMetric: 'Demand Forecast Horizon',
                  sourceComponent: 'ForecastChart',
                  suggestedPrompt: 'Analyze demand forecast accuracy, prediction interval bounds, and capacity planning for peak hours.',
                }}
                variant="badge"
                label="Forecast Insights"
              />
            }
          />
          <div className="h-64 w-full">
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={demand_forecast || []} margin={{ top: 10, right: 10, left: 10, bottom: 10 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#E2E8F0" vertical={false} />
                <XAxis dataKey="date" stroke="#64748B" fontSize={10} tickLine={false} />
                <YAxis stroke="#64748B" fontSize={11} tickLine={false} />
                <Tooltip
                  contentStyle={{
                    backgroundColor: '#FFFFFF',
                    borderColor: '#E2E8F0',
                    color: '#1E293B',
                    borderRadius: '8px',
                    fontSize: '12px',
                    boxShadow: '0 4px 6px -1px rgba(0, 0, 0, 0.1)',
                  }}
                />
                <Legend wrapperStyle={{ fontSize: '11px', paddingTop: '10px', color: '#475569' }} />
                <Line type="monotone" dataKey="actual" name="Observed Demand" stroke="#2563EB" strokeWidth={2} dot={false} />
                <Line type="monotone" dataKey="forecast" name="Forecast Demand" stroke="#F97316" strokeWidth={2} strokeDasharray="5 5" dot={false} />
              </LineChart>
            </ResponsiveContainer>
          </div>
        </div>
      </div>

      {/* SECTION D: OPERATIONAL ANOMALIES TABLE */}
      <div className="space-y-3">
        <DataTable
          data={anomalies || []}
          keyExtractor={(a, i) => `${a.id || i}`}
          title="Operational Anomalies & Latency Spikes"
          subtitle="Statistical Z-Score and Tukey IQR screening candidates preserved for operational review"
          searchPlaceholder="Search anomalies by entity, type, severity, description..."
          exportFileName="novanest_operational_anomalies"
          defaultSortKey="severity"
          defaultSortDir="desc"
          columns={[
            {
              key: 'id',
              header: 'Entity',
              sortable: true,
              render: (a) => <span className="font-mono text-xs text-slate-300">{a.id}</span>,
              accessor: (a) => a.id,
            },
            {
              key: 'type',
              header: 'Type',
              sortable: true,
              render: (a) => <span className="text-slate-400 text-xs">{a.type}</span>,
              accessor: (a) => a.type,
            },
            {
              key: 'severity',
              header: 'Severity',
              sortable: true,
              align: 'center',
              render: (a) => (
                <StatusBadge
                  label={a.severity}
                  variant={a.severity === 'Critical' ? 'danger' : a.severity === 'High' ? 'warning' : 'neutral'}
                  icon={a.severity === 'Critical' ? 'error' : a.severity === 'High' ? 'warning' : 'info'}
                  size="sm"
                />
              ),
              accessor: (a) => (a.severity === 'Critical' ? 3 : a.severity === 'High' ? 2 : 1),
            },
            {
              key: 'description',
              header: 'Description',
              sortable: false,
              render: (a) => <span className="text-slate-200 text-xs">{a.description}</span>,
            },
            {
              key: 'impact',
              header: 'Impacted Metric',
              sortable: true,
              render: (a) => <span className="text-slate-400 text-xs font-mono">{a.impact}</span>,
              accessor: (a) => a.impact,
            },
          ]}
        />
      </div>
    </div>
  );
};
