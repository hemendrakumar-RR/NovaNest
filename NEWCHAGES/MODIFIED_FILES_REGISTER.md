# NOVANEST — MODIFIED FILES REGISTER

This file records every modification to an existing repository file, detailing the original functionality, specific changes made, reasons, and verification results.

---

| Date | File Name | File Path | Original Functionality | What Was Changed | Why Changed | Improvements | Affected Dependencies | Test Results |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| 2026-11-07 | `clean_data.py` | `python/clean_data.py` | Naive cleaning attempting to read `datasets/` with blind `dropna()` | Fixed input path to `datasets/raw/`; implemented specific cleaning functions for all 10 datasets; added datetime ISO formatting & bounds checks | Script was throwing `FileNotFoundError` and dropping rows blindly | Robust error-free cleaning, zero raw data loss, production logging | `pandas`, `numpy`, `pathlib` | Passed (All 10 datasets cleaned & verified) |
| 2026-11-07 | `.gitignore` | `/.gitignore` | Standard python/powerbi ignore rules | Added `*.zip` and `*.tar.gz` | Prevent `datasets.zip` (8.7 MB) archive from cluttering git tracking | Keeps repository lean, prevents archive duplication | Git | Passed (Ignored `datasets.zip`) |
| 2026-11-07 | `feature_engineering.py` | `python/feature_engineering.py` | Basic 7-column feature script reading only orders | Upgraded to modular 38-feature engine joining restaurants, customers, riders, and deliveries | Enable full business metrics, unit economics, and anomaly audit flags | 38 enriched features, reproducible pipeline, error handling | `pandas`, `numpy`, `pathlib` | Passed (49,971 rows x 38 cols verified) |


