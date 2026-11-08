# NovaNest — React 18 + TypeScript Frontend Architecture Audit

## 1. Application Overview & Technology Stack
- **Framework**: React 18.2 with TypeScript (strict type checking enabled).
- **Build Tool**: Vite 5.x with Hot Module Replacement (HMR).
- **Styling**: Tailwind CSS 3.x, Custom CSS Glassmorphism Shaders, Lucide React icons.
- **Data Visualization**: Recharts & custom SVG visual components.
- **3D Graphics**: Three.js WebGL canvas integration in `Hero3DBanner.tsx`.
- **Location**: `C:\Users\madha\OneDrive\Documents\03.CAPSTONE\NovaNest\NovaNest\frontend`.

## 2. Views & Navigation Structure (9 Views)
The React application mirrors the complete 9-domain business analytics architecture:
1. `ExecutiveOverviewView.tsx`: High-level executive dashboard (GMV, orders, revenue, city performance).
2. `CustomerIntelligenceView.tsx`: Customer 360 profile, RFM segment breakdown, churn risk metrics.
3. `RestaurantIntelligenceView.tsx`: Restaurant partner analytics, cuisine distribution, kitchen preparation SLAs.
4. `OperationsIntelligenceView.tsx`: Rider fleet operations, average delivery times, geofencing, SLA violations.
5. `FinancialIntelligenceView.tsx`: Unit economics, contribution margin, revenue streams, delivery fee margins.
6. `DecisionIntelligenceView.tsx`: Next-best-action decision engine, prioritized strategic recommendations.
7. `AiIntelligenceView.tsx`: Dedicated Ask NovaNest AI conversational interface with query suggestion chips.
8. `DecisionSimulatorView.tsx`: Interactive what-if simulation workbench (commission slider, rider fee simulator).
9. `CommandCenterView.tsx`: Unified real-time operational cockpit aggregating live alerts and twin metrics.

## 3. UI Component Inventory (8 Components)
- `HeaderNav.tsx`: Top navigation bar with live status indicators, theme picker, and breadcrumbs.
- `Hero3DBanner.tsx`: Three.js animated background particle banner with interactive mouse glow.
- `Sidebar.tsx`: Collapsible secondary navigation bar with domain icons.
- `ThemeSwitcher.tsx`: Dynamic palette selector supporting 3 themes: Midnight Navy, Cyber Cyan, and Emerald Matrix.
- `KpiCard.tsx`: Reusable metric card with delta indicators, mini sparklines, and status badges.
- `SectionHeader.tsx`: Standardized section banner with subtitle and action button slots.
- `BottomRightDock.tsx`: Floating quick-access menu offering instant shortcuts to AI, simulator, and metrics.
- `FloatingChatbot.tsx`: Non-intrusive floating chat bubble expanding into an interactive AI drawer.

## 4. API Client & State Management (`src/api.ts`)
- Communicates directly with the FastAPI backend at `http://localhost:8000/api`.
- Implements typed fetch wrappers for all 13 endpoints (`fetchHealth`, `fetchOverview`, `askAi`, `simulateScenario`, etc.).
- Robust network error handling: displays graceful inline banners when the backend is offline.

## 5. Build & Performance Audit
- Bundle footprint is highly optimized via Vite code splitting.
- Three.js animation loop safely decouples on component unmount, preventing memory leaks.
