# PHASE 02 — TEST RESULTS & VALIDATION EVIDENCE

All tests were executed directly in the project workspace terminal.

---

### Test 1: Python Data Cleaning Pipeline
- **Command**: `python python/clean_data.py`
- **Exit Code**: `0` (Success)
- **Execution Output**:
  ```
  ============================================================
  🚀 STARTING NOVANEST DATA CLEANING PIPELINE
  Source Directory: C:\Users\madha\OneDrive\Documents\NovaNest-main\datasets\raw
  Output Directory: C:\Users\madha\OneDrive\Documents\NovaNest-main\datasets\cleaned
  ============================================================
  ✅ Cleaned customers.csv        | Rows: 5000    | Cols: 10 | Nulls: 0
  ✅ Cleaned restaurants.csv      | Rows: 1500    | Cols: 9  | Nulls: 0
  ✅ Cleaned menu_items.csv       | Rows: 15000   | Cols: 6  | Nulls: 0
  ✅ Cleaned riders.csv           | Rows: 4000    | Cols: 7  | Nulls: 0
  ✅ Cleaned orders.csv           | Rows: 49971   | Cols: 12 | Nulls: 0
  ✅ Cleaned payments.csv         | Rows: 49971   | Cols: 4  | Nulls: 0
  ✅ Cleaned deliveries.csv       | Rows: 49971   | Cols: 5  | Nulls: 0
  ✅ Cleaned app_events.csv       | Rows: 100000  | Cols: 3  | Nulls: 0
  ✅ Cleaned ratings_reviews.csv  | Rows: 28792   | Cols: 5  | Nulls: 0
  ✅ Cleaned promotions.csv       | Rows: 200     | Cols: 5  | Nulls: 0
  ============================================================
  🎉 ALL 10 DATASETS CLEANED & VERIFIED SUCCESSFULLY
  ============================================================
  ```
- **Result**: **PASSED**. All 10 datasets cleaned and saved with 0 nulls and 0 loss of raw data.

---

### Test 2: Master Data Integrity & Referential Validation
- **Command**: `python "python/data generation/validate_master_data.py"`
- **Exit Code**: `0` (Success)
- **Execution Output**:
  ```
  =================================================================
  🔍 NOVANEST MASTER DATA VALIDATION — Target: CLEANED
  Path: C:\Users\madha\OneDrive\Documents\NovaNest-main\datasets\cleaned
  =================================================================
  ✅ CUSTOMERS        | Rows: 5000    | Cols: 10 | Duplicates: 0   | Nulls: 0
  ✅ RESTAURANTS      | Rows: 1500    | Cols: 9  | Duplicates: 0   | Nulls: 0
  ✅ MENU_ITEMS       | Rows: 15000   | Cols: 6  | Duplicates: 0   | Nulls: 0
  ✅ RIDERS           | Rows: 4000    | Cols: 7  | Duplicates: 0   | Nulls: 0
  ✅ ORDERS           | Rows: 49971   | Cols: 12 | Duplicates: 0   | Nulls: 0
  ✅ PAYMENTS         | Rows: 49971   | Cols: 4  | Duplicates: 0   | Nulls: 0
  ✅ DELIVERIES       | Rows: 49971   | Cols: 5  | Duplicates: 0   | Nulls: 0
  ✅ APP_EVENTS       | Rows: 100000  | Cols: 3  | Duplicates: 0   | Nulls: 0
  ✅ RATINGS_REVIEWS  | Rows: 28792   | Cols: 5  | Duplicates: 0   | Nulls: 0
  ✅ PROMOTIONS       | Rows: 200     | Cols: 5  | Duplicates: 0   | Nulls: 0
  -----------------------------------------------------------------
  Total Records Analyzed: 304,405
  Overall Validation Status: PASSED (Zero Duplicates / Zero Nulls)
  =================================================================
  ```
- **Result**: **PASSED**. 304,405 records checked; zero duplicates, zero missing fields.

---

### Test 3: Feature Engineering Pipeline Execution
- **Command**: `python python/feature_engineering.py`
- **Exit Code**: `0` (Success)
- **Execution Output**:
  ```
  =================================================================
  ⚙️  STARTING NOVANEST FEATURE ENGINEERING PIPELINE
  =================================================================
  ✅ Generated 49971 engineered order records.
  ✅ Total Columns: 38 (Original: 12 -> Engineered: 38)
  ✅ Cross-City Flagged Orders: 38572 (77.2%)
  ✅ Pre-Signup Flagged Orders: 12418 (24.9%)
  ✅ Delivery Delay Flagged Orders: 16119 (32.3%)
  💾 File Saved to: datasets\engineered\orders_engineered.csv
  =================================================================
  ```
- **Result**: **PASSED**. 38 engineered features generated with explicit anomaly flags.

---

### Test 4: End-to-End Orchestrator Validation
- **Command**: `python python/pipeline_runner.py`
- **Exit Code**: `0` (Success)
- **Elapsed Time**: `4.19 seconds`
- **Result**: **PASSED**. Complete automated data workflow functions with 100% reproducibility.

---

### Test 5: Analytical Scripts Execution
- **Command**: All 4 analysis scripts in `python/data analysis/` executed.
- **Exit Code**: `0` across all 4 scripts.
- **Result**: **PASSED**.
