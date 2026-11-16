import React, { useState } from 'react';
import type { LucideIcon } from 'lucide-react';
import { HelpCircle, TrendingUp, TrendingDown, Minus, Info } from 'lucide-react';
import { ContextualAIPayload } from '../types/contextualAi';
import { ContextualAIButton } from './ContextualAIButton';

export interface KpiCardProps {
  label: string;
  value: string | number;
  subtext?: string;
  delta?: string;
  deltaPositive?: boolean;
  previousValue?: string | number;
  percentageChange?: number | string;
  trendDirection?: 'up' | 'down' | 'neutral';
  calculationTooltip?: string;
  dataFreshness?: string;
  icon?: LucideIcon;
  accent?: 'sapphire' | 'emerald' | 'green' | 'amber' | 'crimson' | 'cyan' | 'orange';
  aiPayload?: ContextualAIPayload;
}

export const KpiCard: React.FC<KpiCardProps> = ({
  label,
  value,
  subtext,
  delta,
  deltaPositive,
  previousValue,
  percentageChange,
  trendDirection,
  calculationTooltip,
  dataFreshness,
  icon: Icon,
  accent = 'sapphire',
  aiPayload
}) => {
  const [showTooltip, setShowTooltip] = useState(false);

  // Border highlight: Royal Blue for sapphire/default, Orange for alerts/amber/orange, Green for emerald, Red for crimson
  const accentBorder: Record<string, string> = {
    sapphire: 'border-l-blue-600',
    cyan: 'border-l-sky-500',
    orange: 'border-l-orange-500',
    amber: 'border-l-amber-500',
    green: 'border-l-green-600',
    emerald: 'border-l-green-600',
    crimson: 'border-l-red-600',
  };

  const iconBg: Record<string, string> = {
    sapphire: 'bg-blue-50 text-blue-600',
    cyan: 'bg-sky-50 text-sky-600',
    orange: 'bg-orange-50 text-orange-600',
    amber: 'bg-amber-50 text-amber-600',
    green: 'bg-green-50 text-green-600',
    emerald: 'bg-green-50 text-green-600',
    crimson: 'bg-red-50 text-red-600',
  };

  const selectedBorder = accentBorder[accent || 'sapphire'] || 'border-l-blue-600';
  const selectedIconBg = iconBg[accent || 'sapphire'] || 'bg-blue-50 text-blue-600';

  // Resolve trend icon & styling
  const resolvedTrend = trendDirection || (deltaPositive === true ? 'up' : deltaPositive === false ? 'down' : 'neutral');
  const isPositive = resolvedTrend === 'up';
  const isNegative = resolvedTrend === 'down';

  return (
    <div className={`bg-white rounded-xl p-5 border border-slate-200 border-l-4 ${selectedBorder} relative overflow-hidden group shadow-sm hover:shadow-md transition-all duration-200`}>
      {/* Top Header Row */}
      <div className="flex items-start justify-between">
        <div className="flex-1 min-w-0 pr-2">
          <div className="flex items-center gap-1.5 mb-1">
            <p className="text-xs font-semibold tracking-wider uppercase text-slate-500 truncate">{label}</p>
            {calculationTooltip && (
              <div className="relative inline-block">
                <button
                  type="button"
                  onClick={() => setShowTooltip(!showTooltip)}
                  onMouseEnter={() => setShowTooltip(true)}
                  onMouseLeave={() => setShowTooltip(false)}
                  className="text-slate-400 hover:text-slate-600 transition-colors p-0.5 rounded focus:outline-none"
                  aria-label={`Calculation formula for ${label}`}
                  title={calculationTooltip}
                >
                  <HelpCircle size={13} />
                </button>
                {showTooltip && (
                  <div className="absolute left-0 bottom-full mb-1.5 z-30 w-64 p-2.5 rounded-lg bg-white border border-slate-200 text-[11px] text-slate-800 shadow-xl animate-fadeIn">
                    <div className="flex items-center gap-1 text-blue-600 font-semibold mb-1">
                      <Info size={12} />
                      <span>Certified Formula</span>
                    </div>
                    <code className="text-slate-700 bg-slate-50 p-1 rounded font-mono text-[10px] break-words block border border-slate-100">{calculationTooltip}</code>
                  </div>
                )}
              </div>
            )}
          </div>
          <h3 className="text-2xl font-bold tracking-tight text-slate-800 num-tabular">{value}</h3>
        </div>

        <div className="flex items-center gap-1.5 shrink-0">
          {aiPayload && (
            <ContextualAIButton
              payload={aiPayload}
              size="xs"
              variant="compact"
              ariaLabel={`Analyze ${label} with NovaNest AI`}
            />
          )}
          {Icon && (
            <div className={`p-2.5 rounded-xl ${selectedIconBg} shadow-xs transition-colors`}>
              <Icon size={18} />
            </div>
          )}
        </div>
      </div>

      {/* Metric Change / Comparison Subtext */}
      <div className="mt-3.5 pt-3 border-t border-slate-100 flex items-center justify-between text-xs">
        <div className="flex items-center gap-2">
          {percentageChange !== undefined && (
            <span
              className={`inline-flex items-center gap-0.5 px-1.5 py-0.5 rounded font-medium text-[11px] num-tabular ${
                isPositive
                  ? 'bg-green-50 text-green-700 border border-green-200'
                  : isNegative
                  ? 'bg-red-50 text-red-700 border border-red-200'
                  : 'bg-slate-100 text-slate-700 border border-slate-200'
              }`}
            >
              {isPositive && <TrendingUp size={11} />}
              {isNegative && <TrendingDown size={11} />}
              {!isPositive && !isNegative && <Minus size={11} />}
              <span>{typeof percentageChange === 'number' ? `${percentageChange > 0 ? '+' : ''}${percentageChange}%` : percentageChange}</span>
            </span>
          )}

          {delta && (
            <span
              className={`font-semibold text-xs num-tabular ${
                deltaPositive === true ? 'text-green-600' : deltaPositive === false ? 'text-red-600' : 'text-slate-500'
              }`}
            >
              {delta}
            </span>
          )}

          {subtext && <span className="text-slate-500 text-[11px] truncate max-w-[130px]">{subtext}</span>}
          {previousValue && !subtext && (
            <span className="text-slate-500 text-[11px]">prev: <strong className="text-slate-700 num-tabular">{previousValue}</strong></span>
          )}
        </div>

        {dataFreshness && (
          <span className="text-[10px] text-slate-500 font-medium tracking-tight">
            {dataFreshness}
          </span>
        )}
      </div>
    </div>
  );
};
