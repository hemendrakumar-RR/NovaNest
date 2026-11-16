import React from 'react';
import { CheckCircle2, AlertTriangle, XCircle, Info, Clock, ArrowUpRight, ArrowDownRight, Minus } from 'lucide-react';

export type BadgeVariant = 'success' | 'warning' | 'danger' | 'info' | 'neutral' | 'accent';

interface StatusBadgeProps {
  label: string;
  variant?: BadgeVariant;
  icon?: 'check' | 'warning' | 'error' | 'info' | 'clock' | 'up' | 'down' | 'neutral';
  size?: 'sm' | 'md';
  className?: string;
}

export const StatusBadge: React.FC<StatusBadgeProps> = ({
  label,
  variant = 'neutral',
  icon,
  size = 'md',
  className = '',
}) => {
  const getVariantStyles = () => {
    switch (variant) {
      case 'success':
        return 'bg-green-50 text-green-700 border-green-200';
      case 'warning':
        return 'bg-amber-50 text-amber-700 border-amber-200';
      case 'danger':
        return 'bg-red-50 text-red-700 border-red-200';
      case 'info':
        return 'bg-sky-50 text-sky-700 border-sky-200';
      case 'accent':
        return 'bg-orange-50 text-orange-700 border-orange-200';
      case 'neutral':
      default:
        return 'bg-slate-100 text-slate-700 border-slate-200';
    }
  };

  const renderIcon = () => {
    const iconSize = size === 'sm' ? 'w-3 h-3' : 'w-3.5 h-3.5';
    switch (icon) {
      case 'check':
        return <CheckCircle2 className={`${iconSize} shrink-0`} aria-hidden="true" />;
      case 'warning':
        return <AlertTriangle className={`${iconSize} shrink-0`} aria-hidden="true" />;
      case 'error':
        return <XCircle className={`${iconSize} shrink-0`} aria-hidden="true" />;
      case 'info':
        return <Info className={`${iconSize} shrink-0`} aria-hidden="true" />;
      case 'clock':
        return <Clock className={`${iconSize} shrink-0`} aria-hidden="true" />;
      case 'up':
        return <ArrowUpRight className={`${iconSize} shrink-0 text-green-600`} aria-hidden="true" />;
      case 'down':
        return <ArrowDownRight className={`${iconSize} shrink-0 text-red-600`} aria-hidden="true" />;
      case 'neutral':
        return <Minus className={`${iconSize} shrink-0 text-slate-500`} aria-hidden="true" />;
      default:
        return null;
    }
  };

  const sizeStyles = size === 'sm' ? 'px-2 py-0.5 text-[11px]' : 'px-2.5 py-1 text-xs';

  return (
    <span
      role="status"
      className={`inline-flex items-center gap-1.5 font-semibold rounded-md border ${getVariantStyles()} ${sizeStyles} ${className}`}
    >
      {renderIcon()}
      <span>{label}</span>
    </span>
  );
};
