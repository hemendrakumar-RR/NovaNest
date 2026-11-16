# NOVANEST — PHASE 21: STREAMLIT COMMUNITY CLOUD DEPLOYMENT
## COMPLETE STEP-BY-STEP DEPLOYMENT GUIDE

### PREREQUISITES
1. A GitHub account.
2. A free account on [Streamlit Community Cloud](https://share.streamlit.io).
3. NovaNest repository pushed to your GitHub account (awaiting user approval).

---

### STEP 1: PREPARE GITHUB REPOSITORY
1. Confirm that `.gitignore` contains:
   ```gitignore
   .env
   .streamlit/secrets.toml
   backup/
   bin/
   *.sql
   *.sql.enc
   *.sig
   node_modules/
   frontend/dist/
   ```
2. Commit all application changes and push to your private or public GitHub repository:
   ```bash
   git add .
   git commit -m "feat(phase21): prepare NovaNest for Streamlit Community Cloud deployment"
   git push origin main
   ```
   *(Note: Antigravity strictly does NOT execute git push without explicit user consent).*

---

### STEP 2: CONNECT REPOSITORY ON STREAMLIT COMMUNITY CLOUD
1. Navigate to [https://share.streamlit.io](https://share.streamlit.io) and sign in with your GitHub account.
2. Click **"New app"** (or **"Create app"**).
3. Select your repository: `<your-github-username>/NovaNest-main`.
4. Set the deployment fields:
   - **Branch**: `main`
   - **Main file path**: `streamlit_app/app.py`
   - **App URL**: `https://<your-chosen-app-name>.streamlit.app` (e.g. `https://novanest.streamlit.app`)
5. Click **"Advanced settings"** before deploying.

---

### STEP 3: CONFIGURE SECRETS (ADVANCED SETTINGS)
In the **Secrets** text area of Advanced Settings, enter your environment configuration:

#### Option A: Standalone Deployment (Bundled 304,405 Cleaned & Engineered CSV Records)
```toml
# NovaNest Streamlit Community Cloud Secrets
DATA_SOURCE = "csv"

# Optional: Remote FastAPI Backend (if you host the API on Render/Railway/VPS)
# NOVANEST_API_URL = "https://your-api-url.example.com"
# NOVANEST_API_KEY = "your-operator-api-key"
# NOVANEST_ADMIN_KEY = "your-admin-api-key"
```

#### Option B: Connected Cloud Database Deployment (External MySQL)
```toml
# NovaNest Streamlit Community Cloud Secrets
DATA_SOURCE = "mysql"

# External Cloud MySQL (e.g. Aiven, PlanetScale, AWS RDS, DigitalOcean Managed MySQL)
DB_HOST = "your-cloud-mysql-host.example.com"
DB_PORT = 3306
DB_USER = "novanest_app"
DB_PASSWORD = "your-secure-password"
DB_NAME = "novanest_db"

# Remote FastAPI Backend
# NOVANEST_API_URL = "https://your-api-url.example.com"
# NOVANEST_API_KEY = "your-operator-api-key"
# NOVANEST_ADMIN_KEY = "your-admin-api-key"
```

---

### STEP 4: DEPLOY AND OBSERVE LOGS
1. Click **"Deploy!"**.
2. Streamlit Cloud will allocate a container, clone your repository, and install dependencies from `requirements.txt`.
3. In the bottom-right corner, click **"Manage app"** -> **"Logs"** to monitor build progress:
   - Installing `pandas`, `plotly`, `scikit-learn`, `streamlit`...
   - Running `streamlit run streamlit_app/app.py`...
4. In ~60 to 90 seconds, your app will load at:
   `https://<your-chosen-app-name>.streamlit.app`

---

### STEP 5: POST-DEPLOYMENT VERIFICATION CHECKLIST
- [ ] **Home Page**: Verify title "NovaNest — Enterprise Business Analytics" and official blue/slate theme.
- [ ] **Data Source Badge**: Sidebar indicates data source (`MySQL Database` or `CSV File Store (Cleaned & Engineered)`).
- [ ] **Page 01 (Executive Overview)**: Metrics load cleanly (GMV, Total Orders, Active Customers, AOV).
- [ ] **Page 02 to 06**: Analytical charts, tables, and KPI cards render without error.
- [ ] **Page 07 (Ask NovaNest)**: Inquire about business metrics; test multi-turn conversation.
- [ ] **Page 08 & 09 (Decision Simulator & Digital Twin)**: Test simulation slider controls and map rendering.
