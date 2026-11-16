"""
NovaNest Multi-Agent Foundation - Agent Registry & Capability Contracts
-----------------------------------------------------------------------
Manages agent registration, discovery metadata, Pydantic I/O contracts,
table/scope permission boundaries, and explicit operational readiness gating.

Phase 06.1 Safety Guarantee:
- Unfinished or handlerless domain agents can NEVER be marked OPERATIONAL.
- Discovery defaults strictly to verified operational agents unless explicitly queried.
"""

from __future__ import annotations

from enum import Enum
import threading
from typing import Any, Callable, Dict, FrozenSet, List, Optional, Set, Type

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from python.ai.agents.contracts import AgentDomain, AgentRequest, AgentResult, sanitize_text
from python.ai.analyst.sql_ast import ALLOWED_TABLES


VALID_SCOPES: FrozenSet[str] = frozenset({"read", "operator", "admin"})


class AgentAvailability(str, Enum):
    OPERATIONAL = "operational"
    PLANNED = "planned"
    DISABLED = "disabled"
    MAINTENANCE = "maintenance"


class AuthorizationDecision(BaseModel):
    """Structured RBAC and table-ACL check outcome returned by `AgentRegistry`."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    allowed: bool
    agent_id: str
    reason: str = ""
    missing_scopes: List[str] = Field(default_factory=list)
    unauthorized_tables: List[str] = Field(default_factory=list)


class AgentRegistration(BaseModel):
    """Typed capability, contract, and permission boundary declaration for an agent."""

    model_config = ConfigDict(extra="forbid", arbitrary_types_allowed=True)

    agent_id: str = Field(min_length=2, max_length=80)
    domain: AgentDomain
    version: str = Field(default="1.0.0", min_length=1, max_length=32)
    description: str = Field(min_length=1, max_length=400)
    capabilities: List[str] = Field(default_factory=list)
    supported_intents: List[str] = Field(default_factory=list)
    input_contract: Type[BaseModel] = AgentRequest
    output_contract: Type[BaseModel] = AgentResult
    allowed_tables: List[str] = Field(default_factory=list)
    required_scopes: List[str] = Field(default_factory=lambda: ["read"])
    availability: AgentAvailability = AgentAvailability.PLANNED
    is_implemented: bool = False
    timeout_seconds: float = Field(default=3.0, gt=0.0, le=60.0)

    @field_validator("agent_id")
    @classmethod
    def _validate_agent_id(cls, v: str) -> str:
        clean = v.strip()
        if not clean or any(ch.isspace() for ch in clean):
            raise ValueError("agent_id must be non-empty and contain no whitespace.")
        return clean

    @field_validator("description")
    @classmethod
    def _sanitize_desc(cls, v: str) -> str:
        return sanitize_text(v.strip())

    @field_validator("input_contract", "output_contract")
    @classmethod
    def _check_contract_subclass(cls, model_cls: Any) -> Type[BaseModel]:
        if not isinstance(model_cls, type) or not issubclass(model_cls, BaseModel):
            raise ValueError("Agent contracts must be Pydantic BaseModel subclasses.")
        return model_cls

    @field_validator("allowed_tables")
    @classmethod
    def _validate_allowed_tables(cls, tables: List[str]) -> List[str]:
        out: List[str] = []
        for tbl in tables:
            clean = tbl.strip().lower()
            if clean not in ALLOWED_TABLES:
                raise ValueError(
                    f"Unauthorized SQL table '{tbl}' in agent ACL. Permitted tables: {sorted(ALLOWED_TABLES)}"
                )
            if clean not in out:
                out.append(clean)
        return out

    @field_validator("required_scopes")
    @classmethod
    def _validate_required_scopes(cls, scopes: List[str]) -> List[str]:
        out: List[str] = []
        for sc in scopes:
            clean = sc.strip().lower()
            if clean not in VALID_SCOPES:
                raise ValueError(f"Unknown scope '{sc}'. Must be one of {sorted(VALID_SCOPES)}.")
            if clean not in out:
                out.append(clean)
        return out or ["read"]

    @model_validator(mode="after")
    def _prevent_unfinished_operational(self) -> "AgentRegistration":
        if self.availability == AgentAvailability.OPERATIONAL and not self.is_implemented:
            raise ValueError(
                f"Unfinished agent '{self.agent_id}' (is_implemented=False) cannot be registered as OPERATIONAL."
            )
        return self

    def to_safe_metadata(self) -> Dict[str, Any]:
        """Serialize capability discovery metadata cleanly for status/telemetry endpoints."""
        return {
            "agent_id": self.agent_id,
            "domain": self.domain.value,
            "version": self.version,
            "description": self.description,
            "capabilities": list(self.capabilities),
            "supported_intents": list(self.supported_intents),
            "input_contract": self.input_contract.__name__,
            "output_contract": self.output_contract.__name__,
            "allowed_tables": list(self.allowed_tables),
            "required_scopes": list(self.required_scopes),
            "availability": self.availability.value,
            "is_implemented": self.is_implemented,
            "timeout_seconds": self.timeout_seconds,
        }


PLANNED_DOMAIN_BLUEPRINTS: List[Dict[str, Any]] = [
    {
        "agent_id": "financial_agent",
        "domain": AgentDomain.FINANCIAL,
        "description": "Planned Phase 06.2 financial metrics, GMV/revenue, unit economics, and leakage screening auditor.",
        "capabilities": ["kpi_reconciliation", "margin_analysis", "leakage_screening"],
        "allowed_tables": ["orders", "payments", "promotions", "restaurants"],
        "required_scopes": ["read"],
    },
    {
        "agent_id": "customer_agent",
        "domain": AgentDomain.CUSTOMER,
        "description": "Planned Phase 06.2 RFM segmentation, retention cohort, and churn caveat specialist.",
        "capabilities": ["rfm_segmentation", "cohort_retention", "churn_risk_triage"],
        "allowed_tables": ["customers", "orders", "ratings_reviews"],
        "required_scopes": ["operator"],
    },
    {
        "agent_id": "operations_agent",
        "domain": AgentDomain.OPERATIONS,
        "description": "Planned Phase 06.2 delivery ETA, SLA breach, fleet allocation, and anomaly specialist.",
        "capabilities": ["sla_monitoring", "delivery_latency", "fleet_allocation"],
        "allowed_tables": ["deliveries", "riders", "orders"],
        "required_scopes": ["read"],
    },
    {
        "agent_id": "restaurant_agent",
        "domain": AgentDomain.RESTAURANT,
        "description": "Planned Phase 06.2 merchant health, cancellation hotspots, ratings, and menu mix specialist.",
        "capabilities": ["merchant_health", "cancellation_hotspots", "cuisine_performance"],
        "allowed_tables": ["restaurants", "orders", "menu_items", "ratings_reviews"],
        "required_scopes": ["read"],
    },
    {
        "agent_id": "decision_agent",
        "domain": AgentDomain.DECISION,
        "description": "Planned Phase 06.2 Next-Best-Action and Digital Twin scenario simulation synthesizer.",
        "capabilities": ["next_best_action", "scenario_simulation", "cross_domain_synthesis"],
        "allowed_tables": ["orders", "customers", "restaurants", "deliveries", "riders", "promotions"],
        "required_scopes": ["operator"],
    },
]


class AgentRegistry:
    """Thread-safe catalog of agent capabilities, contracts, and RBAC/table boundaries."""

    def __init__(self, preload_planned_blueprints: bool = False) -> None:
        self._lock = threading.RLock()
        self._registrations: Dict[str, AgentRegistration] = {}
        self._handlers: Dict[str, Callable[..., Any]] = {}
        self._locked: bool = False

        if preload_planned_blueprints:
            self.register_planned_domain_blueprints()

    def lock(self) -> None:
        """Freeze registry against further runtime registration, overwrite, or availability mutation."""
        with self._lock:
            self._locked = True

    @property
    def is_locked(self) -> bool:
        with self._lock:
            return self._locked

    def register(
        self,
        registration: AgentRegistration,
        handler: Optional[Callable[..., Any]] = None,
        overwrite: bool = False,
    ) -> AgentRegistration:
        """
        Register an agent descriptor and optional execution callable.
        Enforces strict invariant that OPERATIONAL agents must have a callable handler
        and `is_implemented=True`.
        """
        with self._lock:
            if self._locked:
                raise PermissionError(
                    f"AgentRegistry is locked; cannot register or modify '{registration.agent_id}'."
                )

        if registration.availability == AgentAvailability.OPERATIONAL:
            if handler is None or not callable(handler) or not registration.is_implemented:
                raise ValueError(
                    f"Cannot register '{registration.agent_id}' as OPERATIONAL without `is_implemented=True` "
                    "and a callable execution handler."
                )

        if handler is not None and not callable(handler):
            raise ValueError(f"Handler for agent '{registration.agent_id}' must be callable.")

        with self._lock:
            if registration.agent_id in self._registrations and not overwrite:
                raise ValueError(f"Agent '{registration.agent_id}' is already registered.")
            self._registrations[registration.agent_id] = registration
            if handler is not None:
                self._handlers[registration.agent_id] = handler
            elif overwrite:
                self._handlers.pop(registration.agent_id, None)
            return registration

    def register_planned_domain_blueprints(self) -> List[AgentRegistration]:
        """
        Optionally register the 5 blueprint domain agents strictly as PLANNED (non-operational).
        Never marks unfinished domain agents as OPERATIONAL.
        """
        registered: List[AgentRegistration] = []
        for spec in PLANNED_DOMAIN_BLUEPRINTS:
            entry = AgentRegistration(
                agent_id=spec["agent_id"],
                domain=spec["domain"],
                description=spec["description"],
                capabilities=spec["capabilities"],
                allowed_tables=spec["allowed_tables"],
                required_scopes=spec["required_scopes"],
                availability=AgentAvailability.PLANNED,
                is_implemented=False,
            )
            with self._lock:
                if entry.agent_id not in self._registrations:
                    self._registrations[entry.agent_id] = entry
                    registered.append(entry)
        return registered

    def get(self, agent_id: str) -> Optional[AgentRegistration]:
        with self._lock:
            return self._registrations.get(agent_id)

    def get_handler(self, agent_id: str) -> Optional[Callable[..., Any]]:
        """Return callable handler ONLY if agent is OPERATIONAL and implemented."""
        with self._lock:
            reg = self._registrations.get(agent_id)
            if reg is None or reg.availability != AgentAvailability.OPERATIONAL or not reg.is_implemented:
                return None
            return self._handlers.get(agent_id)

    def set_availability(self, agent_id: str, availability: AgentAvailability) -> AgentRegistration:
        """Update agent availability while blocking premature promotion to OPERATIONAL."""
        with self._lock:
            if self._locked:
                raise PermissionError(
                    f"AgentRegistry is locked; cannot mutate availability for '{agent_id}'."
                )
            existing = self._registrations.get(agent_id)
            if existing is None:
                raise KeyError(f"Unknown agent_id '{agent_id}'.")
            if availability == AgentAvailability.OPERATIONAL:
                handler = self._handlers.get(agent_id)
                if not existing.is_implemented or handler is None or not callable(handler):
                    raise ValueError(
                        f"Cannot promote unfinished agent '{agent_id}' to OPERATIONAL without callable handler."
                    )
            updated = existing.model_copy(update={"availability": availability})
            self._registrations[agent_id] = updated
            return updated

    def list_agents(self, include_non_operational: bool = False) -> List[AgentRegistration]:
        """List registered agents, defaulting strictly to OPERATIONAL entries."""
        with self._lock:
            entries = list(self._registrations.values())
            if include_non_operational:
                return entries
            return [e for e in entries if e.availability == AgentAvailability.OPERATIONAL and e.is_implemented]

    def discover(
        self,
        *,
        domain: Optional[AgentDomain] = None,
        capability: Optional[str] = None,
        include_non_operational: bool = False,
    ) -> List[AgentRegistration]:
        """Discover matching registered agents filtered by domain and/or capability tag."""
        candidates = self.list_agents(include_non_operational=include_non_operational)
        results: List[AgentRegistration] = []
        for reg in candidates:
            if domain is not None and reg.domain != domain:
                continue
            if capability is not None and capability.lower() not in {c.lower() for c in reg.capabilities}:
                continue
            results.append(reg)
        return results

    def authorize(
        self,
        agent_id: str,
        *,
        principal_scopes: Set[str] | FrozenSet[str] | List[str],
        requested_tables: Optional[List[str]] = None,
    ) -> AuthorizationDecision:
        """Verify agent availability, caller RBAC scopes, and table-level ACL boundaries."""
        with self._lock:
            reg = self._registrations.get(agent_id)
            if reg is None:
                return AuthorizationDecision(
                    allowed=False,
                    agent_id=agent_id,
                    reason=f"Agent '{agent_id}' is not registered.",
                )

            if reg.availability != AgentAvailability.OPERATIONAL or not reg.is_implemented:
                return AuthorizationDecision(
                    allowed=False,
                    agent_id=agent_id,
                    reason=f"Agent '{agent_id}' is '{reg.availability.value}' and not operational.",
                )

            caller_scopes = {str(s).strip().lower() for s in principal_scopes}
            missing_scopes = [s for s in reg.required_scopes if s not in caller_scopes]
            if missing_scopes:
                return AuthorizationDecision(
                    allowed=False,
                    agent_id=agent_id,
                    reason=f"Insufficient principal scopes for '{agent_id}'.",
                    missing_scopes=missing_scopes,
                )

            allowed_set = set(reg.allowed_tables)
            bad_tables: List[str] = []
            for tbl in requested_tables or []:
                clean = tbl.strip().lower()
                if clean not in ALLOWED_TABLES or clean not in allowed_set:
                    bad_tables.append(tbl)

            if bad_tables:
                return AuthorizationDecision(
                    allowed=False,
                    agent_id=agent_id,
                    reason=f"Requested SQL tables violate ACL boundary for '{agent_id}'.",
                    unauthorized_tables=bad_tables,
                )

            return AuthorizationDecision(
                allowed=True,
                agent_id=agent_id,
                reason="Authorized",
            )

    def validate_input(self, agent_id: str, payload: Dict[str, Any] | BaseModel) -> BaseModel:
        """Validate candidate request payload against the registered agent's `input_contract`."""
        with self._lock:
            reg = self._registrations.get(agent_id)
            if reg is None:
                raise KeyError(f"Unknown agent_id '{agent_id}'.")
            contract = reg.input_contract
        if isinstance(payload, contract):
            return payload
        if isinstance(payload, BaseModel):
            return contract.model_validate(payload.model_dump())
        return contract.model_validate(payload)

    def validate_output(self, agent_id: str, payload: Dict[str, Any] | BaseModel) -> BaseModel:
        """Validate candidate response payload against the registered agent's `output_contract`."""
        with self._lock:
            reg = self._registrations.get(agent_id)
            if reg is None:
                raise KeyError(f"Unknown agent_id '{agent_id}'.")
            contract = reg.output_contract
        if isinstance(payload, contract):
            return payload
        if isinstance(payload, BaseModel):
            return contract.model_validate(payload.model_dump())
        return contract.model_validate(payload)

