import React from 'react';
import { Sparkles } from 'lucide-react';
import { ContextualAIPayload, launchContextualAI } from '../types/contextualAi';

export interface ContextualAIButtonProps {
  payload: ContextualAIPayload;
  size?: 'xs' | 'sm' | 'md';
  variant?: 'icon' | 'badge' | 'button' | 'compact';
  label?: string;
  tooltip?: string;
  ariaLabel?: string;
  className?: string;
}

export const ContextualAIButton: React.FC<ContextualAIButtonProps> = ({
  payload,
  size = 'sm',
  variant = 'icon',
  label = 'Ask AI',
  tooltip,
  ariaLabel,
  className = '',
}) => {
  const handleClick = (e: React.MouseEvent) => {
    e.stopPropagation();
    launchContextualAI(payload);
  };

  const defaultTooltip =
    tooltip ||
    ariaLabel ||
    `Ask NovaNest AI to analyze ${
      payload.selectedMetric ||
      payload.entityName ||
      payload.entityId ||
      payload.kpiOrChartId.replace(/_/g, ' ')
    }`;

  const buttonAria = ariaLabel || defaultTooltip;

  const iconSizes = {
    xs: 11,
    sm: 13,
    md: 15,
  };

  if (variant === 'icon') {
    return (
      <button
        onClick={handleClick}
        className={`group p-1.5 rounded-lg text-slate-500 hover:text-blue-600 hover:bg-slate-100 border border-transparent hover:border-slate-200 transition-all duration-200 cursor-pointer ${className}`}
        title={defaultTooltip}
        aria-label={buttonAria}
      >
        <Sparkles
          size={iconSizes[size]}
          className="group-hover:rotate-12 group-hover:scale-110 transition-transform text-blue-600"
        />
      </button>
    );
  }

  if (variant === 'badge') {
    return (
      <button
        onClick={handleClick}
        className={`inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[10px] font-medium bg-blue-50 hover:bg-blue-100 text-blue-700 border border-blue-200 shadow-2xs transition-all duration-200 cursor-pointer ${className}`}
        title={defaultTooltip}
        aria-label={buttonAria}
      >
        <Sparkles size={iconSizes.xs} className="text-blue-600 animate-pulse" />
        <span>{label}</span>
      </button>
    );
  }

  if (variant === 'compact') {
    return (
      <button
        onClick={handleClick}
        className={`inline-flex items-center gap-1 px-1.5 py-0.5 rounded text-[11px] font-mono text-slate-500 hover:text-blue-700 hover:bg-slate-100 transition-colors cursor-pointer ${className}`}
        title={defaultTooltip}
        aria-label={buttonAria}
      >
        <Sparkles size={11} className="text-blue-600" />
        <span>{label}</span>
      </button>
    );
  }

  // default 'button' variant
  return (
    <button
      onClick={handleClick}
      className={`inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-semibold bg-blue-600 hover:bg-blue-700 text-white shadow-xs transition-all duration-200 cursor-pointer ${className}`}
      title={defaultTooltip}
      aria-label={buttonAria}
    >
      <Sparkles size={iconSizes[size]} className="text-white animate-pulse" />
      <span>{label}</span>
    </button>
  );
};

