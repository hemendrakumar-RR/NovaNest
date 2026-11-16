"""
NovaNest Platform Full Suite Automated Verification
Tests:
1. Backend REST API Endpoints (FastAPI on http://127.0.0.1:8000)
2. Frontend Web Server & Build Artifacts (React + Vite)
3. Streamlit Analytics Hub (http://localhost:8501)
4. Core Data Store & Asset Integrity
"""

import sys
import os
import requests
import json
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

def test_api_endpoints():
    print("\n--- 1. Testing FastAPI REST API Endpoints ---")
    base_url = "http://127.0.0.1:8000"
    endpoints = [
        ("GET", "/api/health", None, ["status", "data_source", "datasets"]),
        ("GET", "/api/overview", None, ["kpis", "revenue_trend", "city_breakdown", "top_restaurants"]),
        ("GET", "/api/customer/overview", None, ["kpis", "rfm_segments", "clv_tiers", "churn_distribution", "cohort_retention"]),
        ("GET", "/api/customer/list?limit=5", None, None), # Returns list
        ("GET", "/api/customer/360/C000001", None, ["customer_id", "profile", "digital_twin", "order_history", "recommendations"]),
        ("GET", "/api/restaurant/overview", None, ["kpis", "health_distribution", "risk_distribution", "performance_matrix", "early_warnings"]),
        ("GET", "/api/operations/overview", None, ["kpis", "demand_forecast", "rider_allocation", "anomalies"]),
        ("GET", "/api/financial/overview", None, ["kpis", "unit_economics", "revenue_leakage", "promotions"]),
        ("POST", "/api/ai/ask", {"question": "What are the top 5 restaurants by revenue?"}, ["question", "route", "sql_query", "sql_valid", "answer"]),
        ("GET", "/api/decision/actions", None, None), # Returns list
        ("POST", "/api/decision/simulate", {
            "commission_change_pct": 2.0,
            "delivery_fee_change_pct": 5.0,
            "discount_change_pct": -5.0,
            "demand_change_pct": 8.0,
            "churn_reduction_pct": 3.0,
            "aov_change_pct": 4.0
        }, None),
        ("GET", "/api/digital-twin/state", None, ["vitality_index", "pillars", "systemic_alerts", "impact_ripple_chains"])
    ]

    all_passed = True
    http = requests.Session()
    api_key = os.getenv("NOVANEST_API_KEY") or os.getenv("NOVANEST_ADMIN_KEY") or ""
    if api_key:
        http.headers.update({"X-API-Key": api_key})
    for method, path, payload, required_keys in endpoints:
        url = f"{base_url}{path}"
        try:
            if method == "GET":
                resp = http.get(url, timeout=25)
            else:
                resp = http.post(url, json=payload, timeout=25)
            
            if resp.status_code == 200:
                data = resp.json()
                if required_keys is None:
                    # Valid list or dictionary response
                    if isinstance(data, (list, dict)) and len(data) > 0:
                        print(f"  [PASS] {method} {path} (HTTP 200, valid payload with {len(data)} items)")
                    else:
                        print(f"  [FAIL] {method} {path} (Empty payload returned)")
                        all_passed = False
                else:
                    missing = [k for k in required_keys if k not in data]
                    if not missing:
                        print(f"  [PASS] {method} {path} (HTTP 200, valid schema: {required_keys})")
                    else:
                        print(f"  [FAIL] {method} {path} (Missing keys: {missing})")
                        all_passed = False
            else:
                print(f"  [FAIL] {method} {path} (HTTP {resp.status_code})")
                all_passed = False
        except Exception as e:
            print(f"  [FAIL] {method} {path} (Error: {e})")
            all_passed = False
            
    return all_passed

def test_frontend_server_and_build():
    print("\n--- 2. Testing Frontend Web Server & Build ---")
    all_passed = True
    try:
        resp = requests.get("http://localhost:5173", timeout=5)
        if resp.status_code == 200 and "novanest" in resp.text.lower():
            print("  [PASS] Vite Dev Server at http://localhost:5173 (HTTP 200, NOVANEST branding found)")
        else:
            print(f"  [FAIL] Vite Dev Server returned HTTP {resp.status_code}")
            all_passed = False
    except Exception as e:
        print(f"  [FAIL] Vite Dev Server check failed: {e}")
        all_passed = False

    dist_index = BASE_DIR / "frontend" / "dist" / "index.html"
    if dist_index.exists():
        print(f"  [PASS] Production build verified at {dist_index}")
    else:
        print(f"  [WARN] Production build dist/index.html not found")
        
    return all_passed

def test_streamlit_app():
    print("\n--- 3. Testing Streamlit Hub ---")
    all_passed = True
    try:
        resp = requests.get("http://localhost:8501/_stcore/health", timeout=5)
        if resp.status_code == 200:
            print("  [PASS] Streamlit Server at http://localhost:8501 (Health check HTTP 200)")
        else:
            print(f"  [FAIL] Streamlit returned HTTP {resp.status_code}")
            all_passed = False
    except Exception as e:
        print(f"  [FAIL] Streamlit server check failed: {e}")
        all_passed = False
    return all_passed

def test_dataset_and_assets():
    print("\n--- 4. Testing Datasets & Protected Assets ---")
    all_passed = True
    pbix = BASE_DIR / "powerbi" / "NovaNest.pbix"
    if pbix.exists() and pbix.stat().st_size > 5_000_000:
        print(f"  [PASS] Protected Asset preserved: NovaNest.pbix ({pbix.stat().st_size:,} bytes)")
    else:
        print(f"  [FAIL] NovaNest.pbix missing or corrupted")
        all_passed = False
        
    cleaned_dir = BASE_DIR / "datasets" / "cleaned"
    if cleaned_dir.exists() and len(list(cleaned_dir.glob("*.csv"))) >= 5:
        print(f"  [PASS] Cleaned datasets verified ({len(list(cleaned_dir.glob('*.csv')))} tables)")
    else:
        print("  [FAIL] Cleaned datasets missing")
        all_passed = False
        
    engineered_dir = BASE_DIR / "datasets" / "engineered"
    if engineered_dir.exists() and len(list(engineered_dir.glob("*.csv"))) >= 3:
        print(f"  [PASS] Engineered datasets verified ({len(list(engineered_dir.glob('*.csv')))} tables)")
    else:
        print("  [FAIL] Engineered datasets missing")
        all_passed = False

    return all_passed

if __name__ == "__main__":
    t1 = test_api_endpoints()
    t2 = test_frontend_server_and_build()
    t3 = test_streamlit_app()
    t4 = test_dataset_and_assets()
    
    if t1 and t2 and t3 and t4:
        print("\n=======================================================")
        print("ALL VERIFICATION CHECKS PASSED: PLATFORM HEALTHY & READY")
        print("=======================================================")
        sys.exit(0)
    else:
        print("\n=======================================================")
        print("SOME VERIFICATION CHECKS FAILED - CHECK DETAILS ABOVE")
        print("=======================================================")
        sys.exit(1)
