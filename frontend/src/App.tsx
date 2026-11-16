import React, { useState, useEffect, Suspense, lazy } from 'react';
import { HeaderNav } from './components/HeaderNav';
import { Sidebar, TabKey } from './components/Sidebar';
import { GlobalFilterBar, GlobalFilterState, DEFAULT_FILTER_STATE } from './components/GlobalFilterBar';
import { FloatingChatbot } from './components/FloatingChatbot';
import { BottomRightDock } from './components/BottomRightDock';
import { ErrorBoundary } from './components/ErrorBoundary';
import { SkeletonLoader } from './components/ui/SkeletonLoader';
import { api } from './services/api';

// Route-based dynamic imports for optimized code-splitting and reduced initial bundle footprint
const ExecutiveOverviewView = lazy(() => import('./views/ExecutiveOverviewView').then(m => ({ default: m.ExecutiveOverviewView })));
const CustomerIntelligenceView = lazy(() => import('./views/CustomerIntelligenceView').then(m => ({ default: m.CustomerIntelligenceView })));
const RestaurantIntelligenceView = lazy(() => import('./views/RestaurantIntelligenceView').then(m => ({ default: m.RestaurantIntelligenceView })));
const OperationsIntelligenceView = lazy(() => import('./views/OperationsIntelligenceView').then(m => ({ default: m.OperationsIntelligenceView })));
const FinancialIntelligenceView = lazy(() => import('./views/FinancialIntelligenceView').then(m => ({ default: m.FinancialIntelligenceView })));
const AiIntelligenceView = lazy(() => import('./views/AiIntelligenceView').then(m => ({ default: m.AiIntelligenceView })));
const DecisionIntelligenceView = lazy(() => import('./views/DecisionIntelligenceView').then(m => ({ default: m.DecisionIntelligenceView })));
const DecisionSimulatorView = lazy(() => import('./views/DecisionSimulatorView').then(m => ({ default: m.DecisionSimulatorView })));
const CommandCenterView = lazy(() => import('./views/CommandCenterView').then(m => ({ default: m.CommandCenterView })));
const ExecutiveAiCopilot = lazy(() => import('./components/ExecutiveAiCopilot').then(m => ({ default: m.ExecutiveAiCopilot })));

export function App() {
  const getInitialTab = (): TabKey => {
    try {
      const params = new URLSearchParams(window.location.search);
      const tabParam = params.get('tab') as TabKey;
      const validTabs: TabKey[] = ['overview', 'customer', 'restaurant', 'operations', 'financial', 'ai', 'decision', 'simulator', 'command_center', 'copilot'];
      if (tabParam && validTabs.includes(tabParam)) return tabParam;
      const hash = window.location.hash.replace('#', '') as TabKey;
      if (hash && validTabs.includes(hash)) return hash;
    } catch (e) {}
    return 'overview';
  };

  const getInitialFilters = (): GlobalFilterState => {
    try {
      const params = new URLSearchParams(window.location.search);
      const city = params.get('city');
      const start = params.get('startDate') || params.get('start_date');
      const end = params.get('endDate') || params.get('end_date');
      const rest = params.get('restaurantId') || params.get('restaurant_id');
      const seg = params.get('customerSegment') || params.get('customer_segment');
      const status = params.get('orderStatus') || params.get('order_status');
      const pm = params.get('paymentMethod') || params.get('payment_method');
      return {
        ...DEFAULT_FILTER_STATE,
        ...(city ? { city } : {}),
        ...(start ? { startDate: start, dateRange: 'custom' } : {}),
        ...(end ? { endDate: end, dateRange: 'custom' } : {}),
        ...(rest ? { restaurantId: rest } : {}),
        ...(seg ? { customerSegment: seg } : {}),
        ...(status ? { orderStatus: status } : {}),
        ...(pm ? { paymentMethod: pm } : {}),
      };
    } catch (e) {
      return DEFAULT_FILTER_STATE;
    }
  };

  const [activeTab, setActiveTabState] = useState<TabKey>(getInitialTab);
  const [filters, setFilters] = useState<GlobalFilterState>(getInitialFilters);
  const [dataSource, setDataSource] = useState('CSV File Store');
  const [apiConnected, setApiConnected] = useState(true);
  const [authEpoch, setAuthEpoch] = useState(0);
  const [mobileSidebarOpen, setMobileSidebarOpen] = useState(false);

  const setActiveTab = (tab: TabKey) => {
    setActiveTabState(tab);
    setMobileSidebarOpen(false);
    try {
      const url = new URL(window.location.href);
      url.searchParams.set('tab', tab);
      window.history.replaceState({}, '', url.toString());
    } catch (e) {}
  };

  useEffect(() => {
    const onAuthUpdated = () => setAuthEpoch((prev) => prev + 1);
    window.addEventListener('novanest-auth-updated', onAuthUpdated);
    return () => window.removeEventListener('novanest-auth-updated', onAuthUpdated);
  }, []);

  useEffect(() => {
    const checkHealth = () => {
      api
        .getHealth()
        .then((res) => {
          setDataSource(res.data_source);
          setApiConnected(true);
        })
        .catch(() => setApiConnected(false));
    };

    checkHealth();
    const interval = setInterval(checkHealth, 20000);
    return () => clearInterval(interval);
  }, []);

  const handleCityChangeFromNav = (newCity: string) => {
    setFilters((prev) => ({ ...prev, city: newCity }));
  };

  return (
    <div className="min-h-screen bg-slate-50 text-slate-800 flex flex-col font-sans">
      {/* Top Navigation */}
      <HeaderNav
        dataSource={dataSource}
        selectedCity={filters.city}
        onCityChange={handleCityChangeFromNav}
        apiConnected={apiConnected}
        activeTab={activeTab}
        onTabChange={setActiveTab}
        onToggleMobileSidebar={() => setMobileSidebarOpen((prev) => !prev)}
        isMobileSidebarOpen={mobileSidebarOpen}
      />

      {/* Main Workspace */}
      <div className="flex-1 flex overflow-hidden">
        {/* Navigation Sidebar (Desktop + Mobile slide-over drawer) */}
        <Sidebar
          activeTab={activeTab}
          onTabChange={setActiveTab}
          isOpen={mobileSidebarOpen}
          onClose={() => setMobileSidebarOpen(false)}
        />

        {/* Viewport Content Area */}
        <main className="flex-1 overflow-y-auto p-4 md:p-6 lg:p-8 bg-slate-50">
          <div className="max-w-7xl mx-auto">
            {/* Global Synchronized Multi-Criteria Filter Bar */}
            <GlobalFilterBar filters={filters} onFilterChange={setFilters} />

            <ErrorBoundary viewKey={`${activeTab}-${filters.city}-${authEpoch}`}>
              <Suspense
                fallback={
                  <div className="space-y-6 animate-pulse" aria-busy="true" aria-live="polite">
                    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
                      <SkeletonLoader variant="kpi" count={4} />
                    </div>
                    <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                      <SkeletonLoader variant="chart" count={2} />
                    </div>
                    <SkeletonLoader variant="table" count={5} />
                  </div>
                }
              >
                <React.Fragment key={`${activeTab}-${filters.city}-${filters.dateRange}-${authEpoch}`}>
                  {activeTab === 'overview' && (
                    <ExecutiveOverviewView
                      selectedCity={filters.city}
                      filters={filters}
                      onNavigate={setActiveTab}
                    />
                  )}
                  {activeTab === 'customer' && <CustomerIntelligenceView filters={filters} />}
                  {activeTab === 'restaurant' && <RestaurantIntelligenceView filters={filters} />}
                  {activeTab === 'operations' && <OperationsIntelligenceView filters={filters} />}
                  {activeTab === 'financial' && <FinancialIntelligenceView filters={filters} />}
                  {activeTab === 'ai' && <AiIntelligenceView />}
                  {activeTab === 'decision' && <DecisionIntelligenceView onNavigate={setActiveTab} />}
                  {activeTab === 'simulator' && <DecisionSimulatorView />}
                  {activeTab === 'command_center' && <CommandCenterView />}
                  {activeTab === 'copilot' && (
                    <ExecutiveAiCopilot
                      activeCity={filters.city}
                      onNavigateToTab={(tab) => setActiveTab(tab as TabKey)}
                    />
                  )}
                </React.Fragment>
              </Suspense>
            </ErrorBoundary>
          </div>
        </main>
      </div>

      {/* Bottom-Right ThreeUI AnimatedTopDock */}
      <BottomRightDock onTabChange={setActiveTab} />

      {/* Global Floating AI Chatbot Widget */}
      <FloatingChatbot />
    </div>
  );
}

export default App;
