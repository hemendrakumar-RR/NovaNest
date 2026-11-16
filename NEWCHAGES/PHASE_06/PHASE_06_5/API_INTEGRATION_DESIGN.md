# NOVANEST PHASE 06.5 — API INTEGRATION DESIGN
## REST & TELEMETRY CONTRACT SPECIFICATIONS

- **Phase**: `06.5 — API Integration Design`
- **Date**: `2026-11-13`
- **Status**: `PROPOSED` (100% Backward Compatible with Phase 05.3–06.4 Schemas)

---

## 1. Review of Existing API Surface

The existing FastAPI backend exposed in [`api/main.py`](file:///C:/Users/madha/OneDrive/Documents/NovaNest-main/api/main.py) provides the following endpoints:

| Endpoint | Method | Scope Required | Core Payload / Behavior |
|---|---|---|---|
| `/api/ai/ask` | `POST` | `operator` | Accepts `ChatInquiry`, invokes `MasterOrchestrator.orchestrate`, returns `ChatResponse`. Bounds: `question <= 4000`, `session_id <= 128`, `city_filter <= 100`. |
| `/api/ai/agents/status` | `GET` | `read` | Returns orchestrator version, active contexts, data store label, and list of 5 domain agents with their versions, capabilities, and table ACLs. |
| `/api/ai/traces/{request_id}` | `GET` | `operator` | Returns execution trace for `request_id`, strictly isolated by caller `principal_id`. Returns `404` for cross-principal access. |
| `/api/ai/reset` | `POST` | `admin` | Flushes session contexts from both legacy `conversation_manager` and Phase 06 `AgentContextManager`. Requires `admin` role. |

---

## 2. API Contract Enhancements for Phase 06.5

To power the unified business intelligence experience, conversational follow-ups, and execution progress visualization, the API is extended with backward-compatible schemas and an optional progressive execution endpoint.

### A. Enhanced Inquiry Contract: `ChatInquiryV2`

Extends `ChatInquiry` with conversational client metadata without breaking existing clients:

```python
class ClientContext(BaseModel):
    active_view: Optional[str] = Field(None, max_length=64, description="Origin dashboard tab, e.g. 'customer', 'operations'")
    selected_entity_type: Optional[str] = Field(None, max_length=32, description="Entity type, e.g. 'customer_id', 'restaurant_id'")
    selected_entity_id: Optional[str] = Field(None, max_length=64, description="Entity ID, e.g. 'CUST-1042', 'REST-089'")
    active_kpi_id: Optional[str] = Field(None, max_length=16, description="Specific KPI card triggering query, e.g. 'KPI-08'")

class ChatInquiryV2(BaseModel):
    question: str = Field(..., min_length=1, max_length=4000)
    session_id: Optional[str] = Field("default", max_length=128)
    city_filter: Optional[str] = Field(None, max_length=100)
    parent_request_id: Optional[str] = Field(None, max_length=64, description="Parent turn request ID for explicit tree threading")
    client_context: Optional[ClientContext] = None
```

### B. Detailed Agent Execution Telemetry in `ChatResponse`

To support real-time execution cards without exposing private CoT, `ChatResponse` adds structured `execution_stages` and `verification_details`:

```python
class AgentExecutionSummary(BaseModel):
    agent_id: str
    domain: str
    stage: int  # 1 (Parallel Domain) or 2 (Sequential Decision)
    status: str  # "success", "partial", "timeout", "blocked", "failed"
    elapsed_ms: float
    data_sources: List[str]
    records_analyzed: int
    facts_count: int
    recommendations_count: int
    failure_reason: Optional[str] = None

class VerificationSummary(BaseModel):
    outcome: str  # "verified", "partial", "rejected", "not_run"
    rules_evaluated: int
    grounded_kpi_count: int
    unconfirmed_risk_count: int
    caveat_count: int
    violations: List[Dict[str, str]]

class ChatResponseV2(BaseModel):
    question: str
    resolved_query: Optional[str]
    intent: Optional[str]
    route: str
    answer: str
    provider_status: str
    request_id: str
    trace_id: str
    orchestration_mode: str
    
    # Granular Execution Telemetry
    execution_stages: List[Dict[str, Any]]
    agents_invoked: List[AgentExecutionSummary]
    verification_details: VerificationSummary
    
    # Grounded Evidence
    verified_metrics: List[Dict[str, Any]]
    suggested_chart: Optional[Dict[str, Any]]
    root_cause_analysis: Optional[Dict[str, Any]]
    simulation_results: Optional[Dict[str, Any]]
    recommendations: List[Dict[str, Any]]
    follow_up_suggestions: List[str]
    provenance: Dict[str, Any]
    limitations: List[str]
    ml_confidence_warnings: List[str]
    timestamp: str
```

---

## 3. Progressive Orchestration Progress (SSE Telemetry Stream)

### Endpoint: `GET /api/ai/ask/progress/{request_id}` (Server-Sent Events)

For complex multi-agent queries taking > 1.5 seconds, clients can optionally connect to an SSE stream to render real-time progress steps:

```
GET /api/ai/ask/progress/req_8f93e1a0
Accept: text/event-stream
X-API-Key: <operator_key>

event: progress
data: {"stage": "routing", "status": "analyzing_intent", "elapsed_ms": 25}

event: progress
data: {"stage": "stage1_dispatched", "agents": ["financial_agent", "operations_agent", "restaurant_agent"], "elapsed_ms": 110}

event: agent_complete
data: {"agent_id": "operations_agent", "status": "success", "elapsed_ms": 180, "facts_emitted": 3}

event: agent_complete
data: {"agent_id": "financial_agent", "status": "success", "elapsed_ms": 420, "facts_emitted": 4}

event: progress
data: {"stage": "stage2_synthesis", "agent": "decision_agent", "elapsed_ms": 1050}

event: agent_complete
data: {"agent_id": "decision_agent", "status": "success", "elapsed_ms": 2200}

event: verification
data: {"outcome": "verified", "kpis_grounded": 4, "elapsed_ms": 2240}

event: complete
data: {"request_id": "req_8f93e1a0", "total_ms": 2255, "status": "success"}
```

**Fallback for Standard HTTP Clients**:
Standard `POST /api/ai/ask` continues to return the complete JSON payload synchronously within the configured client timeout (`68,000 ms`), ensuring 100% backward compatibility with all existing test suites and third-party API clients.

---

## 4. Partial Agent Failure & Degradation Contract

When one or more domain agents fail or exceed their per-agent timeout (`35.0s`), `MasterOrchestrator` degrades gracefully rather than aborting the entire request:

```json
{
  "request_id": "req_part_4a2c",
  "orchestration_mode": "multi_agent",
  "status": "partial",
  "verification_outcome": "verified",
  "grounding_verified": true,
  "answer": "Executive Briefing: Financial performance remains strong with GMV of ₹4.66 Cr and Net Revenue of ₹4.64 Cr. However, restaurant partner analysis degraded due to a timeout.",
  "agents_invoked": [
    {
      "agent_id": "financial_agent",
      "stage": 1,
      "status": "success",
      "elapsed_ms": 412.5,
      "data_sources": ["orders", "payments"]
    },
    {
      "agent_id": "restaurant_agent",
      "stage": 1,
      "status": "timeout",
      "elapsed_ms": 35002.1,
      "failure_reason": "Per-agent deadline exceeded (35.0s)",
      "data_sources": ["restaurants"]
    },
    {
      "agent_id": "decision_agent",
      "stage": 2,
      "status": "success",
      "elapsed_ms": 820.4,
      "data_sources": ["orders"]
    }
  ],
  "limitations": [
    "Partial domain coverage: restaurant_agent timed out; merchant risk analysis omitted."
  ],
  "verified_metrics": [
    {"label": "GMV (KPI-01)", "value": "₹4.66 Cr (₹46,590,125.00)", "provenance": "CSV File Store:orders"}
  ]
}
```

---

## 5. TypeScript Contract Definitions (`frontend/src/services/api.ts`)

```typescript
export interface ClientContext {
  active_view?: string;
  selected_entity_type?: 'customer_id' | 'restaurant_id' | 'rider_id' | 'kpi_id';
  selected_entity_id?: string;
  active_kpi_id?: string;
}

export interface ChatInquiry {
  question: string;
  session_id?: string;
  city_filter?: string;
  parent_request_id?: string;
  client_context?: ClientContext;
}

export interface AgentExecutionStage {
  stage_number: number;
  stage_name: string;
  status: 'pending' | 'running' | 'completed' | 'partial' | 'failed';
  agents: InvokedAgentSummary[];
}

export interface VerificationDetails {
  outcome: 'verified' | 'partial' | 'rejected' | 'not_run';
  grounded_kpi_count: number;
  unconfirmed_risk_count: number;
  caveat_count: number;
  violations?: Array<{ code: string; message: string }>;
}
```

---

## 6. Backward Compatibility & Error Mapping Key

| HTTP Status | Trigger / Condition | Error Response Payload | Client Handling |
|---|---|---|---|
| `400 Bad Request` | Empty query, `q.length > 4000`, `city.length > 100`, `session.length > 128` | `{"detail": "..."}` | Renders validation warning without retrying. |
| `401 Unauthorized` | Missing or invalid `X-API-Key` | `{"detail": "Authentication required..."}` | Redirects to login modal or prompts for API token. |
| `403 Forbidden` | `viewer` key used on `/api/ai/ask` or `/api/ai/reset` | `{"detail": "Insufficient permissions. Requires 'operator' role."}` | Displays permission lock pill. |
| `404 Not Found` | Requesting trace owned by different principal | `{"detail": "Execution trace not found for caller principal."}` | Fails closed; trace panel displays "Not available". |
| `503 Service Unavailable` | Circuit breaker `OPEN` or active requests at semaphore cap | `{"detail": "AI assistant temporarily busy; please retry."}` | Triggers `ApiErrorState` with one-click `Retry` re-submitting `lastFailedQuery`. |

