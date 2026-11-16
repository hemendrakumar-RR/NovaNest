"""
NovaNest Recommendation Lifecycle & Human-in-the-Loop Governance Engine (Phase 08)
-----------------------------------------------------------------------------------
Implements the 6-state recommendation lifecycle:
    Proposed -> Approved / Rejected -> In progress -> Implemented -> Outcome measured

Enforces enterprise safety rules:
1. Strict Human Approval Requirement: No automated operational or financial actions.
2. Complete audit trail tracking user approvals, timestamps, and realized business variance.
"""

from __future__ import annotations

import json
import threading
from pathlib import Path
from typing import Any, Dict, List, Optional

from python.decision.prescriptive_contracts import (
    PrescriptiveRecommendation,
    RealizedOutcomeRecord,
    RecommendationLifecycleStatus,
    utc_now_iso,
)


class HumanApprovalRequiredError(PermissionError):
    """Raised when an automated agent or pipeline attempts to execute an unapproved action."""
    pass


class InvalidLifecycleTransitionError(ValueError):
    """Raised when an invalid state transition is requested."""
    pass


class RecommendationLifecycleManager:
    """
    Thread-safe lifecycle and governance store for prescriptive business recommendations.
    """

    def __init__(self, store_path: Optional[Path] = None):
        self.store_path = store_path or (
            Path(__file__).resolve().parents[2] / "models" / "recommendations_store.json"
        )
        self._lock = threading.Lock()
        self._recommendations: Dict[str, PrescriptiveRecommendation] = {}
        self._load_store()

    def _load_store(self) -> None:
        with self._lock:
            if not self.store_path.exists():
                return
            try:
                payload = json.loads(self.store_path.read_text(encoding="utf-8"))
                for rec_id, rec_data in payload.get("recommendations", {}).items():
                    try:
                        self._recommendations[rec_id] = PrescriptiveRecommendation.model_validate(rec_data)
                    except Exception:
                        pass
            except Exception:
                pass

    def _persist_store(self) -> None:
        try:
            self.store_path.parent.mkdir(parents=True, exist_ok=True)
            payload = {
                "updated_at": utc_now_iso(),
                "total_recommendations": len(self._recommendations),
                "recommendations": {
                    rec_id: rec.model_dump()
                    for rec_id, rec in self._recommendations.items()
                },
            }
            self.store_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
        except Exception:
            pass

    def register_recommendation(self, rec: PrescriptiveRecommendation) -> PrescriptiveRecommendation:
        """Registers a new recommendation in the PROPOSED state."""
        with self._lock:
            # Force default state to PROPOSED on ingestion
            rec_to_store = rec.model_copy(update={"lifecycle_status": RecommendationLifecycleStatus.PROPOSED})
            self._recommendations[rec_to_store.recommendation_id] = rec_to_store
            self._persist_store()
            return rec_to_store

    def register_all(self, recs: List[PrescriptiveRecommendation]) -> List[PrescriptiveRecommendation]:
        """Bulk registers a list of recommendations."""
        registered = []
        for r in recs:
            registered.append(self.register_recommendation(r))
        return registered

    def get_recommendation(self, recommendation_id: str) -> Optional[PrescriptiveRecommendation]:
        with self._lock:
            return self._recommendations.get(recommendation_id)

    def list_recommendations(
        self,
        domain: Optional[str] = None,
        status: Optional[RecommendationLifecycleStatus] = None,
    ) -> List[PrescriptiveRecommendation]:
        with self._lock:
            recs = list(self._recommendations.values())
            if domain:
                recs = [r for r in recs if r.domain.value == domain or r.domain == domain]
            if status:
                recs = [r for r in recs if r.lifecycle_status == status]
            return recs

    def approve_recommendation(
        self,
        recommendation_id: str,
        approved_by: str,
        approval_notes: Optional[str] = None,
    ) -> PrescriptiveRecommendation:
        """
        Human-in-the-loop approval transition: Proposed -> Approved.
        """
        with self._lock:
            rec = self._recommendations.get(recommendation_id)
            if not rec:
                raise KeyError(f"Recommendation '{recommendation_id}' not found")

            if rec.lifecycle_status != RecommendationLifecycleStatus.PROPOSED:
                raise InvalidLifecycleTransitionError(
                    f"Cannot approve recommendation in '{rec.lifecycle_status.value}' state. Must be 'Proposed'."
                )

            updated = rec.model_copy(
                update={
                    "lifecycle_status": RecommendationLifecycleStatus.APPROVED,
                    "approved_by": approved_by,
                    "approved_at": utc_now_iso(),
                }
            )
            self._recommendations[recommendation_id] = updated
            self._persist_store()
            return updated

    def reject_recommendation(
        self,
        recommendation_id: str,
        rejected_by: str,
        rejection_reason: str,
    ) -> PrescriptiveRecommendation:
        """
        Human rejection transition: Proposed -> Rejected.
        """
        with self._lock:
            rec = self._recommendations.get(recommendation_id)
            if not rec:
                raise KeyError(f"Recommendation '{recommendation_id}' not found")

            if rec.lifecycle_status not in (
                RecommendationLifecycleStatus.PROPOSED,
                RecommendationLifecycleStatus.APPROVED,
            ):
                raise InvalidLifecycleTransitionError(
                    f"Cannot reject recommendation in '{rec.lifecycle_status.value}' state."
                )

            updated = rec.model_copy(
                update={
                    "lifecycle_status": RecommendationLifecycleStatus.REJECTED,
                    "rejection_reason": f"Rejected by {rejected_by}: {rejection_reason}",
                }
            )
            self._recommendations[recommendation_id] = updated
            self._persist_store()
            return updated

    def start_implementation(
        self,
        recommendation_id: str,
        operator_user: str,
    ) -> PrescriptiveRecommendation:
        """
        Transition: Approved -> In progress.
        Fails if recommendation has not received human approval.
        """
        with self._lock:
            rec = self._recommendations.get(recommendation_id)
            if not rec:
                raise KeyError(f"Recommendation '{recommendation_id}' not found")

            if rec.lifecycle_status != RecommendationLifecycleStatus.APPROVED:
                raise HumanApprovalRequiredError(
                    f"Action execution blocked: Recommendation '{recommendation_id}' is in "
                    f"'{rec.lifecycle_status.value}' state. Explicit human approval is required before implementation."
                )

            updated = rec.model_copy(
                update={"lifecycle_status": RecommendationLifecycleStatus.IN_PROGRESS}
            )
            self._recommendations[recommendation_id] = updated
            self._persist_store()
            return updated

    def mark_implemented(
        self,
        recommendation_id: str,
        operator_user: str,
    ) -> PrescriptiveRecommendation:
        """
        Transition: In progress -> Implemented.
        """
        with self._lock:
            rec = self._recommendations.get(recommendation_id)
            if not rec:
                raise KeyError(f"Recommendation '{recommendation_id}' not found")

            if rec.lifecycle_status != RecommendationLifecycleStatus.IN_PROGRESS:
                raise InvalidLifecycleTransitionError(
                    f"Cannot mark implemented: Recommendation is in '{rec.lifecycle_status.value}' state. Must be 'In progress'."
                )

            updated = rec.model_copy(
                update={"lifecycle_status": RecommendationLifecycleStatus.IMPLEMENTED}
            )
            self._recommendations[recommendation_id] = updated
            self._persist_store()
            return updated

    def record_realized_outcome(
        self,
        recommendation_id: str,
        realized_gross_benefit: float,
        actual_cost: float,
        measured_by: str = "Finance Auditor",
        audit_notes: str = "Audited realized financial outcome",
    ) -> PrescriptiveRecommendation:
        """
        Transition: Implemented -> Outcome measured.
        Records audited financial outcome and calculates variance against initial projection.
        """
        with self._lock:
            rec = self._recommendations.get(recommendation_id)
            if not rec:
                raise KeyError(f"Recommendation '{recommendation_id}' not found")

            if rec.lifecycle_status != RecommendationLifecycleStatus.IMPLEMENTED:
                raise InvalidLifecycleTransitionError(
                    f"Cannot record outcome: Recommendation is in '{rec.lifecycle_status.value}' state. Must be 'Implemented'."
                )

            proj = rec.financial_impact
            r_ben = round(float(realized_gross_benefit), 2)
            a_cost = round(float(actual_cost), 2)
            r_net = round(r_ben - a_cost, 2)
            var_pct = round(((r_ben - proj.gross_benefit) / proj.gross_benefit * 100.0), 2) if proj.gross_benefit > 0 else 0.0

            outcome = RealizedOutcomeRecord(
                measured_at=utc_now_iso(),
                realized_gross_benefit=r_ben,
                actual_cost=a_cost,
                realized_net_impact=r_net,
                benefit_variance_pct=var_pct,
                measured_by=measured_by,
                notes=audit_notes,
            )

            updated = rec.model_copy(
                update={
                    "lifecycle_status": RecommendationLifecycleStatus.OUTCOME_MEASURED,
                    "realized_outcome": outcome,
                }
            )
            self._recommendations[recommendation_id] = updated
            self._persist_store()
            return updated

    # Convenient aliases for API & UI parity
    start_progress = start_implementation
    record_outcome = record_realized_outcome


# Default singleton instance
_GLOBAL_LIFECYCLE_MANAGER: Optional[RecommendationLifecycleManager] = None


def get_recommendation_lifecycle_manager() -> RecommendationLifecycleManager:
    global _GLOBAL_LIFECYCLE_MANAGER
    if _GLOBAL_LIFECYCLE_MANAGER is None:
        _GLOBAL_LIFECYCLE_MANAGER = RecommendationLifecycleManager()
    return _GLOBAL_LIFECYCLE_MANAGER
