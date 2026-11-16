# NovaNest — Phase 18 File Changes Register

**Phase**: 18  
**Title**: Independent Security Audit & Penetration Testing  
**Lead Agent**: Principal Security Architect & Defensive Penetration Tester  
**Date**: 2026-11-15  
**Status**: COMPLETE  

---

## Summary of Files Modified or Created

| File Path | Action | Type | Purpose |
| :--- | :--- | :--- | :--- |
| `python/decision/prescriptive_contracts.py` | MODIFIED | Backend Contract | Return `supporting_evidence` list and financial fields |
| `api/main.py` | MODIFIED | Backend Gateway | Enforce RBAC on `/api/records/customers` (operator scope required) |
| `api/pagination.py` | MODIFIED | Backend Engine | Reject non-whitelisted sort columns with HTTP 400 |
| `docker/nginx.conf` | MODIFIED | Infrastructure | Preserve HTTP security headers in child static location block |
| `frontend/src/services/api.ts` | MODIFIED | Frontend Client | Add normalizers `normalizePrescriptiveRecommendation` and `normalizePrescriptiveFinancialCharts` |
| `frontend/src/views/ExecutiveOverviewView.tsx` | MODIFIED | Frontend View | Defensive `.slice()` array chaining and localized ErrorBoundary |
| `frontend/src/views/DecisionIntelligenceView.tsx` | MODIFIED | Frontend View | Defensive `.map()` array chaining and localized ErrorBoundary |
| `tests/test_phase18_security_audit.py` | CREATED | Test Suite | 15 comprehensive automated defensive security test cases |
| `NEWCHAGES/PHASE18/PHASE_PLAN.md` | CREATED | Governance | Milestone plan and security testing scope |
| `NEWCHAGES/PHASE18/SECURITY_BASELINE.md` | CREATED | Governance | Pre-audit security architecture baseline inventory |
| `NEWCHAGES/PHASE18/SECURITY_FINDINGS.md` | CREATED | Governance | Detailed analysis of Findings 01–05 with CVSS 3.1 |
| `NEWCHAGES/PHASE18/REMEDIATION_LOG.md` | CREATED | Governance | Chronological log of applied remediations |
| `NEWCHAGES/PHASE18/IMPLEMENTATION_LOG.md` | CREATED | Governance | Verification and implementation log |
| `NEWCHAGES/PHASE18/FILE_CHANGES.md` | CREATED | Governance | File modification audit record |
| `NEWCHAGES/PHASE18/TEST_RESULTS.md` | CREATED | Governance | Automated test execution evidence |
| `NEWCHAGES/PHASE18/PHASE_SUMMARY.md` | CREATED | Governance | Executive closeout summary |

---

## Detailed Code Diffs

### 1. `python/decision/prescriptive_contracts.py`
```diff
@@ -107,4 +107,17 @@
         "title": self.proposed_action[:60] if self.proposed_action else "Prescriptive Action",
         "target_type": self.domain,
         "entity_id": self.recommendation_id,
         "evidence": "; ".join(self.supporting_evidence) if isinstance(self.supporting_evidence, (list, tuple)) else str(self.supporting_evidence or ""),
+        "supporting_evidence": list(self.supporting_evidence) if isinstance(self.supporting_evidence, (list, tuple)) else ([str(self.supporting_evidence)] if self.supporting_evidence else []),
         "expected_impact": f"Projected Net Impact: ₹{self.financial_impact.net_financial_impact:,.2f}",
         "confidence": self.confidence_tier.value if hasattr(self.confidence_tier, "value") else str(self.confidence_tier),
         "action": self.proposed_action,
         "priority": self.priority.value if hasattr(self.priority, "value") else str(self.priority),
         "domain": self.domain,
         "recommendation_id": self.recommendation_id,
         "business_problem": self.problem_statement,
+        "problem_statement": self.problem_statement,
         "proposed_action": self.proposed_action,
         "expected_benefit": f"Gross Benefit: ₹{self.financial_impact.gross_benefit:,.2f}",
+        "expected_gross_benefit_rupees": self.financial_impact.gross_benefit,
         "implementation_cost": f"Cost: ₹{self.financial_impact.implementation_cost:,.2f}",
+        "implementation_cost_rupees": self.financial_impact.implementation_cost,
         "net_financial_impact": f"Net Impact: ₹{self.financial_impact.net_financial_impact:,.2f}",
+        "net_financial_impact_rupees": self.financial_impact.net_financial_impact,
+        "roi_multiple": self.financial_impact.roi_multiple,
+        "payback_period_days": self.financial_impact.payback_period_days,
+        "status_history": [s.to_dict() for s in self.status_history] if self.status_history else [],
```

### 2. `api/main.py`
```diff
@@ -3245,6 +3245,13 @@
     if entity_key not in table_map:
         raise HTTPException(
             status_code=400,
             detail=f"Invalid entity '{entity}'. Supported entities: {list(table_map.keys())}"
         )
+
+    # Enforce PII protection: customer records require operator scope
+    if entity_key == "customers" and "operator" not in principal.scopes:
+        raise HTTPException(
+            status_code=403,
+            detail="Insufficient permissions: 'operator' scope required to access individual customer records.",
+        )
```

### 3. `api/pagination.py`
```diff
@@ -120,8 +120,13 @@
     whitelist = SORT_WHITELISTS[entity_key]

-    # Resolve Sort Column
-    resolved_sort = None
-    if sort_by and sort_by.lower() in whitelist:
-        resolved_sort = whitelist[sort_by.lower()]
-    else:
-        resolved_sort, def_dir = DEFAULT_SORT[entity_key]
-        if not sort_by:
-            sort_dir = def_dir
+    # Resolve Sort Column strictly against whitelist; fail-closed on invalid columns
+    resolved_sort = None
+    if sort_by:
+        if sort_by.lower() not in whitelist:
+            raise HTTPException(
+                status_code=400,
+                detail=f"Invalid sort column '{sort_by}' for entity '{entity_key}'. Allowed columns: {list(whitelist.keys())}",
+            )
+        resolved_sort = whitelist[sort_by.lower()]
+    else:
+        resolved_sort, def_dir = DEFAULT_SORT[entity_key]
+        sort_dir = def_dir
```

### 4. `docker/nginx.conf`
```diff
@@ -48,6 +48,11 @@
     location ~* \.(?:css|js|jpg|jpeg|gif|png|ico|cur|gz|svg|svgz|mp4|ogg|ogv|webm|htc|woff|woff2|ttf|eot)$ {
         expires 1y;
         access_log off;
         add_header Cache-Control "public, max-age=31536000, immutable";
+        add_header X-Frame-Options "SAMEORIGIN" always;
+        add_header X-Content-Type-Options "nosniff" always;
+        add_header X-XSS-Protection "1; mode=block" always;
+        add_header Referrer-Policy "strict-origin-when-cross-origin" always;
     }
```
