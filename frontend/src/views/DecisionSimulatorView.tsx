import React, { useState, useEffect } from 'react';
import {
  Sliders,
  TrendingUp,
  Percent,
  Sparkles,
  RefreshCw,
  ArrowRight,
  ShieldCheck,
  CheckCircle2,
  DollarSign,
  AlertTriangle,
  Users,
  Store,
  Truck,
  FileText,
  Activity,
  Layers,
} from 'lucide-react';
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from 'recharts';
import { SectionHeader } from '../components/SectionHeader';
import { ApiErrorState } from '../components/ApiStatePanel';
import { api, ControlledSimulationResult } from '../services/api';
import { formatCurrency, formatNumber } from '../utils/formatters';

interface ScenarioDef {
  id: string;
  name: string;
  category: string;
  icon: any;
  description: string;
  defaultOverrides: Record<string, number>;
  controls: Array<{
    key: string;
    label: string;
    min: number;
    max: number;
    step: number;
    unit: string;
    desc: string;
  }>;
}

const SCENARIOS: ScenarioDef[] = [
  {
    id: 'promotion_optimization',
    name: 'Promotional Discount Capping (20% Cap)',
    category: 'Revenue Optimization',
    icon: DollarSign,
    description: 'Enforces a strict 20% ceiling on platform coupons and curbs uncontained customer subsidies.',
    defaultOverrides: {
      discount_reduction_pct: 15.0,
      volume_elasticity_pct: -1.5,
    },
    controls: [
      {
        key: 'discount_reduction_pct',
        label: 'Discount Expenditure Reduction',
        min: 5,
        max: 30,
        step: 1,
        unit: '%',
        desc: 'Targeted reduction in overall coupon expenditure by capping excessive promos.',
      },
      {
        key: 'volume_elasticity_pct',
        label: 'Volume Elasticity Sensitivity',
        min: -5.0,
        max: 0.0,
        step: 0.5,
        unit: '%',
        desc: 'Projected volume elasticity loss from highly coupon-dependent customers.',
      },
    ],
  },
  {
    id: 'delivery_fee_restructuring',
    name: 'Delivery Fee Surcharge & Basket MOV',
    category: 'Revenue Optimization',
    icon: Layers,
    description: 'Adds a ₹10 surcharge on dispatches >5km and incentivizes basket sizes above ₹350.',
    defaultOverrides: {
      fee_delta_rupees: 10.0,
      aov_uplift_pct: 3.5,
      volume_elasticity_pct: -2.5,
    },
    controls: [
      {
        key: 'fee_delta_rupees',
        label: 'Delivery Surcharge (>5km)',
        min: 5,
        max: 25,
        step: 5,
        unit: '₹',
        desc: 'Additional delivery surcharge applied to long-distance orders.',
      },
      {
        key: 'aov_uplift_pct',
        label: 'Average Order Value Uplift',
        min: 1.0,
        max: 10.0,
        step: 0.5,
        unit: '%',
        desc: 'Estimated basket uplift stimulated by combo bundle suggestions.',
      },
      {
        key: 'volume_elasticity_pct',
        label: 'Volume Drop from Surcharge',
        min: -6.0,
        max: -0.5,
        step: 0.5,
        unit: '%',
        desc: 'Estimated customer churn from delivery fee increase.',
      },
    ],
  },
  {
    id: 'rider_capacity_expansion',
    name: 'Peak Hour Rider Fleet Expansion',
    category: 'Rider Logistics',
    icon: Truck,
    description: 'Allocates an incentive bonus pool to surge rider active rosters during peak dinner hours (19:00-22:00).',
    defaultOverrides: {
      fleet_expansion_pct: 15.0,
      sla_reduction_pct: 25.0,
      cost_incentive_pool: 45000.0,
    },
    controls: [
      {
        key: 'fleet_expansion_pct',
        label: 'Active Rider Roster Expansion',
        min: 5,
        max: 30,
        step: 5,
        unit: '%',
        desc: 'Target percentage increase in active riders during peak dinner hours.',
      },
      {
        key: 'sla_reduction_pct',
        label: 'SLA Breach (>45m) Reduction',
        min: 10,
        max: 50,
        step: 5,
        unit: '%',
        desc: 'Targeted reduction in delivery duration breaches.',
      },
      {
        key: 'cost_incentive_pool',
        label: 'Monthly Rider Incentive Pool',
        min: 20000,
        max: 90000,
        step: 5000,
        unit: '₹',
        desc: 'Budget dedicated to peak-hour completion bonuses.',
      },
    ],
  },
  {
    id: 'restaurant_capacity_acceleration',
    name: 'Merchant Kitchen Prep Acceleration',
    category: 'Restaurant Optimization',
    icon: Store,
    description: 'Deploys dispatch buffer adjustments and kitchen order streaming to reduce preparation bottlenecks.',
    defaultOverrides: {
      cancellation_drop_pct: 40.0,
    },
    controls: [
      {
        key: 'cancellation_drop_pct',
        label: 'Merchant Cancellation Reduction',
        min: 15,
        max: 60,
        step: 5,
        unit: '%',
        desc: 'Targeted reduction in partner cancellations through kitchen optimization.',
      },
    ],
  },
  {
    id: 'customer_retention_campaign',
    name: 'VIP Customer Retention Defense',
    category: 'Customer Retention',
    icon: Users,
    description: 'Deploys a targeted retention budget to re-engage inactive VIP Champions before terminal attrition.',
    defaultOverrides: {
      retention_budget: 45000.0,
      retention_rate_pct: 35.0,
    },
    controls: [
      {
        key: 'retention_budget',
        label: 'Targeted Retention Voucher Budget',
        min: 20000,
        max: 100000,
        step: 5000,
        unit: '₹',
        desc: 'Allocated coupon pool restricted to verified VIP champions inactive >60 days.',
      },
      {
        key: 'retention_rate_pct',
        label: 'Target VIP Re-engagement Rate',
        min: 15,
        max: 60,
        step: 5,
        unit: '%',
        desc: 'Expected conversion rate of inactive VIPs placing an order within 30 days.',
      },
    ],
  },
];

export const DecisionSimulatorView: React.FC = () => {
  const [selectedScenarioId, setSelectedScenarioId] = useState<string>('promotion_optimization');
  const [paramOverrides, setParamOverrides] = useState<Record<string, number>>(
    SCENARIOS[0].defaultOverrides
  );
  const [simResult, setSimResult] = useState<ControlledSimulationResult | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<unknown>(null);

  const activeScenario = SCENARIOS.find((s) => s.id === selectedScenarioId) || SCENARIOS[0];

  const handleScenarioChange = (scenarioId: string) => {
    setSelectedScenarioId(scenarioId);
    const target = SCENARIOS.find((s) => s.id === scenarioId) || SCENARIOS[0];
    setParamOverrides({ ...target.defaultOverrides });
  };

  const handleParamChange = (key: string, value: number) => {
    setParamOverrides((prev) => ({ ...prev, [key]: value }));
  };

  const runSimulation = () => {
    setLoading(true);
    setError(null);
    api
      .simulatePrescriptiveScenario(selectedScenarioId, paramOverrides)
      .then((res) => setSimResult(res))
      .catch((err) => {
        console.error('Controlled scenario error:', err);
        setError(err);
      })
      .finally(() => setLoading(false));
  };

  useEffect(() => {
    runSimulation();
  }, [selectedScenarioId]);

  // Comparison chart data
  const chartData = simResult
    ? [
        {
          metric: 'Gross Food GMV',
          Baseline: Math.round(simResult.baseline.realized_gross_gmv / 100000),
          Simulated: Math.round(simResult.projected_outcomes.projected_gross_gmv / 100000),
        },
        {
          metric: 'Net Revenue',
          Baseline: Math.round(simResult.baseline.realized_net_revenue / 100000),
          Simulated: Math.round(simResult.projected_outcomes.projected_net_revenue / 100000),
        },
        {
          metric: 'Contribution Profit',
          Baseline: Math.round(simResult.baseline.net_contribution_margin / 100000),
          Simulated: Math.round(simResult.projected_outcomes.projected_contribution_margin / 100000),
        },
      ]
    : [];

  return (
    <div className="space-y-8 animate-fadeIn">
      {/* Page Header */}
      <div>
        <div className="flex items-center gap-2 mb-1">
          <span className="text-xs font-bold uppercase tracking-widest text-sapphire-400">
            PHASE 09 PRESCRIPTIVE SIMULATOR
          </span>
          <span className="text-slate-600">•</span>
          <span className="text-xs text-slate-400">What-If Controlled Decision Lab</span>
        </div>
        <h1 className="text-3xl font-extrabold tracking-tight text-white flex items-center gap-3">
          <Sliders className="text-sapphire-400" size={32} />
          Executive What-If Scenario Simulator
        </h1>
        <p className="text-sm text-slate-400 mt-1 max-w-3xl">
          Simulate prescriptive interventions across pricing elasticities, promotional caps, delivery surcharges,
          rider capacity incentives, and merchant bottleneck acceleration before capital deployment.
        </p>
      </div>

      {/* SCENARIO SELECTOR TABS */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-3">
        {SCENARIOS.map((sc) => {
          const Icon = sc.icon;
          const isSelected = sc.id === selectedScenarioId;
          return (
            <button
              key={sc.id}
              onClick={() => handleScenarioChange(sc.id)}
              className={`p-4 rounded-xl text-left border transition-all flex flex-col justify-between ${
                isSelected
                  ? 'bg-sapphire-950/40 border-sapphire-500 shadow-md shadow-sapphire-500/10'
                  : 'bg-obsidian-900/80 border-slate-800 hover:border-slate-700 hover:bg-obsidian-800/80'
              }`}
            >
              <div>
                <div className="flex items-center justify-between mb-2">
                  <div
                    className={`p-2 rounded-lg ${
                      isSelected ? 'bg-sapphire-600 text-white' : 'bg-obsidian-950 text-slate-400'
                    }`}
                  >
                    <Icon size={16} />
                  </div>
                  <span className="text-[10px] font-bold uppercase text-slate-500">{sc.category}</span>
                </div>
                <h4 className="text-xs font-bold text-white line-clamp-2 leading-tight">{sc.name}</h4>
              </div>
              <div className="mt-3 pt-2 border-t border-slate-800/60 flex items-center justify-between text-[11px]">
                <span className={isSelected ? 'text-sapphire-400 font-semibold' : 'text-slate-500'}>
                  {isSelected ? 'Active Model' : 'Select'}
                </span>
                <ArrowRight size={12} className={isSelected ? 'text-sapphire-400' : 'text-slate-600'} />
              </div>
            </button>
          );
        })}
      </div>

      {/* PROJECTION DISCLAIMER BANNER */}
      {simResult && simResult.is_simulation_projection && (
        <div className="p-3.5 rounded-xl bg-amber-500/10 border border-amber-500/30 flex items-start gap-3 text-xs text-amber-200">
          <AlertTriangle size={18} className="text-amber-400 shrink-0 mt-0.5" />
          <div>
            <span className="font-bold uppercase tracking-wider text-amber-300">
              SIMULATION PROJECTION DISCLAIMER:
            </span>{' '}
            {simResult.disclaimer}
          </div>
        </div>
      )}

      {/* MAIN SIMULATION WORKSPACE */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        {/* LEFT COLUMN: INTERACTIVE CONTROLS */}
        <div className="glass-card p-6 rounded-xl border border-slate-800 space-y-6">
          <div>
            <span className="text-xs font-bold uppercase tracking-widest text-sapphire-400">
              Model Parameters
            </span>
            <h3 className="text-base font-bold text-white mt-1">{activeScenario.name}</h3>
            <p className="text-xs text-slate-400 mt-1">{activeScenario.description}</p>
          </div>

          <div className="space-y-5 pt-3 border-t border-slate-800">
            {activeScenario.controls.map((ctrl) => {
              const currentVal = paramOverrides[ctrl.key] ?? ctrl.min;
              return (
                <div key={ctrl.key} className="space-y-1.5">
                  <div className="flex justify-between items-center text-xs">
                    <span className="font-semibold text-slate-200">{ctrl.label}</span>
                    <span className="font-mono font-bold text-sapphire-400 px-2 py-0.5 rounded bg-obsidian-950 border border-slate-800">
                      {currentVal > 0 && ctrl.key !== 'fee_delta_rupees' && ctrl.key !== 'cost_incentive_pool' && ctrl.key !== 'retention_budget'
                        ? `+${currentVal}`
                        : currentVal}
                      {ctrl.unit}
                    </span>
                  </div>
                  <input
                    type="range"
                    min={ctrl.min}
                    max={ctrl.max}
                    step={ctrl.step}
                    value={currentVal}
                    onChange={(e) => handleParamChange(ctrl.key, parseFloat(e.target.value))}
                    className="w-full accent-sapphire-500 bg-obsidian-950 cursor-pointer h-1.5 rounded-lg"
                  />
                  <p className="text-[11px] text-slate-500">{ctrl.desc}</p>
                </div>
              );
            })}
          </div>

          <div className="pt-4 border-t border-slate-800 flex items-center justify-between">
            <button
              onClick={() => setParamOverrides({ ...activeScenario.defaultOverrides })}
              className="text-xs text-slate-400 hover:text-white flex items-center gap-1 transition-colors"
            >
              <RefreshCw size={12} /> Reset Defaults
            </button>
            <button
              onClick={runSimulation}
              disabled={loading}
              className="px-4 py-2 rounded-lg bg-sapphire-600 hover:bg-sapphire-500 text-white text-xs font-semibold flex items-center gap-1.5 shadow-md shadow-sapphire-500/20 transition-all"
            >
              {loading ? (
                <>
                  <RefreshCw size={13} className="animate-spin" /> Simulating...
                </>
              ) : (
                <>
                  <Sparkles size={13} /> Re-run Projection
                </>
              )}
            </button>
          </div>
        </div>

        {/* RIGHT COLUMN: PROJECTED OUTCOMES & COMPARISON (2 SPANS) */}
        <div className="lg:col-span-2 space-y-6">
          {error ? (
            <ApiErrorState
              title="Simulation Engine Error"
              error={error}
              onRetry={runSimulation}
            />
          ) : !simResult ? (
            <div className="flex items-center justify-center h-80 glass-card rounded-xl border border-slate-800">
              <RefreshCw size={24} className="animate-spin text-sapphire-500" />
            </div>
          ) : (
            <>
              {/* PROJECTED VARIANCE CARDS */}
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                <div className="glass-card p-4 rounded-xl border border-slate-800 bg-obsidian-900/80">
                  <span className="text-[10px] font-bold uppercase tracking-wider text-slate-400">
                    Net Margin Delta
                  </span>
                  <div className="mt-1 flex items-baseline gap-1">
                    <span
                      className={`text-xl font-black ${
                        simResult.variance_deltas.margin_delta_rupees >= 0
                          ? 'text-green-600'
                          : 'text-red-600'
                      }`}
                    >
                      {simResult.variance_deltas.margin_delta_rupees >= 0 ? '+' : ''}
                      {formatCurrency(simResult.variance_deltas.margin_delta_rupees)}
                    </span>
                  </div>
                  <span className="text-[10px] text-slate-500 mt-1 block">
                    {simResult.variance_deltas.margin_delta_percentage >= 0 ? '+' : ''}
                    {simResult.variance_deltas.margin_delta_percentage.toFixed(2)}% margin shift
                  </span>
                </div>

                <div className="glass-card p-4 rounded-xl border border-slate-800 bg-obsidian-900/80">
                  <span className="text-[10px] font-bold uppercase tracking-wider text-slate-400">
                    Projected Delivered Orders
                  </span>
                  <div className="mt-1 flex items-baseline gap-1">
                    <span className="text-xl font-black text-white">
                      {formatNumber(simResult.projected_outcomes.projected_delivered_orders)}
                    </span>
                  </div>
                  <span
                    className={`text-[10px] mt-1 block font-mono ${
                      simResult.variance_deltas.orders_delta >= 0 ? 'text-green-600' : 'text-amber-500'
                    }`}
                  >
                    {simResult.variance_deltas.orders_delta >= 0 ? '+' : ''}
                    {formatNumber(simResult.variance_deltas.orders_delta)} vs baseline
                  </span>
                </div>

                <div className="glass-card p-4 rounded-xl border border-slate-800 bg-obsidian-900/80">
                  <span className="text-[10px] font-bold uppercase tracking-wider text-slate-400">
                    Projected Food GMV
                  </span>
                  <div className="mt-1 flex items-baseline gap-1">
                    <span className="text-xl font-black text-cyan-400">
                      {formatCurrency(simResult.projected_outcomes.projected_gross_gmv)}
                    </span>
                  </div>
                  <span className="text-[10px] text-slate-500 mt-1 block font-mono">
                    {simResult.variance_deltas.gmv_delta >= 0 ? '+' : ''}
                    {formatCurrency(simResult.variance_deltas.gmv_delta)} delta
                  </span>
                </div>

                <div className="glass-card p-4 rounded-xl border border-slate-800 bg-obsidian-900/80">
                  <span className="text-[10px] font-bold uppercase tracking-wider text-slate-400">
                    SLA Breaches Prevented
                  </span>
                  <div className="mt-1 flex items-baseline gap-1">
                    <span className="text-xl font-black text-amber-300">
                      {formatNumber(simResult.variance_deltas.sla_breaches_prevented)}
                    </span>
                  </div>
                  <span className="text-[10px] text-slate-500 mt-1 block">
                    Rate: {simResult.projected_outcomes.projected_sla_breach_rate_pct.toFixed(1)}% (was{' '}
                    {simResult.baseline.sla_breach_rate_pct.toFixed(1)}%)
                  </span>
                </div>
              </div>

              {/* SIDE-BY-SIDE BASELINE VS PROJECTED METRICS TABLE */}
              <div className="glass-card p-6 rounded-xl border border-slate-800 space-y-4">
                <h4 className="text-sm font-bold text-white flex items-center gap-2">
                  <Activity className="text-sapphire-400" size={16} />
                  Audited Baseline vs. Simulated Projection
                </h4>

                <div className="overflow-x-auto">
                  <table className="w-full text-left text-xs">
                    <thead>
                      <tr className="border-b border-slate-800 text-slate-400 font-semibold uppercase text-[10px]">
                        <th className="pb-2">Metric</th>
                        <th className="pb-2 text-right">Audited Baseline</th>
                        <th className="pb-2 text-right">Simulated Projection</th>
                        <th className="pb-2 text-right">Variance Delta</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-slate-800/60 font-mono">
                      <tr>
                        <td className="py-2.5 font-sans text-slate-300">Delivered Orders</td>
                        <td className="py-2.5 text-right text-slate-400">
                          {formatNumber(simResult.baseline.delivered_orders)}
                        </td>
                        <td className="py-2.5 text-right font-bold text-white">
                          {formatNumber(simResult.projected_outcomes.projected_delivered_orders)}
                        </td>
                        <td
                          className={`py-2.5 text-right font-bold ${
                            simResult.variance_deltas.orders_delta >= 0 ? 'text-green-600' : 'text-amber-500'
                          }`}
                        >
                          {simResult.variance_deltas.orders_delta >= 0 ? '+' : ''}
                          {formatNumber(simResult.variance_deltas.orders_delta)}
                        </td>
                      </tr>
                      <tr>
                        <td className="py-2.5 font-sans text-slate-700">Gross Food GMV</td>
                        <td className="py-2.5 text-right text-slate-500">
                          {formatCurrency(simResult.baseline.realized_gross_gmv)}
                        </td>
                        <td className="py-2.5 text-right font-bold text-slate-800">
                          {formatCurrency(simResult.projected_outcomes.projected_gross_gmv)}
                        </td>
                        <td
                          className={`py-2.5 text-right font-bold ${
                            simResult.variance_deltas.gmv_delta >= 0 ? 'text-green-600' : 'text-amber-500'
                          }`}
                        >
                          {simResult.variance_deltas.gmv_delta >= 0 ? '+' : ''}
                          {formatCurrency(simResult.variance_deltas.gmv_delta)}
                        </td>
                      </tr>
                      <tr>
                        <td className="py-2.5 font-sans text-slate-700">Net Platform Revenue</td>
                        <td className="py-2.5 text-right text-slate-500">
                          {formatCurrency(simResult.baseline.realized_net_revenue)}
                        </td>
                        <td className="py-2.5 text-right font-bold text-slate-800">
                          {formatCurrency(simResult.projected_outcomes.projected_net_revenue)}
                        </td>
                        <td
                          className={`py-2.5 text-right font-bold ${
                            simResult.variance_deltas.net_revenue_delta >= 0 ? 'text-green-600' : 'text-amber-500'
                          }`}
                        >
                          {simResult.variance_deltas.net_revenue_delta >= 0 ? '+' : ''}
                          {formatCurrency(simResult.variance_deltas.net_revenue_delta)}
                        </td>
                      </tr>
                      <tr>
                        <td className="py-2.5 font-sans text-slate-700">Net Contribution Margin</td>
                        <td className="py-2.5 text-right text-slate-500">
                          {formatCurrency(simResult.baseline.net_contribution_margin)} (
                          {simResult.baseline.margin_percentage}%)
                        </td>
                        <td className="py-2.5 text-right font-bold text-blue-600">
                          {formatCurrency(simResult.projected_outcomes.projected_contribution_margin)} (
                          {simResult.projected_outcomes.projected_margin_percentage}%)
                        </td>
                        <td
                          className={`py-2.5 text-right font-bold ${
                            simResult.variance_deltas.margin_delta_rupees >= 0
                              ? 'text-green-600'
                              : 'text-red-600'
                          }`}
                        >
                          {simResult.variance_deltas.margin_delta_rupees >= 0 ? '+' : ''}
                          {formatCurrency(simResult.variance_deltas.margin_delta_rupees)}
                        </td>
                      </tr>
                    </tbody>
                  </table>
                </div>
              </div>

              {/* COMPARISON CHART */}
              <div className="glass-card p-6 rounded-xl border border-slate-200 bg-white">
                <h4 className="text-sm font-bold text-slate-800 mb-1">Financial Impact Comparison (Lakhs INR)</h4>
                <p className="text-xs text-slate-500 mb-4">
                  Visual comparison between audited historical baseline and simulated scenario outcomes.
                </p>

                <div className="h-64 w-full">
                  <ResponsiveContainer width="100%" height="100%">
                    <BarChart data={chartData}>
                      <CartesianGrid strokeDasharray="3 3" stroke="#E2E8F0" />
                      <XAxis dataKey="metric" stroke="#64748b" tick={{ fontSize: 11 }} />
                      <YAxis
                        stroke="#64748b"
                        tick={{ fontSize: 11 }}
                        tickFormatter={(v) => `₹${v}L`}
                      />
                      <Tooltip
                        contentStyle={{ backgroundColor: '#FFFFFF', borderColor: '#E2E8F0', color: '#1E293B', borderRadius: '8px', boxShadow: '0 4px 6px -1px rgba(0,0,0,0.1)' }}
                        formatter={(val: any) => [`₹${val} Lakhs`, 'Amount']}
                      />
                      <Legend wrapperStyle={{ fontSize: '11px', paddingTop: '10px', color: '#475569' }} />
                      <Bar dataKey="Baseline" fill="#94A3B8" radius={[4, 4, 0, 0]} />
                      <Bar dataKey="Simulated" fill="#2563EB" radius={[4, 4, 0, 0]} />
                    </BarChart>
                  </ResponsiveContainer>
                </div>
              </div>

              {/* AUDITED ASSUMPTIONS LIST */}
              <div className="glass-card p-5 rounded-xl border border-slate-200 bg-white space-y-2">
                <span className="text-[10px] font-bold uppercase tracking-wider text-slate-500 flex items-center gap-1.5">
                  <ShieldCheck size={13} className="text-green-600" /> Grounded Scenario Assumptions
                </span>
                <ul className="space-y-1.5 pl-1 text-xs">
                  {(simResult.scenario_assumptions || []).map((ass, i) => (
                    <li key={i} className="text-slate-300 flex items-start gap-2">
                      <span className="text-sapphire-400 font-bold">•</span>
                      <span>{ass}</span>
                    </li>
                  ))}
                </ul>
              </div>
            </>
          )}
        </div>
      </div>
    </div>
  );
};
