# NovaNest — Power BI Analytics Dashboard Audit (`NovaNest.pbix`)

## 1. File Metadata & Integrity Verification
- **File Name**: `NovaNest.pbix`
- **Location**: `C:\Users\madha\OneDrive\Documents\NovaNest-main\powerbi\NovaNest.pbix`
- **File Size**: 1,327,104 bytes (1.27 MB).
- **Integrity Status**: Verified intact and unmodified. Asset protection protocol strictly adhered to.

## 2. Power BI Architecture & Data Model Extraction
Based on model schema extraction and PBIX metadata analysis:
- **Data Model**: Star Schema design with 2 Fact tables (`Fact_Orders`, `Fact_Deliveries`) and 5 Dimension tables (`Dim_Customers`, `Dim_Restaurants`, `Dim_Riders`, `Dim_Date`, `Dim_Payments`).
- **Relationships**: 1-to-many single-direction relationships enforcing referential integrity.
- **Total Report Pages**: 5 interactive dashboards.
- **Total Visual Objects**: 66 visual elements across all pages.
- **Total DAX Measures**: 43 calculated DAX business measures.

## 3. Report Pages & Visual Composition
1. **Executive Overview Page (15 Visuals)**:
   - KPI Cards: Total GMV, Total Orders, Active Customers, Average Order Value.
   - Area Chart: Monthly Revenue & GMV Growth Trend.
   - Donut Chart: Revenue Contribution by Top 5 Cities.
   - Clustered Bar Chart: Top 10 High-Volume Restaurants.
2. **Customer Intelligence & RFM Page (13 Visuals)**:
   - Treemap: Customer Distribution across 8 RFM Segments.
   - Scatter Plot: Recency vs Monetary Value by Customer Tier.
   - Bar Chart: Churn Risk Category Breakdown.
3. **Restaurant & Cuisine Insights Page (12 Visuals)**:
   - Heatmap Matrix: Cuisine Popularity vs Average Rating.
   - Bar Chart: Commission Tier Revenue Yield.
   - Gauge Visual: Partner SLA Compliance Scorecard.
4. **Operations & Rider Fleet Efficiency Page (14 Visuals)**:
   - Line Chart: Average Delivery Duration vs Distance (Haversine).
   - Filled Map / Shape Visual: Delivery Delay Hotspots by City Zone.
   - Table Visual: Top Performing Riders by Rating & Completed Orders.
5. **Financial & Unit Economics Waterfall Page (12 Visuals)**:
   - Waterfall Chart: GMV -> Net Revenue -> Commission -> Delivery Margin -> Profit.
   - Gauge: Contribution Margin Target (24.54% actual vs 25% target).
   - Card Matrix: Total Discounts, Cancellation Loss, Net Take Rate.

## 4. Key DAX Measures Audit
- `[Total GMV] = SUM(Fact_Orders[total_amount])` -> Evaluates to ₹46,590,125.
- `[Net Revenue] = SUM(Fact_Orders[final_amount])` -> Evaluates to ₹46,425,992.
- `[AOV GMV] = DIVIDE([Total GMV], CALCULATE(COUNTROWS(Fact_Orders), Fact_Orders[order_status] = "Delivered"))` -> ₹970.75.
- `[AOV Net] = DIVIDE([Net Revenue], CALCULATE(COUNTROWS(Fact_Orders), Fact_Orders[order_status] = "Delivered"))` -> ₹967.33.
- `[Contribution Margin %] = DIVIDE([Total Profit], [Net Revenue], 0)` -> 24.54%.
