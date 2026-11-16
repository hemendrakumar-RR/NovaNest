import React from 'react';
import { AnimatedTopDock } from "@designcodeio/threeui";
import "@designcodeio/threeui/style.css";
import { TabKey } from './Sidebar';

interface BottomRightDockProps {
  onTabChange: (tab: TabKey) => void;
}

export const BottomRightDock: React.FC<BottomRightDockProps> = ({ onTabChange }) => {
  /* Connect AnimatedTopDock items to existing NovaNest navigation destinations */
  const handleDockClick = (e: React.MouseEvent<HTMLDivElement>) => {
    const btn = (e.target as HTMLElement).closest('button[data-dock-item]');
    if (!btn || !onTabChange) return;
    const label = btn.textContent?.trim().toLowerCase();
    if (label?.includes('product')) {
      onTabChange('overview');
    } else if (label?.includes('solutions')) {
      onTabChange('decision');
    } else if (label?.includes('docs')) {
      onTabChange('command_center');
    } else if (label?.includes('pricing')) {
      onTabChange('financial');
    } else if (label?.includes('changelog')) {
      onTabChange('operations');
    }
  };

  return (
    <aside
      aria-label="NovaNest Command Navigation Dock"
      className="fixed bottom-22 sm:bottom-24 right-5 sm:right-6 z-40 hidden md:flex items-center justify-end pointer-events-auto"
    >
      <div
        className="shader-frame bottom-dock-frame"
        onClick={handleDockClick}
        title="Quick Navigation Dock"
      >
        <AnimatedTopDock
          variant="modern"
          proximity={138}
          spring={0.19}
          damping={0.70}
          widthGrowth={17}
          heightGrowth={16}
          drop={3.5}
        />
      </div>
    </aside>
  );
};
