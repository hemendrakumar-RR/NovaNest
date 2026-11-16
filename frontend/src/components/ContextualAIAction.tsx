import React from 'react';
import { Sparkles } from 'lucide-react';
import { ContextualAIPayload, launchContextualAI } from '../types/contextualAi';

export interface ContextualAIActionProps {
  payload: ContextualAIPayload;
  label?: string;
  size?: 'xs' | 'sm';
  className?: string;
}

export const ContextualAIAction: React.FC<ContextualAIActionProps> = ({
  payload,
  label = 'Ask AI',
  size = 'xs',
  className = '',
}) => {
  const handleClick = (e: React.MouseEvent) => {
    e.stopPropagation();
    launchContextualAI(payload);
  };

  const tooltip = `Launch NovaNest AI analysis for ${
    payload.entityName || payload.entityId || payload.selectedMetric || payload.kpiOrChartId
  }`;

  const sizeClasses =
    size === 'xs'
      ? 'px-2 py-0.5 text-[11px] gap-1'
      : 'px-2.5 py-1 text-xs gap-1.5';

  return (
    <button
      onClick={handleClick}
      className={`inline-flex items-center rounded bg-sapphire-950/60 hover:bg-sapphire-900/90 text-cyan-300 hover:text-white border border-sapphire-700/40 hover:border-cyan-400/60 transition-all font-medium duration-150 cursor-pointer shadow-sm ${sizeClasses} ${className}`}
      title={tooltip}
      aria-label={tooltip}
    >
      <Sparkles size={size === 'xs' ? 11 : 13} className="text-cyan-400 animate-pulse" />
      <span>{label}</span>
    </button>
  );
};

