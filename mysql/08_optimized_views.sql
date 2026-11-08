-- ======================================================================
-- NOVANEST MYSQL ANALYTICS — REUSABLE ANALYTICAL VIEWS
-- File: 08_optimized_views.sql
-- Database: novanest_db
-- ======================================================================

-- ======================================================================
-- 1. VIEW: Customer RFM Segmentation
-- ======================================================================
CREATE OR REPLACE VIEW vw_customer_rfm AS
SELECT
    c.customer_id,
    c.customer_name,
    c.city,
    c.persona,
    c.subscription_type,
    DATEDIFF(CURDATE(), MAX(o.order_datetime)) AS recency_days,
    COUNT(o.order_id) AS frequency,
    COALESCE(SUM(o.final_amount), 0) AS monetary,
    ROUND(COALESCE(AVG(o.final_amount), 0), 2) AS aov,
    CASE
        WHEN COUNT(o.order_id) >= 20 AND SUM(o.final_amount) >= 15000 THEN 'Champions'
        WHEN COUNT(o.order_id) >= 10 THEN 'Loyal Customers'
        WHEN COUNT(o.order_id) >= 5 THEN 'Potential Loyalists'
        WHEN COUNT(o.order_id) = 1 THEN 'New / At Risk'
        ELSE 'Occasional'
    END AS rfm_segment
FROM customers c
LEFT JOIN orders_table o ON c.customer_id = o.customer_id
GROUP BY c.customer_id, c.customer_name, c.city, c.persona, c.subscription_type;

-- ======================================================================
-- 2. VIEW: Monthly Cohort Retention
-- ======================================================================
CREATE OR REPLACE VIEW vw_monthly_cohort_retention AS
SELECT
    DATE_FORMAT(c.signup_date, '%Y-%m') AS cohort_month,
    DATE_FORMAT(o.order_datetime, '%Y-%m') AS order_month,
    TIMESTAMPDIFF(MONTH, c.signup_date, o.order_datetime) AS cohort_period_months,
    COUNT(DISTINCT o.customer_id) AS active_customers,
    ROUND(SUM(o.final_amount), 2) AS cohort_revenue
FROM customers c
JOIN orders_table o ON c.customer_id = o.customer_id
WHERE o.order_status = 'Delivered'
GROUP BY cohort_month, order_month, cohort_period_months;

-- ======================================================================
-- 3. VIEW: Unit Economics & Order Margin
-- ======================================================================
CREATE OR REPLACE VIEW vw_unit_economics AS
SELECT
    o.order_id,
    o.order_datetime,
    o.order_status,
    r.city AS restaurant_city,
    r.restaurant_name,
    o.order_amount,
    o.discount_amount,
    o.delivery_fee,
    o.final_amount,
    r.commission_percentage,
    ROUND((o.order_amount * r.commission_percentage) / 100.0, 2) AS commission_revenue,
    ROUND(((o.order_amount * r.commission_percentage) / 100.0) + o.delivery_fee, 2) AS gross_inflow,
    30.00 AS estimated_fulfillment_cost,
    ROUND(((o.order_amount * r.commission_percentage) / 100.0) + o.delivery_fee - 30.00, 2) AS estimated_profit,
    ROUND(((((o.order_amount * r.commission_percentage) / 100.0) + o.delivery_fee - 30.00) / o.final_amount) * 100.0, 2) AS profit_margin_pct
FROM orders_table o
JOIN restaurants r ON o.restaurant_id = r.restaurant_id;

-- ======================================================================
-- 4. VIEW: Rider Performance & Efficiency
-- ======================================================================
CREATE OR REPLACE VIEW vw_rider_efficiency AS
SELECT
    rd.rider_id,
    rd.rider_name,
    rd.city,
    rd.vehicle_type,
    rd.shift_type,
    COUNT(d.delivery_id) AS total_deliveries,
    ROUND(AVG(d.distance_km), 2) AS avg_distance_km,
    ROUND(AVG(d.delivery_duration), 2) AS avg_duration_minutes,
    ROUND(AVG(d.distance_km / (d.delivery_duration / 60.0)), 2) AS avg_speed_kph,
    ROUND(100.0 * SUM(CASE WHEN d.delivery_duration > 45 THEN 1 ELSE 0 END) / COUNT(d.delivery_id), 2) AS delay_percentage
FROM riders rd
JOIN deliveries d ON rd.rider_id = d.rider_id
GROUP BY rd.rider_id, rd.rider_name, rd.city, rd.vehicle_type, rd.shift_type;

-- ======================================================================
-- 5. VIEW: Restaurant Partner Performance
-- ======================================================================
CREATE OR REPLACE VIEW vw_restaurant_performance AS
SELECT
    r.restaurant_id,
    r.restaurant_name,
    r.city,
    r.restaurant_type,
    r.cuisine_type,
    r.avg_rating AS listed_rating,
    ROUND(AVG(rr.restaurant_rating), 2) AS customer_avg_rating,
    COUNT(o.order_id) AS total_orders,
    ROUND(SUM(o.final_amount), 2) AS gross_revenue,
    ROUND(AVG(o.final_amount), 2) AS aov,
    ROUND(SUM(o.order_amount * r.commission_percentage / 100.0), 2) AS total_commission_earned
FROM restaurants r
LEFT JOIN orders_table o ON r.restaurant_id = o.restaurant_id
LEFT JOIN ratings_reviews rr ON o.order_id = rr.order_id
GROUP BY r.restaurant_id, r.restaurant_name, r.city, r.restaurant_type, r.cuisine_type, r.avg_rating;

-- ======================================================================
-- 6. VIEW: Monthly Revenue & Growth Dynamics
-- ======================================================================
CREATE OR REPLACE VIEW vw_monthly_revenue AS
WITH monthly_agg AS (
    SELECT
        DATE_FORMAT(order_datetime, '%Y-%m') AS month,
        COUNT(*) AS total_orders,
        COUNT(DISTINCT customer_id) AS active_customers,
        ROUND(SUM(final_amount), 2) AS revenue,
        ROUND(AVG(final_amount), 2) AS aov,
        ROUND(SUM(discount_amount), 2) AS total_discounts
    FROM orders_table
    WHERE order_status = 'Delivered'
    GROUP BY month
)
SELECT
    month,
    total_orders,
    active_customers,
    revenue,
    aov,
    total_discounts,
    LAG(revenue) OVER(ORDER BY month) AS previous_month_revenue,
    ROUND(
        100.0 * (revenue - LAG(revenue) OVER(ORDER BY month)) / LAG(revenue) OVER(ORDER BY month),
        2
    ) AS mom_growth_pct
FROM monthly_agg;

-- ======================================================================
-- 7. VIEW: Customer Lifetime Value (CLV)
-- ======================================================================
CREATE OR REPLACE VIEW vw_customer_lifetime_value AS
SELECT
    c.customer_id,
    c.customer_name,
    c.city,
    c.persona,
    c.signup_date,
    DATEDIFF(MAX(o.order_datetime), c.signup_date) AS customer_tenure_days,
    COUNT(o.order_id) AS total_orders,
    ROUND(SUM(o.final_amount), 2) AS total_spent,
    ROUND(AVG(o.final_amount), 2) AS aov,
    ROUND(SUM(o.final_amount * 0.20), 2) AS estimated_clv_contribution,
    CASE
        WHEN SUM(o.final_amount) >= 20000 THEN 'Platinum Tier'
        WHEN SUM(o.final_amount) >= 10000 THEN 'Gold Tier'
        WHEN SUM(o.final_amount) >= 4000 THEN 'Silver Tier'
        ELSE 'Bronze Tier'
    END AS clv_tier
FROM customers c
JOIN orders_table o ON c.customer_id = o.customer_id
GROUP BY c.customer_id, c.customer_name, c.city, c.persona, c.signup_date;

