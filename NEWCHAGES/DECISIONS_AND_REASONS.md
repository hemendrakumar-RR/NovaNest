# NOVANEST — DECISIONS AND REASONS
**Architectural Decision Records (ADR)**

---

### ADR-001: Preservation of Raw Datasets
- **Status**: Accepted
- **Context**: The raw datasets in `datasets/raw/` represent the simulated ground truth for the 5-city food delivery marketplace.
- **Decision**: Never perform in-place modification or destructive cleaning on `datasets/raw/*.csv`. All transformations must read from `datasets/raw/` and write to `datasets/cleaned/` or `datasets/engineered/`.
- **Reason**: Maintains 100% pipeline reproducibility and prevents accidental data loss.

---

### ADR-002: Dynamic Path Resolution using `pathlib.Path`
- **Status**: Accepted
- **Context**: Legacy scripts contained hardcoded relative paths like `Path(__file__).resolve().parent.parent` which resolved differently depending on the folder depth (`python/` vs `python/data generation/`).
- **Decision**: Standardize dynamic project-root discovery using `Path(__file__).resolve().parents[N]` or root-anchoring, ensuring scripts execute identically from terminal root or subdirectories.
- **Reason**: Eliminates `FileNotFoundError` across all Python runners.

---

### ADR-003: Non-Destructive Handling of Cross-City and Temporal Anomalies
- **Status**: Accepted
- **Context**: Audit revealed 38,572 orders where customer city != restaurant/rider city, and 12,418 orders occurring before customer signup date.
- **Decision**: Do not arbitrarily drop or delete these records from `datasets/cleaned/orders.csv`, as dropping them would destroy 77% of the order dataset and break referential integrity with `payments.csv` and `deliveries.csv`. Instead:
  1. Document the anomalies in `reports/data_quality_report.md`.
  2. Maintain `datasets/cleaned/` with referential consistency intact.
  3. Create an enriched feature-engineered dataset `datasets/engineered/orders_geo_temporal_enriched.csv` with explicit anomaly flags (`cross_city_flag`, `pre_signup_order_flag`) so downstream ML models can either filter or train on verified subsets.
- **Reason**: Preserves existing metrics, avoids downstream join breakage, and maintains mathematical honesty without fabricating data.

---

### ADR-004: Preservation of Power BI Report (`powerbi/NovaNest.pbix`)
- **Status**: Accepted
- **Context**: `NovaNest.pbix` is a 5.6 MB binary file containing 5 dashboards and 27 DAX measures.
- **Decision**: Strictly treat `powerbi/NovaNest.pbix` as a protected read-only asset. Inspect internal schema and visual layouts via safe zip extraction. Never overwrite or re-save without explicit backup and user consent.
- **Reason**: Protects against binary corruption.
