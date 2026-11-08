# PHASE 04 — FINAL KPI AUDIT & CERTIFICATION REPORT
**Milestone: Rigorous Mathematical Audit of Core KPIs, Funnel Reality, & Cohort Mechanics**  
**Audit Timestamp:** 2026-11-08  
**Audit Scope:** `python/analytics/`, `datasets/analytics/`, `reports/kpi_cross_validation_report.md`, `tests/test_analytics.py`  
**Certification Status:** **AUDITED, CORRECTED & CERTIFIED**

---

## 1. Executive Summary & Audit Context
Following the completion of the Phase 4 analytics tier, an in-depth audit was conducted to resolve critical mathematical, terminology, and data-generator discrepancies. The audit resolved:
1. **Average Order Value (AOV)**: Dual definitions established: Net AOV (₹967.33 = Net Revenue / Completed Orders) vs Gross AOV (₹970.75 = GMV / Completed Orders).
2. **Contribution Margin & Estimated Profit**: Resolved numerator/denominator filter inconsistency across order statuses:
   - Realized Delivered Operating Profit: ₹10,953,031.58 on Delivered Net Revenue of ₹46,425,992.00 $\rightarrow$ **23.59%**.
   - Gross Booking Profit (all orders): ₹11,393,907.16 on Gross Final Amount of ₹48,281,651.00 $\rightarrow$ **23.60%**.
   - Resolved the previous 24.54% apples-to-oranges ratio (All Orders Profit / Delivered Revenue) and 24.52% row-level arithmetic mean.
3. **CLV Terminology**: Renamed to `Historical Realized Spend per Customer (Cumulative ARPU)` (₹9,285.20 realized / ₹9,656.33 gross), removing ungrounded "predictive lifetime value" claims.
4. **Rider Utilization Terminology**: Renamed to `Delivered Orders per Active Rider` (12.49 deliveries/rider; 12.00 completed deliveries/rider) due to fleet capacity and shift hours being unrecorded.
5. **Restaurant Performance Metrics**: Fully segregated into 5 dimensions: Customer Inflow Throughput (₹30,950.66), Food GMV (₹31,060.08), Merchant Food Payout (₹24,077.85), Platform Commission (₹6,982.23), and Order Volume (32.0 orders/restaurant).
6. **Marketing Funnel Reality**: Confirmed `app_events.csv` lacks timestamps and reflects independent random draws (`random.choice(event_types)`). Re-engineered `funnel_analysis.py` to evaluate **Unique-User Stage Reach** and **Event-Presence Overlap**, explicitly disabling chronological sequence/drop-off claims.
7. **Cohort Assignment**: Confirmed acquisition cohorts are anchored on **First Non-Cancelled Order Month**, isolating 11 cohorts with Month 0 = 100.0% and Month 1 average retention = 53.36%.
8. **Automated Test Expansion**: Expanded `tests/test_analytics.py` from 7 to 12 rigorous tests, validating empty datasets, zero denominators, missing values, and idempotency (12/12 passed in 2.88s).

---

## 2. Before vs After KPI Audit Table

| KPI ID | Reported Before Audit | Audited & Corrected After Audit | Unit | Before Value | After Value | Root Cause & Resolution |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **KPI-01** | Gross Merchandise Value | Gross Merchandise Value (GMV) | INR | ₹46,590,125.00 | ₹46,590,125.00 | Exact food item total on delivered non-cancelled orders. Unchanged. |
| **KPI-02** | Net Revenue | Net Revenue (Platform Inflow) | INR | ₹46,425,992.00 | ₹46,425,992.00 | Customer final payable on delivered orders. Unchanged. |
| **KPI-03** | Average Order Value | Average Order Value (Net AOV) | INR | ₹967.33 | ₹967.33 | Clarified Net AOV (₹967.33) vs Gross AOV (₹970.75 = GMV / 47,994). Both documented. |
| **KPI-04** | Take Rate | Take Rate | % | 22.48% | 22.48% | Realized Commission / Delivered GMV. Unchanged. |
| **KPI-05** | Total Orders Placed | Total Orders Placed | Count | 49,971 | 49,971 | Total orders placed across all statuses. Unchanged. |
| **KPI-06** | Completed Orders | Completed Orders | Count | 47,994 | 47,994 | Delivered orders fulfilled (96.04% completion). Unchanged. |
| **KPI-07** | Cancellation Rate | Cancellation Rate | % | 3.96% | 3.96% | 1,977 cancelled / 49,971 placed. Unchanged. |
| **KPI-08** | Delivery SLA Breach Rate| Delivery SLA Breach Rate | % | 32.26% | 32.26% | 16,120 deliveries > 45 mins. Unchanged. |
| **KPI-09** | Average Delivery Time | Average Delivery Time | Mins | 37.38 | 37.38 | Mean trip duration. Unchanged. |
| **KPI-10** | Rider Utilization | Delivered Orders per Active Rider| Deliveries/Rider | 12.49 | 12.49 | Renamed from "Utilization" to "Delivered Orders per Rider". Fleet capacity/shift data not in schema. |
| **KPI-11** | Restaurant Avg Revenue | Restaurant Avg Gross Revenue Throughput | INR | ₹30,950.66 | ₹30,950.66 | Net Revenue / 1,500. Differentiated from Food GMV (₹31,060.08) and Net Food Payout (₹24,077.85). |
| **KPI-12** | Contribution Margin Pct| Contribution Margin Percentage | % | 23.60% | **23.59%** | Corrected to Realized Delivered Profit (₹10.95M) / Net Revenue (₹46.43M). Gross booking margin is 23.60%. |
| **KPI-13** | Total Estimated Profit | Total Estimated Operating Profit| INR | ₹11,393,907.16 | **₹10,953,031.58** | Standardized to Realized Profit on Delivered Orders. (All orders gross booking profit is ₹11,393,907.16). |
| **KPI-14** | Repeat-Purchase Rate | Customer Repeat-Purchase Rate | % | 99.94% | 99.94% | 4,997 customers with >1 order. Strictly distinct from cohort retention decay. |
| **KPI-15** | Cohort Retention (M1) | Cohort Retention Rate (Month 1) | % | 53.36% | 53.36% | Anchored on first valid order month across 11 cohorts. Unchanged. |
| **KPI-16** | Customer Lifetime Value| Historical Realized Spend per Customer | INR | ₹9,656.33 | **₹9,285.20** | Renamed from "CLV" to "Historical Realized Spend / Cumulative ARPU". Value is ₹9,285.20 delivered (₹9,656.33 all placed). |

---

## 3. Detailed Audit Findings & Mathematical Proofs

### A. Average Order Value (AOV)
- **Mathematical Formula for Gross AOV**:
  $$\text{Gross AOV} = \frac{\text{GMV}}{\text{Completed Orders}} = \frac{46,590,125.00}{47,994} = ₹970.7486 \approx ₹970.75$$
- **Mathematical Formula for Net AOV**:
  $$\text{Net AOV} = \frac{\text{Net Revenue}}{\text{Completed Orders}} = \frac{46,425,992.00}{47,994} = ₹967.3291 \approx ₹967.33$$
- **Audit Decision**: The core metric is now formally designated as `Average Order Value (Net AOV)` in KPI-03, reflecting actual customer out-of-pocket spend per order. `Gross AOV` (₹970.75) is recorded in metadata and reports.

### B. Contribution Margin & Operating Profit Filter Reconciliation
- **The Prior Mismatch**:
  - Total Estimated Profit across all 49,971 orders = ₹11,393,907.16.
  - Net Revenue across 47,994 delivered orders = ₹46,425,992.00.
  - Dividing these two disparate subsets produced:
    $$\frac{11,393,907.16}{46,425,992.00} = 24.542\%$$
  - However, `kpi_engine.py` reported 23.60% because its denominator used `total final_amount` across all 49,971 orders:
    $$\frac{11,393,907.16}{48,281,651.00} = 23.5988\% \approx 23.60\%$$
- **The Realized Filter Reconciliation**:
  - Delivered Orders Realized Profit:
    $$\sum (\text{commission\_revenue} + \text{delivery\_fee} - 30.0) = ₹10,953,031.58$$
  - Delivered Orders Net Revenue:
    $$\sum \text{final\_amount} = ₹46,425,992.00$$
  - Realized Contribution Margin:
    $$\frac{10,953,031.58}{46,425,992.00} \times 100 = \mathbf{23.5925\% \approx 23.59\%}$$
- **Audit Decision**: KPI-12 is standardized to **23.59%** (Realized Contribution Margin on Delivered Orders) and KPI-13 is standardized to **₹10,953,031.58** (Realized Operating Profit). Both booking-level metrics (23.60% and ₹11.39M) are preserved and documented in notes.

### C. Customer Lifetime Value (CLV) Renaming & Methodological Boundaries
- **Prior Claim**: `Total Net Spend / Total Customers` = ₹9,656.33 labeled as "Customer Lifetime Value (Realized CLV)".
- **Audit Finding**: This metric represents historical cumulative average revenue per user (ARPU) over an 11-to-12 month historical window. Labeling it "Customer Lifetime Value" conflates historical spend with forward-looking actuarial lifetime value (which requires churn hazard functions, discount rates, and retention curves).
- **Audit Decision**: Renamed to `Historical Realized Spend per Customer (Cumulative ARPU)`.
  - Realized on Delivered Orders: $\frac{46,425,992.00}{5,000} = \mathbf{₹9,285.20}$.
  - Gross on All Placed Orders: $\frac{48,281,651.00}{5,000} = \mathbf{₹9,656.33}$.

### D. Rider Utilization Renaming
- **Prior Claim**: `Delivered Orders / Active Riders` = 12.49 labeled as "Rider Utilization".
- **Audit Finding**: In logistics engineering, "utilization" is a percentage: $\frac{\text{Active Trip Hours}}{\text{Available Shift Hours}} \times 100$. The dataset schema contains only `rider_id`, `rider_city`, and delivery timestamps, but no shift rosters or login hours.
- **Audit Decision**: Renamed to `Delivered Orders per Active Rider` with unit `Deliveries/Rider`.

### E. Restaurant Multi-Dimensional Performance
- **Throughput**: Customer cash inflow per restaurant = $\frac{46,425,992.00}{1,500} = ₹30,950.66$.
- **Food GMV**: Food catalogue sales per restaurant = $\frac{46,590,125.00}{1,500} = ₹31,060.08$.
- **Merchant Payout**: Net restaurant food earnings (GMV - Commission) = $\frac{36,116,778.42}{1,500} = ₹24,077.85$.
- **Platform Commission**: Commission captured per restaurant = $\frac{10,473,346.58}{1,500} = ₹6,982.23$.
- **Order Volume**: Orders per restaurant = $\frac{47,994}{1,500} = 32.0$ orders.

---

## 4. Clickstream Funnel Reality & Methodological Boundaries

- **Dataset Schema**: `app_events.csv` contains exactly: `event_id`, `customer_id`, `event_type`.
- **Generator Implementation**: `python/data generation/generate_app_events.py` lines 44-46 draw from `event_types` using `random.choice(event_types)` for 100,000 independent samples.
- **Methodological Rule Enforced**:
  - **No Chronological Sequence**: Timestamps do NOT exist. We cannot infer whether "Checkout" happened before or after "Add to Cart".
  - **No Temporal Conversion Funnel**: Step-by-step conversion drop-off cannot be claimed without temporal causality.
  - **Valid Analytical Scope**:
    - **Unique-User Stage Reach**: 4,835 users opened the app (96.7%), 4,818 viewed restaurants (96.36%), 4,826 viewed menus (96.52%), 4,836 added to cart (96.72%), 4,819 checked out (96.38%), and 4,817 completed an order (96.34%).
    - **Stage Co-occurrence**: 4,043 users (80.86%) logged at least one event in all 6 stages.
    - Exported: `datasets/analytics/app_funnel_summary.csv` and `datasets/analytics/app_event_overlap_matrix.csv`.

---

## 5. Five-Layer Validation Status Matrix

All 16 KPIs are formally segregated across 5 distinct status tiers:

| KPI ID | KPI Name | Python Exec | SQL Static | SQL Live | DAX Review | Power BI Runtime |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **KPI-01** | Gross Merchandise Value (GMV) | VALIDATED | VALIDATED | BLOCKED (No .env) | REVIEWED | PENDING |
| **KPI-02** | Net Revenue (Platform Inflow) | VALIDATED | VALIDATED | BLOCKED (No .env) | REVIEWED | PENDING |
| **KPI-03** | Average Order Value (Net AOV) | VALIDATED | VALIDATED | BLOCKED (No .env) | REVIEWED | PENDING |
| **KPI-04** | Take Rate | VALIDATED | VALIDATED | BLOCKED (No .env) | REVIEWED | PENDING |
| **KPI-05** | Total Orders Placed | VALIDATED | VALIDATED | BLOCKED (No .env) | REVIEWED | PENDING |
| **KPI-06** | Completed Orders | VALIDATED | VALIDATED | BLOCKED (No .env) | REVIEWED | PENDING |
| **KPI-07** | Cancellation Rate | VALIDATED | VALIDATED | BLOCKED (No .env) | REVIEWED | PENDING |
| **KPI-08** | Delivery SLA Breach Rate | VALIDATED | VALIDATED | BLOCKED (No .env) | REVIEWED | PENDING |
| **KPI-09** | Average Delivery Time | VALIDATED | VALIDATED | BLOCKED (No .env) | REVIEWED | PENDING |
| **KPI-10** | Delivered Orders per Active Rider | VALIDATED | VALIDATED | BLOCKED (No .env) | REVIEWED | PENDING |
| **KPI-11** | Restaurant Avg Revenue Throughput | VALIDATED | VALIDATED | BLOCKED (No .env) | REVIEWED | PENDING |
| **KPI-12** | Contribution Margin Percentage | VALIDATED | VALIDATED | BLOCKED (No .env) | REVIEWED | PENDING |
| **KPI-13** | Total Estimated Operating Profit | VALIDATED | VALIDATED | BLOCKED (No .env) | REVIEWED | PENDING |
| **KPI-14** | Customer Repeat-Purchase Rate | VALIDATED | VALIDATED | BLOCKED (No .env) | REVIEWED | PENDING |
| **KPI-15** | Cohort Retention Rate (Month 1 Avg)| VALIDATED | VALIDATED | BLOCKED (No .env) | REVIEWED | PENDING |
| **KPI-16** | Cumulative ARPU / Historical Spend | VALIDATED | VALIDATED | BLOCKED (No .env) | REVIEWED | PENDING |

---

## 6. Automated Testing Certification

- Test File: [tests/test_analytics.py](file:///c:/Users/madha/OneDrive/Documents/NovaNest-main/tests/test_analytics.py)
- Execution Command: `python -m unittest tests/test_analytics.py -v`
- Execution Result: **12 / 12 PASSED in 2.880s**
- Zero failures, zero warnings, zero regressions.

*Phase 04 Final Audit Certified by NovaNest Analytics Governance on 2026-11-08.*
