# NOVANEST — PHASE 21: STREAMLIT COMMUNITY CLOUD DEPLOYMENT
## KNOWN LIMITATIONS & HOSTING BOUNDARIES

### 1. ENVIRONMENT BOUNDARIES OF FREE COMMUNITY CLOUD
Streamlit Community Cloud is a free, shared multi-tenant hosting service with deliberate operational boundaries:

1. **Localhost Network Isolation**:
   - The cloud container cannot connect to the developer's laptop (`localhost`, `127.0.0.1`, or local Docker networks).
   - This is by design for cloud security. Local MySQL is NOT directly accessible unless hosted on a public cloud provider with TLS encryption (e.g., Aiven, AWS RDS, PlanetScale).
   - **Mitigation**: NovaNest's automated single-source CSV failover ensures that all 10 canonical tables and 9 engineered datasets (304,405 records) load seamlessly, maintaining 100% analytics fidelity.

2. **Ephemeral Filesystem**:
   - Files written to the container disk at runtime are ephemeral and lost on container restart.
   - **Mitigation**: NovaNest treats analytics as read-only or session-scoped. Permanent state must reside in external cloud MySQL or client session state.

3. **Inactivity Sleep**:
   - Free Streamlit Community Cloud apps enter "sleep mode" after 7 consecutive days of zero traffic.
   - When a user visits a sleeping app, clicking "Wake up" boots the app within ~30 seconds.

4. **Resource Ceilings**:
   - 1 GB RAM allocation per app container.
   - NovaNest uses ~250 MB peak memory under full dataset load, which operates comfortably within the 1 GB ceiling.

5. **AI Master Orchestrator Execution Modes**:
   - When deployed without an external public FastAPI backend URL, `Ask NovaNest` (Page 07) relies on either in-process execution or displays a graceful service offline notification.
   - For complete production multi-agent AI execution, deploy the FastAPI backend to a free/low-cost container service (e.g. Railway, Render, or VPS) and point `NOVANEST_API_URL` to it.

6. **Power BI PBIX Files**:
   - Desktop `.pbix` files require Microsoft Power BI Desktop to open and interact with locally.
   - In a pure web cloud environment, embedding requires publishing the report to the Microsoft Power BI Service and configuring a public embed iframe or Azure Active Directory App Registration.
