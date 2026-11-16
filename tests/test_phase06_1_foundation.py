"""
NovaNest Phase 06.1 — Core Multi-Agent Foundation & Shared Contracts Test Suite
==============================================================================
Verifies typed Pydantic v2 contracts, principal-isolated concurrent AgentContext,
OutputVerifier numerical/grounding/loss-framing checks, AgentRegistry capability &
ACL enforcement, secret-redacted ExecutionTracer, and legacy AI compatibility.
"""

from concurrent.futures import ThreadPoolExecutor
import json
import sys
import time
import unittest
from pathlib import Path

import pandas as pd
from pydantic import ValidationError

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from api.auth import AuthPrincipal
from python.ai.agents import (
    AgentAvailability,
    AgentContext,
    AgentContextManager,
    AgentDomain,
    AgentError,
    AgentExecutionMetadata,
    AgentMessage,
    AgentRegistration,
    AgentRegistry,
    AgentRequest,
    AgentResult,
    AgentStatus,
    ChartSpec,
    DataProvenance,
    DatasetMetadataEntry,
    ExecutionTracer,
    GroundedFact,
    KpiDefinitionEntry,
    MessageRole,
    ModelCaveat,
    OutputVerifier,
    SqlAuditTrace,
    TraceVerificationOutcome,
    VerificationOutcome,
    extract_dataset_metadata_from_frames,
    load_certified_kpi_entries,
)
from python.ai.agents.context import (
    AgentExecutionHistoryEntry,
    MAX_CONVERSATION_TURNS,
    MAX_DATASET_METADATA_ENTRIES,
    MAX_EXECUTION_HISTORY_ENTRIES,
)


class TestPhase061Foundation(unittest.TestCase):
    """Comprehensive verification for Phase 06.1 Multi-Agent Foundation layer."""

    def test_01_valid_contract_construction_and_json_serialization(self):
        """Verify valid contracts instantiate cleanly and serialize safely to JSON."""
        prov = DataProvenance(
            source_name="orders.csv",
            source_type="csv",
            dataset_or_table="orders",
            row_count=49971,
            filters_applied=["order_status != 'Cancelled'"],
            as_of_utc="2026-11-11T14:00:00Z",
        )
        fact = GroundedFact(
            label="Gross Merchandise Value (GMV)",
            value=46590125.0,
            unit="INR",
            kpi_id="KPI-01",
            source="orders.csv",
            formula="SUM(order_amount) WHERE order_status != 'Cancelled'",
        )
        caveat = ModelCaveat(
            model_name="NovaNest Customer Churn Predictor v2",
            domain="customer",
            validation_status="NEEDS_MORE_DATA",
            metric_summary="ROC-AUC 0.5161 on leak-free holdout",
            warning="Use heuristic RFM/CLV prioritization; calibrated churn probability is near random baseline.",
            is_production_ready=False,
        )
        sql_trace = SqlAuditTrace(
            sql="SELECT COUNT(*) AS total_orders FROM orders LIMIT 25",
            tables_accessed=["orders"],
            row_count=1,
            execution_ms=1.4,
            validated_by_ast=True,
        )
        chart = ChartSpec(
            chart_type="bar",
            title="GMV by City",
            x_key="city",
            y_key="gmv",
            data=[{"city": "Mumbai", "gmv": 12500000.0}],
        )
        req = AgentRequest(
            request_id="req_test_01",
            agent_id="financial_agent",
            domain=AgentDomain.FINANCIAL,
            principal_id="operator:a1b2c3d4e5f6",
            session_id="sess_exec_01",
            user_query="What is total GMV and Net Revenue?",
            allowed_tables=["orders", "payments"],
            required_scopes=["read"],
            timeout_seconds=3.0,
        )
        msg = AgentMessage(
            request_id=req.request_id,
            session_id=req.session_id,
            role=MessageRole.ORCHESTRATOR,
            sender="orchestrator",
            recipient="financial_agent",
            content="Compute KPI-01 GMV and KPI-02 Net Revenue.",
            payload={"kpis": ["KPI-01", "KPI-02"]},
        )
        res = AgentResult(
            request_id=req.request_id,
            execution_id=req.execution_id,
            agent_id="financial_agent",
            domain=AgentDomain.FINANCIAL,
            status=AgentStatus.SUCCESS,
            summary="GMV is ₹4.66 Cr (₹46,590,125.00).",
            facts=[fact],
            metrics={"gmv": 46590125.0, "net_revenue": 46425992.0},
            table_rows=[{"kpi": "GMV", "value": 46590125.0}],
            charts=[chart],
            caveats=[caveat],
            provenance=[prov],
            sql_traces=[sql_trace],
            execution=AgentExecutionMetadata(
                request_id=req.request_id,
                execution_id=req.execution_id,
                agent_id="financial_agent",
                elapsed_ms=12.5,
            ),
        )

        safe_json = json.dumps(res.to_safe_dict())
        decoded = json.loads(safe_json)
        self.assertEqual(decoded["status"], "success")
        self.assertEqual(decoded["facts"][0]["kpi_id"], "KPI-01")
        self.assertEqual(msg.payload["kpis"], ["KPI-01", "KPI-02"])

    def test_02_contract_rejects_dataframes_secrets_and_invalid_boundaries(self):
        """Verify contracts forbid raw DataFrames, raw Bearer/API keys, bad tables, and bad statuses."""
        df = pd.DataFrame([{"order_id": 1, "amount": 100.0}])

        # Raw DataFrames forbidden anywhere in AgentMessage / AgentResult / AgentRequest
        with self.assertRaises(ValidationError):
            AgentMessage(
                request_id="req_bad_df",
                role=MessageRole.AGENT,
                sender="financial_agent",
                recipient="orchestrator",
                payload={"raw_df": df},
            )

        with self.assertRaises(ValidationError):
            AgentResult(
                request_id="req_bad_df2",
                agent_id="financial_agent",
                domain=AgentDomain.FINANCIAL,
                status=AgentStatus.SUCCESS,
                table_rows=[{"nested_df": df}],
            )

        # Raw secrets forbidden in principal_id
        for bad_pid in (
            "Bearer mysecrettokenvalue1234",
            "AIzaSyD-ExampleInvalidKey1234567890",
            "sk-live-secret-token-value-123456",
            "user with spaces",
        ):
            with self.assertRaises(ValidationError):
                AgentRequest(
                    agent_id="financial_agent",
                    domain=AgentDomain.FINANCIAL,
                    principal_id=bad_pid,
                    user_query="Check revenue",
                )

        # Unauthorized SQLite system table forbidden in SqlAuditTrace & AgentRequest
        with self.assertRaises(ValidationError):
            SqlAuditTrace(sql="SELECT * FROM sqlite_master", tables_accessed=["sqlite_master"], row_count=1)

        with self.assertRaises(ValidationError):
            AgentRequest(
                agent_id="financial_agent",
                domain=AgentDomain.FINANCIAL,
                principal_id="operator:abc123",
                user_query="Query table",
                allowed_tables=["sqlite_schema"],
            )

        # Error status without error record or summary must fail validation
        with self.assertRaises(ValidationError):
            AgentResult(
                request_id="req_empty_err",
                agent_id="financial_agent",
                domain=AgentDomain.FINANCIAL,
                status=AgentStatus.ERROR,
                summary="",
                errors=[],
            )

        # Row limit > 100 rejected
        with self.assertRaises(ValidationError):
            AgentResult(
                request_id="req_too_many_rows",
                agent_id="financial_agent",
                domain=AgentDomain.FINANCIAL,
                status=AgentStatus.SUCCESS,
                table_rows=[{"row": i} for i in range(105)],
            )

    def test_03_contract_sanitizes_embedded_secrets_and_pii(self):
        """Verify message content, error messages, and dict secrets are safely redacted."""
        msg = AgentMessage(
            request_id="req_redact",
            role=MessageRole.USER,
            sender="api_gateway",
            recipient="orchestrator",
            content="User alice@novanest.in called with Bearer super_secret_token_987654 and +91 9876543210",
            payload={
                "authorization": "Bearer raw_header_secret_12345",
                "x-api-key": "topsecret_api_key",
                "note": "Contact bob@example.com for AIzaSyDummySecretKey123456789012345",
            },
        )
        serialized = json.dumps(msg.model_dump(mode="json"))
        self.assertNotIn("alice@novanest.in", serialized)
        self.assertNotIn("bob@example.com", serialized)
        self.assertNotIn("super_secret_token_987654", serialized)
        self.assertNotIn("raw_header_secret_12345", serialized)
        self.assertNotIn("topsecret_api_key", serialized)
        self.assertNotIn("AIzaSyDummySecretKey", serialized)
        self.assertIn("[REDACTED_EMAIL]", serialized)
        self.assertIn("[REDACTED_TOKEN]", serialized)
        self.assertIn("[REDACTED_SECRET]", serialized)

    def test_04_agent_context_principal_isolation_and_auth_principal(self):
        """Verify strict cross-principal isolation on AgentContext and AgentContextManager."""
        principal_a = AuthPrincipal(
            role="operator",
            scopes=frozenset({"read", "operator"}),
            principal_id="operator:111111aaaaaa",
        )
        principal_b = AuthPrincipal(
            role="operator",
            scopes=frozenset({"read", "operator"}),
            principal_id="operator:222222bbbbbb",
        )

        ctx_a = AgentContext.from_auth_principal(
            principal_a,
            session_id="shared-chat-id",
            user_query="Analyze Q4 Net Revenue",
            business_domains=[AgentDomain.FINANCIAL],
        )
        ctx_b = AgentContext.from_auth_principal(
            principal_b,
            session_id="shared-chat-id",
            user_query="Analyze Delivery SLA breaches",
            business_domains=[AgentDomain.OPERATIONS],
        )

        # Direct snapshot access across principals fails closed
        with self.assertRaises(PermissionError):
            ctx_a.snapshot(caller_principal_id=principal_b.principal_id)
        with self.assertRaises(PermissionError):
            ctx_a.to_safe_dict(caller_principal_id=principal_b.principal_id)

        # Manager keeps identically-named session_ids strictly separated per principal
        manager = AgentContextManager()
        manager.put_context(ctx_a)
        manager.put_context(ctx_b)
        self.assertEqual(manager.active_count(), 2)

        got_a = manager.get_context(principal_a.principal_id, "shared-chat-id")
        got_b = manager.get_context(principal_b.principal_id, "shared-chat-id")
        self.assertIsNotNone(got_a)
        self.assertIsNotNone(got_b)
        self.assertEqual(got_a.user_query, "Analyze Q4 Net Revenue")
        self.assertEqual(got_b.user_query, "Analyze Delivery SLA breaches")

        # Removing session A must leave session B intact
        self.assertTrue(manager.remove_context(principal_a.principal_id, "shared-chat-id"))
        self.assertIsNone(manager.get_context(principal_a.principal_id, "shared-chat-id"))
        self.assertIsNotNone(manager.get_context(principal_b.principal_id, "shared-chat-id"))

    def test_05_agent_context_bounds_deadlines_cancellation_and_metadata(self):
        """Verify turn/history/metadata size limits, cancellation, deadline tracking, and KPI loading."""
        ctx = AgentContext(
            principal_id="viewer:deadbeef1234",
            principal_role="viewer",
            session_id="bounds-test",
            user_query="Executive overview for Bearer hidden_secret_token_99999",
            timeout_seconds=0.25,
            load_default_kpis=True,
        )
        # User query secret scrubbed immediately
        self.assertNotIn("hidden_secret_token_99999", ctx.user_query)

        # Turn history bounded to MAX_CONVERSATION_TURNS
        for i in range(MAX_CONVERSATION_TURNS + 8):
            ctx.record_turn("user", f"Turn message {i}")
        snap = ctx.snapshot()
        self.assertEqual(len(snap.conversation_context), MAX_CONVERSATION_TURNS)
        self.assertEqual(snap.conversation_context[-1].content, f"Turn message {MAX_CONVERSATION_TURNS + 7}")

        # Execution history bounded to MAX_EXECUTION_HISTORY_ENTRIES
        for i in range(MAX_EXECUTION_HISTORY_ENTRIES + 6):
            ctx.record_execution_step(
                AgentExecutionHistoryEntry(
                    agent_id=f"agent_{i}",
                    domain=AgentDomain.FINANCIAL,
                    status=AgentStatus.SUCCESS,
                    elapsed_ms=1.5,
                    summary=f"step {i}",
                )
            )
        snap2 = ctx.snapshot()
        self.assertEqual(len(snap2.agent_execution_history), MAX_EXECUTION_HISTORY_ENTRIES)

        # Dataset metadata cap enforced without storing raw DataFrames
        frames = {"orders": pd.DataFrame([{"order_id": 1, "final_amount": 500.0}])}
        meta_map = extract_dataset_metadata_from_frames(frames)
        self.assertEqual(meta_map["orders"].row_count, 1)
        self.assertEqual(meta_map["orders"].columns, ["order_id", "final_amount"])

        for i in range(MAX_DATASET_METADATA_ENTRIES):
            ctx.register_dataset_metadata(DatasetMetadataEntry(dataset_name=f"ds_{i}", row_count=i))
        with self.assertRaises(ValueError):
            ctx.register_dataset_metadata(DatasetMetadataEntry(dataset_name="overflow_ds", row_count=1))

        # Certified KPI catalog loaded cleanly
        self.assertIn("KPI-01", snap2.kpi_definitions)
        self.assertAlmostEqual(snap2.kpi_definitions["KPI-01"].value or 0.0, 46590125.0, places=2)

        # Safe JSON serialization check
        safe_dict = ctx.to_safe_dict()
        self.assertFalse(safe_dict["cancelled"])

        # Cooperative cancellation & deadline expiration
        ctx.cancel("Operator cancelled slow query")
        self.assertTrue(ctx.is_cancelled())
        self.assertEqual(ctx.snapshot().cancellation_reason, "Operator cancelled slow query")
        time.sleep(0.28)
        self.assertTrue(ctx.is_expired())
        self.assertEqual(ctx.remaining_seconds(), 0.0)

    def test_06_output_verifier_currency_percentage_and_rounding_tolerances(self):
        """Verify OutputVerifier matches exact INR, Cr/Lakhs rounding, Indian commas, and percentages."""
        verifier = OutputVerifier(load_default_kpis=True)
        text = (
            "Executive Summary: Gross Merchandise Value (KPI-01) reached ₹4.66 Cr "
            "(exact ₹46,590,125.00), while Net Revenue (KPI-02) reached ₹4,64,25,992.00 "
            "across 49,971 total orders and 47,994 delivered orders. Cancellation rate is 3.96%, "
            "SLA breach rate is 32.26%, and mean delivery duration is 37.4 mins."
        )
        report = verifier.verify(text)
        self.assertEqual(report.outcome, VerificationOutcome.VERIFIED)
        self.assertTrue(report.is_verified)
        self.assertEqual(report.unsupported_claims, [])
        self.assertEqual(report.violations, [])
        self.assertGreaterEqual(report.supported_claims_count, 7)

    def test_07_output_verifier_rejects_hallucinated_numbers(self):
        """Verify OutputVerifier rejects fabricated figures not grounded in KPIs or evidence."""
        verifier = OutputVerifier(load_default_kpis=True)
        hallucinated = (
            "GMV jumped to ₹8.75 Cr across 92,400 orders with a 14.20% cancellation rate."
        )
        report = verifier.verify(hallucinated)
        self.assertEqual(report.outcome, VerificationOutcome.REJECTED)
        self.assertFalse(report.is_verified)
        self.assertEqual(len(report.unsupported_claims), 3)
        self.assertTrue(any(v.code == "UNSUPPORTED_NUMERIC_CLAIM" for v in report.violations))

    def test_08_output_verifier_unconfirmed_loss_protection_and_missing_data(self):
        """
        Verify OutputVerifier NEVER allows unconfirmed financial screening risks
        to be presented as confirmed losses, while allowing honest screening framing
        and reporting missing/blocked data honestly.
        """
        verifier = OutputVerifier(load_default_kpis=True)
        leakage_fact = GroundedFact(
            label="Unconfirmed Revenue Leakage Exposure",
            value=553946.31,
            unit="INR",
            source="revenue_leakage.csv",
            is_confirmed=False,
            is_confirmed_loss=False,
        )
        fin_res = AgentResult(
            request_id="req_leak",
            agent_id="financial_agent",
            domain=AgentDomain.FINANCIAL,
            status=AgentStatus.PARTIAL,
            summary="Screening identified ₹5.54 L across 4,669 flagged rows (is_confirmed_loss=False).",
            facts=[leakage_fact, GroundedFact(label="Flagged Orders", value=4669, unit="Count")],
            is_confirmed_loss=False,
            data_gaps=["merchant_vs_platform_promo_funding_split_unavailable"],
        )

        # Misleading confirmed-loss prose MUST be rejected
        bad_prose = "Audit proved a confirmed financial loss of ₹5.54 L from promotional revenue leakage."
        bad_report = verifier.verify(bad_prose, agent_results=[fin_res])
        self.assertEqual(bad_report.outcome, VerificationOutcome.REJECTED)
        self.assertFalse(bad_report.is_verified)
        self.assertFalse(bad_report.unconfirmed_loss_preserved)
        self.assertTrue(any(v.code == "UNCONFIRMED_LOSS_FRAMING" for v in bad_report.violations))

        # Honest non-confirmed prose preserves partial verification + missing data flags
        honest_prose = (
            "Screening flagged ₹553,946.31 (₹5.54 L) across 4,669 orders as promotional leakage risk; "
            "this is NOT a confirmed financial loss (is_confirmed_loss=False) pending promo funding reconciliation."
        )
        honest_report = verifier.verify(honest_prose, agent_results=[fin_res])
        self.assertTrue(honest_report.unconfirmed_loss_preserved)
        self.assertTrue(honest_report.is_verified)
        self.assertEqual(honest_report.outcome, VerificationOutcome.PARTIAL)
        self.assertIn("financial_agent:partial", honest_report.missing_data_flags)
        self.assertTrue(any("merchant_vs_platform_promo_funding_split_unavailable" in f for f in honest_report.missing_data_flags))

    def test_09_output_verifier_detects_conflicting_agent_results(self):
        """Verify OutputVerifier catches conflicting numbers across two AgentResult payloads."""
        verifier = OutputVerifier(load_default_kpis=True)
        res_fin = AgentResult(
            request_id="req_conf",
            agent_id="financial_agent",
            domain=AgentDomain.FINANCIAL,
            status=AgentStatus.SUCCESS,
            facts=[GroundedFact(label="Net Revenue", kpi_id="KPI-02", value=46425992.0, unit="INR")],
        )
        res_ops = AgentResult(
            request_id="req_conf",
            agent_id="operations_agent",
            domain=AgentDomain.OPERATIONS,
            status=AgentStatus.SUCCESS,
            facts=[GroundedFact(label="Net Revenue", kpi_id="KPI-02", value=41200000.0, unit="INR")],
        )
        report = verifier.verify(
            "Net Revenue stands at ₹4.64 Cr.",
            agent_results=[res_fin, res_ops],
        )
        self.assertEqual(report.outcome, VerificationOutcome.REJECTED)
        self.assertFalse(report.is_verified)
        self.assertEqual(len(report.conflicts), 1)
        self.assertTrue(any(v.code == "CONFLICTING_AGENT_RESULTS" for v in report.violations))

    def test_10_agent_registry_blocks_unfinished_operational_and_enforces_contracts(self):
        """
        Verify AgentRegistry supports discovery/contracts AND strictly prevents
        unfinished domain agents from being registered or promoted as OPERATIONAL.
        """
        registry = AgentRegistry(preload_planned_blueprints=True)

        # Zero domain agents may be OPERATIONAL in Phase 06.1
        self.assertEqual(registry.list_agents(include_non_operational=False), [])
        all_planned = registry.list_agents(include_non_operational=True)
        self.assertEqual(len(all_planned), 5)
        self.assertTrue(all(reg.availability == AgentAvailability.PLANNED for reg in all_planned))
        self.assertIsNone(registry.get_handler("financial_agent"))

        # Attempting to register an unimplemented agent as OPERATIONAL MUST fail
        with self.assertRaises(ValidationError):
            AgentRegistration(
                agent_id="unfinished_fin",
                domain=AgentDomain.FINANCIAL,
                description="Unfinished stub",
                availability=AgentAvailability.OPERATIONAL,
                is_implemented=False,
            )

        # Even if marked is_implemented=True, missing callable handler fails registration
        stub_reg = AgentRegistration(
            agent_id="no_handler_agent",
            domain=AgentDomain.FINANCIAL,
            description="Missing runtime callable",
            availability=AgentAvailability.OPERATIONAL,
            is_implemented=True,
        )
        with self.assertRaises(ValueError):
            registry.register(stub_reg, handler=None)

        # Promoting a PLANNED domain agent without handler MUST fail
        with self.assertRaises(ValueError):
            registry.set_availability("financial_agent", AgentAvailability.OPERATIONAL)

        # Registering a real operational health/utility capability with handler works cleanly
        def _echo_capability(req: AgentRequest) -> AgentResult:
            return AgentResult(
                request_id=req.request_id,
                execution_id=req.execution_id,
                agent_id=req.agent_id,
                domain=req.domain,
                status=AgentStatus.SUCCESS,
                summary="Contract probe succeeded",
            )

        probe_reg = AgentRegistration(
            agent_id="contract_probe_agent",
            domain=AgentDomain.GENERAL,
            description="Foundation probe agent for I/O validation tests",
            capabilities=["contract_probe"],
            allowed_tables=["orders", "restaurants"],
            required_scopes=["operator"],
            availability=AgentAvailability.OPERATIONAL,
            is_implemented=True,
        )
        registry.register(probe_reg, handler=_echo_capability)
        self.assertEqual(len(registry.discover(capability="contract_probe")), 1)

        validated_req = registry.validate_input(
            "contract_probe_agent",
            {
                "agent_id": "contract_probe_agent",
                "domain": "general",
                "principal_id": "operator:abc123",
                "user_query": "Run health check",
            },
        )
        result = registry.get_handler("contract_probe_agent")(validated_req)
        validated_res = registry.validate_output("contract_probe_agent", result)
        self.assertEqual(validated_res.status, AgentStatus.SUCCESS)

    def test_11_agent_registry_permission_boundaries(self):
        """Verify AgentRegistry enforces scope RBAC, table ACLs, and operational availability."""
        registry = AgentRegistry(preload_planned_blueprints=True)

        # Planned agent cannot be authorized
        planned_decision = registry.authorize(
            "financial_agent",
            principal_scopes={"read", "operator", "admin"},
            requested_tables=["orders"],
        )
        self.assertFalse(planned_decision.allowed)

        # Register operational restricted probe
        registry.register(
            AgentRegistration(
                agent_id="ops_sql_probe",
                domain=AgentDomain.OPERATIONS,
                description="Bounded ops table reader",
                allowed_tables=["deliveries", "riders"],
                required_scopes=["operator"],
                availability=AgentAvailability.OPERATIONAL,
                is_implemented=True,
            ),
            handler=lambda r: r,
        )

        # Viewer lacks 'operator' scope
        viewer_denial = registry.authorize(
            "ops_sql_probe",
            principal_scopes={"read"},
            requested_tables=["deliveries"],
        )
        self.assertFalse(viewer_denial.allowed)
        self.assertIn("operator", viewer_denial.missing_scopes)

        # Operator querying unauthorized 'customers' PII table fails table ACL check
        table_denial = registry.authorize(
            "ops_sql_probe",
            principal_scopes={"read", "operator"},
            requested_tables=["deliveries", "customers"],
        )
        self.assertFalse(table_denial.allowed)
        self.assertEqual(table_denial.unauthorized_tables, ["customers"])

        # Operator querying authorized tables passes cleanly
        ok = registry.authorize(
            "ops_sql_probe",
            principal_scopes={"read", "operator"},
            requested_tables=["deliveries", "riders"],
        )
        self.assertTrue(ok.allowed)

    def test_12_execution_tracer_timing_redaction_and_isolation(self):
        """Verify ExecutionTracer captures timing/sources/errors cleanly while redacting secrets."""
        tracer = ExecutionTracer(max_traces=3)
        req_id = "req_trace_01"
        tracer.start_trace(request_id=req_id, principal_id="operator:abc999", session_id="s1")

        with tracer.span(
            req_id,
            agent_id="financial_agent",
            domain=AgentDomain.FINANCIAL,
            metadata={"authorization": "Bearer raw_bearer_secret_abc123", "note": "AIzaSySecretKey0000111122223333"},
        ) as ctx_span:
            time.sleep(0.01)
            ctx_span["data_sources_used"] = ["orders.csv", "kpi_definitions.json"]
            ctx_span["verification_outcome"] = TraceVerificationOutcome.VERIFIED
            ctx_span["errors"] = [
                AgentError(
                    code="WARN_SAMPLE",
                    message="Ignored email leak user@novanest.in and token Bearer tok_999999999",
                    recoverable=True,
                )
            ]

        trace = tracer.finish_trace(req_id, verification_outcome=TraceVerificationOutcome.VERIFIED)
        self.assertIsNotNone(trace)
        self.assertEqual(trace.status, AgentStatus.SUCCESS)
        self.assertGreater(trace.duration_ms, 0.0)
        self.assertEqual(len(trace.spans), 1)
        self.assertEqual(trace.spans[0].data_sources_used, ["orders.csv", "kpi_definitions.json"])

        serialized = json.dumps(trace.to_safe_dict())
        self.assertNotIn("raw_bearer_secret_abc123", serialized)
        self.assertNotIn("AIzaSySecretKey", serialized)
        self.assertNotIn("user@novanest.in", serialized)
        self.assertNotIn("tok_999999999", serialized)

        # Principal isolation check on trace retrieval
        self.assertIsNone(tracer.get_trace(req_id, principal_id="operator:other_user"))
        self.assertIsNotNone(tracer.get_trace(req_id, principal_id="operator:abc999"))

        # Bounded trace buffer evicts oldest beyond max_traces=3
        for idx in range(4):
            tracer.start_trace(request_id=f"req_evict_{idx}", principal_id="viewer:x")
        self.assertIsNone(tracer.get_trace(req_id))

    def test_13_concurrent_context_and_tracer_stress(self):
        """Verify concurrent multi-thread reads/writes on AgentContext and ExecutionTracer remain consistent."""
        ctx = AgentContext(
            principal_id="operator:concurrent_user",
            principal_role="operator",
            session_id="concurrent-sess",
            user_query="Concurrent telemetry stress test",
            timeout_seconds=10.0,
        )
        tracer = ExecutionTracer(max_traces=20)
        tracer.start_trace(request_id=ctx.request_id, principal_id=ctx.principal_id, session_id=ctx.session_id)
        kpi_snapshot = load_certified_kpi_entries(kpi_ids=["KPI-01"])
        ctx.register_kpi_definition(KpiDefinitionEntry(**kpi_snapshot["KPI-01"].model_dump()))

        def _worker(idx: int) -> bool:
            ctx.record_turn("user", f"Concurrent query turn {idx}")
            ctx.record_execution_step(
                AgentExecutionHistoryEntry(
                    agent_id=f"worker_{idx % 4}",
                    domain=AgentDomain.OPERATIONS,
                    status=AgentStatus.SUCCESS,
                    elapsed_ms=1.0,
                    summary=f"Worker step {idx}",
                )
            )
            with tracer.span(ctx.request_id, agent_id=f"worker_{idx % 4}", domain=AgentDomain.OPERATIONS) as s:
                s["data_sources_used"] = ["deliveries.csv"]
            snap = ctx.snapshot(caller_principal_id=ctx.principal_id)
            return len(snap.conversation_context) <= MAX_CONVERSATION_TURNS and len(snap.agent_execution_history) <= MAX_EXECUTION_HISTORY_ENTRIES

        with ThreadPoolExecutor(max_workers=8) as pool:
            results = list(pool.map(_worker, range(32)))

        self.assertTrue(all(results))
        final_snap = ctx.snapshot()
        self.assertEqual(len(final_snap.conversation_context), MAX_CONVERSATION_TURNS)
        self.assertEqual(len(final_snap.agent_execution_history), MAX_EXECUTION_HISTORY_ENTRIES)
        final_trace = tracer.finish_trace(ctx.request_id)
        self.assertEqual(len(final_trace.spans), 32)

    def test_14_legacy_phase06_0_orchestrator_remains_intact(self):
        """Verify Phase 06.0 AskNovaNestOrchestrator and analyze_business_inquiry remain undisturbed."""
        from python.ai.analyst.orchestrator import AskNovaNestOrchestrator, analyze_business_inquiry

        self.assertTrue(callable(analyze_business_inquiry))
        orch = AskNovaNestOrchestrator(data={})
        resp = orch.process_query(
            "Calculate compound interest on 2000 at 20% for 2 years",
            session_id="phase061-compat",
            principal="viewer:compat",
        )
        self.assertEqual(resp.get("intent"), "CALCULATION")
        self.assertIn("880.00", resp.get("answer", ""))


if __name__ == "__main__":
    unittest.main(verbosity=2)
