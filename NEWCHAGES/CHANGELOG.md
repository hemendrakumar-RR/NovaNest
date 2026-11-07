# NOVANEST — CHANGELOG

All notable changes to the NovaNest project will be documented in this file.
The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [Unreleased] - Phase 02: Data Intelligence & Pipeline Stabilization

### Added
- Created `NEWCHAGES/` change management infrastructure with 8 root tracking registers and 9 phase folders.
- Created `NEWCHAGES/ROADMAP_STATUS.md` tracking detailed progress across all 10 project milestones.
- Created `.gitignore` protecting secrets, virtual environments, caches, and IDE artifacts.
- Created `.env.example` defining environment configuration templates for MySQL and application runtime.
- Created `requirements.txt` declaring all core dependencies.

### Changed
- Refactored `python/clean_data.py`:
  - Resolved `FileNotFoundError` bug by pointing source dataset path to `datasets/raw/`.
  - Replaced naive `dropna()` with granular dataset-specific cleaning functions.
  - Implemented data type casting, string sanitization, datetime ISO formatting, and bounds checking.
  - Preserved raw datasets intact while outputting validated cleaned files to `datasets/cleaned/`.

---

## [0.1.0] - 2026-11-07 - Phase 01: Complete System Audit

### Added
- Completed comprehensive file-by-file audit of all 6 workspace folders.
- Generated `reports/NOVANEST_MASTER_AUDIT.md` documenting architecture, technical gaps, and 10-phase master roadmap.
- Initialized local Git repository on branch `main`.
