import React, { useState, useEffect } from 'react';
import { Database, Activity, Clock, MapPin, Menu, X } from 'lucide-react';
import { formatTimeToIST } from '../utils/formatters';
import { ThemeSwitcher } from './ThemeSwitcher';
import { TabKey } from './Sidebar';

interface HeaderNavProps {
  dataSource: string;
  selectedCity: string;
  onCityChange: (city: string) => void;
  apiConnected: boolean;
  activeTab?: TabKey;
  onTabChange?: (tab: TabKey) => void;
  onToggleMobileSidebar?: () => void;
  isMobileSidebarOpen?: boolean;
}

export const HeaderNav: React.FC<HeaderNavProps> = ({
  dataSource,
  selectedCity,
  onCityChange,
  apiConnected,
  onToggleMobileSidebar,
  isMobileSidebarOpen = false,
}) => {
  const [time, setTime] = useState(formatTimeToIST(new Date(), true));

  useEffect(() => {
    const timer = setInterval(() => {
      setTime(formatTimeToIST(new Date(), true));
    }, 1000);
    return () => clearInterval(timer);
  }, []);

  const cities = ['All', 'Bangalore', 'Chennai', 'Coimbatore', 'Hyderabad', 'Vijayawada'];

  return (
    <header className="sticky top-0 z-40 min-h-16 lg:min-h-20 bg-white border-b border-slate-200 px-4 lg:px-6 flex items-center justify-between gap-4 shadow-sm">
      {/* LEFT: Mobile Menu Button + NovaNest Wordmark & Subtitle */}
      <div className="flex items-center gap-3 shrink-0">
        {onToggleMobileSidebar && (
          <button
            onClick={onToggleMobileSidebar}
            className="md:hidden p-2 rounded-lg text-slate-600 hover:text-slate-800 hover:bg-slate-100 focus:outline-none focus:ring-2 focus:ring-blue-600"
            aria-label={isMobileSidebarOpen ? 'Close navigation drawer' : 'Open navigation drawer'}
            aria-expanded={isMobileSidebarOpen}
          >
            {isMobileSidebarOpen ? <X size={20} /> : <Menu size={20} />}
          </button>
        )}

        <div className="w-9 h-9 rounded-lg bg-blue-600 flex items-center justify-center shadow-md shadow-blue-500/20">
          <Activity className="text-white" size={20} />
        </div>
        <div>
          <div className="flex items-center gap-2">
            <span className="font-extrabold tracking-wider text-base text-slate-800">NOVANEST</span>
            <span className="text-[10px] font-bold px-1.5 py-0.5 rounded bg-blue-50 text-blue-600 border border-blue-200">
              DECISION SUITE 2.0
            </span>
          </div>
          <p className="text-[10px] sm:text-[11px] font-semibold tracking-wider text-slate-500 hidden sm:block">
            END - TO - END BUSINESS ANALYTICS SYSTEM
          </p>
        </div>
      </div>

      {/* RIGHT: Essential Controls (Territory Filter, IST Clock, Pipeline Status, Core Engine, Theme) */}
      <div className="flex items-center gap-2.5 sm:gap-3 shrink-0">
        {/* City Filter */}
        <div className="flex items-center gap-1.5 bg-slate-50 border border-slate-200 rounded-lg px-2.5 py-1.5 text-xs">
          <MapPin size={14} className="text-slate-500" />
          <select
            value={selectedCity}
            onChange={(e) => onCityChange(e.target.value)}
            className="bg-transparent text-slate-800 outline-none cursor-pointer pr-1 focus:ring-1 focus:ring-blue-600 rounded"
            aria-label="Filter territory by city"
          >
            {cities.map((c) => (
              <option key={c} value={c} className="bg-white text-slate-800">
                {c === 'All' ? 'All Territories' : c}
              </option>
            ))}
          </select>
        </div>

        {/* Data Source Badge */}
        <div className="hidden 2xl:flex items-center gap-2 bg-slate-50 border border-slate-200 rounded-lg px-3 py-1.5 text-xs">
          <Database size={13} className="text-blue-600" />
          <span className="text-slate-500">Data Pipeline:</span>
          <span className="font-medium text-slate-800">{dataSource || 'CSV File Store'}</span>
        </div>

        {/* Live Clock */}
        <div className="hidden lg:flex items-center gap-1.5 text-xs text-slate-500 font-mono">
          <Clock size={13} />
          <span>{time}</span>
        </div>

        {/* API Status Indicator */}
        <div
          className={`flex items-center gap-2 px-2.5 py-1.5 rounded-lg text-xs font-medium border ${
            apiConnected
              ? 'bg-green-50 text-green-700 border-green-200'
              : 'bg-red-50 text-red-700 border-red-200'
          }`}
          role="status"
          aria-label={apiConnected ? 'FastAPI Core Engine Online' : 'FastAPI Core Engine Offline'}
        >
          <span className="relative flex h-2 w-2">
            <span
              className={`animate-ping absolute inline-flex h-full w-full rounded-full opacity-75 ${
                apiConnected ? 'bg-green-400' : 'bg-red-400'
              }`}
            />
            <span
              className={`relative inline-flex rounded-full h-2 w-2 ${
                apiConnected ? 'bg-green-600' : 'bg-red-600'
              }`}
            />
          </span>
          <span className="hidden sm:inline">{apiConnected ? 'Core Engine Online' : 'Engine Offline'}</span>
        </div>

        {/* Theme Switcher Popover */}
        <ThemeSwitcher />
      </div>
    </header>
  );
};
