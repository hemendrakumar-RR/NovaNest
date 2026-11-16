import React, { useEffect } from 'react';
import {
  LayoutDashboard,
  Users,
  Store,
  Truck,
  IndianRupee,
  BrainCircuit,
  Sliders,
  Cpu,
  Sparkles,
  X,
} from 'lucide-react';

export type TabKey =
  | 'overview'
  | 'customer'
  | 'restaurant'
  | 'operations'
  | 'financial'
  | 'ai'
  | 'decision'
  | 'simulator'
  | 'command_center'
  | 'copilot';

interface SidebarProps {
  activeTab: TabKey;
  onTabChange: (tab: TabKey) => void;
  isOpen?: boolean;
  onClose?: () => void;
}

export const Sidebar: React.FC<SidebarProps> = ({
  activeTab,
  onTabChange,
  isOpen = false,
  onClose,
}) => {
  const navItems = [
    {
      key: 'overview' as TabKey,
      label: 'Executive Overview',
      subtitle: 'C-Suite Performance Radar',
      icon: LayoutDashboard,
    },
    {
      key: 'customer' as TabKey,
      label: 'Customer Intelligence',
      subtitle: 'RFM, CLV & 360 Profiles',
      icon: Users,
    },
    {
      key: 'restaurant' as TabKey,
      label: 'Restaurant Intelligence',
      subtitle: 'Merchant Health & Risk Signals',
      icon: Store,
    },
    {
      key: 'operations' as TabKey,
      label: 'Operations Intelligence',
      subtitle: 'Demand Forecasts & Logistics',
      icon: Truck,
    },
    {
      key: 'financial' as TabKey,
      label: 'Financial Intelligence',
      subtitle: 'P&L Economics & Leakage Audit',
      icon: IndianRupee,
    },
    {
      key: 'decision' as TabKey,
      label: 'Decision Intelligence',
      subtitle: 'Next-Best-Action Queue',
      icon: BrainCircuit,
    },
    {
      key: 'simulator' as TabKey,
      label: 'Decision Simulator',
      subtitle: 'Multi-Variable What-If Lab',
      icon: Sliders,
    },
    {
      key: 'command_center' as TabKey,
      label: 'Command Center',
      subtitle: 'Analytical Digital Twin Matrix',
      icon: Cpu,
    },
    {
      key: 'copilot' as TabKey,
      label: 'AI Business Copilot',
      subtitle: 'Conversational Decision Agent',
      icon: Sparkles,
    },
  ];

  // Close on Escape key
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'Escape' && isOpen && onClose) {
        onClose();
      }
    };
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [isOpen, onClose]);

  const handleSelectTab = (key: TabKey) => {
    onTabChange(key);
    if (onClose) onClose();
  };

  const navContent = (isMobileMode = false) => (
    <>
      <div className="space-y-1">
        <div className="flex items-center justify-between px-3 py-2">
          <span className="text-[11px] font-bold uppercase tracking-wider text-slate-500">
            Intelligence Ecosystem
          </span>
          {isMobileMode && onClose && (
            <button
              onClick={onClose}
              className="p-1 rounded-lg text-slate-500 hover:text-slate-800 hover:bg-slate-100 focus:outline-none focus:ring-2 focus:ring-blue-600"
              aria-label="Close navigation menu"
            >
              <X size={18} />
            </button>
          )}
        </div>

        {navItems.map((item) => {
          const Icon = item.icon;
          const isActive = activeTab === item.key;

          return (
            <button
              key={item.key}
              onClick={() => handleSelectTab(item.key)}
              className={`w-full text-left px-3.5 py-3 rounded-xl transition-all duration-150 flex items-center gap-3.5 group relative focus:outline-none focus-visible:ring-2 focus-visible:ring-blue-600 ${
                isActive
                  ? 'bg-blue-50 text-blue-600 border border-blue-200 shadow-sm'
                  : 'text-slate-700 hover:text-blue-600 hover:bg-blue-50/50 border border-transparent'
              }`}
              aria-current={isActive ? 'page' : undefined}
            >
              <div
                className={`p-2 rounded-lg transition-colors ${
                  isActive
                    ? 'bg-blue-600 text-white shadow-sm shadow-blue-500/20'
                    : 'bg-slate-100 text-blue-600 group-hover:bg-blue-100'
                }`}
              >
                <Icon size={18} />
              </div>
              <div className="overflow-hidden">
                <p className={`text-sm font-semibold truncate ${isActive ? 'text-blue-600' : 'text-slate-800'}`}>
                  {item.label}
                </p>
                <p className="text-[11px] text-slate-500 truncate">{item.subtitle}</p>
              </div>

              {isActive && (
                <div className="absolute right-2 w-1.5 h-6 rounded-full bg-blue-600 shadow-sm shadow-blue-600/30" />
              )}
            </button>
          );
        })}
      </div>

      {/* Footer Info */}
      <div className="pt-4 border-t border-slate-200 px-3">
        <div className="p-3 rounded-lg bg-slate-50 border border-slate-200 text-xs">
          <div className="flex items-center justify-between text-slate-500 mb-1">
            <span>Platform Status</span>
            <span className="text-green-600 font-medium">Active (Dual UI)</span>
          </div>
          <p className="text-[11px] text-slate-500">Streamlit: port 8502</p>
          <p className="text-[11px] text-slate-500">FastAPI API: port 8001</p>
        </div>
      </div>
    </>
  );

  return (
    <>
      {/* Desktop Persistent Sidebar */}
      <aside
        className="hidden md:flex w-64 lg:w-72 bg-white border-r border-slate-200 p-4 flex-col justify-between shrink-0 min-h-[calc(100vh-4rem)] shadow-sm"
        aria-label="Desktop Navigation"
      >
        {navContent(false)}
      </aside>

      {/* Mobile Backdrop & Slide-over Drawer */}
      {isOpen && (
        <div className="md:hidden fixed inset-0 z-50 flex">
          {/* Backdrop */}
          <div
            className="fixed inset-0 bg-slate-900/40 backdrop-blur-sm transition-opacity"
            onClick={onClose}
            aria-hidden="true"
          />

          {/* Drawer content */}
          <aside
            className="relative z-50 w-72 max-w-[85vw] bg-white border-r border-slate-200 p-4 flex flex-col justify-between shadow-2xl overflow-y-auto animate-fadeIn"
            aria-label="Mobile Navigation"
          >
            {navContent(true)}
          </aside>
        </div>
      )}
    </>
  );
};
