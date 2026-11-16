"""
NovaNest Multi-Agent Foundation Package (Phase 06.1)
-----------------------------------------------------
Provides shared Pydantic v2 typed contracts, principal-isolated execution context,
capability/permission registry, numeric & grounding output verifier, and safe
execution tracing prior to Domain Agent and MasterOrchestrator implementation.
"""

from typing import Dict, Tuple, Type

from python.ai.agents.base import BaseDomainAgent
from python.ai.agents.context import (
    AgentContext,
    AgentContextManager,
    AgentContextSnapshot,
    AgentExecutionHistoryEntry,
    ConversationTurnSummary,
    DatasetMetadataEntry,
    KpiDefinitionEntry,
    extract_dataset_metadata_from_frames,
    load_certified_kpi_entries,
)
from python.ai.agents.contracts import (
    ActionRecommendation,
    AgentDomain,
    AgentError,
    AgentExecutionMetadata,
    AgentMessage,
    AgentRequest,
    AgentResult,
    AgentStatus,
    ChartSpec,
    DataProvenance,
    GroundedFact,
    MessageRole,
    ModelCaveat,
    SeverityLevel,
    SqlAuditTrace,
    contains_secret_pattern,
    detect_prompt_injection,
    neutralize_untrusted_text,
    sanitize_text,
    sanitize_user_query,
)
from python.ai.agents.output_verifier import (
    ConflictDetail,
    ExtractedClaim,
    OutputVerifier,
    VerificationOutcome,
    VerificationReport,
    VerificationSeverity,
    VerificationViolation,
)
from python.ai.agents.registry import (
    PLANNED_DOMAIN_BLUEPRINTS,
    AgentAvailability,
    AgentRegistration,
    AgentRegistry,
    AuthorizationDecision,
)
from python.ai.agents.tracing import (
    AgentSpanTrace,
    ExecutionTrace,
    ExecutionTracer,
    TraceVerificationOutcome,
)
from python.ai.agents.financial_agent import FinancialAgent
from python.ai.agents.customer_agent import CustomerAgent
from python.ai.agents.operations_agent import OperationsAgent
from python.ai.agents.restaurant_agent import RestaurantAgent
from python.ai.agents.decision_agent import DecisionAgent


DOMAIN_AGENT_CLASSES: Tuple[Type[BaseDomainAgent], ...] = (
    FinancialAgent,
    CustomerAgent,
    OperationsAgent,
    RestaurantAgent,
    DecisionAgent,
)


def build_domain_agents(*, strict_verification: bool = True) -> Dict[str, BaseDomainAgent]:
    """Instantiate all five Phase 06.2 domain intelligence agents keyed by `agent_id`."""
    agents: Dict[str, BaseDomainAgent] = {}
    for cls in DOMAIN_AGENT_CLASSES:
        inst = cls(strict_verification=strict_verification)
        agents[inst.AGENT_ID] = inst
    return agents


def create_default_domain_registry(
    *,
    preload_planned_blueprints: bool = False,
    strict_verification: bool = True,
) -> AgentRegistry:
    """Create an `AgentRegistry` pre-registered with all 5 operational Phase 06.2 domain agents."""
    registry = AgentRegistry(preload_planned_blueprints=preload_planned_blueprints)
    for agent in build_domain_agents(strict_verification=strict_verification).values():
        agent.register_into(registry, overwrite=True)
    return registry


from python.ai.agents.synthesizer import SynthesisOutput, synthesize_agent_results
from python.ai.agents.master_orchestrator import (
    IntentRouter,
    MasterOrchestrator,
    OrchestrationMode,
    OrchestrationOutcome,
    RoutingPlan,
)

__all__ = [
    # Base & Domain Agents (Phase 06.2)
    "BaseDomainAgent",
    "DOMAIN_AGENT_CLASSES",
    "FinancialAgent",
    "CustomerAgent",
    "OperationsAgent",
    "RestaurantAgent",
    "DecisionAgent",
    "build_domain_agents",
    "create_default_domain_registry",
    # Master Orchestrator & Cross-Agent Synthesis (Phase 06.3)
    "IntentRouter",
    "MasterOrchestrator",
    "OrchestrationMode",
    "OrchestrationOutcome",
    "RoutingPlan",
    "SynthesisOutput",
    "synthesize_agent_results",
    # Contracts
    "ActionRecommendation",
    "AgentDomain",
    "AgentError",
    "AgentExecutionMetadata",
    "AgentMessage",
    "AgentRequest",
    "AgentResult",
    "AgentStatus",
    "ChartSpec",
    "DataProvenance",
    "GroundedFact",
    "MessageRole",
    "ModelCaveat",
    "SeverityLevel",
    "SqlAuditTrace",
    "contains_secret_pattern",
    "detect_prompt_injection",
    "neutralize_untrusted_text",
    "sanitize_text",
    "sanitize_user_query",
    # Context
    "AgentContext",
    "AgentContextManager",
    "AgentContextSnapshot",
    "AgentExecutionHistoryEntry",
    "ConversationTurnSummary",
    "DatasetMetadataEntry",
    "KpiDefinitionEntry",
    "extract_dataset_metadata_from_frames",
    "load_certified_kpi_entries",
    # Registry
    "PLANNED_DOMAIN_BLUEPRINTS",
    "AgentAvailability",
    "AgentRegistration",
    "AgentRegistry",
    "AuthorizationDecision",
    # Output Verification
    "ConflictDetail",
    "ExtractedClaim",
    "OutputVerifier",
    "VerificationOutcome",
    "VerificationReport",
    "VerificationSeverity",
    "VerificationViolation",
    # Tracing
    "AgentSpanTrace",
    "ExecutionTrace",
    "ExecutionTracer",
    "TraceVerificationOutcome",
]

