"""
NovaNest Prescriptive Decision Intelligence Contracts (Phase 08)
----------------------------------------------------------------
Defines standardized data contracts, enums, financial calculation structures,
and lifecycle state machine models for prescriptive decision intelligence.
"""

from __future__ import annotations

from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, ConfigDict, Field, field_validator
import uuid
from datetime import datetime, timezone


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def make_rec_id(prefix: str = "REC-") -> str:
    token = uuid.uuid4().hex[:8].upper()
    return f"{prefix}{token}"


class RecommendationLifecycleStatus(str, Enum):
    PROPOSED = "Proposed"
    APPROVED = "Approved"
    REJECTED = "Rejected"
    IN_PROGRESS = "In progress"
    IMPLEMENTED = "Implemented"
    OUTCOME_MEASURED = "Outcome measured"


class PrescriptiveDomain(str, Enum):
    CUSTOMER_RETENTION = "customer_retention"
    REVENUE_OPTIMIZATION = "revenue_optimization"
    RESTAURANT_OPTIMIZATION = "restaurant_optimization"
    RIDER_LOGISTICS = "rider_logistics"
    CROSS_DOMAIN = "cross_domain"


class ConfidenceTier(str, Enum):
    HIGH = "HIGH"
    MODERATE = "MODERATE"
    LOW_EMPIRICAL = "LOW_EMPIRICAL"
    OPERATIONAL_GATED = "OPERATIONAL_GATED"


class FinancialImpactBreakdown(BaseModel):
    """Rigorous financial calculation structure for prescriptive recommendations."""

    model_config = ConfigDict(extra="forbid")

    gross_benefit: float = Field(default=0.0, description="Gross projected savings or revenue uplift (₹)")
    implementation_cost: float = Field(default=0.0, description="Estimated operational/promotional cost (₹)")
    net_financial_impact: float = Field(default=0.0, description="Net impact = gross_benefit - implementation_cost (₹)")
    roi_multiple: float = Field(default=0.0, description="Net impact / implementation_cost or ratio")
    payback_period_days: Optional[int] = Field(default=30, description="Estimated days to break even on cost")
    measurement_period: str = Field(default="30 days", max_length=64)
    success_metric: str = Field(default="", max_length=200)
    is_estimated: bool = Field(default=True, description="True for forward projections; False for audited actuals")


class RealizedOutcomeRecord(BaseModel):
    """Tracks post-implementation audited business results against estimates."""

    model_config = ConfigDict(extra="forbid")

    measured_at: str = Field(default_factory=utc_now_iso)
    realized_gross_benefit: float = Field(default=0.0)
    actual_cost: float = Field(default=0.0)
    realized_net_impact: float = Field(default=0.0)
    benefit_variance_pct: float = Field(default=0.0, description="% difference vs initial projected benefit")
    measured_by: str = Field(default="Operator", max_length=100)
    notes: str = Field(default="", max_length=500)


class PrescriptiveRecommendation(BaseModel):
    """
    Standardized, evidence-grounded business recommendation with financial calculations,
    risk governance, confidence tiering, and lifecycle management.
    """

    model_config = ConfigDict(extra="forbid")

    recommendation_id: str = Field(default_factory=make_rec_id, max_length=80)
    title: str = Field(min_length=1, max_length=200)
    domain: PrescriptiveDomain
    target_type: str = Field(min_length=1, max_length=80)
    entity_id: str = Field(default="Global", max_length=120)

    # Core Prescriptive Narrative
    business_problem: str = Field(min_length=1, max_length=500)
    supporting_evidence: List[str] = Field(default_factory=list)
    proposed_action: str = Field(min_length=1, max_length=500)
    expected_benefit: str = Field(min_length=1, max_length=500)

    # Financial & Risk Quantification
    financial_impact: FinancialImpactBreakdown
    risk_and_uncertainty: str = Field(default="", max_length=500)
    confidence_tier: ConfidenceTier = Field(default=ConfidenceTier.MODERATE)
    confidence_caveat: str = Field(default="", max_length=500)

    # Governance & Lifecycle
    lifecycle_status: RecommendationLifecycleStatus = Field(default=RecommendationLifecycleStatus.PROPOSED)
    human_approval_required: bool = Field(default=True)
    is_simulation_projection: bool = Field(default=True)
    created_at: str = Field(default_factory=utc_now_iso)
    approved_by: Optional[str] = Field(default=None, max_length=100)
    approved_at: Optional[str] = Field(default=None)
    rejection_reason: Optional[str] = Field(default=None, max_length=500)
    realized_outcome: Optional[RealizedOutcomeRecord] = Field(default=None)
    priority: str = Field(default="Medium", max_length=32)

    @property
    def status(self) -> RecommendationLifecycleStatus:
        return self.lifecycle_status

    def to_action_recommendation_dict(self) -> Dict[str, Any]:
        """Convert to dict compatible with ActionRecommendation, PrescriptiveRecommendation and UI rendering."""
        evidence_list = list(self.supporting_evidence) if self.supporting_evidence else []
        evidence_str = "; ".join(evidence_list) if evidence_list else self.business_problem

        # Extract financial quantification safely
        impl_cost = float(getattr(self.financial_impact, "implementation_cost", 0.0) or 0.0)
        net_impact = float(getattr(self.financial_impact, "net_financial_impact", 0.0) or 0.0)
        gross_ben = float(getattr(self.financial_impact, "gross_benefit", 0.0) or 0.0)
        if gross_ben == 0.0 and net_impact != 0.0:
            gross_ben = net_impact + impl_cost

        roi = float(
            getattr(self.financial_impact, "roi_multiple", 0.0)
            or (net_impact / impl_cost if impl_cost > 0 else 0.0)
        )
        payback = int(getattr(self.financial_impact, "payback_period_days", 30) or 30)

        # Build status history
        history_entries = []
        if hasattr(self, "status_history") and self.status_history and isinstance(self.status_history, list):
            for h in self.status_history:
                if hasattr(h, "model_dump"):
                    history_entries.append(h.model_dump())
                elif isinstance(h, dict):
                    history_entries.append(h)
        if not history_entries:
            history_entries.append({
                "status": self.lifecycle_status.value,
                "changed_at": self.created_at,
                "changed_by": self.approved_by or "System Engine",
                "notes": f"Recommendation initialized in {self.lifecycle_status.value} state",
            })

        return {
            "title": self.title,
            "target_type": self.target_type,
            "entity_id": self.entity_id,
            "evidence": evidence_str[:500],
            "supporting_evidence": evidence_list,
            "expected_impact": self.expected_benefit[:500],
            "confidence": f"{self.confidence_tier.value}: {self.confidence_caveat}"[:200],
            "action": self.proposed_action[:500],
            "priority": self.priority,
            "domain": self.domain.value if hasattr(self.domain, "value") else str(self.domain),
            "recommendation_id": self.recommendation_id,
            "business_problem": self.business_problem[:500],
            "problem_statement": self.business_problem[:500],
            "proposed_action": self.proposed_action[:500],
            "expected_benefit": self.expected_benefit[:500],
            "expected_gross_benefit_rupees": gross_ben,
            "implementation_cost": impl_cost,
            "implementation_cost_rupees": impl_cost,
            "net_financial_impact": net_impact,
            "net_financial_impact_rupees": net_impact,
            "roi_multiple": roi,
            "payback_period_days": payback,
            "status_history": history_entries,
            "financial_impact": {
                "gross_benefit": gross_ben,
                "implementation_cost": impl_cost,
                "net_financial_impact": net_impact,
                "net_financial_benefit_rupees": net_impact,
                "implementation_cost_rupees": impl_cost,
                "measurement_period": self.financial_impact.measurement_period,
                "success_metric": self.financial_impact.success_metric,
                "roi_multiple": roi,
                "payback_period_days": payback,
                "is_estimated": getattr(self.financial_impact, "is_estimated", True),
            },
            "risk_and_uncertainty": self.risk_and_uncertainty[:500],
            "confidence_tier": self.confidence_tier.value,
            "measurement_period": self.financial_impact.measurement_period,
            "success_metric": self.financial_impact.success_metric[:200],
            "lifecycle_status": self.lifecycle_status.value,
            "status": self.lifecycle_status.value,
            "human_approval_required": self.human_approval_required,
            "requires_human_approval": self.human_approval_required,
            "is_simulation_projection": self.is_simulation_projection,
            "realized_outcome": self.realized_outcome.model_dump() if self.realized_outcome else None,
            "approved_by": self.approved_by,
            "approved_at": self.approved_at,
            "rejection_reason": self.rejection_reason,
        }
