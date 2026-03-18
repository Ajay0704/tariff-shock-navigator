# AS-IS Process Document
## Current State: Tariff Impact Analysis

**Version:** 1.0
**Date:** March 2026
**Author:** Arunachalam Thirumurthi (Operations Analyst)

---

## 1. Overview

This document describes the current-state (AS-IS) process for how operations and supply chain teams analyze tariff exposure and trade risk before the Tariff Shock Navigator was implemented.

---

## 2. Current Process Flow

```
Step 1: Identify relevant import categories
        |
        v
Step 2: Manual download from Census.gov trade portal
        (spreadsheet export, no API)
        |
        v
Step 3: Open in Excel or Google Sheets
        (filter by country manually)
        |
        v
Step 4: Lookup tariff rates from USTR PDFs
        (no structured rate database)
        |
        v
Step 5: Manually calculate exposure per product line
        (= import_value * tariff_rate)
        |
        v
Step 6: Build summary pivot tables
        (no DuckDB, no SQL)
        |
        v
Step 7: Copy figures into PowerPoint for exec review
        (charts built manually in Excel)
        |
        v
Step 8: Distribute via email
        (no version control, no reproducibility)
```

---

## 3. AS-IS Pain Points

| # | Pain Point | Business Impact |
|---|-----------|----------------|
| P-01 | Manual Census download - no API | Analyst time: 4-6 hours per analysis cycle |
| P-02 | No HS10-level granularity | Misses product-specific exposure ($186.58B total not visible) |
| P-03 | USTR tariff rate lookup is manual PDF search | Rate errors common; Vietnam 46% rate often missed |
| P-04 | No scenario modeling | Cannot quantify escalation risk ($46.65B gap unknown) |
| P-05 | BLS data not integrated | Import price spikes (125 events, 2020-2025) not flagged |
| P-06 | Federal Register not monitored | Policy signals (100 documents in 2023-2026) go untracked |
| P-07 | Excel-only analysis | Handles 42,327 rows slowly; 126,981 scenario rows infeasible |
| P-08 | No risk scoring | Critical vs Low tier distinctions not quantified |
| P-09 | No version control | No git history; analysis not reproducible |
| P-10 | Chart creation is manual | 6+ hours per reporting cycle for visual output |

---

## 4. Current Data Assets

| Asset | Current State | Limitation |
|-------|-------------|-----------|
| Census trade data | Manual portal downloads, partial | Not at HS10 level; only high-level aggregates |
| Tariff rate reference | PDF table (USTR website) | Not structured; manually updated |
| Import price data | BLS website tables, downloaded ad hoc | No time-series analysis; no MoM spike detection |
| Policy tracker | Email inbox / Google News alerts | Not structured; no linkage to financial impact |
| Risk scoring | None | No quantitative framework exists |
| Scenario model | None | Escalation and relief scenarios are guesses |

---

## 5. Current Technology Stack

| Layer | Current Tool | Limitation |
|-------|-------------|-----------|
| Data ingestion | Manual browser download | No automation; no reproducibility |
| Data storage | Local Excel / Google Sheets | 42,327 rows hits performance limits |
| Query / analysis | Excel pivot tables | No SQL; no joins; no complex aggregations |
| Visualization | Excel charts | No custom dark-mode charts; no Python viz |
| Version control | None | No git; no commit history |
| Documentation | None | No BRD, no KPI dictionary |

---

## 6. Metrics: AS-IS Baseline

| Metric | Current State |
|--------|--------------|
| Analysis cycle time | 2-3 days per cycle |
| HS code granularity | HS2 or HS4 only |
| Countries covered | 1-2 (usually only China) |
| Scenario models | 0 |
| Chart production time | 4-6 hours manually |
| Reproducibility | 0% (manual, no scripts) |
| Data pipeline automation | 0% |

---

## 7. Handoff to TO-BE

The TO-BE process directly addresses each pain point above. See `TO_BE_Process.md` for the target state.
