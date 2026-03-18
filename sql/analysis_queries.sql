-- =============================================================
-- analysis_queries.sql
-- Tariff Shock Navigator - 8 DuckDB Analytical Queries
-- Data sources: data/processed/*.csv
-- =============================================================

-- Q1: Total import value and tariff exposure by country
-- Ranked by total tariff exposure descending
SELECT
    country_clean AS country,
    COUNT(*) AS product_lines,
    ROUND(SUM(import_value_usd) / 1e9, 3) AS import_value_B,
    ROUND(SUM(tariff_exposure_usd) / 1e9, 3) AS tariff_exposure_B,
    ROUND(SUM(tariff_exposure_usd) / NULLIF(SUM(import_value_usd), 0) * 100, 4) AS effective_rate_pct,
    risk_tier
FROM read_csv_auto('data/processed/hs10_with_risk.csv')
GROUP BY country_clean, risk_tier
ORDER BY tariff_exposure_B DESC;

-- Q2: Top 15 HS chapters by tariff exposure across all countries
SELECT
    chapter_clean AS hs_chapter,
    country_clean AS country,
    ROUND(SUM(import_value_usd) / 1e9, 4) AS import_value_B,
    ROUND(SUM(tariff_exposure_usd) / 1e9, 4) AS tariff_exposure_B,
    COUNT(DISTINCT I_COMMODITY) AS unique_products,
    ROUND(AVG(tariff_rate_pct), 2) AS avg_tariff_rate
FROM read_csv_auto('data/processed/hs10_with_risk.csv')
GROUP BY chapter_clean, country_clean
ORDER BY tariff_exposure_B DESC
LIMIT 15;

-- Q3: Scenario comparison - baseline vs escalation vs relief
SELECT
    scenario,
    scenario_label,
    country_clean AS country,
    ROUND(SUM(adjusted_tariff_exposure_usd) / 1e9, 3) AS total_exposure_B,
    ROUND(AVG(adjusted_tariff_rate_pct), 4) AS avg_rate_pct,
    COUNT(*) AS product_lines
FROM read_csv_auto('data/processed/scenario_results.csv')
GROUP BY scenario, scenario_label, country_clean
ORDER BY scenario, total_exposure_B DESC;

-- Q4: Top 20 products by import value from China (Critical risk)
SELECT
    I_COMMODITY AS hs10_code,
    SUBSTRING(I_COMMODITY_LDESC, 1, 60) AS description,
    ROUND(import_value_usd / 1e9, 4) AS import_value_B,
    tariff_rate_pct,
    ROUND(tariff_exposure_usd / 1e6, 2) AS tariff_exposure_M,
    composite_risk
FROM read_csv_auto('data/processed/hs10_with_risk.csv')
WHERE country_clean = 'China'
ORDER BY import_value_usd DESC
LIMIT 20;

-- Q5: Risk tier distribution summary with financial totals
SELECT
    risk_tier,
    country_clean AS country,
    COUNT(*) AS product_lines,
    ROUND(SUM(import_value_usd) / 1e9, 3) AS import_value_B,
    ROUND(SUM(tariff_exposure_usd) / 1e9, 3) AS exposure_B,
    ROUND(AVG(composite_risk), 3) AS avg_composite_risk,
    ROUND(AVG(tariff_rate_pct), 2) AS avg_tariff_rate_pct
FROM read_csv_auto('data/processed/hs10_with_risk.csv')
GROUP BY risk_tier, country_clean
ORDER BY avg_composite_risk DESC;

-- Q6: Monthly import trend - total value by country and month
SELECT
    year_month,
    intended_country AS country,
    ROUND(total_import_value / 1e9, 3) AS import_value_B,
    record_count
FROM read_csv_auto('data/processed/monthly_trends.csv')
ORDER BY year_month, country;

-- Q7: BLS import price spikes - months with largest MoM change
SELECT
    series_id,
    year_month,
    ROUND(value, 2) AS price_index,
    ROUND(mom_change_pct, 4) AS mom_change_pct,
    ROUND(yoy_change_pct, 4) AS yoy_change_pct,
    spike
FROM read_csv_auto('data/processed/bls_trends.csv')
WHERE spike = true
ORDER BY ABS(mom_change_pct) DESC
LIMIT 20;

-- Q8: Escalation scenario - incremental exposure delta vs baseline
SELECT
    country_clean AS country,
    ROUND(SUM(CASE WHEN scenario = 'escalation' THEN adjusted_tariff_exposure_usd ELSE 0 END) / 1e9, 3)
        AS escalation_B,
    ROUND(SUM(CASE WHEN scenario = 'baseline' THEN adjusted_tariff_exposure_usd ELSE 0 END) / 1e9, 3)
        AS baseline_B,
    ROUND(
        (SUM(CASE WHEN scenario = 'escalation' THEN adjusted_tariff_exposure_usd ELSE 0 END)
        - SUM(CASE WHEN scenario = 'baseline' THEN adjusted_tariff_exposure_usd ELSE 0 END)) / 1e9, 3
    ) AS incremental_exposure_B,
    ROUND(
        (SUM(CASE WHEN scenario = 'escalation' THEN adjusted_tariff_exposure_usd ELSE 0 END)
        - SUM(CASE WHEN scenario = 'baseline' THEN adjusted_tariff_exposure_usd ELSE 0 END))
        / NULLIF(SUM(CASE WHEN scenario = 'baseline' THEN adjusted_tariff_exposure_usd ELSE 0 END), 0)
        * 100, 2
    ) AS pct_increase
FROM read_csv_auto('data/processed/scenario_results.csv')
WHERE scenario IN ('baseline', 'escalation')
GROUP BY country_clean
ORDER BY incremental_exposure_B DESC;
