import React from 'react';

interface SkeletonLoaderProps {
  variant?: 'kpi' | 'chart' | 'table' | 'text' | 'card';
  count?: number;
  className?: string;
  height?: string;
}

export const SkeletonLoader: React.FC<SkeletonLoaderProps> = ({
  variant = 'card',
  count = 1,
  className = '',
  height,
}) => {
  const items = Array.from({ length: count });

  const renderSkeleton = (key: number) => {
    switch (variant) {
      case 'kpi':
        return (
          <div
            key={key}
            className={`p-5 rounded-2xl bg-white border border-slate-200 animate-pulse shadow-sm ${className}`}
            style={{ minHeight: height || '120px' }}
            role="status"
            aria-label="Loading KPI metric"
          >
            <div className="flex justify-between items-start mb-3">
              <div className="h-4 w-28 bg-slate-200 rounded-md" />
              <div className="h-8 w-8 bg-blue-50 rounded-xl" />
            </div>
            <div className="h-8 w-36 bg-slate-200 rounded-lg mb-2" />
            <div className="h-3.5 w-20 bg-slate-100 rounded" />
          </div>
        );

      case 'chart':
        return (
          <div
            key={key}
            className={`p-6 rounded-2xl bg-white border border-slate-200 animate-pulse flex flex-col justify-between shadow-sm ${className}`}
            style={{ height: height || '320px' }}
            role="status"
            aria-label="Loading chart data"
          >
            <div className="flex justify-between items-center mb-6">
              <div>
                <div className="h-5 w-44 bg-slate-200 rounded-md mb-2" />
                <div className="h-3 w-64 bg-slate-100 rounded" />
              </div>
              <div className="h-7 w-24 bg-slate-100 rounded-lg" />
            </div>
            <div className="flex-1 flex items-end gap-3 px-4 pb-2">
              <div className="w-full bg-blue-100 rounded-t-lg h-[40%]" />
              <div className="w-full bg-blue-200 rounded-t-lg h-[75%]" />
              <div className="w-full bg-blue-100 rounded-t-lg h-[55%]" />
              <div className="w-full bg-blue-200 rounded-t-lg h-[90%]" />
              <div className="w-full bg-blue-100 rounded-t-lg h-[65%]" />
              <div className="w-full bg-blue-200 rounded-t-lg h-[80%]" />
              <div className="w-full bg-blue-100 rounded-t-lg h-[50%]" />
            </div>
          </div>
        );

      case 'table':
        return (
          <div
            key={key}
            className={`p-5 rounded-2xl bg-white border border-slate-200 animate-pulse shadow-sm ${className}`}
            role="status"
            aria-label="Loading data table"
          >
            <div className="h-6 w-48 bg-slate-200 rounded mb-4" />
            <div className="space-y-3">
              <div className="h-9 w-full bg-slate-100 rounded-lg" />
              <div className="h-9 w-full bg-slate-50 rounded-lg" />
              <div className="h-9 w-full bg-slate-100 rounded-lg" />
              <div className="h-9 w-full bg-slate-50 rounded-lg" />
              <div className="h-9 w-full bg-slate-100 rounded-lg" />
            </div>
          </div>
        );

      case 'text':
        return (
          <div key={key} className={`space-y-2 animate-pulse ${className}`} role="status">
            <div className="h-4 w-3/4 bg-slate-200 rounded" />
            <div className="h-4 w-full bg-slate-100 rounded" />
            <div className="h-4 w-5/6 bg-slate-100 rounded" />
          </div>
        );

      case 'card':
      default:
        return (
          <div
            key={key}
            className={`p-5 rounded-2xl bg-white border border-slate-200 animate-pulse shadow-sm ${className}`}
            style={{ height: height || 'auto' }}
            role="status"
            aria-label="Loading card content"
          >
            <div className="h-5 w-1/3 bg-slate-200 rounded mb-3" />
            <div className="h-4 w-2/3 bg-slate-100 rounded mb-2" />
            <div className="h-4 w-1/2 bg-slate-100 rounded" />
          </div>
        );
    }
  };

  return (
    <div
      className={count > 1 ? 'grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4' : ''}
      aria-busy="true"
      aria-live="polite"
    >
      {items.map((_, idx) => renderSkeleton(idx))}
    </div>
  );
};
