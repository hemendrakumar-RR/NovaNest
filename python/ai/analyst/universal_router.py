"""
NovaNest Universal Query Classifier & Intent Router
---------------------------------------------------
Intelligently classifies user questions into general knowledge, programming,
mathematical calculations, project architecture, business data intelligence,
multi-domain comparisons, root-cause analysis, recommendations, and decision simulations.
Prevents non-business technical and general questions from being forced into database queries.
"""

import re
from typing import Dict, Any, List, Optional


def _extract_router_domains(q_lower: str) -> List[str]:
    """Identify specific NovaNest business domains referenced by a query."""
    domains: List[str] = []

    if any(k in q_lower for k in ["leakage", "subsidy", "subsidies", "coupon", "margin deficit", "excessive discount", "burn", "drain"]):
        domains.append("financial_leakage")
    if any(k in q_lower for k in ["cancel", "cancellation", "rejected", "failed order"]):
        domains.append("cancellations")
    if any(k in q_lower for k in ["revenue", "gmv", "profit", "profitability", "sales", "margin", "income", "aov", "financial", "earnings", "commission", "order volume", "order count", "orders placed", "total orders"]):
        if not ("revenue leakage" in q_lower and "financial" not in q_lower and "profit" not in q_lower and "operational" not in q_lower):
            domains.append("financial")
    if any(k in q_lower for k in ["churn", "retention", "clv", "lifetime value", "rfm", "customer", "customers", "vip"]) or re.search(r"\bcust-\d+\b", q_lower):
        domains.append("customers")
    if any(k in q_lower for k in ["restaurant", "restaurants", "partner", "merchant", "kitchen", "rating", "cuisine"]) or re.search(r"\brest-\d+\b", q_lower):
        domains.append("restaurants")
    if any(k in q_lower for k in ["delivery", "deliveries", "eta", "rider", "riders", "fleet", "delay", "delays", "dispatch", "duration", "speed", "operational", "operations", "sla", "logistics"]) or re.search(r"\brider-\d+\b", q_lower):
        domains.append("operations")
    if any(
        k in q_lower
        for k in [
            "business performance",
            "analyze my business",
            "analyse my business",
            "analyze business",
            "how is business",
            "how is my business",
            "how is our business",
            "overall performance",
            "platform performance",
            "overview",
            "executive summary",
            "our metrics",
            "all metrics",
            "business health",
        ]
    ):
        if "business_overview" not in domains:
            domains.append("business_overview")

    # Disambiguate "delivery fee" revenue inquiries without operational keywords
    if "financial" in domains and "operations" in domains and not any(
        w in q_lower for w in ["compare", "both", "and operational", "and delivery", "and financial", "vs", "across"]
    ):
        if "delivery fee" in q_lower and "sla" not in q_lower and "eta" not in q_lower and "delay" not in q_lower:
            domains = [d for d in domains if d != "operations"]

    return domains


def _make_result(
    intent: str,
    category: str,
    requires_business_data: bool,
    description: str,
    domains: Optional[List[str]] = None,
) -> Dict[str, Any]:
    doms = domains or []
    return {
        "intent": intent,
        "category": category,
        "requires_business_data": requires_business_data,
        "description": description,
        "domains": doms,
        "is_multi_domain": len(doms) > 1,
    }


def classify_query(query: str, last_topic: Optional[str] = None) -> Dict[str, Any]:
    """
    Classifies user inquiry into intent, category, matched business domains,
    and whether business data access is needed.
    """
    q = (query or "").strip()
    q_lower = q.lower()

    # 1. GREETING & CASUAL CONVERSATION
    greeting_patterns = [
        r"^(hi|hello|hey|greetings|howdy|hola)(\s+there)?(!|\.|\?)?$",
        r"^(good\s+(morning|afternoon|evening|day))(!|\.|\?)?$",
        r"^how\s+are\s+you(\s+doing)?(\s+today)?(\?)?$",
        r"^(hi|hello|hey)[,\s]+how\s+are\s+you.*",
        r"^(who\s+are\s+you|what\s+is\s+your\s+name|what\s+can\s+you\s+do|tell\s+me\s+about\s+yourself)(\?)?$",
        r"^(thank\s+you|thanks|great\s+job|awesome|bye|goodbye)(!|\.|\?)?$",
    ]
    if any(re.search(pat, q_lower) for pat in greeting_patterns):
        return _make_result(
            "GREETING",
            "casual",
            False,
            "Casual greeting and conversational assistant introduction",
        )

    # 2. PROGRAMMING & TECHNICAL QUESTIONS
    code_indicators = [
        "write a python", "write python", "python program", "python code", "python script",
        "write a program", "write a function", "write code", "write a script", "write an algorithm",
        "in python", "in java", "in javascript", "in typescript", "in c++", "in golang", "in rust",
        "how to code", "how to program", "how do i code", "code snippet",
        "fix this error", "nullpointerexception", "syntaxerror", "typeerror", "indexerror",
        "how to debug", "regex for", "sql query to find", "write sql query",
        "write a class", "async/await", "list comprehension", "lambda function",
        "recursion", "sorting algorithm", "binary search", "pandas dataframe",
        "rest api", "fastapi route", "react component", "dockerfile", "git commit",
        "what is python", "difference between sql and nosql",
    ]
    if any(k in q_lower for k in code_indicators):
        return _make_result(
            "PROGRAMMING",
            "technical",
            False,
            "Programming, code generation, or software engineering explanation",
        )

    # 3. MATHEMATICAL & FINANCIAL CALCULATIONS
    calc_indicators = [
        "calculate compound interest", "compound interest on", "compound interest",
        "calculate simple interest", "simple interest on",
        "calculate ", "compute ", "what is 2000 at", "what is the sum of",
        "standard deviation of", "derivative of", "integral of",
        "percentage increase", "percentage decrease",
    ]
    if any(k in q_lower for k in calc_indicators) or (
        re.search(r"\bcalculate\b|\bcompute\b|\bsolve\b", q_lower) and re.search(r"\d+", q_lower)
    ):
        return _make_result(
            "CALCULATION",
            "mathematics",
            False,
            "Mathematical, statistical, or financial formula calculation",
        )

    # 4. PROJECT KNOWLEDGE (NOVANEST SPECIFIC ARCHITECTURE)
    project_indicators = [
        "what is novanest", "how does novanest work", "novanest architecture",
        "explain novanest", "features of novanest", "digital twin in novanest",
        "decision simulator in novanest", "tech stack of novanest",
        "how is the project built", "what models are used in novanest",
        "tell me about novanest", "about this project", "project architecture",
    ]
    if any(k in q_lower for k in project_indicators):
        return _make_result(
            "PROJECT_KNOWLEDGE",
            "project",
            False,
            "NovaNest architecture, design patterns, and platform components",
        )

    domains = _extract_router_domains(q_lower)

    # 5. DECISION SIMULATOR (WHAT-IF SCENARIOS)
    simulation_indicators = [
        "what happens if", "what if", "simulate", "simulation", "scenario",
        "if we change", "if commission", "if delivery fee", "if discount",
        "if demand", "if retention", "if cancel", "if delivery time",
    ]
    if any(k in q_lower for k in simulation_indicators):
        if any(
            w in q_lower
            for w in [
                "commission", "fee", "discount", "demand", "delivery time", "eta",
                "churn", "retention", "price", "spending", "cancel", "aov", "rider", "prep",
            ]
        ):
            return _make_result(
                "SIMULATION",
                "business_simulation",
                True,
                "Decision Simulator scenario modeling",
                domains=domains or ["simulation"],
            )

    # 6. ROOT-CAUSE ANALYSIS (WHY BUSINESS ANOMALIES OR DECLINES OCCURRED)
    rca_starters = [
        "why did", "why are", "why is", "root cause", "what caused",
        "reason for", "reason behind", "what is driving", "what drives",
    ]
    rca_targets = [
        "cancel", "revenue", "loss", "leakage", "delay", "slow", "churn",
        "drop", "spike", "underperform", "declining", "decline", "decreasing",
        "increasing", "worsening", "degrading", "delivery performance", "sla",
        "eta", "rating", "margin", "profitability",
    ]
    if any(w in q_lower for w in rca_starters) and (any(m in q_lower for m in rca_targets) or bool(domains)):
        return _make_result(
            "ROOT_CAUSE",
            "root_cause_analysis",
            True,
            "Empirical root-cause investigation using multi-table platform evidence",
            domains=domains,
        )

    # 7. EXPLICIT SQL GENERATION / ENTITY RANKING DATABASE INQUIRIES
    sql_starters = ["select ", "with ", "show me all ", "list all ", "which restaurants "]
    if (
        any(q_lower.startswith(w) for w in sql_starters)
        or "which restaurants" in q_lower
        or re.match(
            r"^\s*(?:/\*.*?\*/\s*|--[^\n]*\n\s*|\(*\s*)*(?:SELECT|WITH|DROP|DELETE|UPDATE|INSERT|ALTER|TRUNCATE|CREATE|REPLACE|ATTACH|DETACH|PRAGMA)\b",
            q,
            re.IGNORECASE | re.DOTALL,
        )
    ):
        return _make_result(
            "NL2SQL",
            "business_sql",
            True,
            "Natural language to safe SQL query",
            domains=domains,
        )

    # 8. STRATEGIC RECOMMENDATIONS & ACTION PLANNING
    rec_starters = [
        "suggest ways", "how can we improve", "how to improve", "ways to improve",
        "recommendations for", "suggest strategies", "recommend actions",
        "recommended actions", "what actions should", "action plan to",
        "how to reduce", "how do we reduce", "how to increase", "how can we boost",
        "improve profitability", "improve retention", "reduce churn", "reduce cancellations",
    ]
    if any(k in q_lower for k in rec_starters) or (
        re.search(r"\b(recommend|suggest|advise)\b", q_lower) and (bool(domains) or "action" in q_lower)
    ):
        return _make_result(
            "RECOMMENDATIONS",
            "strategic_recommendations",
            True,
            "Data-backed strategic recommendations and Next Best Action interventions",
            domains=domains or ["financial", "operations", "customers"],
        )

    # 9. BUSINESS DATA INTELLIGENCE (BROAD, COMPARATIVE & METRIC QUERIES)
    explicit_business_signals = [
        "our revenue", "total revenue", "gross gmv", "platform revenue",
        "our orders", "cancellation rate", "how many orders", "cancellations", "order volume", "order count", "total orders", "orders placed",
        "customer churn", "high churn customers", "churn risk", "vip customers", "clv capital", "lifetime value",
        "restaurant health", "merchant partners", "underperforming restaurants",
        "top 5 restaurants", "top restaurants", "delivery time", "average eta",
        "rider allocation", "revenue leakage", "coupon leakage", "discount cost",
        "in our database", "in our platform", "in our dataset", "our business metrics",
        "customer retention", "improve customer retention", "business performance",
        "operational performance", "financial performance", "delivery performance",
    ]
    has_question_metric_intent = bool(
        domains
        and (
            any(
                w in q_lower
                for w in [
                    "our ", "my ", "we ", "us ", "how many", "how is", "what is", "what are",
                    "compare", "analyze", "analyse", "show", "total", "average", "rate",
                    "performance", "count", "breakdown", "split", "trend", "explain customer churn",
                ]
            )
            or any(k in q_lower for k in explicit_business_signals)
        )
    )
    if any(k in q_lower for k in explicit_business_signals) or has_question_metric_intent:
        return _make_result(
            "BUSINESS_DATA",
            "multi_domain_intelligence" if len(domains) > 1 else "business_intelligence",
            True,
            "Data-grounded business intelligence from project data",
            domains=domains,
        )

    # 10. GENERAL KNOWLEDGE / CONCEPTS / OPEN-ENDED REASONING
    return _make_result(
        "GENERAL",
        "general_knowledge",
        False,
        "General knowledge, conceptual explanation, or open-ended reasoning",
    )
