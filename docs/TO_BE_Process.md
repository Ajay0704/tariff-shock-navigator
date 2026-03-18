# TO-BE Process Document
## Target State: Tariff Shock Navigator Pipeline

**Version:** 1.0
**Date:** March 2026
**Author:** Arunachalam Thirumurthi (Operations Analyst)

---

## 1. Overview

This document describes the target-state (TO-BE) process delivered by the Tariff Shock Navigator. It replaces the manual, Excel-based AS-IS workflow with an automated, reproducible Python + DuckDB + API pipeline.

---

## 2. Target Process Flow

```
Step 1: scripts/01_fetch_all_real_data.py
        - Census HS10 API  -> 42,327 rows
        - Census Monthly   -> 42,420 rows
        - BLS API          -> 285 rows
        - Federal Register -> 100 documents
        - All saved to data/raw/
        |
        v
Step 2: scripts/02_process_data.py
        - Assign USTR tariff rates (HS chapter x country matrix)
        - Compute tariff_exposure_usd per product line
        - Compute composite risk score (0-10)
        - Run 3 scenario models -> 126,981 scenario rows
        - Aggregate monthly/country/chapter summaries
        - All saved to data/processed/
        |
        v
Step 3: scripts/03_run_sql.py
        - 8 DuckDB SQL queries on processed CSVs
        - Results saved to outputs/q1_*.csv through q8_*.csv
        |
        v
Step 4: scripts/04_charts.py
        - 6 publication-quality PNG charts
        - Heatmap, bar, scenario, trends, BLS index, risk quadrant
        - Saved to charts/
        |
        v
Step 5: scripts/05_exec_briefing.py
        - Load all metrics from CSVs (no hardcoding)
        - Auto-generate executive_briefing.md
        - Saved to outputs/
        |
        v
Step 6: Review, version, push
        - git commit with structured messages
        - git push to GitHub (public portfolio)
```

---

## 3. TO-BE Improvements vs AS-IS

| Pain Point | AS-IS | TO-BE |
|-----------|-------|-------|
| P-01: Manual Census download | 4-6 hours | Automated API call, < 5 minutes |
| P-02: No HS10 granularity | HS2/HS4 only | 42,327 HS10 product lines |
| P-03: Manual USTR lookup | PDF search | Structured Python dict with chapter-rate mapping |
| P-04: No scenario modeling | 0 scenarios | 3 scenarios x 42,327 rows = 126,981 rows |
| P-05: BLS not integrated | Ad hoc | 285 rows, MoM/YoY, spike detection |
| P-06: Federal Register not tracked | Email alerts | 100 structured documents with metadata |
| P-07: Excel performance limits | Crashes at 40k rows | DuckDB handles 126,981 rows in seconds |
| P-08: No risk scoring | None | 0-10 composite risk index with tier labels |
| P-09: No version control | None | Git with 5 structured commits |
| P-10: Manual charts | 4-6 hours | 6 charts auto-generated in < 1 minute |

---

## 4. TO-BE Technology Stack

| Layer | Tool | Benefit |
|-------|------|---------|
| Data ingestion | Python 3 + requests | Automated, reproducible, version-controlled |
| Data storage | CSV flat files + DuckDB in-memory | Portable, no database setup required |
| Processing | pandas + numpy | 42,327-row operations in seconds |
| SQL analytics | DuckDB 1.5.0 | OLAP-grade queries on CSV files |
| Visualization | matplotlib + seaborn | Publication-quality dark-mode charts |
| Documentation | Markdown (.md) | Renders on GitHub without tooling |
| Version control | Git + GitHub | Full history, public portfolio |

---

## 5. TO-BE Metrics

| Metric | Target State | Achieved |
|--------|-------------|---------|
| Analysis cycle time | < 30 minutes from cold start | Yes |
| HS code granularity | HS10 (10 digits) | 42,327 rows |
| Countries covered | 4 (China, Vietnam, India, Mexico) | Yes |
| Scenario models | 3 | 126,981 rows |
| Chart production time | < 1 minute automated | 6 charts in < 60 seconds |
| Reproducibility | 100% (run scripts in order) | Yes |
| Data pipeline automation | 100% API-driven | Yes |
| Risk scoring | 0-10 composite index | Yes |

---

## 6. File Structure

```
tariff-shock-navigator/
  data/
    raw/                    <- API outputs (never modified)
    processed/              <- Transformed, analysis-ready
  scripts/                  <- Numbered, sequential Python scripts
  sql/                      <- DuckDB analytical queries
  charts/                   <- 6 PNG charts
  outputs/                  <- SQL results, executive briefing
  docs/                     <- BRD, AS-IS, TO-BE, KPI Dictionary
  README.md                 <- Project overview with real numbers
```

---

## 7. Reproducibility Instructions

```bash
# From clean state:
cd tariff-shock-navigator

# Step 1: Pull all data
python scripts/01_fetch_all_real_data.py

# Step 2: Process
python scripts/02_process_data.py

# Step 3: SQL analysis
python scripts/03_run_sql.py

# Step 4: Charts
python scripts/04_charts.py

# Step 5: Executive briefing
python scripts/05_exec_briefing.py
```

All outputs will be regenerated from live government APIs.
