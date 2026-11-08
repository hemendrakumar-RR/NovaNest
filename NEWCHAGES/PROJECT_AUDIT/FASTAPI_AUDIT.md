# NovaNest — FastAPI Backend Architecture & Route Inventory Audit

## 1. Application Overview
- **Entrypoint**: `api/main.py` (894 lines of code, 38.4 KB).
- **Data Access Layer**: `api/loader.py` (142 lines of code, 4.8 KB).
- **Framework**: FastAPI (ASGI application running on Uvicorn).
- **Middleware**: CORS middleware enabled with unrestricted origins (`*`) for cross-origin frontend communication.
- **Port Binding**: Default port 8000.

## 2. Complete REST Endpoint Inventory (13 Endpoints)

| # | HTTP Method | Path | Function Name | Request Model / Params | Response Description |
|---|---|---|---|---|---|
| 1 | `GET` | `/api/health` | `get_health` | None | System status, uptime, dataset row counts, memory source |
| 2 | `GET` | `/api/overview` | `get_executive_overview` | `city: Optional[str] = 'All'` | Executive KPIs (GMV, Orders, AOV, Margin, Active Users) |
| 3 | `GET` | `/api/customer/overview` | `get_customer_overview` | None | Customer demographics, RFM distribution, churn risk breakdown |
| 4 | `GET` | `/api/customer/list` | `get_customer_list` | `limit: int = 50` | Tabular list of customer records with spend metrics |
| 5 | `GET` | `/api/customer/360/{customer_id}` | `get_customer_360` | Path `customer_id: str` | Deep customer profile, order history, preferred cuisines, LTV |
| 6 | `GET` | `/api/restaurant/overview` | `get_restaurant_overview` | None | Restaurant partner counts, cuisine breakdown, rating distributions |
| 7 | `GET` | `/api/operations/overview` | `get_operations_overview` | None | Rider fleet stats, average delivery time, SLA compliance rate |
| 8 | `GET` | `/api/financial/overview` | `get_financial_overview` | None | Revenue streams, commission earnings, delivery fee economics |
| 9 | `POST` | `/api/ai/ask` | `ask_novanest_ai` | Body `req: ChatInquiry` | Natural language question response from Universal AI Engine |
| 10 | `POST` | `/api/ai/reset` | `reset_ai_chat_session` | Body `req: ResetSessionRequest` | Clears conversation memory for specified session ID |
| 11 | `GET` | `/api/decision/actions` | `get_decision_actions` | None | Next-best-action recommendations prioritized by ROI |
| 12 | `POST` | `/api/decision/simulate` | `simulate_scenario` | Body `params: SimulationParams` | What-if simulation outcome (commission change, rider incentive) |
| 13 | `GET` | `/api/digital-twin/state` | `get_digital_twin_state` | None | Full state snapshot across all 5 digital twins and active alerts |

## 3. Data Ingestion & In-Memory Caching Architecture (`api/loader.py`)
- Implements a singleton cache pattern (`_cached_data`, `_cached_source`).
- **Primary Source**: Attempts connection to MySQL database via `mysql.connector` with a 3-second connection timeout.
- **Graceful Fallback**: If MySQL is unreachable, it seamlessly loads CSV files from `datasets/cleaned/` and `datasets/engineered/`.
- **Sanitization Utility**: `sanitize_for_json()` traverses all dictionary outputs and converts `NaN`, `Infinity`, `NaT`, and non-serializable NumPy types into clean JSON-compliant values (`None`, `0.0`).

## 4. Security & Performance Observations
- **Input Validation**: Handled securely via Pydantic schemas (`ChatInquiry`, `SimulationParams`).
- **Rate Limiting**: Currently unconfigured; recommended for production deployment.
- **Asynchronous Execution**: Endpoint handlers are defined synchronously (`def`), allowing FastAPI's threadpool to handle blocking Pandas data operations without starving the event loop.
