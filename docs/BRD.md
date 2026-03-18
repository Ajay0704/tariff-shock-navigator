# Business Requirements Document (BRD)
## Tariff Shock Navigator

**Version:** 1.0
**Date:** March 2026
**Author:** Arunachalam Thirumurthi (Operations Analyst)
**Status:** Final

---

## 1. Business Context

U.S. importers face unprecedented tariff volatility. Section 301 tariffs on Chinese goods (25%-37.5%), a 46% tariff on Vietnamese imports (April 2025 executive order), and ongoing USMCA renegotiation pressure from Mexico create significant cost uncertainty for supply chain and procurement teams.

In 2023, the U.S. imported $1,098 billion in goods from China, Vietnam, India, and Mexico combined. Under current tariff schedules, the annual tariff exposure on those imports is estimated at $186.58 billion - an effective burden of 16.99% on total import value.

Operations teams currently lack a centralized, data-driven tool to:
1. Quantify tariff exposure at the product (HS10) level
2. Model alternative tariff scenarios before they materialize
3. Prioritize sourcing risk by country and HS chapter
4. Connect policy signals (Federal Register) to financial impact

---

## 2. Objectives

| ID | Objective |
|----|-----------|
| OBJ-01 | Ingest real Census, BLS, and Federal Register data at HS10 granularity |
| OBJ-02 | Compute tariff exposure and composite risk scores for 42,327 product lines |
| OBJ-03 | Model 3 tariff scenarios: baseline, +25% escalation, -10% relief |
| OBJ-04 | Identify highest-risk HS chapters and source countries |
| OBJ-05 | Provide exec-ready briefing auto-generated from live data |
| OBJ-06 | Surface BLS price index spikes as early warning signals |

---

## 3. Scope

### In Scope
- 4 countries: China, Vietnam, India, Mexico
- Full year 2023 HS10 import data (42,327 rows, api.census.gov)
- 12-month HS4 monthly trends (42,420 rows)
- BLS import price index series 2020-2025 (285 rows)
- Federal Register tariff policy events (100 documents)
- 3 tariff scenario simulations (126,981 scenario rows)
- 8 DuckDB SQL analytical queries
- 6 visualization charts (matplotlib/seaborn)
- Executive briefing markdown

### Out of Scope
- Real-time data feeds (data is pulled at analysis time)
- Export duty or foreign tariff analysis
- Countries outside the 4 listed above
- HS codes at 2-digit or 6-digit (HS10 and HS4 only)

---

## 4. Functional Requirements

| ID | Requirement | Priority |
|----|------------|---------|
| FR-01 | System shall ingest Census HS10 data for 4 countries with >= 40,000 rows | Must Have |
| FR-02 | System shall assign USTR tariff rates to each HS10-country combination | Must Have |
| FR-03 | System shall compute tariff_exposure_usd = import_value * tariff_rate | Must Have |
| FR-04 | System shall generate risk scores on 0-10 scale blending country and rate factors | Must Have |
| FR-05 | System shall model baseline, escalation, and relief scenarios | Must Have |
| FR-06 | System shall aggregate to monthly, country, and chapter summaries | Must Have |
| FR-07 | System shall run 8 DuckDB analytical queries and export results | Should Have |
| FR-08 | System shall generate 6 publication-quality charts from real data | Should Have |
| FR-09 | System shall auto-generate executive briefing from live processed data | Should Have |
| FR-10 | System shall ingest Federal Register policy events | Could Have |

---

## 5. Non-Functional Requirements

| ID | Requirement |
|----|------------|
| NFR-01 | All raw data sourced from government APIs (Census, BLS, Federal Register) |
| NFR-02 | No synthetic, Kaggle, or learning-platform data permitted |
| NFR-03 | Scripts must be reproducible from clean state via numbered sequence |
| NFR-04 | Pipeline must complete in under 30 minutes on standard hardware |
| NFR-05 | All outputs must include data provenance (source URL or API reference) |
| NFR-06 | Charts must be readable in dark and light environments |

---

## 6. Data Sources

| Source | API Endpoint | Rows | Notes |
|--------|-------------|------|-------|
| U.S. Census Bureau (HS10) | api.census.gov/data/timeseries/intltrade/imports/hs | 42,327 | Annual 2023, COMM_LVL=HS10, 4 countries |
| U.S. Census Bureau (Monthly HS4) | Same endpoint | 42,420 | COMM_LVL=HS4, 12 months |
| BLS Import Price Index | api.bls.gov/publicAPI/v2/timeseries/data/ | 285 | Series: EIUIR, EIUIR100, EIUIR300, EIUIR400 |
| Federal Register | federalregister.gov/api/v1/documents.json | 100 | Term: tariff+import, since 2023-01-01 |
| USTR Tariff Schedules | ustr.gov (hardcoded from published rates) | N/A | Section 301 + April 2025 executive order |

---

## 7. Stakeholders

| Role | Name / Group | Interest |
|------|-------------|---------|
| Operations Analyst | Arunachalam Thirumurthi | Primary builder and analyst |
| Supply Chain Leadership | TBD | Scenario and risk outputs |
| Finance/FP&A | TBD | Exposure quantification |
| Procurement | TBD | Product-level sourcing decisions |

---

## 8. Success Criteria

1. All 4 data sources successfully ingested with verified row counts
2. 42,327 HS10 product lines assigned tariff rates and risk scores
3. Scenario simulation generates 126,981 rows (3 scenarios x 42,327 products)
4. All 8 SQL queries return results and are saved to outputs/
5. All 6 charts render with real data values (no placeholders)
6. Executive briefing is auto-generated with correct dollar figures from CSVs
7. Full project committed to GitHub with clean git history

---

## 9. Assumptions and Constraints

- Tariff rates are as published by USTR as of April 2025; actual rates may differ post-negotiation
- Census API data reflects reported imports; actual duties paid may differ due to exemptions
- BLS series EIUIR200 and EIUINS returned 0 data points and are excluded
- Vietnam 46% rate is from April 2025 executive order; subject to change
- Mexico default rate is 0.0% (USMCA), with specific HS chapter exceptions (72, 73, 76)
