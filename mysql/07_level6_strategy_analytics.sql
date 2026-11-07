-- ======================================================================
-- NOVANEST MYSQL ANALYTICS — LEVEL 6: STRATEGY ANALYTICS
-- Retention, Churn, Cohort, RFM, and Funnel Analytics
-- Database: novanest_db
-- ======================================================================

-- ======================================================================
-- 🥇 RETENTION ANALYSIS
-- ======================================================================

-- Query 1: Repeat Customer Analysis
-- Business Question: How many customers came back and ordered again?
SELECT
customer_id,
COUNT(*) AS total_orders
FROM orders_table
GROUP BY customer_id
HAVING total_orders > 1
ORDER BY total_orders DESC;

-- Query 2: Retention Percentage
-- Business Question: How many customers are retained (ordered more than once)?
WITH customer_order_summary AS (
    SELECT
        customer_id,
        COUNT(*) AS total_orders
    FROM orders_table
    GROUP BY customer_id
)
SELECT
    ROUND(
        100.0 * COUNT(CASE WHEN total_orders > 1 THEN 1 END) / COUNT(*),
        2
    ) AS retention_rate
FROM customer_order_summary;

-- Query 3: One-time vs Repeat Customers
WITH customer_order_summary AS (
    SELECT
        customer_id,
        COUNT(*) AS total_orders
    FROM orders_table
    GROUP BY customer_id
)
SELECT
    CASE
        WHEN total_orders = 1 THEN 'One Time'
        ELSE 'Repeat'
    END AS customer_type,
    COUNT(*) AS customers
FROM customer_order_summary
GROUP BY customer_type;

-- ======================================================================
-- 🥈 CHURN ANALYSIS
-- ======================================================================

-- Query 4: Inactive / One-Time Customers
-- Business Question: Which customers ordered only once and dropped off?
SELECT
customer_id
FROM orders_table
GROUP BY customer_id
HAVING COUNT(*) = 1;

-- Query 5: Churn Percentage
-- Business Question: What percentage of customers churned after a single order?
WITH customer_order_summary AS (
    SELECT
        customer_id,
        COUNT(*) AS total_orders
    FROM orders_table
    GROUP BY customer_id
)
SELECT
    ROUND(
        100.0 * COUNT(CASE WHEN total_orders = 1 THEN 1 END) / COUNT(*),
        2
    ) AS churn_rate
FROM customer_order_summary;

-- Query 6: Churn by Persona
SELECT
c.persona,
COUNT(*) AS churned_customers
FROM customers c
JOIN (
    SELECT
        customer_id
    FROM orders_table
    GROUP BY customer_id
    HAVING COUNT(*) = 1
) t
ON c.customer_id = t.customer_id
GROUP BY c.persona
ORDER BY churned_customers DESC;

-- ======================================================================
-- 🥉 COHORT ANALYSIS
-- ======================================================================

-- Query 7: Customer Signup Cohorts
SELECT
DATE_FORMAT(signup_date, '%Y-%m') AS cohort_month,
COUNT(*) AS customers
FROM customers
GROUP BY cohort_month
ORDER BY cohort_month;

-- Query 8: Monthly Revenue Cohorts
SELECT
DATE_FORMAT(order_datetime, '%Y-%m') AS month,
SUM(final_amount) AS revenue
FROM orders_table
GROUP BY month
ORDER BY month;

-- Query 9: Average Revenue Per Month
SELECT
DATE_FORMAT(order_datetime, '%Y-%m') AS month,
ROUND(AVG(final_amount), 2) AS avg_revenue
FROM orders_table
GROUP BY month;

-- Query 10: Monthly Customer Growth
SELECT
DATE_FORMAT(signup_date, '%Y-%m') AS month,
COUNT(*) AS new_customers
FROM customers
GROUP BY month
ORDER BY month;

-- ======================================================================
-- 🏅 RFM ANALYSIS (Recency, Frequency, Monetary)
-- ======================================================================

-- Query 11: Base RFM Metrics per Customer
SELECT
customer_id,
DATEDIFF(CURDATE(), MAX(order_datetime)) AS recency,
COUNT(*) AS frequency,
SUM(final_amount) AS monetary
FROM orders_table
GROUP BY customer_id
ORDER BY monetary DESC;

-- Query 12: Top 20 Most Valuable Customers
SELECT
customer_id,
SUM(final_amount) AS spending
FROM orders_table
GROUP BY customer_id
ORDER BY spending DESC
LIMIT 20;

-- Query 13: Customer Frequency Segments (VIP, Regular, Occasional)
SELECT
customer_id,
COUNT(*) AS frequency,
CASE
    WHEN COUNT(*) >= 20 THEN 'VIP'
    WHEN COUNT(*) >= 10 THEN 'Regular'
    ELSE 'Occasional'
END AS segment
FROM orders_table
GROUP BY customer_id;

-- ======================================================================
-- 🏅 FUNNEL ANALYSIS (App Clickstream Conversion)
-- ======================================================================

-- Query 14: Total Funnel Event Counts
SELECT
event_type,
COUNT(*) AS total_events
FROM app_events
GROUP BY event_type
ORDER BY total_events DESC;

-- Query 15: Funnel Conversion Percentage
SELECT
event_type,
COUNT(*) AS total_events,
ROUND(
    100.0 * COUNT(*) / SUM(COUNT(*)) OVER(),
    2
) AS percentage
FROM app_events
GROUP BY event_type;

-- Query 16: Unique Customers Per Funnel Stage
SELECT
event_type,
COUNT(DISTINCT customer_id) AS unique_customers
FROM app_events
GROUP BY event_type;
