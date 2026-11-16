"""
NovaNest Platform — Comprehensive CI/CD Pipeline Execution Harness
------------------------------------------------------------------
Automates and validates all 5 CI pipeline stages locally:
1. Backend CI (Python unit tests, API contracts, RBAC, MySQL integration)
2. AI Platform CI (5 domain agents, Master Orchestrator, memory, SSE streaming)
3. Frontend CI (Oxlint, TypeScript compile, Vite production bundle, Nginx config)
4. Docker CI (Docker Compose dev & prod config validation, container healthchecks)
5. Security CI (SQL AST injection defense, secret scanning, RBAC enforcement)

Generates machine-readable JUnit XML reports in `test-results/` and
a consolidated `test-results/ci-summary.json`.
"""

import json
import os
import re
import subprocess
import sys
import time
import unittest
import xml.etree.ElementTree as ET
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
RESULTS_DIR = PROJECT_ROOT / "test-results"
RESULTS_DIR.mkdir(parents=True, exist_ok=True)

# Add paths
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))
if str(PROJECT_ROOT / "python") not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT / "python"))


def get_docker_cmd():
    """Locate docker executable."""
    paths = [
        "docker",
        r"C:\Users\madha\AppData\Local\Programs\DockerDesktop\resources\bin\docker.exe"
    ]
    for p in paths:
        try:
            res = subprocess.run([p, "--version"], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            if res.returncode == 0:
                return p
        except Exception:
            continue
    return "docker"


def run_unittest_suite(suite_names, suite_display_name, xml_filename):
    """Run specified unittest module names, capture results, and output JUnit XML."""
    loader = unittest.TestLoader()
    combined_suite = unittest.TestSuite()
    
    for name in suite_names:
        suite = loader.loadTestsFromName(name)
        combined_suite.addTests(suite)

    total_tests = combined_suite.countTestCases()
    print(f"\n======================================================================")
    print(f"▶ EXECUTING {suite_display_name} ({total_tests} tests)")
    print(f"======================================================================")
    
    start_time = time.time()
    runner = unittest.TextTestRunner(verbosity=1)
    result = runner.run(combined_suite)
    duration = time.time() - start_time
    
    passed = result.testsRun - len(result.failures) - len(result.errors) - len(result.skipped)
    failures = len(result.failures)
    errors = len(result.errors)
    skipped = len(result.skipped)

    # Generate JUnit XML
    ts = ET.Element("testsuite", {
        "name": suite_display_name,
        "tests": str(result.testsRun),
        "failures": str(failures),
        "errors": str(errors),
        "skipped": str(skipped),
        "time": f"{duration:.3f}"
    })
    
    # Track test cases
    for failure in result.failures:
        test_case = failure[0]
        err_msg = failure[1]
        tc = ET.SubElement(ts, "testcase", {
            "classname": test_case.__class__.__name__,
            "name": test_case._testMethodName,
            "time": "0.000"
        })
        f_el = ET.SubElement(tc, "failure", {"message": "Test failed"})
        f_el.text = err_msg

    for err in result.errors:
        test_case = err[0]
        err_msg = err[1]
        tc = ET.SubElement(ts, "testcase", {
            "classname": test_case.__class__.__name__,
            "name": getattr(test_case, "_testMethodName", str(test_case)),
            "time": "0.000"
        })
        e_el = ET.SubElement(tc, "error", {"message": "Test encountered error"})
        e_el.text = err_msg

    xml_path = RESULTS_DIR / xml_filename
    tree = ET.ElementTree(ts)
    ET.indent(tree, space="  ")
    tree.write(str(xml_path), encoding="utf-8", xml_declaration=True)
    
    print(f"  ✓ {suite_display_name} Result: {passed} passed, {failures} failed, {errors} errors, {skipped} skipped ({duration:.2f}s)")
    print(f"  ✓ JUnit XML report written to {xml_path.name}")
    
    return {
        "name": suite_display_name,
        "total": result.testsRun,
        "passed": passed,
        "failures": failures,
        "errors": errors,
        "skipped": skipped,
        "duration": round(duration, 3),
        "xml_report": str(xml_path),
        "success": result.wasSuccessful()
    }


def run_frontend_ci():
    """Execute Frontend static linting, TypeScript compile, Vite build, and Nginx config validation."""
    suite_display_name = "Frontend CI & Edge Router"
    xml_filename = "frontend-results.xml"
    print(f"\n======================================================================")
    print(f"▶ EXECUTING {suite_display_name}")
    print(f"======================================================================")
    
    start_time = time.time()
    steps = [
        {"name": "test_oxlint_static_analysis", "cmd": 'cmd /c "cd frontend && npx oxlint"'},
        {"name": "test_typescript_compilation", "cmd": 'cmd /c "cd frontend && npx tsc -b"'},
        {"name": "test_vite_production_build", "cmd": 'cmd /c "cd frontend && npm run build"'},
        {
            "name": "test_nginx_configuration",
            "cmd": f'$env:PATH += ";C:\\Users\\madha\\AppData\\Local\\Programs\\DockerDesktop\\resources\\bin"; docker exec novanest-frontend nginx -t',
            "powershell": True
        }
    ]
    
    passed = 0
    failures = 0
    ts = ET.Element("testsuite", {"name": suite_display_name})
    
    for s in steps:
        t0 = time.time()
        print(f"  Running {s['name']}...")
        if s.get("powershell"):
            proc = subprocess.run(["powershell", "-NoProfile", "-Command", s["cmd"]], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        else:
            proc = subprocess.run(s["cmd"], shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        t_step = time.time() - t0
        
        tc = ET.SubElement(ts, "testcase", {
            "classname": "FrontendValidation",
            "name": s["name"],
            "time": f"{t_step:.3f}"
        })
        
        if proc.returncode == 0:
            passed += 1
            print(f"    ✓ {s['name']} passed ({t_step:.2f}s)")
        else:
            failures += 1
            print(f"    ✗ {s['name']} failed with code {proc.returncode} ({t_step:.2f}s)")
            f_el = ET.SubElement(tc, "failure", {"message": f"Command failed: {proc.stderr[:100]}"})
            f_el.text = proc.stderr or proc.stdout
            
    duration = time.time() - start_time
    ts.set("tests", str(len(steps)))
    ts.set("failures", str(failures))
    ts.set("errors", "0")
    ts.set("skipped", "0")
    ts.set("time", f"{duration:.3f}")
    
    xml_path = RESULTS_DIR / xml_filename
    tree = ET.ElementTree(ts)
    ET.indent(tree, space="  ")
    tree.write(str(xml_path), encoding="utf-8", xml_declaration=True)
    
    print(f"  ✓ {suite_display_name} Result: {passed} passed, {failures} failed ({duration:.2f}s)")
    print(f"  ✓ JUnit XML report written to {xml_path.name}")
    
    return {
        "name": suite_display_name,
        "total": len(steps),
        "passed": passed,
        "failures": failures,
        "errors": 0,
        "skipped": 0,
        "duration": round(duration, 3),
        "xml_report": str(xml_path),
        "success": failures == 0
    }


def run_security_ci():
    """Execute Security CI: SQL AST injection checks, secret scanning, RBAC verification."""
    suite_display_name = "Security CI & Threat Modeling"
    xml_filename = "security-results.xml"
    print(f"\n======================================================================")
    print(f"▶ EXECUTING {suite_display_name}")
    print(f"======================================================================")
    
    start_time = time.time()
    ts = ET.Element("testsuite", {"name": suite_display_name})
    
    tests = []
    
    # Test 1: SQL AST Injection Defense
    t0 = time.time()
    try:
        from python.ai.analyst.sql_ast import validate_sql_ast
        ok1, _, _ = validate_sql_ast("DROP TABLE customers")
        ok2, _, _ = validate_sql_ast("SELECT * FROM customers WHERE id = 1; DELETE FROM orders")
        ok3, _, _ = validate_sql_ast("SELECT customer_id, name FROM customers LIMIT 10")
        ast_passed = (not ok1) and (not ok2) and ok3
        tests.append(("test_sql_ast_injection_defense", ast_passed, time.time() - t0, ""))
    except Exception as e:
        tests.append(("test_sql_ast_injection_defense", False, time.time() - t0, str(e)))

    # Test 2: Secret Scanning Audit
    t0 = time.time()
    patterns = [
        r'(?i)BEGIN\s+RSA\s+PRIVATE\s+KEY',
        r'(?i)AWS_SECRET_ACCESS_KEY\s*=\s*[\'"][A-Za-z0-9/+=]{40}[\'"]',
        r'(?i)ghp_[A-Za-z0-9]{36}',
    ]
    leaks = []
    for ext in ["*.py", "*.json", "*.yml", "*.yaml"]:
        for p in PROJECT_ROOT.glob(ext):
            if any(x in str(p) for x in [".git", "scratch", "test-results", ".gemini", "node_modules"]):
                continue
            try:
                content = p.read_text(encoding="utf-8", errors="ignore")
                for pat in patterns:
                    if re.search(pat, content):
                        leaks.append(f"{p.name}")
            except Exception:
                pass
    secret_passed = len(leaks) == 0
    tests.append(("test_secret_leak_detection", secret_passed, time.time() - t0, f"Leaks found: {leaks}" if leaks else ""))

    # Test 3: SQL Validator Keyword Blocking
    t0 = time.time()
    try:
        from python.ai.conversational.sql_validator import validate_sql
        val1 = validate_sql("DROP TABLE customers;")
        val2 = validate_sql("SELECT count(*) FROM orders;")
        sql_val_passed = (not val1) and val2
        tests.append(("test_sql_keyword_validator", sql_val_passed, time.time() - t0, ""))
    except Exception as e:
        tests.append(("test_sql_keyword_validator", False, time.time() - t0, str(e)))

    passed = 0
    failures = 0
    for name, success, t_step, err in tests:
        tc = ET.SubElement(ts, "testcase", {
            "classname": "SecurityValidation",
            "name": name,
            "time": f"{t_step:.3f}"
        })
        if success:
            passed += 1
            print(f"    ✓ {name} passed ({t_step:.2f}s)")
        else:
            failures += 1
            print(f"    ✗ {name} failed: {err} ({t_step:.2f}s)")
            f_el = ET.SubElement(tc, "failure", {"message": err or "Failed"})
            f_el.text = err

    duration = time.time() - start_time
    ts.set("tests", str(len(tests)))
    ts.set("failures", str(failures))
    ts.set("errors", "0")
    ts.set("skipped", "0")
    ts.set("time", f"{duration:.3f}")
    
    xml_path = RESULTS_DIR / xml_filename
    tree = ET.ElementTree(ts)
    ET.indent(tree, space="  ")
    tree.write(str(xml_path), encoding="utf-8", xml_declaration=True)
    
    print(f"  ✓ {suite_display_name} Result: {passed} passed, {failures} failed ({duration:.2f}s)")
    print(f"  ✓ JUnit XML report written to {xml_path.name}")
    
    return {
        "name": suite_display_name,
        "total": len(tests),
        "passed": passed,
        "failures": failures,
        "errors": 0,
        "skipped": 0,
        "duration": round(duration, 3),
        "xml_report": str(xml_path),
        "success": failures == 0
    }


def main():
    start_all = time.time()
    print("=" * 70)
    print("       NOVANEST CONTINUOUS INTEGRATION & AUTOMATED TESTING       ")
    print("                      Phase 06.12 Pipeline                       ")
    print("=" * 70)
    
    stages = []
    
    # ------------------------------------------------------------------
    # Stage 1: Backend CI
    # ------------------------------------------------------------------
    backend_suites = [
        "tests.run_all_tests",
        "tests.test_phase05_3_security_and_contracts",
        "tests.test_phase06_7_mysql_integration",
        "tests.test_phase06_10_acceptance_and_readiness",
        "tests.test_phase06_13_security_hardening",
    ]
    stages.append(run_unittest_suite(backend_suites, "Backend CI & Database Integration", "backend-results.xml"))

    # ------------------------------------------------------------------
    # Stage 2: AI Platform CI
    # ------------------------------------------------------------------
    ai_suites = [
        "tests.test_phase06_2_domain_agents",
        "tests.test_phase06_3_orchestrator",
        "tests.test_ask_novanest_ai_suite",
        "tests.test_phase07_ml_optimization",
        "tests.test_phase08_prescriptive_intelligence",
        "tests.test_phase09_executive_ui_and_parity",
    ]
    stages.append(run_unittest_suite(ai_suites, "AI Platform & Multi-Agent Intelligence CI", "ai-platform-results.xml"))

    # ------------------------------------------------------------------
    # Stage 3: Frontend CI
    # ------------------------------------------------------------------
    stages.append(run_frontend_ci())

    # ------------------------------------------------------------------
    # Stage 4: Docker CI
    # ------------------------------------------------------------------
    docker_suites = [
        "tests.test_phase06_11_2_docker_runtime",
        "tests.test_phase06_11_containerization",
        "tests.test_phase10_production_operations",
    ]
    stages.append(run_unittest_suite(docker_suites, "Docker CI, Observability & Container Runtime", "docker-results.xml"))

    # ------------------------------------------------------------------
    # Stage 5: Security CI
    # ------------------------------------------------------------------
    stages.append(run_security_ci())

    # ------------------------------------------------------------------
    # Consolidated CI Summary
    # ------------------------------------------------------------------
    total_duration = time.time() - start_all
    total_tests = sum(s["total"] for s in stages)
    total_passed = sum(s["passed"] for s in stages)
    total_failures = sum(s["failures"] for s in stages)
    total_errors = sum(s["errors"] for s in stages)
    total_skipped = sum(s["skipped"] for s in stages)
    overall_success = all(s["success"] for s in stages)
    
    summary = {
        "pipeline": "NovaNest CI/CD Automated Testing (Phase 06.12)",
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
        "total_duration_seconds": round(total_duration, 2),
        "overall_status": "PASSED" if overall_success else "FAILED",
        "metrics": {
            "total_tests": total_tests,
            "passed": total_passed,
            "failed": total_failures,
            "errors": total_errors,
            "skipped": total_skipped,
            "pass_rate_pct": round((total_passed / total_tests * 100), 2) if total_tests else 0
        },
        "stages": stages
    }
    
    summary_path = RESULTS_DIR / "ci-summary.json"
    with open(summary_path, "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2)
        
    print("\n" + "=" * 70)
    print("                    CI/CD PIPELINE EXECUTION SUMMARY             ")
    print("=" * 70)
    print(f"Overall Status:    {'✅ PASSED' if overall_success else '❌ FAILED'}")
    print(f"Total Stages:      {len(stages)} / {len(stages)} Passed")
    print(f"Total Tests Run:   {total_tests}")
    print(f"Passed:            {total_passed}")
    print(f"Failures:          {total_failures}")
    print(f"Errors:            {total_errors}")
    print(f"Skipped:           {total_skipped}")
    print(f"Pass Rate:         {summary['metrics']['pass_rate_pct']}%")
    print(f"Total Duration:    {total_duration:.2f}s")
    print(f"Artifacts Directory: {RESULTS_DIR}")
    print("=" * 70)
    
    for s in stages:
        status_icon = "✅" if s["success"] else "❌"
        print(f"  {status_icon} {s['name']:<42} {s['passed']}/{s['total']} passed ({s['duration']:.2f}s)")
    print("=" * 70 + "\n")
    
    if not overall_success:
        sys.exit(1)


if __name__ == "__main__":
    main()
