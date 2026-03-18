# KPI Dictionary
## Tariff Shock Navigator

**Version:** 1.0
**Date:** March 2026
**Author:** Arunachalam Thirumurthi (Operations Analyst)

---

## Overview

This dictionary defines every metric, index, and derived field produced by the Tariff Shock Navigator pipeline.
All values are computed from U.S. Census Bureau, BLS, and Federal Register data. No synthetic values are used.

---

## 1. Core Trade Metrics

### import_value_usd
- **Definition:** Annual import value of a specific HS10 product from a specific country, in U.S. dollars
- **Source:** U.S. Census Bureau, `GEN_VAL_YR` field from timeseries/intltrade/imports/hs
- **Formula:** Direct from API, no transformation
- **Unit:** USD
- **Aggregated values:**
  - China total: $427,246,582,836 (2023)
  - Vietnam total: $114,408,343,727 (2023)
  - India total: $83,557,090,891 (2023)
  - Mexico total: $472,907,368,135 (2023)
  - **Grand total: $1,098,119,385,589 ($1.098T)**

### tariff_rate_pct
- **Definition:** Applicable tariff rate (percent) for a given HS10 product-country combination
- **Source:** USTR published schedules; Section 301 tariffs; April 2025 executive order
- **Formula:** Looked up from `tariff_rates` dict in `02_process_data.py`; chapter-level rate map with country default
- **Unit:** Percent (e.g., 25.0 = 25%)
- **Values in use:**
  - China: 37% (HS 61, 62), 27.5% (HS 87), 25% (all other chapters)
  - Vietnam: 46% (all chapters, flat)
  - India: 26% (all chapters, flat)
  - Mexico: 25% (HS 72, 73), 10% (HS 76), 0% (all others, USMCA)

### tariff_exposure_usd
- **Definition:** Estimated annual tariff cost if all imports are dutiable at the applicable rate
- **Formula:** `import_value_usd * tariff_rate_pct / 100`
- **Unit:** USD
- **Aggregated values:**
  - China: $109,223,808,285 ($109.2B)
  - Vietnam: $52,627,838,114 ($52.6B)
  - India: $21,724,843,682 ($21.7B)
  - Mexico: $3,004,788,215 ($3.0B)
  - **Grand total: $186,581,278,296 ($186.6B)**

---

## 2. Risk Metrics

### risk_score
- **Definition:** Country-level risk score on a 0-10 scale, reflecting tariff volatility, policy unpredictability, and geopolitical risk
- **Source:** Analyst-assigned based on USTR/geopolitical context
- **Values:**
  - China: 9.2 (Critical)
  - Vietnam: 6.8 (High)
  - India: 4.5 (Medium)
  - Mexico: 2.8 (Low)

### risk_tier
- **Definition:** Categorical risk bucket derived from risk_score
- **Values:**
  - Critical (score >= 8.5): China
  - High (score 5.0-8.4): Vietnam
  - Medium (score 3.0-4.9): India
  - Low (score < 3.0): Mexico

### composite_risk
- **Definition:** Product-line composite risk index blending country risk score and tariff rate weight
- **Formula:** `risk_score * 0.6 + (tariff_rate_pct / 50.0) * 10.0 * 0.4`
- **Unit:** 0-10 dimensionless index
- **Interpretation:** Higher = greater exposure. China HS 61 products score ~7.52; Mexico baseline scores ~1.83

### effective_tariff_rate_pct
- **Definition:** Actual realized tariff rate across a country or chapter portfolio (exposure-weighted)
- **Formula:** `total_tariff_exposure_usd / total_import_value_usd * 100`
- **Values:**
  - China: 25.56%
  - Vietnam: 46.00%
  - India: 26.00%
  - Mexico: 0.64%
  - **Overall: 16.99%**

---

## 3. Scenario Metrics

### scenario
- **Definition:** Identifier for one of three tariff scenario models
- **Values:** `baseline`, `escalation`, `relief`

### adjusted_tariff_rate_pct
- **Definition:** Tariff rate after applying scenario multiplier
- **Formula:** `tariff_rate_pct * scenario_multiplier` (capped at 100%)
- **Multipliers:** baseline=1.0, escalation=1.25, relief=0.90

### adjusted_tariff_exposure_usd
- **Definition:** Tariff exposure under the specified scenario
- **Formula:** `import_value_usd * adjusted_tariff_rate_pct / 100`
- **Scenario totals:**
  - Baseline: $186,581,278,296 ($186.6B)
  - Escalation: $233,226,597,870 ($233.2B, +$46.6B)
  - Relief: $167,923,150,467 ($167.9B, -$18.7B)

### margin_impact_pct
- **Definition:** Estimated margin compression from tariff exposure; assumes 35% of tariff cost is absorbed by importer
- **Formula:** `(adjusted_tariff_exposure_usd / import_value_usd) * 0.35 * 100`
- **Unit:** Percent

---

## 4. BLS Metrics

### series_id
- **Definition:** BLS Import Price Index series identifier
- **Active series:**
  - `EIUIR`: All Imports Index (base 2000=100)
  - `EIUIR100`: Industrial Supplies and Materials
  - `EIUIR300`: Capital Goods
  - `EIUIR400`: Consumer Goods
- **Excluded:** EIUIR200, EIUINS (returned 0 data points)

### value
- **Definition:** Index value for the given series, year, and period
- **Unit:** Index (2000=100)
- **Latest values (2025):** EIUIR=141.8, EIUIR100=291.3, EIUIR300=117.2, EIUIR400=117.7

### mom_change_pct
- **Definition:** Month-over-month percentage change in BLS index value
- **Formula:** `(value - prev_value) / prev_value * 100`
- **Unit:** Percent

### yoy_change_pct
- **Definition:** Year-over-year percentage change in BLS index value
- **Formula:** `(value - prev_year_value) / prev_year_value * 100`
- **Unit:** Percent

### spike
- **Definition:** Boolean flag indicating a significant price movement
- **Formula:** `abs(mom_change_pct) > 0.5`
- **Count:** 125 spike events detected across all series (2020-2025)

---

## 5. Coverage Metrics

| Metric | Value |
|--------|-------|
| Total HS10 product lines | 42,327 |
| Unique HS10 product codes | 16,344 |
| Unique HS chapters | 98 |
| Countries | 4 (China, Vietnam, India, Mexico) |
| Monthly HS4 rows | 42,420 |
| Months covered | Jan-Dec 2023 |
| BLS observations | 285 |
| BLS years covered | 2020-2025 |
| Federal Register documents | 100 |
| Scenario rows | 126,981 |

---

## 6. Column Reference by File

### data/processed/hs10_with_risk.csv (42,327 rows)
| Column | Type | Description |
|--------|------|-------------|
| I_COMMODITY | str | HS10 code (10 digits) |
| I_COMMODITY_LDESC | str | Product description |
| import_value_usd | float | Annual import value (USD) |
| tariff_rate_pct | float | Applicable tariff rate (%) |
| tariff_exposure_usd | float | Annual tariff exposure (USD) |
| risk_score | float | Country risk score (0-10) |
| risk_tier | str | Critical / High / Medium / Low |
| composite_risk | float | Composite risk index (0-10) |
| country_clean | str | Country name |
| chapter_clean | str | HS chapter (2 digits) |

### data/processed/scenario_results.csv (126,981 rows)
Extends hs10_with_risk.csv with: `scenario`, `scenario_label`, `adjusted_tariff_rate_pct`, `adjusted_tariff_exposure_usd`, `margin_impact_pct`

### data/processed/bls_trends.csv (285 rows)
Extends raw BLS data with: `mom_change_pct`, `yoy_change_pct`, `spike`, `year_month`
