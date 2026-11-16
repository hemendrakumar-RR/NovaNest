import React, { useState } from 'react';
import {
  Filter,
  RotateCcw,
  Calendar,
  MapPin,
  Store,
  Users,
  CreditCard,
  CheckCircle,
  X,
  ChevronDown,
  ChevronUp,
} from 'lucide-react';

export interface GlobalFilterState {
  dateRange: 'all' | '30d' | '90d' | 'q1_2026' | 'custom';
  startDate?: string;
  endDate?: string;
  city: string;
  restaurantId?: string;
  customerSegment?: string;
  orderStatus?: string;
  paymentMethod?: string;
}

export const DEFAULT_FILTER_STATE: GlobalFilterState = {
  dateRange: 'all',
  startDate: '',
  endDate: '',
  city: 'All',
  restaurantId: '',
  customerSegment: 'All',
  orderStatus: 'All',
  paymentMethod: 'All',
};

interface GlobalFilterBarProps {
  filters: GlobalFilterState;
  onFilterChange: (newFilters: GlobalFilterState) => void;
  isLoading?: boolean;
}

const CITIES = ['All', 'Bangalore', 'Chennai', 'Hyderabad', 'Coimbatore', 'Vijayawada'];

const CUSTOMER_SEGMENTS = [
  'All',
  'Student',
  'Young Professional',
  'Working Professional',
  'Family',
  'Budget Conscious',
  'Premium Gourmet',
];

const ORDER_STATUSES = ['All', 'Delivered', 'Cancelled'];

const PAYMENT_METHODS = ['All', 'UPI', 'Credit Card', 'Debit Card', 'Cash', 'Wallet'];

export const GlobalFilterBar: React.FC<GlobalFilterBarProps> = ({
  filters,
  onFilterChange,
  isLoading = false,
}) => {
  const [draftFilters, setDraftFilters] = useState<GlobalFilterState>({ ...filters });
  const [isExpanded, setIsExpanded] = useState(false);

  // Sync draft if external filter changes
  React.useEffect(() => {
    setDraftFilters({ ...filters });
  }, [filters]);

  const handleDateRangeChange = (val: GlobalFilterState['dateRange']) => {
    let sDate = '';
    let eDate = '';
    if (val === '30d') {
      sDate = '2026-05-18';
      eDate = '2026-06-17';
    } else if (val === '90d') {
      sDate = '2026-03-18';
      eDate = '2026-06-17';
    } else if (val === 'q1_2026') {
      sDate = '2026-01-01';
      eDate = '2026-03-31';
    }
    setDraftFilters((prev) => ({
      ...prev,
      dateRange: val,
      startDate: sDate,
      endDate: eDate,
    }));
  };

  const handleApply = (e?: React.FormEvent) => {
    if (e) e.preventDefault();
    onFilterChange({ ...draftFilters });
  };

  const handleReset = () => {
    setDraftFilters({ ...DEFAULT_FILTER_STATE });
    onFilterChange({ ...DEFAULT_FILTER_STATE });
  };

  const removeFilter = (key: keyof GlobalFilterState) => {
    const updated = { ...filters };
    if (key === 'dateRange') {
      updated.dateRange = 'all';
      updated.startDate = '';
      updated.endDate = '';
    } else if (key === 'city') {
      updated.city = 'All';
    } else if (key === 'customerSegment') {
      updated.customerSegment = 'All';
    } else if (key === 'orderStatus') {
      updated.orderStatus = 'All';
    } else if (key === 'paymentMethod') {
      updated.paymentMethod = 'All';
    } else if (key === 'restaurantId') {
      updated.restaurantId = '';
    }
    setDraftFilters(updated);
    onFilterChange(updated);
  };

  // Determine active filter badges
  const activePills: Array<{ key: keyof GlobalFilterState; label: string; value: string }> = [];
  if (filters.city && filters.city !== 'All') {
    activePills.push({ key: 'city', label: 'City', value: filters.city });
  }
  if (filters.dateRange !== 'all') {
    const rangeLabel =
      filters.dateRange === '30d'
        ? 'Last 30 Days'
        : filters.dateRange === '90d'
        ? 'Last 90 Days'
        : filters.dateRange === 'q1_2026'
        ? 'Q1 2026'
        : `${filters.startDate || 'Start'} to ${filters.endDate || 'End'}`;
    activePills.push({ key: 'dateRange', label: 'Date', value: rangeLabel });
  }
  if (filters.restaurantId && filters.restaurantId.trim()) {
    activePills.push({ key: 'restaurantId', label: 'Partner', value: filters.restaurantId.trim() });
  }
  if (filters.customerSegment && filters.customerSegment !== 'All') {
    activePills.push({ key: 'customerSegment', label: 'Segment', value: filters.customerSegment });
  }
  if (filters.orderStatus && filters.orderStatus !== 'All') {
    activePills.push({ key: 'orderStatus', label: 'Status', value: filters.orderStatus });
  }
  if (filters.paymentMethod && filters.paymentMethod !== 'All') {
    activePills.push({ key: 'paymentMethod', label: 'Payment', value: filters.paymentMethod });
  }

  return (
    <div className="bg-white border border-slate-200 rounded-xl p-3.5 shadow-sm mb-6">
      <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-3">
        {/* Left Side: Summary & Quick Toggle */}
        <div className="flex items-center gap-2.5 flex-wrap">
          <div className="flex items-center gap-2 text-xs font-bold uppercase tracking-wider text-slate-800">
            <Filter size={15} className="text-blue-600" />
            <span>Global Filters</span>
            {activePills.length > 0 && (
              <span className="px-1.5 py-0.5 rounded-full bg-blue-50 text-blue-600 border border-blue-200 text-[10px]">
                {activePills.length} Active
              </span>
            )}
          </div>

          {/* Quick city select right on the collapsed bar */}
          <div className="flex items-center gap-1.5 text-xs">
            <MapPin size={13} className="text-slate-500 ml-2" />
            <select
              value={draftFilters.city}
              onChange={(e) => {
                const nextCity = e.target.value;
                setDraftFilters((prev) => ({ ...prev, city: nextCity }));
                onFilterChange({ ...filters, city: nextCity });
              }}
              className="bg-slate-50 border border-slate-200 text-slate-800 rounded-md px-2 py-1 text-xs focus:outline-none focus:ring-1 focus:ring-blue-600"
            >
              {CITIES.map((c) => (
                <option key={c} value={c}>
                  City: {c}
                </option>
              ))}
            </select>
          </div>

          {/* Quick Date Range select */}
          <div className="flex items-center gap-1.5 text-xs">
            <Calendar size={13} className="text-slate-500" />
            <select
              value={draftFilters.dateRange}
              onChange={(e) => {
                const nextVal = e.target.value as GlobalFilterState['dateRange'];
                handleDateRangeChange(nextVal);
                if (nextVal !== 'custom') {
                  let s = '';
                  let end = '';
                  if (nextVal === '30d') {
                    s = '2026-05-18';
                    end = '2026-06-17';
                  } else if (nextVal === '90d') {
                    s = '2026-03-18';
                    end = '2026-06-17';
                  } else if (nextVal === 'q1_2026') {
                    s = '2026-01-01';
                    end = '2026-03-31';
                  }
                  onFilterChange({ ...filters, dateRange: nextVal, startDate: s, endDate: end });
                }
              }}
              className="bg-slate-50 border border-slate-200 text-slate-800 rounded-md px-2 py-1 text-xs focus:outline-none focus:ring-1 focus:ring-blue-600"
            >
              <option value="all">Timeline: All-Time (12M)</option>
              <option value="30d">Latest 30 Days (Cycle)</option>
              <option value="90d">Quarterly (90 Days)</option>
              <option value="q1_2026">Q1 2026 Certified</option>
              <option value="custom">Custom Date Range...</option>
            </select>
          </div>

          {/* Expand / Collapse All Filters Button */}
          <button
            type="button"
            onClick={() => setIsExpanded(!isExpanded)}
            className="flex items-center gap-1 text-xs font-semibold text-blue-600 hover:text-blue-700 ml-1 py-1 px-2 rounded-md hover:bg-blue-50 transition-colors"
          >
            <span>{isExpanded ? 'Less Filters' : 'More Filters (Segment, Status, Partner)'}</span>
            {isExpanded ? <ChevronUp size={14} /> : <ChevronDown size={14} />}
          </button>
        </div>

        {/* Right Side: Active Filter Badges & Reset Button */}
        <div className="flex items-center gap-2 flex-wrap">
          {activePills.map((pill) => (
            <span
              key={pill.key}
              className="inline-flex items-center gap-1.5 px-2 py-1 rounded-md text-[11px] font-medium bg-blue-50 text-blue-700 border border-blue-200"
            >
              <span className="text-slate-500">{pill.label}:</span>
              <strong className="text-slate-900 font-semibold">{pill.value}</strong>
              <button
                type="button"
                onClick={() => removeFilter(pill.key)}
                className="hover:text-red-600 p-0.5 rounded focus:outline-none"
                title={`Remove ${pill.label} filter`}
              >
                <X size={11} />
              </button>
            </span>
          ))}

          {activePills.length > 0 && (
            <button
              type="button"
              onClick={handleReset}
              className="flex items-center gap-1 text-[11px] text-slate-500 hover:text-slate-800 px-2 py-1 rounded-md hover:bg-slate-100 transition-colors border border-slate-200"
              title="Reset all filters to default"
            >
              <RotateCcw size={11} />
              <span>Reset</span>
            </button>
          )}
        </div>
      </div>

      {/* Expanded Multi-Filter Form Panel */}
      {isExpanded && (
        <form onSubmit={handleApply} className="mt-3.5 pt-3.5 border-t border-slate-100">
          <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-3">
            {/* 1. Date Range Preset */}
            <div>
              <label className="block text-[11px] font-semibold text-slate-600 uppercase tracking-wider mb-1">
                Date Window
              </label>
              <select
                value={draftFilters.dateRange}
                onChange={(e) => handleDateRangeChange(e.target.value as GlobalFilterState['dateRange'])}
                className="w-full bg-slate-50 border border-slate-200 rounded-lg p-2 text-xs text-slate-800 focus:outline-none focus:ring-1 focus:ring-blue-600"
              >
                <option value="all">All Available (12 Months)</option>
                <option value="30d">Last 30 Days (Cycle)</option>
                <option value="90d">Last 90 Days (Quarter)</option>
                <option value="q1_2026">Q1 2026 (Jan - Mar)</option>
                <option value="custom">Custom Date Range</option>
              </select>
            </div>

            {/* 2. City Selector */}
            <div>
              <label className="block text-[11px] font-semibold text-slate-600 uppercase tracking-wider mb-1">
                Territory
              </label>
              <select
                value={draftFilters.city}
                onChange={(e) => setDraftFilters((prev) => ({ ...prev, city: e.target.value }))}
                className="w-full bg-slate-50 border border-slate-200 rounded-lg p-2 text-xs text-slate-800 focus:outline-none focus:ring-1 focus:ring-blue-600"
              >
                {CITIES.map((c) => (
                  <option key={c} value={c}>
                    {c === 'All' ? 'All Operating Cities' : c}
                  </option>
                ))}
              </select>
            </div>

            {/* 3. Customer Segment */}
            <div>
              <label className="block text-[11px] font-semibold text-slate-600 uppercase tracking-wider mb-1">
                Customer Persona
              </label>
              <select
                value={draftFilters.customerSegment}
                onChange={(e) => setDraftFilters((prev) => ({ ...prev, customerSegment: e.target.value }))}
                className="w-full bg-slate-50 border border-slate-200 rounded-lg p-2 text-xs text-slate-800 focus:outline-none focus:ring-1 focus:ring-blue-600"
              >
                {CUSTOMER_SEGMENTS.map((s) => (
                  <option key={s} value={s}>
                    {s}
                  </option>
                ))}
              </select>
            </div>

            {/* 4. Order Status */}
            <div>
              <label className="block text-[11px] font-semibold text-slate-600 uppercase tracking-wider mb-1">
                Fulfillment Status
              </label>
              <select
                value={draftFilters.orderStatus}
                onChange={(e) => setDraftFilters((prev) => ({ ...prev, orderStatus: e.target.value }))}
                className="w-full bg-slate-50 border border-slate-200 rounded-lg p-2 text-xs text-slate-800 focus:outline-none focus:ring-1 focus:ring-blue-600"
              >
                {ORDER_STATUSES.map((st) => (
                  <option key={st} value={st}>
                    {st === 'All' ? 'All (Delivered + Cancelled)' : st}
                  </option>
                ))}
              </select>
            </div>

            {/* 5. Payment Method */}
            <div>
              <label className="block text-[11px] font-semibold text-slate-600 uppercase tracking-wider mb-1">
                Payment Channel
              </label>
              <select
                value={draftFilters.paymentMethod}
                onChange={(e) => setDraftFilters((prev) => ({ ...prev, paymentMethod: e.target.value }))}
                className="w-full bg-slate-50 border border-slate-200 rounded-lg p-2 text-xs text-slate-800 focus:outline-none focus:ring-1 focus:ring-blue-600"
              >
                {PAYMENT_METHODS.map((pm) => (
                  <option key={pm} value={pm}>
                    {pm}
                  </option>
                ))}
              </select>
            </div>

            {/* 6. Specific Merchant Search */}
            <div>
              <label className="block text-[11px] font-semibold text-slate-600 uppercase tracking-wider mb-1">
                Merchant ID (Optional)
              </label>
              <input
                type="text"
                placeholder="e.g. R00123"
                value={draftFilters.restaurantId || ''}
                onChange={(e) => setDraftFilters((prev) => ({ ...prev, restaurantId: e.target.value }))}
                className="w-full bg-slate-50 border border-slate-200 rounded-lg p-2 text-xs text-slate-800 placeholder-slate-400 focus:outline-none focus:ring-1 focus:ring-blue-600"
              />
            </div>
          </div>

          {/* Custom Date Pickers (Shown only when dateRange === 'custom') */}
          {draftFilters.dateRange === 'custom' && (
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 mt-3 p-3 bg-slate-50 rounded-lg border border-slate-200">
              <div>
                <label className="block text-[11px] text-slate-600 font-medium mb-1">From Date (YYYY-MM-DD)</label>
                <input
                  type="date"
                  value={draftFilters.startDate || ''}
                  onChange={(e) => setDraftFilters((prev) => ({ ...prev, startDate: e.target.value }))}
                  className="w-full bg-white border border-slate-200 rounded p-1.5 text-xs text-slate-800"
                />
              </div>
              <div>
                <label className="block text-[11px] text-slate-600 font-medium mb-1">To Date (YYYY-MM-DD)</label>
                <input
                  type="date"
                  value={draftFilters.endDate || ''}
                  onChange={(e) => setDraftFilters((prev) => ({ ...prev, endDate: e.target.value }))}
                  className="w-full bg-white border border-slate-200 rounded p-1.5 text-xs text-slate-800"
                />
              </div>
            </div>
          )}

          {/* Action Row */}
          <div className="flex items-center justify-end gap-2.5 mt-3 pt-2.5 border-t border-slate-100">
            <button
              type="button"
              onClick={handleReset}
              className="px-3 py-1.5 rounded-lg text-xs font-medium text-slate-600 hover:text-slate-800 hover:bg-slate-100 transition-colors border border-slate-200"
            >
              Reset Filters
            </button>
            <button
              type="submit"
              disabled={isLoading}
              className="px-4 py-1.5 rounded-lg text-xs font-semibold bg-blue-600 hover:bg-blue-700 text-white shadow-sm transition-all flex items-center gap-1.5 disabled:opacity-50"
            >
              <CheckCircle size={13} />
              <span>Apply Filters</span>
            </button>
          </div>
        </form>
      )}
    </div>
  );
};
