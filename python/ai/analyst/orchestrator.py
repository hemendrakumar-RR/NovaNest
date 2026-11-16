"""
NovaNest Universal AI Business Analyst & General Assistant Orchestrator
------------------------------------------------------------------------
Orchestrates general knowledge, programming, calculations, project documentation,
and data-grounded business intelligence (safe 9-table SQL, empirical root-cause
analysis, decision simulations, and Next Best Action recommendations).
Never forces general technical questions into business database queries.
"""

import datetime
from typing import Dict, Any, List, Optional
import pandas as pd

from python.ai.provider.factory import get_ai_provider
from python.ai.provider.base import ProviderStatus
from python.ai.analyst.universal_router import classify_query
from python.ai.analyst.universal_engine import compute_calculation, get_offline_knowledge_response
from python.ai.analyst.data_grounding import retrieve_grounded_business_context
from python.ai.analyst.sql_agent import (
    build_readonly_sqlite_connection,
    execute_safe_sql,
    validate_and_sanitize_sql,
)
from python.ai.analyst.sql_ast import starts_like_sql_statement
from python.ai.analyst.root_cause import perform_root_cause_analysis
from python.ai.analyst.simulation_agent import execute_conversational_simulation
from python.ai.analyst.conversation_manager import (
    record_turn,
    get_session_history,
    resolve_follow_up_query,
)
from python.ai.conversational.nl_to_sql import generate_sql


def _normalize_nba_record(rec: Dict[str, Any], source_category: str) -> Dict[str, Any]:
    """Convert raw Next Best Action engine output into the standardized orchestrator recommendation card."""
    target_type = str(rec.get("target_type", source_category))
    entity = str(rec.get("entity_name") or rec.get("entity_id") or target_type)
    condition = str(rec.get("detected_condition", ""))
    action = str(rec.get("recommended_action", ""))
    reason = str(rec.get("reason", ""))
    priority = str(rec.get("priority", "Medium"))

    cond_lower = (condition + " " + action + " " + reason).lower()

    # Preserve domain keywords & attach honest ML / verification confidence caveats
    if "churn" in cond_lower or target_type == "Customer":
        if "high clv" in cond_lower:
            title = f"VIP High-CLV Customer Retention ({entity})"
        else:
            title = f"Customer Churn Re-Engagement ({entity})"
        confidence = "Heuristic RFM/CLV Triage (Churn v2 ROC-AUC 0.5161 — NEEDS_MORE_DATA)"
        expected_impact = condition or "Targets high-value at-risk cohort with measurable holdout uplift"
    elif "leakage" in cond_lower or "discount" in cond_lower:
        title = f"Margin & Promotional Leakage Audit ({entity})"
        confidence = "Investigation Candidate (Unconfirmed Loss — is_confirmed_loss=False)"
        expected_impact = f"{condition} — Verify merchant vs. platform promo funding split before claiming net recovery"
    elif target_type == "Restaurant":
        title = f"Partner Restaurant Remediation ({entity})"
        confidence = f"{priority} Priority (Deterministic Health & Cancellation Audit)"
        expected_impact = condition or reason
    else:
        title = f"{target_type} Optimization ({entity})"
        confidence = f"{priority} Priority (Empirical Telemetry Alert)"
        expected_impact = reason or condition

    return {
        "title": title,
        "target_type": target_type,
        "entity_id": str(rec.get("entity_id", "")),
        "evidence": condition or reason,
        "expected_impact": expected_impact,
        "confidence": confidence,
        "action": action,
        "priority": priority,
    }


def _generate_grounded_recommendations(
    query_text: str,
    data: Optional[Dict[str, Any]],
) -> List[Dict[str, Any]]:
    """
    Generate live recommendations from `python/decision/next_best_action.py`
    and supporting customer/restaurant intelligence engines.
    Zero hardcoded recommendations or fabricated financial impact figures.
    """
    if not data:
        return []

    orders = data.get("orders", pd.DataFrame())
    customers = data.get("customers", pd.DataFrame())
    restaurants = data.get("restaurants", pd.DataFrame())
    ratings = data.get("ratings_reviews", pd.DataFrame())
    churn_df = data.get("customer_churn_predictions", pd.DataFrame())
    alerts_df = data.get("operational_alerts", pd.DataFrame())
    leakage_df = data.get("revenue_leakage", pd.DataFrame())

    from python.decision.next_best_action import (
        generate_customer_next_best_actions,
        generate_restaurant_next_best_actions,
        generate_operational_next_best_actions,
    )

    cust_cards: List[Dict[str, Any]] = []
    rest_cards: List[Dict[str, Any]] = []
    ops_cards: List[Dict[str, Any]] = []

    # 1. Customer NBAs
    try:
        if not orders.empty and not customers.empty and churn_df is not None and not churn_df.empty:
            from python.intelligence.customer.clv import calculate_customer_clv
            from python.intelligence.customer.rfm import calculate_advanced_rfm

            clv_df = calculate_customer_clv(orders, customers)
            rfm_df = calculate_advanced_rfm(orders, customers)
            for item in generate_customer_next_best_actions(churn_df, clv_df, rfm_df):
                cust_cards.append(_normalize_nba_record(item, "Customer"))
    except Exception:
        pass

    # 2. Restaurant NBAs
    try:
        if not orders.empty and not restaurants.empty:
            from python.intelligence.restaurant.health_score import calculate_restaurant_health_score
            from python.intelligence.restaurant.risk_detection import detect_restaurant_risks
            from python.intelligence.restaurant.benchmarking import calculate_restaurant_benchmarks

            ratings_arg = ratings if ratings is not None and not ratings.empty else None
            health_df = calculate_restaurant_health_score(restaurants, orders, ratings_arg)
            risk_df = detect_restaurant_risks(health_df)
            bench_df = calculate_restaurant_benchmarks(health_df)
            for item in generate_restaurant_next_best_actions(risk_df, bench_df):
                rest_cards.append(_normalize_nba_record(item, "Restaurant"))
    except Exception:
        pass

    # 3. Operational & Leakage NBAs
    try:
        a_arg = alerts_df if alerts_df is not None else pd.DataFrame()
        l_arg = leakage_df if leakage_df is not None else pd.DataFrame()
        if not a_arg.empty or not l_arg.empty:
            for item in generate_operational_next_best_actions(a_arg, l_arg):
                ops_cards.append(_normalize_nba_record(item, "Operations"))
    except Exception:
        pass

    ql = (query_text or "").lower()
    if any(k in ql for k in ["retention", "churn", "customer", "vip", "clv"]):
        ordered = cust_cards + ops_cards + rest_cards
    elif any(k in ql for k in ["profit", "profitability", "margin", "leakage", "discount", "revenue", "financial"]):
        # Prioritize leakage / financial alerts, then high-CLV customer retention, then restaurant margin quality
        leakage_first = [c for c in ops_cards if "leakage" in c["title"].lower() or "margin" in c["title"].lower()]
        other_ops = [c for c in ops_cards if c not in leakage_first]
        ordered = leakage_first + cust_cards + rest_cards + other_ops
    elif any(k in ql for k in ["restaurant", "partner", "merchant", "kitchen", "rating"]):
        ordered = rest_cards + ops_cards + cust_cards
    elif any(k in ql for k in ["delivery", "eta", "rider", "delay", "cancel", "operation", "sla"]):
        ordered = ops_cards + rest_cards + cust_cards
    else:
        ordered = ops_cards + cust_cards + rest_cards

    return ordered[:6]


def analyze_business_inquiry(
    question: Optional[str] = None,
    data: Optional[Dict[str, Any]] = None,
    source_name: str = "CSV File Store",
    sqlite_conn: Any = None,
    session_id: str = "default_session",
    query: Optional[str] = None,
    ai_provider: Any = None,
    principal: Optional[Any] = None,
) -> Dict[str, Any]:
    """
    Main entry point for NovaNest Universal AI Assistant.
    Seamlessly handles general technical questions, programming, math, project architecture,
    multi-domain business intelligence, safe 9-table SQL, RCA, simulations, and live NBAs.
    """
    raw_q = (question or query or "").strip()
    if not raw_q:
        return {"error": "Query cannot be empty"}

    # 1. Resolve follow-up query with caller-principal isolated session memory
    augmented_q, resolved_intent, last_topic = resolve_follow_up_query(
        raw_q,
        session_id,
        principal=principal,
    )

    # 2. Universal Query Classification
    classification = classify_query(augmented_q, last_topic)
    intent = resolved_intent or classification["intent"]
    requires_business_data = classification.get("requires_business_data", False)

    # Payload components
    sql_payload = None
    data_rows: List[Dict[str, Any]] = []
    rca_payload = None
    sim_payload = None
    recommendations: List[Dict[str, Any]] = []
    verified_metrics: List[Dict[str, Any]] = []
    suggested_chart = None
    context_topic = last_topic or "general"
    answer_text = ""
    provenance = {
        "data_source": source_name if requires_business_data else "General Knowledge & Reasoning Engine",
        "access_mode": "Read-Only Secure" if requires_business_data else "Open AI Reasoning",
    }

    # 3. Handle Business Data Intents vs General Intents

    # A. SIMULATION INTENT
    if intent == "SIMULATION":
        context_topic = "simulation"
        sim_payload = execute_conversational_simulation(augmented_q, data)
        answer_text = sim_payload["summary"]
        if sim_payload.get("suggested_chart"):
            suggested_chart = sim_payload["suggested_chart"]
        recommendations = [
            {
                "title": sim_payload["recommendation"]["Decision"],
                "target_type": "Simulation",
                "entity_id": "Policy Lever",
                "evidence": f"Baseline vs Simulated Platform Revenue impact: {sim_payload['financial_impact']['revenue_diff']:+,.2f}",
                "expected_impact": sim_payload["recommendation"]["Expected_Benefit"],
                "confidence": "High (Deterministic Simulation)",
                "action": "Review scenario policy levers in Decision Simulator Lab",
                "priority": "High",
            }
        ]

    # B. ROOT CAUSE ANALYSIS INTENT
    elif intent == "ROOT_CAUSE":
        q_low = augmented_q.lower()
        if "cancel" in q_low:
            context_topic = "cancellations"
        elif any(k in q_low for k in ["leakage", "margin", "profit", "discount"]):
            context_topic = "financial_leakage"
        elif any(k in q_low for k in ["churn", "retention", "customer"]):
            context_topic = "customers"
        elif any(k in q_low for k in ["restaurant", "partner", "merchant", "rating"]):
            context_topic = "restaurants"
        else:
            context_topic = "operations"

        rca_payload = perform_root_cause_analysis(augmented_q, data or {})
        grounded_ctx = retrieve_grounded_business_context(augmented_q, data or {}, source_name)
        verified_metrics = grounded_ctx.get("verified_metrics", [])
        data_rows = grounded_ctx.get("table_data", [])[:15]
        if grounded_ctx.get("suggested_chart") is not None:
            suggested_chart = grounded_ctx.get("suggested_chart")

        facts_bullet = "\n".join([f"- **Observed Fact:** {f}" for f in rca_payload["observed_facts"]])
        factors_bullet = (
            "\n".join(
                [
                    f"- **Contributing Factor ({fac['correlation_strength']} correlation):** {fac['factor']} — *{fac['evidence']}*"
                    for fac in rca_payload["contributing_factors"]
                ]
            )
            or "- No secondary correlation drivers exceeded minimum signal thresholds in current data."
        )
        uncert_bullet = "\n".join([f"- **Uncertainty / Caveat:** {u}" for u in rca_payload["uncertainties"]])
        actions_bullet = "\n".join([f"- {act}" for act in rca_payload["recommended_actions"]])

        recommendations = _generate_grounded_recommendations(augmented_q, data)[:3]

        answer_text = (
            f"### Empirical Root-Cause Diagnostic: {rca_payload['investigation_target']}\n\n"
            f"**1. Verified Observed Facts**\n{facts_bullet}\n\n"
            f"**2. Contributing Factors & Strength**\n{factors_bullet}\n\n"
            f"**3. Data Limitations & Model Uncertainties**\n{uncert_bullet}\n\n"
            f"**4. Recommended Interventions**\n{actions_bullet}"
        )

    # C. NATURAL LANGUAGE TO SAFE SQL INTENT
    elif intent == "NL2SQL":
        context_topic = (
            "cancellations"
            if "cancel" in augmented_q.lower()
            else ("restaurants" if "restaurant" in augmented_q.lower() else "financial")
        )
        direct_sql = starts_like_sql_statement(augmented_q)
        raw_sql = augmented_q if direct_sql else generate_sql(augmented_q)

        if raw_sql:
            is_valid, sanitized, val_msg = validate_and_sanitize_sql(raw_sql)
            if not is_valid:
                sql_payload = {
                    "query": sanitized or raw_sql,
                    "valid": False,
                    "validation_message": val_msg,
                }
                answer_text = f"⚠️ **SQL Security Block**: {val_msg}"
            else:
                local_conn = sqlite_conn
                owned_conn = False
                if local_conn is None and data:
                    local_conn = build_readonly_sqlite_connection(data)
                    owned_conn = True

                if local_conn is not None:
                    try:
                        df, exec_msg = execute_safe_sql(sanitized, local_conn)
                    finally:
                        if owned_conn:
                            local_conn.close()

                    if df is None:
                        sql_payload = {
                            "query": sanitized,
                            "valid": False,
                            "validation_message": exec_msg,
                        }
                        answer_text = f"⚠️ **SQL Execution Blocked/Failed**: {exec_msg}"
                    elif not df.empty:
                        data_rows = df.head(15).to_dict(orient="records")
                        table_md = df.head(8).to_markdown(index=False)
                        verified_metrics = [
                            {"label": "Records Returned", "value": f"{len(df):,}", "provenance": source_name},
                            {"label": "Execution Mode", "value": "Safe Read-Only SQL (9-Table Parity)", "provenance": "Database Engine"},
                        ]
                        answer_text = (
                            f"Here are the verified database results for your inquiry:\n\n"
                            f"{table_md}\n\n"
                            f"*Verified against {source_name} using secure read-only SQL: `{sanitized}`*"
                        )
                        sql_payload = {
                            "query": sanitized,
                            "valid": True,
                            "validation_message": "Safe read-only query executed",
                        }
                    else:
                        answer_text = f"The query `{sanitized}` executed successfully, but returned 0 rows in the active dataset."
                        sql_payload = {
                            "query": sanitized,
                            "valid": True,
                            "validation_message": "Safe read-only query executed",
                        }
                else:
                    grounded_ctx = retrieve_grounded_business_context(augmented_q, data or {}, source_name)
                    answer_text = grounded_ctx.get("context_summary", "Database engine unavailable.")
                    verified_metrics = grounded_ctx.get("verified_metrics", [])
                    data_rows = grounded_ctx.get("table_data", [])[:15]
        else:
            grounded_ctx = retrieve_grounded_business_context(augmented_q, data or {}, source_name)
            answer_text = grounded_ctx.get("context_summary", "Query completed against active datasets.")
            verified_metrics = grounded_ctx.get("verified_metrics", [])
            data_rows = grounded_ctx.get("table_data", [])[:15]
            suggested_chart = grounded_ctx.get("suggested_chart")

    # D. RECOMMENDATIONS INTENT (LIVE NEXT BEST ACTION ENGINE)
    elif intent == "RECOMMENDATIONS":
        context_topic = (
            "customers"
            if any(k in augmented_q.lower() for k in ["retention", "churn", "vip"])
            else ("cancellations" if "cancel" in augmented_q.lower() else "financial")
        )
        grounded_ctx = retrieve_grounded_business_context(augmented_q, data or {}, source_name)
        verified_metrics = grounded_ctx.get("verified_metrics", [])
        suggested_chart = grounded_ctx.get("suggested_chart")
        data_rows = grounded_ctx.get("table_data", [])[:15]

        recommendations = _generate_grounded_recommendations(augmented_q, data)
        if recommendations:
            rec_lines = "\n".join(
                [
                    f"- **{r['title']} ({r['priority']}):** {r['action']} "
                    f"(*Evidence:* {r['evidence']} | *Caveat/Confidence:* {r['confidence']})"
                    for r in recommendations
                ]
            )
            answer_text = (
                f"### Data-Grounded Strategic Recommendations (Next Best Action Engine)\n\n"
                f"Addressing **\"{augmented_q}\"** from verified live datasets:\n\n{rec_lines}"
            )
        else:
            answer_text = (
                f"Insufficient live dataset records to compute quantitative Next Best Actions for \"{augmented_q}\". "
                "Please ensure orders, customers, restaurants, and operational alerts tables are loaded."
            )

    # E. BUSINESS DATA INTELLIGENCE (SINGLE & MULTI-DOMAIN + EXECUTIVE OVERVIEW)
    elif intent == "BUSINESS_DATA":
        grounded_ctx = retrieve_grounded_business_context(augmented_q, data or {}, source_name)
        verified_metrics = grounded_ctx.get("verified_metrics", [])
        suggested_chart = grounded_ctx.get("suggested_chart")
        data_rows = grounded_ctx.get("table_data", [])[:15]
        context_topic = grounded_ctx.get("domain", "general")
        answer_text = grounded_ctx.get("context_summary", "")
        provenance = grounded_ctx.get("provenance", provenance)

        if grounded_ctx.get("domain") in ("business_overview", "multi_domain") and data:
            recommendations = _generate_grounded_recommendations(augmented_q, data)[:3]

    # F. CALCULATION INTENT
    elif intent == "CALCULATION":
        context_topic = "math"
        calc_res = compute_calculation(augmented_q)
        if calc_res:
            answer_text = calc_res["explanation"]
        else:
            offline_k = get_offline_knowledge_response(augmented_q, "CALCULATION")
            answer_text = offline_k["answer"]

    # G. NON-BUSINESS GENERAL KNOWLEDGE, PROGRAMMING, GREETING, PROJECT
    else:
        context_topic = intent.lower()
        offline_k = get_offline_knowledge_response(augmented_q, intent)
        answer_text = offline_k["answer"]

    # 4. Generative AI Synthesis (Google Gemini API)
    if ai_provider is None:
        ai_provider = get_ai_provider()
    provider_status = ProviderStatus.UNCONFIGURED

    is_conf = False
    if hasattr(ai_provider, "is_configured"):
        is_conf = ai_provider.is_configured()
    elif hasattr(ai_provider, "get_status"):
        st = ai_provider.get_status().get("status")
        is_conf = st in ["ready", "mock", "error"]
    else:
        is_conf = True

    if is_conf:
        if requires_business_data:
            system_instruction = (
                "You are NovaNest AI, an executive decision intelligence assistant and senior business analyst. "
                "You provide data-grounded business intelligence. Never hallucinate numbers, restaurants, or financial figures. "
                "Rely strictly on the verified numbers, unverified-leakage caveats, and calculations provided in the context. "
                "Format your answer with clear markdown bullet points and professional enterprise tone."
            )
            prompt = (
                f"Verified Business Metrics Context:\n"
                f"{answer_text}\n\n"
                f"User Question: {augmented_q}\n\n"
                f"Provide a clear, executive-level synthesis answering the user's inquiry based strictly on these verified facts."
            )
        else:
            system_instruction = (
                "You are NovaNest AI, an advanced universal AI assistant and senior technical consultant. "
                "You excel at software engineering (Python, SQL, TypeScript, Java), data science, mathematics, "
                "general knowledge, and business strategy. "
                "Provide direct, articulate, insightful answers matching the depth of the user's inquiry. "
                "Format code in clean markdown code blocks with language tags (e.g. ```python), "
                "use tables for structured comparisons, and explain complex concepts step-by-step with clear examples."
            )
            prompt = augmented_q

        history = get_session_history(session_id, limit=6, principal=principal)

        try:
            if hasattr(ai_provider, "generate"):
                ai_res = ai_provider.generate(prompt=prompt, system_instruction=system_instruction, history=history)
            elif hasattr(ai_provider, "generate_response"):
                raw_txt = ai_provider.generate_response(prompt)
                from python.ai.provider.base import AIProviderResult

                ai_res = AIProviderResult(
                    text=raw_txt,
                    status=ProviderStatus.READY,
                    provider_name="custom",
                    model_name=getattr(ai_provider, "model_name", "custom"),
                )
            else:
                ai_res = None

            if ai_res:
                if ai_res.status == ProviderStatus.READY and ai_res.text:
                    answer_text = ai_res.text
                    provider_status = ProviderStatus.READY
                elif ai_res.status == ProviderStatus.MOCK:
                    answer_text = f"{answer_text}\n\n{ai_res.text}" if answer_text else ai_res.text
                    provider_status = ProviderStatus.MOCK
                elif ai_res.status == ProviderStatus.ERROR:
                    provider_status = ProviderStatus.ERROR
                    answer_text = f"⚠️ **AI Provider Notice:** {ai_res.text}\n\n---\n\n{answer_text}"
                else:
                    provider_status = ai_res.status
        except Exception as ex:
            provider_status = ProviderStatus.ERROR
            answer_text = f"⚠️ **AI Provider Notice:** {str(ex)}\n\n---\n\n{answer_text}"
    else:
        provider_status = ProviderStatus.UNCONFIGURED

    # 5. Context-Aware Follow-Up Suggestions (100% grounded, no fake city names)
    if intent == "PROGRAMMING":
        follow_up_suggestions = [
            "How do I add unit tests for this code?",
            "What is the time and space complexity?",
            "Can you optimize this implementation?",
        ]
    elif intent == "CALCULATION":
        follow_up_suggestions = [
            "Calculate compound interest on 5000 at 12% for 3 years",
            "What is the difference between simple and compound interest?",
            "Calculate monthly EMI on this principal",
        ]
    elif intent == "GENERAL":
        follow_up_suggestions = [
            "Can you provide a real-world example?",
            "What are the main advantages and disadvantages?",
            "Explain this step-by-step in more detail",
        ]
    elif intent == "GREETING":
        follow_up_suggestions = [
            "Explain machine learning in simple words",
            "What is the difference between SQL and NoSQL?",
            "Analyze my business performance.",
            "What happens if commission increases by 2%?",
        ]
    elif context_topic == "cancellations":
        follow_up_suggestions = [
            "Which restaurant has the highest cancellation rate?",
            "Why are cancellations higher in Coimbatore?",
            "Simulate what happens if cancellations fall by 2%",
        ]
    elif context_topic in ("financial", "financial_leakage", "multi_domain", "business_overview") or intent == "BUSINESS_DATA":
        follow_up_suggestions = [
            "Where is potential revenue leakage occurring?",
            "Compare financial and operational performance.",
            "Recommend actions to improve profitability.",
        ]
    elif context_topic == "customers":
        follow_up_suggestions = [
            "How many high churn customers do we have?",
            "Suggest ways to improve customer retention.",
            "Why are customers churning?",
        ]
    elif context_topic == "restaurants":
        follow_up_suggestions = [
            "Which restaurants need attention?",
            "What are the top 5 restaurants by revenue?",
            "Why are certain restaurants underperforming?",
        ]
    else:
        follow_up_suggestions = [
            "Why is delivery performance declining?",
            "Which restaurants need attention?",
            "What happens if delivery times decrease by 10%?",
        ]

    # 6. Record Turn in Caller-Scoped, Redacted Session History (no raw DataFrames stored)
    record_turn(session_id, "user", raw_q, intent, context_topic, principal=principal)
    record_turn(session_id, "assistant", answer_text, intent, context_topic, principal=principal)

    prov_stat_val = provider_status.value if hasattr(provider_status, "value") else str(provider_status)

    return {
        "question": raw_q,
        "resolved_query": augmented_q if augmented_q != raw_q else None,
        "intent": intent,
        "route": intent,
        "domains": classification.get("domains", []),
        "is_multi_domain": classification.get("is_multi_domain", False),
        "requires_business_data": requires_business_data,
        "category": classification.get("category", "general"),
        "answer": answer_text,
        "provider_status": prov_stat_val,
        "verified_metrics": verified_metrics,
        "suggested_chart": suggested_chart,
        "sql": sql_payload,
        "sql_query": sql_payload.get("query", "") if sql_payload else "",
        "sql_valid": sql_payload.get("valid", True) if sql_payload else True,
        "validation_message": sql_payload.get("validation_message", "") if sql_payload else "",
        "data_rows": data_rows,
        "root_cause_analysis": rca_payload,
        "simulation_results": sim_payload,
        "recommendations": recommendations,
        "follow_up_suggestions": follow_up_suggestions,
        "insights": [r.get("title") for r in recommendations],
        "provenance": provenance,
        "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat(),
    }


class AskNovaNestOrchestrator:
    """
    Unified orchestrator class for Ask NovaNest AI.
    Provides a clean, testable interface for querying the multi-mode universal intelligence engine.
    """

    def __init__(self, data: Optional[Dict[str, Any]] = None):
        self._data = data

    def process_query(
        self,
        query: str,
        session_id: str = "default_session",
        ai_provider: Any = None,
        principal: Optional[Any] = None,
    ) -> Dict[str, Any]:
        if self._data is None:
            try:
                from api.loader import load_data

                self._data, source_name = load_data()
            except Exception:
                try:
                    from data_loader import load_data

                    self._data, source_name = load_data()
                except Exception:
                    self._data = {}
                    source_name = "CSV File Store"
        else:
            source_name = "CSV File Store"

        return analyze_business_inquiry(
            query=query,
            data=self._data,
            source_name=source_name,
            session_id=session_id,
            ai_provider=ai_provider,
            principal=principal,
        )
