"""
NovaNest Multi-Agent Synthesis & Verification Layer (Phase 06.3)
----------------------------------------------------------------
Combines structured outputs from one or more domain agents into a single
consolidated, provenance-preserving, OutputVerifier-checked response.

Guarantees:
- Preserves every agent's DataProvenance and ModelCaveat disclosures.
- Separates validated CSV/SQL actuals from experimental Phase 05 ML caveats.
- Preserves `is_confirmed_loss=False` across all leakage / promo screening claims.
- Detects missing/blocked/timed-out/failed agents and reports explicit limitations.
- Runs `OutputVerifier` across consolidated prose + child `AgentResult`s and fails
  closed with an explicit documented limitation if verification rejects the output.
"""

from __future__ import annotations

import math
from typing import Any, Dict, List, Optional, Sequence, Tuple, Union

from pydantic import BaseModel, ConfigDict, Field

from python.ai.agents.base import get_certified_kpi_catalog
from python.ai.agents.context import KpiDefinitionEntry
from python.ai.agents.contracts import (
    MAX_CONTRACT_TABLE_ROWS,
    MAX_SUMMARY_CHARS,
    ActionRecommendation,
    AgentError,
    AgentResult,
    AgentStatus,
    ChartSpec,
    DataProvenance,
    GroundedFact,
    ModelCaveat,
    SqlAuditTrace,
    sanitize_text,
)
from python.ai.agents.output_verifier import (
    ConflictDetail,
    OutputVerifier,
    VerificationOutcome,
    VerificationReport,
)


_ACTIVE_STATUSES = {AgentStatus.SUCCESS, AgentStatus.PARTIAL}
_DEGRADED_STATUSES = {
    AgentStatus.ERROR,
    AgentStatus.TIMEOUT,
    AgentStatus.BLOCKED,
    AgentStatus.CANCELLED,
}

_DOMAIN_LABELS: Dict[str, str] = {
    "financial_agent": "Financial Intelligence",
    "customer_agent": "Customer Intelligence",
    "operations_agent": "Operations & Logistics",
    "restaurant_agent": "Restaurant Partner Intelligence",
    "decision_agent": "Decision & Root-Cause Intelligence",
}


class SynthesisOutput(BaseModel):
    """Typed consolidated artifact emitted by `synthesize_agent_results`."""

    model_config = ConfigDict(extra="forbid")

    consolidated_summary: str = Field(default="", max_length=MAX_SUMMARY_CHARS)
    consolidated_narrative: str = Field(default="", max_length=MAX_SUMMARY_CHARS)
    status: AgentStatus
    facts: List[GroundedFact] = Field(default_factory=list)
    metrics: Dict[str, Union[float, int, str, bool, None]] = Field(default_factory=dict)
    table_rows: List[Dict[str, Any]] = Field(default_factory=list)
    charts: List[ChartSpec] = Field(default_factory=list)
    recommendations: List[ActionRecommendation] = Field(default_factory=list)
    caveats: List[ModelCaveat] = Field(default_factory=list)
    provenance: List[DataProvenance] = Field(default_factory=list)
    sql_traces: List[SqlAuditTrace] = Field(default_factory=list)
    errors: List[AgentError] = Field(default_factory=list)
    data_gaps: List[str] = Field(default_factory=list)
    limitations: List[str] = Field(default_factory=list)
    ml_confidence_warnings: List[str] = Field(default_factory=list)
    calculation_steps: List[Dict[str, Any]] = Field(default_factory=list)
    data_source_badges: List[str] = Field(default_factory=list)
    conflicts: List[ConflictDetail] = Field(default_factory=list)
    verification_report: VerificationReport
    grounding_verified: bool = True
    is_confirmed_loss: Optional[bool] = None


def _dedupe_strings(items: Sequence[str]) -> List[str]:
    seen: set[str] = set()
    out: List[str] = []
    for raw in items:
        clean = sanitize_text(str(raw)).strip()
        if clean and clean not in seen:
            seen.add(clean)
            out.append(clean)
    return out


def _collect_provenance_and_badges(
    results: Sequence[AgentResult],
) -> Tuple[List[DataProvenance], List[str], Optional[bool]]:
    provenances: List[DataProvenance] = []
    seen_prov: set[Tuple[str, str, str]] = set()
    badges: List[str] = []
    has_unconfirmed_loss = False

    for res in results:
        if res.is_confirmed_loss is False:
            has_unconfirmed_loss = True
        for p in res.provenance:
            if p.is_confirmed_loss is False:
                has_unconfirmed_loss = True
            key = (p.source_name, p.source_type, p.dataset_or_table or "")
            if key not in seen_prov:
                seen_prov.add(key)
                provenances.append(p)
            ds_label = p.dataset_or_table or p.source_name
            badge = f"{ds_label} ({p.source_type})"
            if p.is_confirmed_loss is False:
                badge = f"{ds_label} (screening only — is_confirmed_loss=False)"
            badges.append(badge)

    return provenances, _dedupe_strings(badges), (False if has_unconfirmed_loss else None)


def _collect_caveats(results: Sequence[AgentResult]) -> Tuple[List[ModelCaveat], List[str]]:
    caveats: List[ModelCaveat] = []
    seen: set[Tuple[str, str]] = set()
    warnings: List[str] = []
    for res in results:
        for c in res.caveats:
            key = (c.model_name, c.domain)
            if key not in seen:
                seen.add(key)
                caveats.append(c)
                readiness = "production-ready" if c.is_production_ready else f"experimental / {c.validation_status}"
                warnings.append(f"[{c.domain}] {c.model_name} ({readiness}): {c.warning}")
    return caveats, _dedupe_strings(warnings)


def _collect_facts_and_steps(
    results: Sequence[AgentResult],
    kpi_catalog: Dict[str, KpiDefinitionEntry],
) -> Tuple[List[GroundedFact], List[Dict[str, Any]], bool]:
    facts: List[GroundedFact] = []
    seen_fact_keys: set[Tuple[str, str]] = set()
    calc_steps: List[Dict[str, Any]] = []
    seen_steps: set[str] = set()
    has_unconfirmed_fact = False

    for res in results:
        for fact in res.facts:
            if fact.is_confirmed_loss is False:
                has_unconfirmed_fact = True
            f_key = ((fact.kpi_id or fact.label).strip().lower(), res.agent_id)
            if f_key not in seen_fact_keys:
                seen_fact_keys.add(f_key)
                facts.append(fact)

            step_key = (fact.kpi_id or fact.label).strip().lower()
            if step_key not in seen_steps:
                kpi_entry = kpi_catalog.get(fact.kpi_id.upper()) if fact.kpi_id else None
                formula = fact.formula or (kpi_entry.mathematical_formula if kpi_entry else None)
                if formula or fact.kpi_id:
                    seen_steps.add(step_key)
                    calc_steps.append(
                        {
                            "kpi_id": fact.kpi_id or "",
                            "name": kpi_entry.name if kpi_entry else fact.label,
                            "value": fact.value,
                            "unit": fact.unit or (kpi_entry.unit if kpi_entry else ""),
                            "formula": sanitize_text(formula or "Aggregated directly from verified dataset"),
                            "source_tables": sanitize_text(
                                (kpi_entry.source_tables if kpi_entry and kpi_entry.source_tables else fact.source)
                            ),
                        }
                    )
    return facts, calc_steps, has_unconfirmed_fact


def _merge_metrics(
    active_results: Sequence[AgentResult],
) -> Dict[str, Union[float, int, str, bool, None]]:
    """
    Merge consistent scalar metrics across active domain agents.
    Ambiguous keys that diverge meaningfully across agents are NOT silently overwritten;
    OutputVerifier inspects raw `agent_results` directly to catch conflicts.
    """
    merged: Dict[str, Union[float, int, str, bool, None]] = {}
    diverged_keys: set[str] = set()
    for res in active_results:
        for key, val in res.metrics.items():
            if key in diverged_keys:
                continue
            if key not in merged:
                merged[key] = val
                continue
            prev = merged[key]
            if (
                isinstance(prev, (int, float))
                and isinstance(val, (int, float))
                and not isinstance(prev, bool)
                and not isinstance(val, bool)
            ):
                tol = max(max(abs(float(prev)), abs(float(val))) * 0.005, 1e-6)
                if math.isfinite(float(prev)) and math.isfinite(float(val)) and abs(float(prev) - float(val)) > tol:
                    merged.pop(key, None)
                    diverged_keys.add(key)
    return merged


def _collect_recommendations(results: Sequence[AgentResult]) -> List[ActionRecommendation]:
    # Put DecisionAgent recommendations first, then remaining domain agents, deduplicated
    ordered = sorted(results, key=lambda r: 0 if r.agent_id == "decision_agent" else 1)
    recs: List[ActionRecommendation] = []
    seen: set[Tuple[str, str]] = set()
    for res in ordered:
        for rec in res.recommendations:
            key = (rec.title.strip().lower(), rec.entity_id.strip().lower())
            if key not in seen:
                seen.add(key)
                recs.append(rec)
    return recs[:12]


def _collect_limitations(
    results: Sequence[AgentResult],
    missing_agents: Optional[Sequence[str]] = None,
) -> Tuple[List[str], List[str], List[AgentError]]:
    gaps: List[str] = []
    limitations: List[str] = []
    errors: List[AgentError] = []

    for res in results:
        gaps.extend(res.data_gaps)
        if res.status in _DEGRADED_STATUSES:
            err_msg = res.errors[0].message if res.errors else res.summary
            limitations.append(
                f"{res.agent_id} did not complete ({res.status.value}): {sanitize_text(err_msg or 'unavailable')}"
            )
        elif res.status == AgentStatus.PARTIAL:
            limitations.append(f"{res.agent_id} returned partial coverage due to dataset or prerequisite gaps.")
        errors.extend(res.errors)

    for missing in missing_agents or []:
        limitations.append(f"Planned agent skipped/unavailable: {sanitize_text(missing)}")

    dedup_gaps = _dedupe_strings(gaps)
    dedup_limits = _dedupe_strings(limitations + dedup_gaps)
    return dedup_gaps, dedup_limits, errors


def _build_draft_narrative(
    *,
    user_query: str,
    active_results: Sequence[AgentResult],
    degraded_results: Sequence[AgentResult],
    caveats: Sequence[ModelCaveat],
    recommendations: Sequence[ActionRecommendation],
    limitations: Sequence[str],
    has_unconfirmed_leakage: bool,
) -> Tuple[str, str]:
    """Compose consolidated Markdown summary & narrative from grounded agent outputs only."""
    if not active_results:
        reasons = "; ".join(limitations) or "All invoked domain agents were blocked, timed out, or unavailable."
        summary = f"Unable to compute domain insights for '{sanitize_text(user_query)}': {reasons}"
        narrative = (
            f"### Orchestration Limitation\n\n"
            f"No domain agent completed successfully.\n\n"
            f"- **Details:** {reasons}\n"
        )
        return summary[:MAX_SUMMARY_CHARS], narrative[:MAX_SUMMARY_CHARS]

    if len(active_results) == 1 and not degraded_results:
        primary = active_results[0]
        base_summary = primary.summary or primary.narrative
        base_narrative = primary.narrative or primary.summary
        extra_sections: List[str] = []
        if limitations and primary.status == AgentStatus.PARTIAL:
            lim_lines = "\n".join(f"- {item}" for item in limitations)
            extra_sections.append(f"### Coverage Limitations\n{lim_lines}")
        narrative = base_narrative if not extra_sections else f"{base_narrative}\n\n" + "\n\n".join(extra_sections)
        return base_summary[:MAX_SUMMARY_CHARS], narrative[:MAX_SUMMARY_CHARS]

    sections: List[str] = []
    summary_parts: List[str] = []

    for res in active_results:
        title = _DOMAIN_LABELS.get(res.agent_id, res.agent_id)
        body = (res.narrative or res.summary or "").strip()
        if not body:
            continue
        sections.append(f"### {title}\n{body}")
        if res.summary:
            summary_parts.append(f"[{res.agent_id}] {res.summary.strip()}")

    if has_unconfirmed_leakage:
        sections.append(
            "### Screening Safeguard\n"
            "- Promotional/discount anomaly and leakage signals are **unconfirmed screening candidates** "
            "(`is_confirmed_loss=False`) and are **not** reported as confirmed financial losses."
        )

    if caveats:
        caveat_lines = "\n".join(
            f"- **{c.model_name}** (`{c.validation_status}`, production-ready={c.is_production_ready}): {c.warning}"
            for c in caveats
        )
        sections.append(f"### Validated Actuals vs Experimental ML Caveats\n{caveat_lines}")

    if recommendations and "Decision & Root-Cause Intelligence" not in "\n".join(sections):
        rec_lines = "\n".join(
            f"- **[{r.priority}] {r.title}** ({r.target_type}): {r.evidence} — *Action:* {r.action}"
            for r in recommendations[:5]
        )
        sections.append(f"### Grounded Recommendations\n{rec_lines}")

    if limitations:
        lim_lines = "\n".join(f"- {item}" for item in limitations)
        sections.append(f"### Partial Coverage & Limitations\n{lim_lines}")

    consolidated_summary = " ".join(summary_parts).strip()
    if limitations:
        consolidated_summary = f"{consolidated_summary} Limitations: {'; '.join(limitations)}"
    consolidated_narrative = "\n\n".join(sections).strip()
    return consolidated_summary[:MAX_SUMMARY_CHARS], consolidated_narrative[:MAX_SUMMARY_CHARS]


def _build_rejected_limitation_response(
    report: VerificationReport,
    limitations: Sequence[str],
) -> Tuple[str, str]:
    """Fail closed when OutputVerifier rejects consolidated synthesis output."""
    conflict_notes = [
        f"Conflicting metric '{c.metric_key}' between {c.agent_a} and {c.agent_b} (withheld pending reconciliation)"
        for c in report.conflicts
    ]
    violation_notes: List[str] = []
    for v in report.violations:
        if v.code == "CONFLICTING_AGENT_RESULTS":
            continue
        if v.code == "UNSUPPORTED_NUMERIC_CLAIM":
            violation_notes.append(
                "[UNSUPPORTED_NUMERIC_CLAIM] An unverified quantitative figure was stripped because it could not be traced to verified agent evidence or certified KPIs."
            )
        else:
            violation_notes.append(f"[{v.code}] {v.message}")
    if report.unsupported_claims and not any("UNSUPPORTED_NUMERIC_CLAIM" in note for note in violation_notes):
        violation_notes.append(
            "Unsupported numeric claim(s) flagged by OutputVerifier and removed prior to response."
        )

    combined = _dedupe_strings(conflict_notes + violation_notes + list(limitations))
    bullet_text = "\n".join(f"- {item}" for item in combined) or "- Verification check failed on synthesized draft."
    summary = (
        "Consolidated response withheld by OutputVerifier due to metric conflict or unverified claim. "
        f"Documented limitations: {'; '.join(combined)}"
    )
    narrative = (
        "### Verification Limitation Notice\n\n"
        "OutputVerifier blocked part or all of the synthesized narrative to prevent unverified or conflicting "
        "business claims from reaching the user:\n\n"
        f"{bullet_text}\n\n"
        "Please narrow the query or resolve conflicting upstream agent definitions before acting on withheld figures."
    )
    return summary[:MAX_SUMMARY_CHARS], narrative[:MAX_SUMMARY_CHARS]


def synthesize_agent_results(
    *,
    user_query: str,
    agent_results: Sequence[AgentResult],
    missing_agents: Optional[Sequence[str]] = None,
    verifier: Optional[OutputVerifier] = None,
    kpi_catalog: Optional[Dict[str, KpiDefinitionEntry]] = None,
    candidate_text_override: Optional[str] = None,
) -> SynthesisOutput:
    """
    Merge domain `AgentResult`s safely, enforce cross-agent consistency and OutputVerifier
    grounding, and return a unified `SynthesisOutput`.
    """
    active_results = [r for r in agent_results if r.status in _ACTIVE_STATUSES]
    degraded_results = [r for r in agent_results if r.status in _DEGRADED_STATUSES]

    catalog = kpi_catalog if kpi_catalog is not None else get_certified_kpi_catalog()
    provenances, badges, prov_unconfirmed = _collect_provenance_and_badges(agent_results)
    caveats, ml_warnings = _collect_caveats(agent_results)
    facts, calc_steps, fact_unconfirmed = _collect_facts_and_steps(active_results, catalog)
    merged_metrics = _merge_metrics(active_results)
    derived_cancel_line = ""
    if (
        isinstance(merged_metrics.get("cancelled_orders"), (int, float))
        and isinstance(merged_metrics.get("total_orders"), (int, float))
        and float(merged_metrics["total_orders"]) > 0
    ):
        cancelled_cnt = int(merged_metrics["cancelled_orders"])
        total_cnt = int(merged_metrics["total_orders"])
        cancel_rate = round((cancelled_cnt / total_cnt) * 100.0, 2)
        merged_metrics["cancellation_rate_pct"] = cancel_rate
        facts.append(
            GroundedFact(
                label="Order Cancellation Rate",
                value=cancel_rate,
                unit="%",
                formula="(cancelled_orders / total_orders) * 100",
                source="Verified Order Metrics",
            )
        )
        calc_steps.append(
            {
                "kpi_id": "KPI-06",
                "name": "Order Cancellation Rate",
                "value": cancel_rate,
                "unit": "%",
                "formula": "(cancelled_orders / total_orders) * 100",
                "source_tables": "orders",
            }
        )
        if "cancel" in (user_query or "").lower():
            derived_cancel_line = (
                f"**Verified Order Cancellation Rate:** {cancel_rate:.2f}% "
                f"({cancelled_cnt:,} cancelled out of {total_cnt:,} total orders)."
            )
    recommendations = _collect_recommendations(active_results)
    data_gaps, limitations, errors = _collect_limitations(agent_results, missing_agents=missing_agents)

    charts: List[ChartSpec] = []
    seen_charts: set[str] = set()
    sql_traces: List[SqlAuditTrace] = []
    table_rows: List[Dict[str, Any]] = []

    for res in active_results:
        for ch in res.charts:
            if ch.title not in seen_charts:
                seen_charts.add(ch.title)
                charts.append(ch)
        sql_traces.extend(res.sql_traces)
        if len(table_rows) < MAX_CONTRACT_TABLE_ROWS and res.table_rows:
            remaining = MAX_CONTRACT_TABLE_ROWS - len(table_rows)
            table_rows.extend(res.table_rows[:remaining])

    has_unconfirmed_leakage = (prov_unconfirmed is False) or fact_unconfirmed
    draft_summary, draft_narrative = _build_draft_narrative(
        user_query=user_query,
        active_results=active_results,
        degraded_results=degraded_results,
        caveats=caveats,
        recommendations=recommendations,
        limitations=limitations,
        has_unconfirmed_leakage=has_unconfirmed_leakage,
    )
    if derived_cancel_line:
        draft_summary = f"{derived_cancel_line} {draft_summary}".strip()[:MAX_SUMMARY_CHARS]
        draft_narrative = f"{derived_cancel_line}\n\n{draft_narrative}".strip()[:MAX_SUMMARY_CHARS]
    text_to_verify = (
        sanitize_text(candidate_text_override)
        if candidate_text_override is not None
        else draft_narrative
    )

    active_verifier = verifier or OutputVerifier(load_default_kpis=True)
    results_for_verifier = active_results if active_results else list(agent_results)
    report = active_verifier.verify(
        text_to_verify,
        facts=facts,
        agent_results=results_for_verifier,
        include_kpi_catalog=True,
        require_non_empty_text=bool(active_results),
    )

    grounding_verified = report.outcome != VerificationOutcome.REJECTED and len(active_results) > 0
    final_summary = draft_summary
    final_narrative = text_to_verify if candidate_text_override is not None else draft_narrative

    if report.outcome == VerificationOutcome.REJECTED:
        grounding_verified = False
        final_summary, final_narrative = _build_rejected_limitation_response(report, limitations)
        limitations = _dedupe_strings(
            limitations
            + [
                (
                    "[UNSUPPORTED_NUMERIC_CLAIM] Unverified numeric figure withheld by OutputVerifier."
                    if v.code == "UNSUPPORTED_NUMERIC_CLAIM"
                    else f"[{v.code}] {v.message}"
                )
                for v in report.violations
            ]
        )
        errors = list(errors) + [
            AgentError(
                code="OUTPUT_VERIFICATION_REJECTED",
                message=sanitize_text(final_summary)[:900],
                agent_id="master_orchestrator",
                recoverable=True,
            )
        ]

    # Determine consolidated AgentStatus accurately
    if not active_results:
        if degraded_results and all(r.status == AgentStatus.BLOCKED for r in degraded_results):
            status = AgentStatus.BLOCKED
        elif degraded_results and all(r.status == AgentStatus.TIMEOUT for r in degraded_results):
            status = AgentStatus.TIMEOUT
        elif degraded_results and all(r.status == AgentStatus.CANCELLED for r in degraded_results):
            status = AgentStatus.CANCELLED
        else:
            status = AgentStatus.ERROR
    elif (
        degraded_results
        or missing_agents
        or any(r.status == AgentStatus.PARTIAL for r in active_results)
        or report.outcome in (VerificationOutcome.PARTIAL, VerificationOutcome.REJECTED)
    ):
        status = AgentStatus.PARTIAL
    else:
        status = AgentStatus.SUCCESS

    return SynthesisOutput(
        consolidated_summary=final_summary,
        consolidated_narrative=final_narrative,
        status=status,
        facts=facts,
        metrics=merged_metrics,
        table_rows=table_rows[:MAX_CONTRACT_TABLE_ROWS],
        charts=charts,
        recommendations=recommendations,
        caveats=caveats,
        provenance=provenances,
        sql_traces=sql_traces,
        errors=errors,
        data_gaps=data_gaps,
        limitations=limitations,
        ml_confidence_warnings=ml_warnings,
        calculation_steps=calc_steps,
        data_source_badges=badges,
        conflicts=list(report.conflicts),
        verification_report=report,
        grounding_verified=grounding_verified,
        is_confirmed_loss=False if has_unconfirmed_leakage else None,
    )

