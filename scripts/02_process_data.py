"""
Script: 02_process_data.py
Purpose: Process all raw data into risk scores, scenarios, monthly trends,
         BLS trends, country summaries, and chapter summaries.
Inputs:  data/raw/census_hs10_imports.csv
         data/raw/census_monthly_hs4.csv
         data/raw/bls_import_prices.csv
         data/raw/federal_register_events.csv
Outputs: data/processed/hs10_with_risk.csv          (42,327 rows)
         data/processed/scenario_results.csv         (126,981 rows = 42,327 x 3)
         data/processed/monthly_trends.csv
         data/processed/bls_trends.csv
         data/processed/country_summary.csv
         data/processed/chapter_summary.csv
"""

import pandas as pd
import numpy as np
import os

print("=" * 60)
print("PHASE 2: DATA PROCESSING")
print("=" * 60)
print()

# ----------------------------------------------------------------
# TARIFF RATES (from USTR published schedules)
# ----------------------------------------------------------------
tariff_rates = {
    "China": {
        "rate_map": {
            "61": 37.0, "62": 37.0, "87": 27.5, "72": 25.0, "73": 25.0,
            "84": 25.0, "85": 25.0, "88": 25.0, "90": 25.0, "94": 25.0,
            "39": 25.0, "29": 25.0, "30": 25.0, "38": 25.0, "76": 25.0,
        },
        "default_rate": 25.0,
        "risk_score": 9.2,
        "risk_tier": "Critical",
    },
    "Vietnam": {
        "rate_map": {},
        "default_rate": 46.0,
        "risk_score": 6.8,
        "risk_tier": "High",
    },
    "India": {
        "rate_map": {},
        "default_rate": 26.0,
        "risk_score": 4.5,
        "risk_tier": "Medium",
    },
    "Mexico": {
        "rate_map": {"72": 25.0, "73": 25.0, "76": 10.0},
        "default_rate": 0.0,
        "risk_score": 2.8,
        "risk_tier": "Low",
    },
}

# Scenario definitions
scenarios = {
    "baseline": {"label": "Baseline (Current Tariffs)", "multiplier": 1.0},
    "escalation": {"label": "Escalation (+25% across all)", "multiplier": 1.25},
    "relief": {"label": "Relief (-10% reduction)", "multiplier": 0.90},
}

# ----------------------------------------------------------------
# STEP 1: Load HS10 data
# ----------------------------------------------------------------
print("--- STEP 1: Loading census_hs10_imports.csv ---")
hs10 = pd.read_csv("data/raw/census_hs10_imports.csv", dtype={"I_COMMODITY": str})
print(f"Loaded: {len(hs10):,} rows, {len(hs10.columns)} columns")
print(f"Columns: {list(hs10.columns)}")
print(f"Countries: {hs10['intended_country'].value_counts().to_dict()}")
print()

# ----------------------------------------------------------------
# STEP 2: Assign tariff rates and compute risk
# ----------------------------------------------------------------
print("--- STEP 2: Assigning tariff rates + computing risk scores ---")

def get_tariff_rate(country, chapter):
    """Return applicable tariff rate for a country/chapter pair."""
    if country not in tariff_rates:
        return 0.0
    info = tariff_rates[country]
    ch = str(chapter).zfill(2)
    return info["rate_map"].get(ch, info["default_rate"])

def get_risk_score(country):
    return tariff_rates.get(country, {}).get("risk_score", 0.0)

def get_risk_tier(country):
    return tariff_rates.get(country, {}).get("risk_tier", "Unknown")

# Normalize column names
hs10["country_clean"] = hs10["intended_country"].str.strip()
hs10["chapter_clean"] = hs10["hs_chapter"].astype(str).str.strip().str.zfill(2)

# Apply tariff rate
hs10["tariff_rate_pct"] = hs10.apply(
    lambda r: get_tariff_rate(r["country_clean"], r["chapter_clean"]), axis=1
)

# Risk scores
hs10["risk_score"] = hs10["country_clean"].apply(get_risk_score)
hs10["risk_tier"] = hs10["country_clean"].apply(get_risk_tier)

# Import value as float
hs10["import_value_usd"] = pd.to_numeric(hs10["GEN_VAL_YR"], errors="coerce").fillna(0.0)

# Tariff exposure = import_value * tariff_rate
hs10["tariff_exposure_usd"] = (hs10["import_value_usd"] * hs10["tariff_rate_pct"] / 100.0).round(2)

# Composite risk index (0-10 scale): blend country risk + tariff rate weight
hs10["composite_risk"] = (
    hs10["risk_score"] * 0.6
    + (hs10["tariff_rate_pct"] / 50.0) * 10.0 * 0.4
).round(3)

print(f"Tariff rate distribution:")
print(hs10["tariff_rate_pct"].value_counts().head(10).to_string())
print()
print(f"Risk tier distribution:")
print(hs10["risk_tier"].value_counts().to_string())
print()
print(f"Total tariff exposure: ${hs10['tariff_exposure_usd'].sum()/1e9:.2f}B")
print()

# Save hs10_with_risk.csv
out1 = "data/processed/hs10_with_risk.csv"
hs10.to_csv(out1, index=False)
print(f"Saved {out1}: {len(hs10):,} rows")
print()

# ----------------------------------------------------------------
# STEP 3: Scenario simulation (3 scenarios x 42,327 rows = 126,981)
# ----------------------------------------------------------------
print("--- STEP 3: Scenario simulation (3 scenarios x 42,327 rows) ---")

scenario_rows = []
for sc_key, sc_info in scenarios.items():
    sc_df = hs10.copy()
    sc_df["scenario"] = sc_key
    sc_df["scenario_label"] = sc_info["label"]
    adjusted_rate = (sc_df["tariff_rate_pct"] * sc_info["multiplier"]).clip(upper=100.0)
    sc_df["adjusted_tariff_rate_pct"] = adjusted_rate.round(4)
    sc_df["adjusted_tariff_exposure_usd"] = (
        sc_df["import_value_usd"] * sc_df["adjusted_tariff_rate_pct"] / 100.0
    ).round(2)
    # Margin impact estimate: 35% of tariff cost is absorbed as margin compression
    sc_df["margin_impact_pct"] = (
        (sc_df["adjusted_tariff_exposure_usd"] / sc_df["import_value_usd"].replace(0, np.nan))
        * 0.35 * 100
    ).round(4).fillna(0.0)
    scenario_rows.append(sc_df)
    total_exp = sc_df["adjusted_tariff_exposure_usd"].sum()
    print(f"  Scenario '{sc_key}': {len(sc_df):,} rows, total exposure ${total_exp/1e9:.2f}B")

scenarios_df = pd.concat(scenario_rows, ignore_index=True)
print(f"\nTotal scenario rows: {len(scenarios_df):,}")

out2 = "data/processed/scenario_results.csv"
scenarios_df.to_csv(out2, index=False)
print(f"Saved {out2}: {len(scenarios_df):,} rows")
print()

# ----------------------------------------------------------------
# STEP 4: Monthly trends from census_monthly_hs4.csv
# ----------------------------------------------------------------
print("--- STEP 4: Monthly trends aggregation ---")
monthly = pd.read_csv("data/raw/census_monthly_hs4.csv", dtype={"I_COMMODITY": str})
print(f"Loaded monthly: {len(monthly):,} rows")

monthly["import_value_usd"] = pd.to_numeric(monthly["GEN_VAL_MO"], errors="coerce").fillna(0.0)
monthly["month_num"] = pd.to_numeric(monthly["month"], errors="coerce").fillna(0).astype(int)
monthly["year_num"] = pd.to_numeric(monthly["year"], errors="coerce").fillna(2023).astype(int)

# Aggregate by year, month, country
monthly_agg = (
    monthly
    .groupby(["year_num", "month_num", "intended_country"], as_index=False)
    .agg(
        total_import_value=("import_value_usd", "sum"),
        record_count=("I_COMMODITY", "count"),
    )
)
monthly_agg["year_month"] = (
    monthly_agg["year_num"].astype(str).str.zfill(4)
    + "-"
    + monthly_agg["month_num"].astype(str).str.zfill(2)
)
monthly_agg = monthly_agg.sort_values(["year_num", "month_num", "intended_country"]).reset_index(drop=True)

print(f"Monthly aggregated: {len(monthly_agg):,} rows")
print(f"Year/month range: {monthly_agg['year_month'].min()} to {monthly_agg['year_month'].max()}")
print(f"Countries: {monthly_agg['intended_country'].unique().tolist()}")
print()
print("Monthly totals by country (all months sum):")
print(monthly_agg.groupby("intended_country")["total_import_value"].sum().apply(lambda x: f"${x/1e9:.2f}B").to_string())
print()

out3 = "data/processed/monthly_trends.csv"
monthly_agg.to_csv(out3, index=False)
print(f"Saved {out3}: {len(monthly_agg):,} rows")
print()

# ----------------------------------------------------------------
# STEP 5: BLS import price trends
# ----------------------------------------------------------------
print("--- STEP 5: BLS import price trends ---")
bls = pd.read_csv("data/raw/bls_import_prices.csv")
print(f"Loaded BLS: {len(bls):,} rows")
print(f"Columns: {list(bls.columns)}")

bls["value"] = pd.to_numeric(bls["value"], errors="coerce")
bls["month_num"] = pd.to_numeric(bls["month"], errors="coerce").fillna(0).astype(int)
bls["year_num"] = pd.to_numeric(bls["year"], errors="coerce").fillna(0).astype(int)

# Sort and compute MoM change per series
bls = bls.sort_values(["series_id", "year_num", "month_num"]).reset_index(drop=True)
bls["prev_value"] = bls.groupby("series_id")["value"].shift(1)
bls["mom_change_pct"] = ((bls["value"] - bls["prev_value"]) / bls["prev_value"] * 100).round(4)
bls["spike"] = bls["mom_change_pct"].abs() > 0.5

# YoY change
bls["prev_year_value"] = bls.groupby(["series_id", "month_num"])["value"].shift(1)
bls["yoy_change_pct"] = ((bls["value"] - bls["prev_year_value"]) / bls["prev_year_value"] * 100).round(4)

bls["year_month"] = (
    bls["year_num"].astype(str).str.zfill(4)
    + "-"
    + bls["month_num"].astype(str).str.zfill(2)
)

print(f"\nBLS series IDs: {bls['series_id'].unique().tolist()}")
print(f"Date range: {bls['year_month'].min()} to {bls['year_month'].max()}")
print(f"Spike count (MoM > 0.5%): {bls['spike'].sum()}")
print()
print("Latest values by series:")
latest = bls.groupby("series_id").last()[["year_month", "value", "mom_change_pct"]].reset_index()
print(latest.to_string(index=False))
print()

out4 = "data/processed/bls_trends.csv"
bls.to_csv(out4, index=False)
print(f"Saved {out4}: {len(bls):,} rows")
print()

# ----------------------------------------------------------------
# STEP 6: Country summary
# ----------------------------------------------------------------
print("--- STEP 6: Country summary ---")
country_summary = (
    hs10.groupby("country_clean", as_index=False)
    .agg(
        total_import_value_usd=("import_value_usd", "sum"),
        total_tariff_exposure_usd=("tariff_exposure_usd", "sum"),
        product_count=("I_COMMODITY", "nunique"),
        avg_tariff_rate_pct=("tariff_rate_pct", "mean"),
        risk_score=("risk_score", "first"),
        risk_tier=("risk_tier", "first"),
    )
)
country_summary["effective_tariff_rate_pct"] = (
    country_summary["total_tariff_exposure_usd"] / country_summary["total_import_value_usd"] * 100
).round(4)
country_summary = country_summary.sort_values("total_import_value_usd", ascending=False)
country_summary["import_value_B"] = (country_summary["total_import_value_usd"] / 1e9).round(3)
country_summary["tariff_exposure_B"] = (country_summary["total_tariff_exposure_usd"] / 1e9).round(3)

print(country_summary.to_string(index=False))
print()

out5 = "data/processed/country_summary.csv"
country_summary.to_csv(out5, index=False)
print(f"Saved {out5}: {len(country_summary):,} rows")
print()

# ----------------------------------------------------------------
# STEP 7: Chapter summary (top HS chapters by exposure)
# ----------------------------------------------------------------
print("--- STEP 7: Chapter summary ---")
chapter_summary = (
    hs10.groupby(["chapter_clean", "country_clean"], as_index=False)
    .agg(
        total_import_value_usd=("import_value_usd", "sum"),
        total_tariff_exposure_usd=("tariff_exposure_usd", "sum"),
        product_count=("I_COMMODITY", "nunique"),
        avg_tariff_rate_pct=("tariff_rate_pct", "mean"),
    )
)
chapter_summary["import_value_B"] = (chapter_summary["total_import_value_usd"] / 1e9).round(4)
chapter_summary["tariff_exposure_B"] = (chapter_summary["total_tariff_exposure_usd"] / 1e9).round(4)
chapter_summary = chapter_summary.sort_values("total_tariff_exposure_usd", ascending=False).reset_index(drop=True)

print(f"Total chapter-country combinations: {len(chapter_summary):,}")
print()
print("Top 20 chapters by tariff exposure:")
print(chapter_summary.head(20).to_string(index=False))
print()

out6 = "data/processed/chapter_summary.csv"
chapter_summary.to_csv(out6, index=False)
print(f"Saved {out6}: {len(chapter_summary):,} rows")
print()

# ----------------------------------------------------------------
# FINAL SUMMARY
# ----------------------------------------------------------------
print("=" * 60)
print("PHASE 2 COMPLETE - ALL OUTPUT FILES")
print("=" * 60)
for f in [out1, out2, out3, out4, out5, out6]:
    sz = os.path.getsize(f)
    rows_count = sum(1 for _ in open(f)) - 1
    print(f"  {f}: {rows_count:,} rows, {sz:,} bytes")

print()
print("Key metrics:")
print(f"  Total HS10 products processed:    {len(hs10):,}")
print(f"  Total scenario rows generated:    {len(scenarios_df):,}")
print(f"  Total import value (4 countries): ${hs10['import_value_usd'].sum()/1e9:.2f}B")
print(f"  Total tariff exposure:            ${hs10['tariff_exposure_usd'].sum()/1e9:.2f}B")
print(f"  Unique HS10 product codes:        {hs10['I_COMMODITY'].nunique():,}")
print(f"  Unique HS chapters:               {hs10['chapter_clean'].nunique():,}")
print()
print("=== DONE ===")
