"""
Script: 03_run_sql.py
Purpose: Run 8 analytical DuckDB SQL queries on processed trade data.
         Print full output of every query. Save results to outputs/.
Inputs:  data/processed/*.csv
Outputs: outputs/q1_country_exposure.csv  through  outputs/q8_escalation_delta.csv
         outputs/sql_results_summary.txt
"""

import duckdb
import pandas as pd
import os

print("=" * 60)
print("PHASE 3: DUCKDB SQL ANALYSIS")
print("=" * 60)
print()

# Connect to in-memory DuckDB
con = duckdb.connect(database=":memory:")
print(f"DuckDB version: {duckdb.__version__}")
print()

# Change working directory context for relative paths in SQL
os.chdir("/home/user/workspace/tariff-shock-navigator")

# ----------------------------------------------------------------
# Define all 8 queries
# ----------------------------------------------------------------
queries = {
    "q1_country_exposure": {
        "title": "Q1: Import Value and Tariff Exposure by Country",
        "sql": """
            SELECT
                country_clean AS country,
                COUNT(*) AS product_lines,
                ROUND(SUM(import_value_usd) / 1e9, 3) AS import_value_B,
                ROUND(SUM(tariff_exposure_usd) / 1e9, 3) AS tariff_exposure_B,
                ROUND(SUM(tariff_exposure_usd) / NULLIF(SUM(import_value_usd), 0) * 100, 4)
                    AS effective_rate_pct,
                risk_tier
            FROM read_csv_auto('data/processed/hs10_with_risk.csv')
            GROUP BY country_clean, risk_tier
            ORDER BY tariff_exposure_B DESC
        """
    },
    "q2_top_chapters": {
        "title": "Q2: Top 15 HS Chapters by Tariff Exposure",
        "sql": """
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
            LIMIT 15
        """
    },
    "q3_scenario_comparison": {
        "title": "Q3: Scenario Comparison - Baseline vs Escalation vs Relief",
        "sql": """
            SELECT
                scenario,
                scenario_label,
                country_clean AS country,
                ROUND(SUM(adjusted_tariff_exposure_usd) / 1e9, 3) AS total_exposure_B,
                ROUND(AVG(adjusted_tariff_rate_pct), 4) AS avg_rate_pct,
                COUNT(*) AS product_lines
            FROM read_csv_auto('data/processed/scenario_results.csv')
            GROUP BY scenario, scenario_label, country_clean
            ORDER BY scenario, total_exposure_B DESC
        """
    },
    "q4_top_china_products": {
        "title": "Q4: Top 20 Products by Import Value from China",
        "sql": """
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
            LIMIT 20
        """
    },
    "q5_risk_tier_summary": {
        "title": "Q5: Risk Tier Distribution with Financial Totals",
        "sql": """
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
            ORDER BY avg_composite_risk DESC
        """
    },
    "q6_monthly_trends": {
        "title": "Q6: Monthly Import Trend by Country",
        "sql": """
            SELECT
                year_month,
                intended_country AS country,
                ROUND(total_import_value / 1e9, 3) AS import_value_B,
                record_count
            FROM read_csv_auto('data/processed/monthly_trends.csv')
            ORDER BY year_month, country
        """
    },
    "q7_bls_spikes": {
        "title": "Q7: BLS Import Price Spikes (Top 20 by MoM Change)",
        "sql": """
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
            LIMIT 20
        """
    },
    "q8_escalation_delta": {
        "title": "Q8: Escalation Scenario - Incremental Exposure vs Baseline",
        "sql": """
            SELECT
                country_clean AS country,
                ROUND(SUM(CASE WHEN scenario = 'escalation'
                    THEN adjusted_tariff_exposure_usd ELSE 0 END) / 1e9, 3) AS escalation_B,
                ROUND(SUM(CASE WHEN scenario = 'baseline'
                    THEN adjusted_tariff_exposure_usd ELSE 0 END) / 1e9, 3) AS baseline_B,
                ROUND(
                    (SUM(CASE WHEN scenario = 'escalation'
                        THEN adjusted_tariff_exposure_usd ELSE 0 END)
                    - SUM(CASE WHEN scenario = 'baseline'
                        THEN adjusted_tariff_exposure_usd ELSE 0 END)) / 1e9, 3
                ) AS incremental_exposure_B,
                ROUND(
                    (SUM(CASE WHEN scenario = 'escalation'
                        THEN adjusted_tariff_exposure_usd ELSE 0 END)
                    - SUM(CASE WHEN scenario = 'baseline'
                        THEN adjusted_tariff_exposure_usd ELSE 0 END))
                    / NULLIF(SUM(CASE WHEN scenario = 'baseline'
                        THEN adjusted_tariff_exposure_usd ELSE 0 END), 0)
                    * 100, 2
                ) AS pct_increase
            FROM read_csv_auto('data/processed/scenario_results.csv')
            WHERE scenario IN ('baseline', 'escalation')
            GROUP BY country_clean
            ORDER BY incremental_exposure_B DESC
        """
    },
}

# ----------------------------------------------------------------
# Run all queries
# ----------------------------------------------------------------
summary_lines = []
results = {}

for qkey, qinfo in queries.items():
    print("-" * 60)
    print(f"RUNNING: {qinfo['title']}")
    print("-" * 60)

    df = con.execute(qinfo["sql"]).fetchdf()
    results[qkey] = df

    # Print FULL output (no truncation)
    pd.set_option("display.max_rows", None)
    pd.set_option("display.max_columns", None)
    pd.set_option("display.width", 200)
    pd.set_option("display.float_format", "{:.4f}".format)
    print(df.to_string(index=False))
    print(f"\nRows returned: {len(df)}")

    # Save to CSV
    out_path = f"outputs/{qkey}.csv"
    df.to_csv(out_path, index=False)
    print(f"Saved: {out_path}")

    summary_lines.append(f"{qkey}: {len(df)} rows -> {out_path}")
    print()

# ----------------------------------------------------------------
# Save summary text
# ----------------------------------------------------------------
print("=" * 60)
print("PHASE 3 COMPLETE - QUERY SUMMARY")
print("=" * 60)
for line in summary_lines:
    print(f"  {line}")

summary_text = "\n".join([
    "Tariff Shock Navigator - SQL Analysis Results Summary",
    "=" * 50,
    "",
] + summary_lines)
with open("outputs/sql_results_summary.txt", "w") as f:
    f.write(summary_text)
print("\nSummary written to outputs/sql_results_summary.txt")
print()
print("=== DONE ===")
