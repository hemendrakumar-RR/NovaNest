# NovaNest — Phase 18 Theme Plan: Complete Dashboard Theme Transformation

**Phase**: 18_THEME  
**Title**: Complete Dashboard Theme Transformation  
**Lead Agent**: Principal Design Systems Architect & UI/UX Engineer  
**Status**: COMPLETE  
**Governance Directory**: `NEWCHAGES/PHASE18_THEME/`  
**Date**: 2026-11-15  

---

## 1. Objectives & Scope

Transform the entire NovaNest application from its legacy dark Emerald Green cockpit aesthetic into a premium, modern, clean, enterprise-grade business intelligence dashboard conforming strictly to the official NovaNest colour palette:

### Official NovaNest Colour Palette:
1. **Background**: `#F8FAFC` (`slate-50`)
2. **Primary (Navigation, Headers)**: `#2563EB` (`blue-600`)
3. **Accent (Buttons, Alerts, Highlights)**: `#F97316` (`orange-500`)
4. **Main Text**: `#1E293B` (`slate-800`)

### Additional Supporting Palette:
- **White Surface**: `#FFFFFF`
- **Secondary Background**: `#F1F5F9` (`slate-100`)
- **Border**: `#E2E8F0` (`slate-200`)
- **Muted Text**: `#64748B` (`slate-500`)
- **Success**: `#16A34A` (`green-600`)
- **Warning**: `#F59E0B` (`amber-500`)
- **Error**: `#DC2626` (`red-600`)
- **Primary Hover**: `#1D4ED8` (`blue-700`)
- **Accent Hover**: `#EA580C` (`orange-600`)

### Scope of Changes:
1. **Global Design System**:
   - Update CSS custom properties in `frontend/src/index.css`.
   - Update Tailwind configuration in `frontend/tailwind.config.js`.
   - Update `ThemeContext.tsx` to make the official enterprise theme default and remove the legacy emerald green theme.
2. **Top Navigation (`HeaderNav.tsx`)**:
   - Crisp white background (`#FFFFFF`), light slate border (`#E2E8F0`), deep slate wordmark (`#1E293B`), royal blue accents (`#2563EB`), and semantic status indicators.
3. **Sidebar Navigation (`Sidebar.tsx`)**:
   - Clean white background (`#FFFFFF`), light slate border (`#E2E8F0`), deep slate typography (`#1E293B`), royal blue icons (`#2563EB`), active light blue background (`#EFF6FF`) with royal blue pill (`#2563EB`).
4. **Executive Overview & KPI Cards (`KpiCard.tsx`, `ExecutiveOverviewView.tsx`)**:
   - White card surfaces, light slate borders, subtle shadows, deep slate typography, royal blue KPI metrics, and vibrant orange alert accents.
5. **All 9 Analytics Views**:
   - Executive Overview, Customer Intelligence, Restaurant Intelligence, Operations Intelligence, Financial Intelligence, Decision Intelligence, Decision Simulator, Command Center, AI Business Copilot.
6. **Charts & Visualizations**:
   - Primary series: `#2563EB`, Secondary: `#F97316`, Tertiary: `#0EA5E9`.
   - Positive: `#16A34A`, Negative: `#DC2626`, Neutral: `#64748B`.
   - Transparent/white backgrounds with slate-200 gridlines and slate-800 labels.
7. **AI Business Copilot & Chatbot (`ExecutiveAiCopilot.tsx`, `FloatingChatbot.tsx`)**:
   - White chat interface, royal blue user bubbles, light slate assistant response cards, vibrant orange action triggers, deep slate text.
8. **Streamlit Multi-Page Dashboard**:
   - Streamlit `.streamlit/config.toml` and `streamlit_app/styles/theme.css` aligned to official palette.
9. **Power BI Theme**:
   - Create `powerbi/novanest_theme.json` and apply to `NovaNest.pbix` with full backup preservation.
10. **Testing & Verification**:
    - Vite production build, regression suites, responsive testing, and high-resolution visual evidence capture.

---

## 2. Work Breakdown Structure

- [ ] **Milestone 1: Centralized Design Tokens & Tailwind Configuration**
- [ ] **Milestone 2: Navigation & Chrome Transformation (HeaderNav & Sidebar)**
- [ ] **Milestone 3: Core Components (KpiCard, GlobalFilterBar, SectionHeader, StatusBadge)**
- [ ] **Milestone 4: Executive Overview & Analytical Views Theming**
- [ ] **Milestone 5: Chart & Data Visualization Color Harmonization**
- [ ] **Milestone 6: AI Business Copilot & Floating Chatbot Restyling**
- [ ] **Milestone 7: Streamlit Theme Integration & Deployment**
- [ ] **Milestone 8: Power BI Theme JSON Creation & PBIX Integration**
- [ ] **Milestone 9: Legacy Theme Elimination & Color Audit**
- [ ] **Milestone 10: Production Compilation, Testing & Visual Capture**
- [ ] **Milestone 11: Governance Documentation & Master Registers Update**
