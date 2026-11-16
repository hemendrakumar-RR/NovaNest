import React, { useState } from 'react';
import {
  Activity,
  CheckCircle2,
  Clock,
  Cpu,
  DollarSign,
  Users,
  Truck,
  UtensilsCrossed,
  BrainCircuit,
  ChevronDown,
  ChevronUp,
  ShieldCheck,
  AlertTriangle,
  RotateCw,
} from 'lucide-react';
import { TelemetryEvent, InvokedAgentSummary } from '../services/api';

interface AgentTelemetryCardProps {
  events?: TelemetryEvent[];
  agentsInvoked?: InvokedAgentSummary[];
  isLive?: boolean;
  totalElapsedMs?: number;
  verificationOutcome?: string;
  isVerified?: boolean;
  activeStage?: number;
}

interface AgentState {
  id: string;
  name: string;
  domain: string;
  icon: React.ElementType;
  stage: number;
  status: 'idle' | 'running' | 'success' | 'failed' | 'timeout' | 'blocked';
  elapsedMs?: number;
  message?: string;
}

const DOMAIN_AGENTS_CONFIG: Array<{
  id: string;
  name: string;
  domain: string;
  icon: React.ElementType;
  defaultStage: number;
}> = [
  { id: 'financial_agent', name: 'Financial Agent', domain: 'FINANCE', icon: DollarSign, defaultStage: 1 },
  { id: 'customer_agent', name: 'Customer Agent', domain: 'CUSTOMER', icon: Users, defaultStage: 1 },
  { id: 'operations_agent', name: 'Operations Agent', domain: 'OPERATIONS', icon: Truck, defaultStage: 1 },
  { id: 'restaurant_agent', name: 'Restaurant Agent', domain: 'RESTAURANT', icon: UtensilsCrossed, defaultStage: 1 },
  { id: 'decision_agent', name: 'Decision Agent', domain: 'DECISION', icon: BrainCircuit, defaultStage: 2 },
];

export const AgentTelemetryCard: React.FC<AgentTelemetryCardProps> = ({
  events = [],
  agentsInvoked = [],
  isLive = false,
  totalElapsedMs,
  verificationOutcome,
  isVerified,
  activeStage,
}) => {
  const [isExpanded, setIsExpanded] = useState<boolean>(true);

  // Derive agent states from live streaming events or completed agentsInvoked summary
  const agentStates: Record<string, AgentState> = {};
  for (const cfg of DOMAIN_AGENTS_CONFIG) {
    agentStates[cfg.id] = {
      id: cfg.id,
      name: cfg.name,
      domain: cfg.domain,
      icon: cfg.icon,
      stage: cfg.defaultStage,
      status: 'idle',
      message: 'Pending dispatch',
    };
  }

  // 1. Reconcile with historical summary if available
  if (agentsInvoked && agentsInvoked.length > 0) {
    for (const inv of agentsInvoked) {
      if (agentStates[inv.agent_id]) {
        agentStates[inv.agent_id].stage = inv.stage;
        agentStates[inv.agent_id].elapsedMs = inv.elapsed_ms;
        const normStatus = (inv.status || '').toLowerCase();
        if (normStatus === 'success' || normStatus === 'partial') {
          agentStates[inv.agent_id].status = 'success';
          agentStates[inv.agent_id].message = `Completed in ${Math.round(inv.elapsed_ms)}ms`;
        } else if (normStatus === 'timeout') {
          agentStates[inv.agent_id].status = 'timeout';
          agentStates[inv.agent_id].message = 'Execution timed out';
        } else if (normStatus === 'blocked') {
          agentStates[inv.agent_id].status = 'blocked';
          agentStates[inv.agent_id].message = 'Blocked by guardrail';
        } else {
          agentStates[inv.agent_id].status = 'failed';
          agentStates[inv.agent_id].message = 'Agent execution error';
        }
      }
    }
  }

  // 2. Overlay live events (latest event takes precedence)
  for (const evt of events) {
    const aid = evt.agent_name;
    if (aid && agentStates[aid]) {
      if (evt.stage) {
        agentStates[aid].stage = evt.stage;
      }
      if (evt.duration_ms !== undefined && evt.duration_ms !== null) {
        agentStates[aid].elapsedMs = evt.duration_ms;
      }

      if (evt.event_type === 'agent_started') {
        agentStates[aid].status = 'running';
        agentStates[aid].message = evt.message || 'Analyzing domain data...';
      } else if (evt.event_type === 'agent_completed') {
        agentStates[aid].status = 'success';
        agentStates[aid].message = evt.message || `Done in ${Math.round(evt.duration_ms || 0)}ms`;
      } else if (evt.event_type === 'agent_failed') {
        const normStatus = (evt.status || '').toLowerCase();
        agentStates[aid].status = normStatus === 'timeout' ? 'timeout' : 'failed';
        agentStates[aid].message = evt.message || 'Execution error';
      }
    }
  }

  // Calculate live progression
  const activeCount = Object.values(agentStates).filter((s) => s.status === 'running').length;
  const completedCount = Object.values(agentStates).filter((s) => s.status === 'success').length;
  const totalAgents = DOMAIN_AGENTS_CONFIG.length;
  const progressPercent = Math.min(100, Math.round(((completedCount + (activeCount > 0 ? 0.5 : 0)) / totalAgents) * 100));

  return (
    <div className="w-full my-3 border border-slate-700/60 rounded-xl bg-slate-900/80 backdrop-blur-md shadow-lg overflow-hidden transition-all duration-200">
      {/* Header bar */}
      <div
        onClick={() => setIsExpanded(!isExpanded)}
        className="flex items-center justify-between px-3.5 py-2.5 bg-slate-800/60 hover:bg-slate-800/80 cursor-pointer select-none transition-colors"
      >
        <div className="flex items-center space-x-2.5">
          <div className="relative flex items-center justify-center w-6 h-6 rounded-lg bg-indigo-500/10 border border-indigo-500/30 text-indigo-400">
            {isLive ? (
              <RotateCw className="w-3.5 h-3.5 animate-spin text-cyan-400" />
            ) : (
              <Cpu className="w-3.5 h-3.5 text-indigo-400" />
            )}
            {isLive && (
              <span className="absolute -top-0.5 -right-0.5 w-2 h-2 rounded-full bg-cyan-400 animate-ping" />
            )}
          </div>
          <div className="flex items-center space-x-2">
            <span className="text-xs font-semibold tracking-wide text-slate-200">
              Multi-Agent Orchestration Telemetry
            </span>
            {isLive ? (
              <span className="px-1.5 py-0.5 text-[10px] font-medium tracking-wider uppercase rounded-full bg-cyan-500/10 text-cyan-400 border border-cyan-500/30 animate-pulse">
                Live Streaming
              </span>
            ) : (
              <span className="px-1.5 py-0.5 text-[10px] font-medium tracking-wider uppercase rounded-full bg-green-50 text-green-700 border border-green-200">
                Verified
              </span>
            )}
          </div>
        </div>

        <div className="flex items-center space-x-3 text-xs text-slate-400">
          {totalElapsedMs !== undefined && totalElapsedMs > 0 && (
            <div className="flex items-center space-x-1 font-mono text-[11px] text-slate-300">
              <Clock className="w-3 h-3 text-slate-400" />
              <span>{Math.round(totalElapsedMs)}ms</span>
            </div>
          )}

          {verificationOutcome && (
            <div
              className={`flex items-center space-x-1 px-1.5 py-0.5 rounded text-[10px] font-medium uppercase tracking-wider ${
                verificationOutcome === 'verified'
                  ? 'bg-green-50 text-green-700 border border-green-200'
                  : verificationOutcome === 'partial'
                  ? 'bg-amber-50 text-amber-700 border border-amber-200'
                  : 'bg-red-50 text-red-700 border border-red-200'
              }`}
            >
              <ShieldCheck className="w-3 h-3" />
              <span>{verificationOutcome}</span>
            </div>
          )}

          <button
            type="button"
            className="p-1 rounded text-slate-400 hover:text-slate-200 transition-colors"
            aria-label={isExpanded ? 'Collapse telemetry' : 'Expand telemetry'}
          >
            {isExpanded ? <ChevronUp className="w-4 h-4" /> : <ChevronDown className="w-4 h-4" />}
          </button>
        </div>
      </div>

      {/* Progress Bar */}
      <div className="w-full h-1 bg-slate-800">
        <div
          className={`h-full transition-all duration-300 ${
            isLive ? 'bg-gradient-to-r from-blue-500 to-indigo-500' : 'bg-green-600'
          }`}
          style={{ width: `${progressPercent}%` }}
        />
      </div>

      {/* Collapsible Content */}
      {isExpanded && (
        <div className="p-3 space-y-2.5 bg-slate-900/40">
          {/* Agent status grid */}
          <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-5 gap-2">
            {DOMAIN_AGENTS_CONFIG.map((cfg) => {
              const state = agentStates[cfg.id];
              const Icon = cfg.icon;

              let statusBorder = 'border-slate-800/80 bg-slate-900/50 text-slate-400';
              let badgeBg = 'bg-slate-800 text-slate-400';
              let badgeText = 'Idle';

              if (state.status === 'running') {
                statusBorder = 'border-cyan-500/40 bg-cyan-950/20 text-cyan-300 shadow-sm shadow-cyan-950/50';
                badgeBg = 'bg-cyan-500/20 text-cyan-300 border border-cyan-500/40 animate-pulse';
                badgeText = 'Running';
              } else if (state.status === 'success') {
                statusBorder = 'border-green-200 bg-green-50 text-green-700';
                badgeBg = 'bg-green-100 text-green-800 border border-green-300';
                badgeText = state.elapsedMs ? `${Math.round(state.elapsedMs)}ms` : 'Success';
              } else if (state.status === 'failed' || state.status === 'timeout' || state.status === 'blocked') {
                statusBorder = 'border-rose-500/30 bg-rose-950/10 text-rose-300';
                badgeBg = 'bg-rose-500/20 text-rose-300 border border-rose-500/40';
                badgeText = state.status.toUpperCase();
              }

              return (
                <div
                  key={cfg.id}
                  className={`flex flex-col justify-between p-2 rounded-lg border text-xs transition-all ${statusBorder}`}
                >
                  <div className="flex items-center justify-between mb-1.5">
                    <div className="flex items-center space-x-1.5 truncate">
                      <Icon className="w-3.5 h-3.5 shrink-0" />
                      <span className="font-medium text-slate-200 truncate">{cfg.name}</span>
                    </div>
                    <span className="text-[9px] uppercase px-1 py-0.5 rounded font-mono bg-slate-800/70 text-slate-400">
                      S{state.stage}
                    </span>
                  </div>

                  <div className="flex items-center justify-between mt-1">
                    <span className={`px-1.5 py-0.5 text-[9px] font-mono rounded tracking-tight ${badgeBg}`}>
                      {badgeText}
                    </span>
                    {state.status === 'success' && (
                      <CheckCircle2 className="w-3.5 h-3.5 text-green-600 shrink-0" />
                    )}
                    {state.status === 'running' && (
                      <RotateCw className="w-3 h-3 text-cyan-400 animate-spin shrink-0" />
                    )}
                    {(state.status === 'failed' || state.status === 'timeout' || state.status === 'blocked') && (
                      <AlertTriangle className="w-3.5 h-3.5 text-rose-400 shrink-0" />
                    )}
                  </div>
                </div>
              );
            })}
          </div>

          {/* Real-time event log ticker */}
          {events.length > 0 && (
            <div className="p-2 rounded-lg bg-slate-950/60 border border-slate-800 font-mono text-[11px] text-slate-300 space-y-1 max-h-24 overflow-y-auto">
              {events.slice(-3).map((evt, idx) => (
                <div key={idx} className="flex items-center space-x-2 truncate">
                  <span className="text-cyan-400 font-semibold uppercase text-[10px]">
                    [{evt.event_type.replace(/_/g, ' ')}]
                  </span>
                  <span className="text-slate-400 truncate">{evt.message}</span>
                </div>
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  );
};
export default AgentTelemetryCard;

