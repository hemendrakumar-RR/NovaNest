"""
Phase 5 — Natural Language to SQL (NL2SQL) Fallback Engine
----------------------------------------------------------
Translates natural language to SQL. Uses pattern matching templates
as a robust fallback when an external LLM provider is unavailable.
"""

import re

# Pre-defined templates mapping intent regex to safe SQL
SQL_TEMPLATES = [
    {
        "pattern": r"(?:which|what)?\s*restaurants?.*(?:highest|worst|most)?\s*cancellation.*rate|highest cancellation.*restaurant|cancellation.*by restaurant",
        "sql": "SELECT r.restaurant_name, COUNT(o.order_id) as total_orders, SUM(CASE WHEN o.order_status = 'Cancelled' THEN 1 ELSE 0 END) as cancelled_orders, ROUND(SUM(CASE WHEN o.order_status = 'Cancelled' THEN 1.0 ELSE 0.0 END) / COUNT(o.order_id) * 100, 2) as cancel_rate_pct FROM orders o JOIN restaurants r ON o.restaurant_id = r.restaurant_id GROUP BY r.restaurant_name HAVING total_orders >= 10 ORDER BY cancel_rate_pct DESC LIMIT 10;"
    },
    {
        "pattern": r"(?:which|what)?\s*restaurants?.*(?:need attention|underperform|critical|at risk|lowest rating|worst rating)",
        "sql": "SELECT r.restaurant_name, r.city, r.avg_rating, COUNT(o.order_id) as total_orders, SUM(CASE WHEN o.order_status = 'Cancelled' THEN 1 ELSE 0 END) as cancelled_orders, ROUND(SUM(CASE WHEN o.order_status = 'Cancelled' THEN 1.0 ELSE 0.0 END) / COUNT(o.order_id) * 100, 2) as cancel_rate_pct FROM orders o JOIN restaurants r ON o.restaurant_id = r.restaurant_id GROUP BY r.restaurant_id, r.restaurant_name, r.city, r.avg_rating HAVING total_orders >= 10 AND CASE WHEN r.avg_rating < 3.8 THEN 1 WHEN cancel_rate_pct > 5.0 THEN 1 ELSE 0 END = 1 ORDER BY cancel_rate_pct DESC, r.avg_rating ASC LIMIT 10;"
    },
    {
        "pattern": r"top (\d+)\s+restaurants",
        "sql": "SELECT r.restaurant_name, COUNT(o.order_id) as total_orders FROM orders o JOIN restaurants r ON o.restaurant_id = r.restaurant_id GROUP BY r.restaurant_name ORDER BY total_orders DESC LIMIT {0};"
    },
    {
        "pattern": r"top\s+restaurants?.*revenue|highest revenue.*restaurant",
        "sql": "SELECT r.restaurant_name, ROUND(SUM(o.final_amount), 2) as total_revenue, COUNT(o.order_id) as total_orders FROM orders o JOIN restaurants r ON o.restaurant_id = r.restaurant_id WHERE o.order_status = 'Delivered' GROUP BY r.restaurant_name ORDER BY total_revenue DESC LIMIT 5;"
    },
    {
        "pattern": r"revenue by city|city.*highest revenue|highest revenue.*city",
        "sql": "SELECT r.city, ROUND(SUM(o.final_amount), 2) as total_revenue FROM orders o JOIN restaurants r ON o.restaurant_id = r.restaurant_id WHERE o.order_status = 'Delivered' GROUP BY r.city ORDER BY total_revenue DESC;"
    },
    {
        "pattern": r"total orders",
        "sql": "SELECT COUNT(*) as total_orders FROM orders;"
    },
    {
        "pattern": r"average delivery fee",
        "sql": "SELECT AVG(delivery_fee) as avg_delivery_fee FROM orders;"
    }
]

def generate_sql(user_input: str) -> str:
    """
    Attempts to map user input to a predefined SQL template.
    Returns SQL query if matched, else an empty string.
    """
    query = user_input.lower()
    
    for template in SQL_TEMPLATES:
        match = re.search(template["pattern"], query)
        if match:
            # If there are groups (like limit number), format the SQL
            if match.groups():
                return template["sql"].format(*match.groups())
            else:
                return template["sql"]
                
    # Fallback to a safe, default query if it looks like a revenue question
    if "revenue" in query:
        return "SELECT ROUND(SUM(final_amount), 2) as total_revenue FROM orders WHERE order_status = 'Delivered';"
        
    return ""
