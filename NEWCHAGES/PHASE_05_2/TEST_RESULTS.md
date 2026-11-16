# PHASE 05.2 — VERIFICATION & TEST RESULTS

All results below reflect direct command and browser executions performed on **2026-11-11**.

---

## 1. React Production Build & Lint (`frontend/`)
| Check | Command | Exit | Observed Output Summary |
|---|---|---|---|
| Production Build | `cmd /c "cd /d frontend && npm run build"` (`tsc -b && vite build`) | **0** | Built in `965ms`; `2667` modules transformed. Artifacts in `frontend/dist/`: `index.html` (`1,177` B), `assets/index-C0RXaDfu.css` (`151,534` B), `assets/retroPixelField-QMb3Zo4Q.js` (`5,236` B), `assets/glassParticleField-DgSq-Qn4.js` (`517,180` B), `assets/index-ROGYJLQj.js` (`833,851` B). Non-fatal warnings: chunk >500 kB & `LinearEncoding`/`sRGBEncoding` in `@designcodeio/threeui`. |
| Linter | `cmd /c "cd /d frontend && npm run lint"` (`oxlint`) | **0** | `0` errors, `75` warnings across 30 files in `29ms`. |

---

## 2. Live FastAPI (`:8000`) + React (`:5173`) Browser CDP Integration (`Edg/158`)
- **Normal Navigation Across All 8 Sidebar Views**:
  - `Executive Overview` (`GMV ₹4.66 Cr`, `49,971` orders, `5,000` customers, `NetRev ₹4.64 Cr`, `1,500` merchants, `Net AOV ₹967`, `2` Recharts SVGs, `5` table rows)
  - `Customer Intelligence` (`5,000`, `AOV ₹967`, `High Churn 15.62%`, `CLV ₹15.0k`, `2` Recharts SVGs, `16` table rows incl. `Indira Aggarwal / Low Risk`, `Diya Shetty / High Risk`)
  - `Restaurant Intelligence` (`1,500`, `Health 64.9/100`, `Critical Risk 0` [mismatch vs Streamlit `3`], `Early Warnings 554`, `2` Recharts SVGs, `18` table rows)
  - `Operations Intelligence` (`49,971` dispatches, `37.4 mins`, `67.7%` SLA, `4,000` riders, `1` Recharts SVG, `5` fleet rows)
  - `Financial Intelligence` (`GMV ₹4.66 Cr`, `NetRev ₹4.64 Cr` / `23.59%`, `Subsidies ₹20.83L`, `Risk Exposure ₹5.54L`, `1` Recharts SVG, `10` promotion rows)
  - `Decision Intelligence` (`9` action cards with empirical readiness caveats & null confidence handled safely)
  - `Decision Simulator` (`Platform Rev ₹1.03 Cr` vs `Baseline ₹95.19L`, `Net Margin 18.0%`, **`Order Volume 0 / Baseline 0`** UI key bug, `38` saved)
  - `Command Center` (`Vitality 85/100`, **`420` At-Risk**, **`₹1.25 Cr` CLV**, **`18` Critical**, **`82.1/100` Health**, **`₹4.50 Cr` GMV**, **`₹81.00L` Net Yield**, **`18%` Margin**, **`₹1.25L` Leakage** — 100% hardcoded API fallbacks rendered)
- **Browser Telemetry During Normal Pass**: `normalConsoleErrors = 0`, `normalPageExceptions = 0`, `normalFailedRequests = 0`, `apiCallsSeen = 36`.
- **Interactive & Fault-Injection Checks**:
  - Header territory dropdown `Mumbai` -> `?city=Mumbai` (`0` orders empty state; `Chennai`, `Coimbatore`, `Vijayawada` absent from dropdown).
  - FloatingChatbot submit -> Uvicorn logged `OPTIONS /api/ai/ask` & `POST /api/ai/ask` `200 OK`.
  - Network fault injection (`Fetch.failRequest` `ConnectionRefused`): `ExecutiveOverviewView` rendered `"Failed to load Executive Overview / Failed to fetch / Retry Connection"`; `RestaurantIntelligenceView` threw **2 unhandled `TypeError: Failed to fetch` exceptions** and rendered empty `<main>` (`""`).

---

## 3. Streamlit Runtime Validation (`AppTest` on 10 Files + Live `:8501`)
| Page | `AppTest` Status | Key Observed Runtime Values / Failure |
|---|---|---|
| `app.py` | **OK** (`0` exc, `1` chart) | **Mismatch**: `GMV ₹484.52 L` (incl. Cancelled) + hardcoded `+14.2% MoM`, `+8.7% MoM`, `4.2★`. |
| `01_Executive_Overview.py` | **FAILED** (`KeyError`) | **CRASH at L166**: `KeyError: "['rating'] not in index"` (`restaurants.csv` has `avg_rating`). Top KPIs (`₹465.90 L`, `48.0k`, `₹967.33`, `4.0%`, `1.5k`) rendered pre-crash. |
| `02_Customer_Intelligence.py` | **OK** (`0` exc, `2` charts, `2` dfs) | **Mismatch**: `High-Value Segment: 0 (0.0%)` (`CLV_Tier` vs `CLV_Segment`), Customer 360 shows `Standard / Recency 0 / Orders 0 / ₹0.00 / CLV ₹0.00` (wrong keys). |
| `03_Restaurant_Intelligence.py` | **OK** (`0` exc, `1` chart, `2` dfs) | Shows **`Critical Risk Partners: 3`**, `Health 64.9/100`, `Warnings 554`. |
| `04_Operations_Intelligence.py` | **OK** (`0` exc, `3` charts, `4` dfs) | `50.0k` dispatches, `4.0k` riders, `37.4 mins`, `67.7%` SLA, `2.2k` Z/IQR flags. |
| `05_Financial_Intelligence.py` | **OK** (`0` exc, `0` charts, `3` dfs) | `GMV ₹465.90 L`, `NetRev ₹464.26 L` (`22.48%` take rate), `Profit ₹109.53 L` (`23.59%`), `Subsidies ₹20.83 L`, `Risk Exposure ₹5.54 L`. |
| `06_Decision_Intelligence.py` | **OK** (`0` exc) | `9` actions (`6` High, `2` Medium, `0/9` dispatched). |
| `07_Ask_NovaNest.py` | **OK** (`0` exc) | Prompt UI & form hydrated cleanly. |
| `08_Decision_Simulator.py` | **OK** (`0` exc, `1` df) | **Mismatch**: `Simulated Net Margin: 0.0% / Baseline: 0.0%` & `Simulated Order Volume: 0 / Baseline: 0` (`Margin`/`Total_Orders` vs `Profit_Margin`/`Orders`). |
| `09_NovaNest_Command_Center.py` | **OK** (`0` exc) | **Mismatch**: `19.6% / ₹484.52 L GMV`, `0 churn risk`, `7,495 delayed / 35.0 mins`, `Healthy Partners: 0`. |

Live Streamlit HTTP + Edge CDP (`http://127.0.0.1:8501`): `consoleErrors = 0`, `pageExceptions = 0` on visited multipage routes, clean Tornado startup/teardown.

---

## 4. MySQL Integration Check
- `MySQL80` Windows service: `Running`.
- Live connection via `.env` (`DB_HOST=localhost`, `DB_PORT=3306`, `DB_NAME=novanest`, `DB_USER=root`, `DB_PASSWORD_SET=True`): **`FAILED — ProgrammingError 1045 (28000): Access denied for user 'root'@'localhost' (using password: YES)`**.
- Classification: **`BLOCKED`** (SQL analytical views could not execute live against `MySQL80`).

---

## 5. Security Probes
- **CORS (`Origin: https://evil.example`)**: `OPTIONS` HTTP `200`, `GET` echoed **`access-control-allow-origin: https://evil.example`** & **`access-control-allow-credentials: true`**.
- **AI NL2SQL Injection Check**: `"DROP TABLE orders"` routed to `GENERAL` (not executed); **`"SELECT name FROM orders, sqlite_master LIMIT 2"`** passed `sql_valid: true` (`validate_and_sanitize_sql` comma-join bypass) and disclosed `sqlite_master` table names (`orders`, `customers`).
- **Error Responses**: Customer `404` (`{"detail":"Customer not found"}`) & Pydantic `422` clean JSON, zero tracebacks.
- **Secrets Scan**: `0` leaked API keys/passwords in tracked source; `.env` excluded in `.gitignore`.
- **Ports Cleanup**: `PORT_8000_CLEAN`, `PORT_5173_CLEAN`, `PORT_8501_CLEAN`, `PORT_9222..9226_CLEAN`.

