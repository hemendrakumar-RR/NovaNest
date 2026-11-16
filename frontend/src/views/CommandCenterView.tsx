import React, { useEffect, useState } from 'react';
import {
  Cpu,
  Activity,
  Layers,
  ArrowRight,
  AlertTriangle,
  Users,
  Store,
  Truck,
  IndianRupee,
  Share2,
  ShieldCheck,
  CheckCircle2,
  Sparkles
} from 'lucide-react';
import { SectionHeader } from '../components/SectionHeader';
import { ApiErrorState, EmptyStateCard } from '../components/ApiStatePanel';
import { api, DigitalTwinState } from '../services/api';
import { formatCurrency, formatNumber, formatTimeToIST } from '../utils/formatters';

const optNum = (v: number | null | undefined) => (v == null ? 'Unavailable' : formatNumber(v));
const optCurr = (v: number | null | undefined) => (v == null ? 'Unavailable' : formatCurrency(v));
const optSuffix = (v: number | null | undefined, suffix: string) => (v == null ? 'Unavailable' : `${v}${suffix}`);

export const CommandCenterView: React.FC = () => {
  const [twin, setTwin] = useState<DigitalTwinState | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<unknown>(null);

  const loadTwinState = () => {
    setLoading(true);
    setError(null);
    api
      .getDigitalTwinState()
      .then((res) => setTwin(res))
      .catch((err) => {
        console.error('Digital Twin state error:', err);
        setError(err);
      })
      .finally(() => setLoading(false));
  };

  useEffect(() => {
    loadTwinState();
  }, []);

  if (loading) {
    return (
      <div className="flex items-center justify-center h-96">
        <div className="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-sapphire-500" />
      </div>
    );
  }

  if (error || !twin) {
    return (
      <ApiErrorState
        title="Digital Twin Command Center Unavailable"
        error={error || 'Empty Digital Twin telemetry payload received.'}
        onRetry={loadTwinState}
      />
    );
  }

  const { vitality_index, pillars, systemic_alerts = [], impact_ripple_chains = [] } = twin;
  const syncedPillars = [
    pillars.customer_twin?.active_base != null || pillars.customer_twin?.engagement_index != null,
    pillars.restaurant_twin?.active_merchants != null || pillars.restaurant_twin?.network_health != null,
    pillars.operations_twin?.active_fleet != null || pillars.operations_twin?.avg_eta_mins != null,
    pillars.financial_twin?.gross_volume != null || pillars.financial_twin?.net_platform_revenue != null,
  ].filter(Boolean).length;
  const systemUnavailable = twin.status === 'unavailable' || syncedPillars === 0;

  return (
    <div className="space-y-8 animate-fadeIn">
      {/* Title */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-slate-800/80 pb-4">
        <div>
          <div className="flex items-center gap-2 mb-1">
            <span className="text-xs font-bold uppercase tracking-widest text-sapphire-400">UNIFIED DIGITAL TWIN</span>
            <span className="text-slate-600">•</span>
            <span className="text-xs text-slate-400">Multi-Agent Systemic Representation</span>
          </div>
          <h1 className="text-3xl font-extrabold tracking-tight text-white">NovaNest Command Center & Digital Twin</h1>
          <p className="text-sm text-slate-400 mt-1">
            Unified analytical Digital Twin orchestrating cross-system state representations, downstream dependency ripple chains, and systemic anomaly alerts.
          </p>
        </div>
        <div className="flex items-center gap-2 text-xs text-slate-400 bg-obsidian-900 border border-slate-800 px-3 py-1.5 rounded-lg font-mono w-fit shrink-0">
          <span className="w-2 h-2 rounded-full bg-cyan-400 animate-pulse" />
          <span>Twin Synchronized: {formatTimeToIST(new Date())}</span>
        </div>
      </div>

      {/* TOP SYSTEMIC VITALITY HERO CARD */}
      <div className="glass-card p-6 border-l-4 border-l-sapphire-500 bg-gradient-to-r from-obsidian-900 via-obsidian-850 to-obsidian-900 flex flex-col md:flex-row items-center justify-between gap-6">
        <div>
          <div className="flex items-center gap-2 mb-2 text-sapphire-400 font-semibold text-xs uppercase tracking-wider">
            <Cpu size={18} /> Platform Systemic Vitality Index
          </div>
          <h2 className="text-4xl font-extrabold text-white tracking-tight num-tabular">
            {vitality_index != null ? (
              <>
                {vitality_index} <span className="text-xl font-normal text-slate-500">/ 100</span>
              </>
            ) : (
              <span className="text-2xl text-amber-400">Unavailable</span>
            )}
          </h2>
          <p className="text-xs text-slate-400 mt-1 max-w-xl">
            Autonomous multi-domain index computed across merchant reliability, fleet on-time fulfillment, customer lifetime retention, and gross platform margins.
          </p>
        </div>

        <div className="flex items-center gap-6 shrink-0">
          <div className="text-center p-3 rounded-xl bg-obsidian-950/80 border border-slate-800">
            <span className="text-[10px] uppercase font-bold text-slate-400 tracking-wider">System State</span>
            <p
              className={`text-sm font-bold mt-1 flex items-center gap-1 justify-center ${
                systemUnavailable
                  ? 'text-crimson-400'
                  : syncedPillars < 4 || (vitality_index != null && vitality_index < 75)
                    ? 'text-amber-400'
                    : 'text-green-600'
              }`}
            >
              <CheckCircle2 size={14} />{' '}
              {systemUnavailable ? 'Unavailable' : syncedPillars < 4 ? 'Partial Sync' : 'Nominal'}
            </p>
          </div>
          <div className="text-center p-3 rounded-xl bg-obsidian-950/80 border border-slate-800">
            <span className="text-[10px] uppercase font-bold text-slate-400 tracking-wider">Active Pillars</span>
            <p className="text-sm font-bold text-sapphire-400 mt-1">{syncedPillars} of 4 Synced</p>
          </div>
        </div>
      </div>

      {/* 4-PILLAR DIGITAL TWIN MATRIX */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        {/* Customer Twin Pillar */}
        <div className="glass-card p-5 border-t-4 border-t-cyan-500 flex flex-col justify-between">
          <div>
            <div className="flex items-center gap-2 mb-3">
              <div className="p-2 rounded-lg bg-cyan-500/10 text-cyan-400">
                <Users size={16} />
              </div>
              <div>
                <h3 className="text-sm font-bold text-white">Customer Twin</h3>
                <p className="text-[10px] text-slate-400">Patron Lifecycle Model</p>
              </div>
            </div>

            <div className="space-y-2.5 mt-3 text-xs">
              <div className="flex justify-between py-1 border-b border-slate-800/60">
                <span className="text-slate-400">Active Patrons:</span>
                <span className="font-semibold text-white num-tabular">{optNum(pillars.customer_twin.active_base)}</span>
              </div>
              <div className="flex justify-between py-1 border-b border-slate-800/60">
                <span className="text-slate-400">At-Risk Accounts:</span>
                <span className="font-semibold text-crimson-400 num-tabular">{optNum(pillars.customer_twin.churn_exposure)}</span>
              </div>
              <div className="flex justify-between py-1 border-b border-slate-800/60">
                <span className="text-slate-400">Total CLV Capital:</span>
                <span className="font-semibold text-green-600 num-tabular">{optCurr(pillars.customer_twin.clv_capital)}</span>
              </div>
              <div className="flex justify-between py-1">
                <span className="text-slate-400">Engagement Index:</span>
                <span className="font-semibold text-cyan-400 num-tabular">{optSuffix(pillars.customer_twin.engagement_index, '%')}</span>
              </div>
            </div>
          </div>
        </div>

        {/* Restaurant Twin Pillar */}
        <div className="glass-card p-5 border-t-4 border-t-blue-600 flex flex-col justify-between">
          <div>
            <div className="flex items-center gap-2 mb-3">
              <div className="p-2 rounded-lg bg-blue-50 text-blue-600">
                <Store size={16} />
              </div>
              <div>
                <h3 className="text-sm font-bold text-white">Restaurant Twin</h3>
                <p className="text-[10px] text-slate-400">Merchant Network Model</p>
              </div>
            </div>

            <div className="space-y-2.5 mt-3 text-xs">
              <div className="flex justify-between py-1 border-b border-slate-800/60">
                <span className="text-slate-400">Active Merchants:</span>
                <span className="font-semibold text-white num-tabular">{optNum(pillars.restaurant_twin.active_merchants)}</span>
              </div>
              <div className="flex justify-between py-1 border-b border-slate-800/60">
                <span className="text-slate-400">Critical Partners:</span>
                <span className="font-semibold text-crimson-400 num-tabular">{optNum(pillars.restaurant_twin.critical_partners)}</span>
              </div>
              <div className="flex justify-between py-1 border-b border-slate-800/60">
                <span className="text-slate-400">Network Health:</span>
                <span className="font-semibold text-green-600 num-tabular">{optSuffix(pillars.restaurant_twin.network_health, '/100')}</span>
              </div>
              <div className="flex justify-between py-1">
                <span className="text-slate-400">Cancellation Rate:</span>
                <span className="font-semibold text-amber-400 num-tabular">{optSuffix(pillars.restaurant_twin.cancellation_rate, '%')}</span>
              </div>
            </div>
          </div>
        </div>

        {/* Operations Twin Pillar */}
        <div className="glass-card p-5 border-t-4 border-t-sapphire-500 flex flex-col justify-between">
          <div>
            <div className="flex items-center gap-2 mb-3">
              <div className="p-2 rounded-lg bg-sapphire-500/10 text-sapphire-400">
                <Truck size={16} />
              </div>
              <div>
                <h3 className="text-sm font-bold text-white">Operations Twin</h3>
                <p className="text-[10px] text-slate-400">Logistics & Fleet Model</p>
              </div>
            </div>

            <div className="space-y-2.5 mt-3 text-xs">
              <div className="flex justify-between py-1 border-b border-slate-800/60">
                <span className="text-slate-400">Active Fleet:</span>
                <span className="font-semibold text-white num-tabular">{optNum(pillars.operations_twin.active_fleet)}</span>
              </div>
              <div className="flex justify-between py-1 border-b border-slate-800/60">
                <span className="text-slate-400">Mean Transit ETA:</span>
                <span className="font-semibold text-blue-600 num-tabular">{optSuffix(pillars.operations_twin.avg_eta_mins, 'm')}</span>
              </div>
              <div className="flex justify-between py-1 border-b border-slate-800/60">
                <span className="text-slate-400">Fulfillment SLA:</span>
                <span className="font-semibold text-sapphire-400 num-tabular">{optSuffix(pillars.operations_twin.dispatch_fulfillment, '%')}</span>
              </div>
              <div className="flex justify-between py-1">
                <span className="text-slate-400">Active Bottlenecks:</span>
                <span className="font-semibold text-amber-400 num-tabular">{optNum(pillars.operations_twin.bottlenecks)}</span>
              </div>
            </div>
          </div>
        </div>

        {/* Financial Twin Pillar */}
        <div className="glass-card p-5 border-t-4 border-t-purple-500 flex flex-col justify-between">
          <div>
            <div className="flex items-center gap-2 mb-3">
              <div className="p-2 rounded-lg bg-purple-500/10 text-purple-400">
                <IndianRupee size={16} />
              </div>
              <div>
                <h3 className="text-sm font-bold text-white">Financial Twin</h3>
                <p className="text-[10px] text-slate-400">P&L Economics Model</p>
              </div>
            </div>

            <div className="space-y-2.5 mt-3 text-xs">
              <div className="flex justify-between py-1 border-b border-slate-800/60">
                <span className="text-slate-400">Gross Volume (GMV):</span>
                <span className="font-semibold text-white num-tabular">{optCurr(pillars.financial_twin.gross_volume)}</span>
              </div>
              <div className="flex justify-between py-1 border-b border-slate-800/60">
                <span className="text-slate-400">Net Platform Yield:</span>
                <span className="font-semibold text-green-600 num-tabular">{optCurr(pillars.financial_twin.net_platform_revenue)}</span>
              </div>
              <div className="flex justify-between py-1 border-b border-slate-800/60">
                <span className="text-slate-400">Take Rate Margin:</span>
                <span className="font-semibold text-purple-400 num-tabular">{optSuffix(pillars.financial_twin.margin_rate, '%')}</span>
              </div>
              <div className="flex justify-between py-1">
                <span className="text-slate-400">Leakage Exposure:</span>
                <span className="font-semibold text-crimson-400 num-tabular">{optCurr(pillars.financial_twin.leakage_exposure)}</span>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* CROSS-DOMAIN DEPENDENCY RIPPLE CHAINS */}
      <div className="glass-card p-6">
        <SectionHeader
          title="Cross-Domain Dependency Impact Ripple Chains"
          subtitle="Real-time causal graph tracing how upstream shocks propagate across customer, restaurant, and financial layers"
          tag="IMPACT GRAPH"
        />

        <div className="space-y-4 pt-2">
          {!impact_ripple_chains || impact_ripple_chains.length === 0 ? (
            <EmptyStateCard
              title="No Impact Ripple Chains Active"
              description="Cross-domain shock dependency chains are unavailable or no active propagation shocks exist."
            />
          ) : (
            impact_ripple_chains.map((chain: any, cIdx: number) => {
              const steps: string[] = Array.isArray(chain?.ripple_steps)
                ? chain.ripple_steps
                : Array.isArray(chain?.chain)
                  ? chain.chain
                  : [];
              return (
                <div
                  key={cIdx}
                  className="p-4 rounded-xl bg-obsidian-950/80 border border-slate-800 flex flex-col md:flex-row items-center gap-3 text-xs"
                >
                  <div className="w-full md:w-48 shrink-0">
                    <span className="text-[10px] font-bold text-sapphire-400 uppercase tracking-wider">Root Shock</span>
                    <p className="font-bold text-white mt-0.5">{chain?.trigger || chain?.cause || 'Upstream Event'}</p>
                  </div>

                  <div className="hidden md:flex text-slate-600">
                    <ArrowRight size={16} />
                  </div>

                  <div className="flex-1 grid grid-cols-1 sm:grid-cols-3 gap-2 w-full">
                    {steps.length === 0 ? (
                      <div className="col-span-3 p-2.5 rounded-lg bg-obsidian-900 border border-slate-800/80 text-slate-400">
                        Telemetry ripple chain unavailable
                      </div>
                    ) : (
                      steps.slice(0, 3).map((step: string, sIdx: number) => (
                        <div
                          key={sIdx}
                          className="p-2.5 rounded-lg bg-obsidian-900 border border-slate-800/80 flex items-center gap-2"
                        >
                          <span className="w-5 h-5 rounded-full bg-sapphire-500/20 text-sapphire-400 font-bold flex items-center justify-center shrink-0 text-[10px]">
                            {sIdx + 1}
                          </span>
                          <span className="text-slate-300 truncate" title={step}>{step}</span>
                        </div>
                      ))
                    )}
                  </div>

                  <div className="hidden md:flex text-slate-600">
                    <ArrowRight size={16} />
                  </div>

                  <div className="w-full md:w-44 shrink-0 text-right">
                    <span className="text-[10px] font-bold text-crimson-400 uppercase tracking-wider">Bottomline Impact</span>
                    <p className="font-bold text-white mt-0.5">
                      {chain?.impact || (steps.length > 0 ? steps[steps.length - 1] : 'Unquantified')}
                    </p>
                  </div>
                </div>
              );
            })
          )}
        </div>
      </div>

      {/* SYSTEMIC ANOMALY ALERTS FEED */}
      <div className="glass-card p-6">
        <SectionHeader
          title="Systemic Anomaly Alert Center"
          subtitle="Automated cross-system alerts triggered by composite threshold violations"
          tag="SYSTEMIC ALERTS"
        />

        <div className="space-y-3">
          {!systemic_alerts || systemic_alerts.length === 0 ? (
            <EmptyStateCard
              title="No Systemic Anomaly Alerts Active"
              description="All monitored cross-system thresholds are within nominal operational bounds."
            />
          ) : (
            systemic_alerts.map((alert: any, aIdx: number) => (
              <div
                key={aIdx}
                className="p-3.5 rounded-lg bg-obsidian-900 border border-slate-800 hover:border-slate-700 flex flex-col sm:flex-row sm:items-center justify-between gap-3 text-xs"
              >
                <div>
                  <div className="flex items-center gap-2">
                    <span className="font-bold text-white">{alert.Category || alert.type || 'Systemic Alert'}</span>
                    <span
                      className={`text-[10px] font-bold px-1.5 py-0.2 rounded uppercase ${
                        alert.Severity === 'Critical' || alert.severity === 'High'
                          ? 'bg-crimson-500/20 text-crimson-400 border border-crimson-500/30'
                          : 'bg-amber-500/20 text-amber-400 border border-amber-500/30'
                      }`}
                    >
                      {alert.Severity || alert.severity || 'Medium'}
                    </span>
                  </div>
                  <p className="text-slate-400 mt-1">
                    Signal:{' '}
                    <span className="text-slate-200 font-medium">
                      {alert.Signal || alert.Metric || alert.metric || 'Threshold Violation'}
                    </span>{' '}
                    • Impact: {alert.Business_Impact || alert.Current_Value || alert.current_value || 'Requires Review'}
                  </p>
                </div>

                <div className="shrink-0 text-left sm:text-right">
                  <span className="text-sapphire-400 font-semibold block text-[11px]">
                    Remediation: {alert.Recommended_Action || alert.action || 'Execute Mitigation Review'}
                  </span>
                </div>
              </div>
            ))
          )}
        </div>
      </div>
    </div>
  );
};
