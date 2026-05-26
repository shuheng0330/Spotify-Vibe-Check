# Streamlit Parity Restoration Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Restore Streamlit-era academic analysis and cluster exploration information in the React + FastAPI app.

**Architecture:** Keep Streamlit removed. Expose missing analysis data through focused FastAPI JSON/image endpoints, then render the restored sections in React without duplicating ML calculations in the browser.

**Tech Stack:** FastAPI, Python unittest, React, TypeScript, Vite.

---

### Task 1: Backend Analysis Parity

**Files:**
- Create: `src/services/analysis_service.py`
- Modify: `src/api/main.py`
- Test: `tests/test_api.py`

- [x] Add failing API tests for diagnostic plot metadata, plot image serving, generated report text, cohesion/separation rows, and feature distribution summaries.
- [x] Add `src.services.analysis_service` to compute Streamlit-equivalent analysis payloads from existing model artifacts.
- [x] Extend `/api/analysis` with `diagnostic_plots`, `cohesion_separation`, and `analysis_report`.
- [x] Add `/api/analysis/plots/{plot_name}` for saved PNG diagnostics.
- [x] Add `/api/feature-distributions` for boxplot-ready cluster summaries.

### Task 2: Frontend Parity Wiring

**Files:**
- Modify: `frontend/src/types.ts`
- Modify: `frontend/src/api.ts`
- Modify: `frontend/src/App.tsx`
- Modify: `frontend/src/components/ExploreClustersTab.tsx`
- Modify: `frontend/src/components/AcademicAnalysisTab.tsx`

- [x] Add frontend DTOs for diagnostic plots, cohesion/separation rows, and feature distributions.
- [x] Fetch feature distributions with initial dashboard data.
- [x] Restore popularity range filtering on the cluster map.
- [x] Render top artists and boxplot-style feature summaries in Explore Clusters.
- [x] Render diagnostic images, cohesion/separation table, and backend-generated analysis report in Academic Analysis.

### Task 3: Verification and Documentation

**Files:**
- Modify: `PROJECT_REQUIREMENTS.md`
- Modify: `ARCHITECTURE_AND_CODING_DESIGN.md`
- Modify: `PROJECT_STATUS.md`
- Modify: `README.md`
- Modify: `frontend/README.md`

- [x] Run backend tests: `.\.venv\Scripts\python.exe -m unittest discover -s tests -v`.
- [x] Run frontend type check: `npm.cmd run lint`.
- [x] Run frontend production build: `npm.cmd run build`.
- [x] Update required project documentation to reflect restored parity endpoints and screens.
