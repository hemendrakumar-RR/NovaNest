import React from 'react';

interface SectionHeaderProps {
  title: string;
  subtitle?: string;
  tag?: string;
  action?: React.ReactNode;
}

export const SectionHeader: React.FC<SectionHeaderProps> = ({
  title,
  subtitle,
  tag,
  action
}) => {
  return (
    <div className="flex flex-col md:flex-row md:items-end justify-between gap-4 mb-6 pt-2">
      <div>
        <div className="flex items-center gap-2.5 mb-1.5">
          {tag && (
            <span className="px-2 py-0.5 text-[10px] font-bold tracking-widest uppercase bg-blue-50 text-blue-600 border border-blue-200 rounded">
              {tag}
            </span>
          )}
          <h2 className="text-xl md:text-2xl font-bold tracking-tight text-slate-800">{title}</h2>
        </div>
        {subtitle && <p className="text-sm text-slate-500 max-w-3xl">{subtitle}</p>}
      </div>
      {action && <div className="flex items-center gap-2">{action}</div>}
    </div>
  );
};
