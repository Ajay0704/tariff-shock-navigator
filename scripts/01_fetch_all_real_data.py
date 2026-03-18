import requests
import pandas as pd
import time
import os
import json

os.makedirs("data/raw", exist_ok=True)

# ═══════════════════════════════════════════════
# SOURCE 1: USITC HTS 2025 — DIRECT CSV DOWNLOAD
# 35,000+ rows of real tariff rates
# URL confirmed working from data.gov catalog
# ═══════════════════════════════════════════════
print("=" * 60)
print("SOURCE 1: USITC HTS 2025 Basic Edition")
print("=" * 60)

hts_url = (
    "https://www.usitc.gov/sites/default/files"
    "/tata/hts/hts_2025_basic_edition_csv.csv"
)
print(f"Downloading: {hts_url}")
r = requests.get(
    hts_url, timeout=60,
    headers={"User-Agent": "Mozilla/5.0"}
)
print(f"Status: {r.status_code}")
print(f"Size: {len(r.content)/1024/1024:.1f} MB")

if r.status_code == 200 and len(r.content) > 100000:
    with open("data/raw/hts_2025.csv", "wb") as f:
        f.write(r.content)
    hts_df = pd.read_csv(
        "data/raw/hts_2025.csv",
        encoding="latin1",
        low_memory=False
    )
    print(f"Rows: {len(hts_df):,}")
    print(f"Columns: {hts_df.columns.tolist()}")
    print(f"Sample:\n{hts_df.head(3).to_string()}")
else:
    print(f"FAILED: {r.text[:200]}")

# ═══════════════════════════════════════════════
# SOURCE 2: CENSUS HS10 — PRODUCT-LEVEL IMPORTS
# Pull at 10-digit level = thousands of rows
# ═══════════════════════════════════════════════
print()
print("=" * 60)
print("SOURCE 2: Census Bureau HS10 Imports by Country")
print("=" * 60)

countries = {
    "5700": "China",
    "5520": "Vietnam",
    "5330": "India",
    "2010": "Mexico"
}

hs10_records = []
for cty_code, cty_name in countries.items():
    print(f"\nPulling {cty_name} at HS10 level...")
    url = (
        "https://api.census.gov/data/timeseries"
        "/intltrade/imports/hs"
        "?get=I_COMMODITY,I_COMMODITY_LDESC,"
        "GEN_VAL_YR,GEN_VAL_MO,CTY_NAME,CTY_CODE"
        "&YEAR=2023&MONTH=12"
        f"&CTY_CODE={cty_code}"
        "&COMM_LVL=HS10"
    )
    try:
        r = requests.get(url, timeout=120)
        print(f"  Status: {r.status_code}")
        if r.status_code == 200:
            rows = r.json()
            headers = rows[0]
            df = pd.DataFrame(rows[1:], columns=headers)
            df["GEN_VAL_YR"] = pd.to_numeric(
                df["GEN_VAL_YR"], errors="coerce"
            )
            df = df[df["GEN_VAL_YR"] > 0].copy()
            df["intended_country"] = cty_name
            df["hs_chapter"] = df["I_COMMODITY"].str[:2]
            df["hs4"] = df["I_COMMODITY"].str[:4]
            df["source"] = "US Census Bureau HS10 API 2023"
            hs10_records.append(df)
            print(f"  Rows returned: {len(df):,}")
            print(
                f"  Total value: "
                f"${df['GEN_VAL_YR'].sum()/1e9:.1f}B"
            )
        else:
            print(f"  Error: {r.text[:200]}")
    except Exception as e:
        print(f"  Exception: {e}")
    time.sleep(2)

if hs10_records:
    hs10_df = pd.concat(hs10_records, ignore_index=True)
    hs10_df.to_csv(
        "data/raw/census_hs10_imports.csv", index=False
    )
    print(f"\nHS10 TOTAL ROWS: {len(hs10_df):,}")
    print(f"Unique HS10 codes: {hs10_df['I_COMMODITY'].nunique():,}")
    print("\nRows per country:")
    print(hs10_df.groupby("intended_country").size())
else:
    print("HS10 failed — falling back to HS6")
    hs6_records = []
    for cty_code, cty_name in countries.items():
        print(f"\nFallback HS6: {cty_name}...")
        url = (
            "https://api.census.gov/data/timeseries"
            "/intltrade/imports/hs"
            "?get=I_COMMODITY,I_COMMODITY_LDESC,"
            "GEN_VAL_YR,GEN_VAL_MO,CTY_NAME,CTY_CODE"
            "&YEAR=2023&MONTH=12"
            f"&CTY_CODE={cty_code}"
            "&COMM_LVL=HS6"
        )
        r = requests.get(url, timeout=60)
        if r.status_code == 200:
            rows = r.json()
            headers = rows[0]
            df = pd.DataFrame(rows[1:], columns=headers)
            df["GEN_VAL_YR"] = pd.to_numeric(
                df["GEN_VAL_YR"], errors="coerce"
            )
            df = df[df["GEN_VAL_YR"] > 0].copy()
            df["intended_country"] = cty_name
            df["hs_chapter"] = df["I_COMMODITY"].str[:2]
            df["source"] = "US Census Bureau HS6 API 2023"
            hs6_records.append(df)
            print(f"  Rows: {len(df):,}")
        time.sleep(1)
    if hs6_records:
        hs6_df = pd.concat(hs6_records, ignore_index=True)
        hs6_df.to_csv(
            "data/raw/census_hs10_imports.csv", index=False
        )
        print(f"\nHS6 TOTAL ROWS: {len(hs6_df):,}")

# ═══════════════════════════════════════════════
# SOURCE 3: CENSUS MONTHLY HS4 — 12 MONTHS
# Time series data for trend analysis
# ═══════════════════════════════════════════════
print()
print("=" * 60)
print("SOURCE 3: Census Monthly HS4 — 12 months 2023")
print("=" * 60)

monthly_records = []
months = [
    "01","02","03","04","05","06",
    "07","08","09","10","11","12"
]

for cty_code, cty_name in countries.items():
    print(f"\n{cty_name} monthly...")
    for month in months:
        url = (
            "https://api.census.gov/data/timeseries"
            "/intltrade/imports/hs"
            "?get=I_COMMODITY,I_COMMODITY_LDESC,"
            "GEN_VAL_YR,GEN_VAL_MO,CTY_NAME,CTY_CODE"
            f"&YEAR=2023&MONTH={month}"
            f"&CTY_CODE={cty_code}"
            "&COMM_LVL=HS4"
        )
        try:
            r = requests.get(url, timeout=30)
            if r.status_code == 200:
                rows = r.json()
                headers = rows[0]
                df = pd.DataFrame(rows[1:], columns=headers)
                df["GEN_VAL_YR"] = pd.to_numeric(
                    df["GEN_VAL_YR"], errors="coerce"
                )
                df["GEN_VAL_MO"] = pd.to_numeric(
                    df["GEN_VAL_MO"], errors="coerce"
                )
                df = df[df["GEN_VAL_MO"] > 0].copy()
                df["intended_country"] = cty_name
                df["year"] = 2023
                df["month"] = int(month)
                df["hs_chapter"] = (
                    df["I_COMMODITY"].str[:2]
                )
                monthly_records.append(df)
            time.sleep(0.3)
        except Exception as e:
            print(f"  {month} error: {e}")
    print(f"  Done {cty_name}")

if monthly_records:
    monthly_df = pd.concat(monthly_records, ignore_index=True)
    monthly_df.to_csv(
        "data/raw/census_monthly_hs4.csv", index=False
    )
    print(f"\nMONTHLY TOTAL ROWS: {len(monthly_df):,}")
    print(f"Months covered: 12")
    print(f"Countries: 4")
    print(f"HS4 codes: {monthly_df['I_COMMODITY'].nunique():,}")

# ═══════════════════════════════════════════════
# SOURCE 4: BLS — 6 SERIES EXPANDED
# ═══════════════════════════════════════════════
print()
print("=" * 60)
print("SOURCE 4: BLS Import Price Index — 6 series")
print("=" * 60)

bls_url = "https://api.bls.gov/publicAPI/v2/timeseries/data/"
payload = {
    "seriesid": [
        "EIUIR",     "EIUIR400",
        "EIUIR200",  "EIUIR100",
        "EIUINS",    "EIUIR300"
    ],
    "startyear": "2020",
    "endyear":   "2025"
}
r = requests.post(
    bls_url,
    data=json.dumps(payload),
    headers={"Content-type": "application/json"},
    timeout=30
)
result = r.json()
print(f"BLS Status: {result['status']}")
bls_records = []
for series in result.get("Results", {}).get("series", []):
    sid = series["seriesID"]
    for row in series["data"]:
        bls_records.append({
            "series_id":    sid,
            "year":         row["year"],
            "period":       row["period"],
            "month":        row.get("periodName", ""),
            "value":        float(row["value"])
        })
    print(f"  {sid}: {len(series['data'])} months")

bls_df = pd.DataFrame(bls_records)
bls_df.to_csv("data/raw/bls_import_prices.csv", index=False)
print(f"BLS TOTAL ROWS: {len(bls_df):,}")

# ═══════════════════════════════════════════════
# FINAL SUMMARY
# ═══════════════════════════════════════════════
print()
print("=" * 60)
print("REAL DATA PULL COMPLETE — SUMMARY")
print("=" * 60)
for f in sorted(os.listdir("data/raw")):
    path = f"data/raw/{f}"
    size = os.path.getsize(path)
    try:
        rows = sum(1 for _ in open(path)) - 1
    except:
        rows = "?"
    print(f"  {f:<40} {rows:>8} rows  {size/1024:>8.1f} KB")
