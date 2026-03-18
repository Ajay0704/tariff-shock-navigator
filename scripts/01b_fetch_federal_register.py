"""
Script: 01b_fetch_federal_register.py
Purpose: Fetch real tariff-related policy events from Federal Register API
Output:  data/raw/federal_register_events.csv
"""

import requests
import pandas as pd
import json
import time

print("=== FETCHING FEDERAL REGISTER TARIFF EVENTS ===")
print()

all_results = []

# Page 1
url1 = (
    "https://www.federalregister.gov/api/v1/documents.json"
    "?conditions[term]=tariff+import"
    "&conditions[publication_date][gte]=2023-01-01"
    "&fields[]=title"
    "&fields[]=publication_date"
    "&fields[]=abstract"
    "&fields[]=document_number"
    "&fields[]=html_url"
    "&fields[]=effective_on"
    "&per_page=100"
    "&order=newest"
    "&page=1"
)

print(f"Fetching page 1: {url1[:80]}...")
r1 = requests.get(url1, timeout=30)
print(f"Status: {r1.status_code}")
data1 = r1.json()
print(f"Total count from API: {data1.get('count', 'N/A')}")
print(f"Results on page 1: {len(data1.get('results', []))}")

results1 = data1.get("results", [])
all_results.extend(results1)

# Page 2 if needed
if len(all_results) < 100 and data1.get("next_page_url"):
    time.sleep(1)
    url2 = data1["next_page_url"]
    print(f"\nFetching page 2: {url2[:80]}...")
    r2 = requests.get(url2, timeout=30)
    print(f"Status: {r2.status_code}")
    data2 = r2.json()
    results2 = data2.get("results", [])
    print(f"Results on page 2: {len(results2)}")
    all_results.extend(results2)

# Also try a second search term to supplement
if len(all_results) < 50:
    time.sleep(1)
    url_extra = (
        "https://www.federalregister.gov/api/v1/documents.json"
        "?conditions[term]=Section+301+tariff"
        "&conditions[publication_date][gte]=2022-01-01"
        "&fields[]=title"
        "&fields[]=publication_date"
        "&fields[]=abstract"
        "&fields[]=document_number"
        "&fields[]=html_url"
        "&fields[]=effective_on"
        "&per_page=50"
        "&order=newest"
    )
    print(f"\nFetching extra results (Section 301): {url_extra[:80]}...")
    r_extra = requests.get(url_extra, timeout=30)
    print(f"Status: {r_extra.status_code}")
    data_extra = r_extra.json()
    results_extra = data_extra.get("results", [])
    print(f"Extra results: {len(results_extra)}")
    all_results.extend(results_extra)

print(f"\nTotal raw results collected: {len(all_results)}")

# Deduplicate by document_number
seen = set()
deduped = []
for r in all_results:
    dn = r.get("document_number", "")
    if dn not in seen:
        seen.add(dn)
        deduped.append(r)

print(f"After dedup: {len(deduped)} unique documents")

# Build DataFrame
rows = []
for doc in deduped:
    rows.append({
        "document_number": doc.get("document_number", ""),
        "title": doc.get("title", ""),
        "publication_date": doc.get("publication_date", ""),
        "effective_on": doc.get("effective_on", ""),
        "abstract": (doc.get("abstract") or "")[:300],
        "html_url": doc.get("html_url", ""),
    })

df = pd.DataFrame(rows)

# Sort by publication_date descending
df["publication_date"] = pd.to_datetime(df["publication_date"], errors="coerce")
df = df.sort_values("publication_date", ascending=False).reset_index(drop=True)

print(f"\nFinal DataFrame shape: {df.shape}")
print(f"Columns: {list(df.columns)}")
print(f"\nRow count: {len(df)}")

if len(df) < 30:
    print("WARNING: Row count below 30 minimum threshold!")
else:
    print(f"PASS: {len(df)} rows >= 30 minimum")

print("\n--- Sample rows (first 5) ---")
for i, row in df.head(5).iterrows():
    print(f"  [{i}] {row['publication_date'].strftime('%Y-%m-%d') if pd.notna(row['publication_date']) else 'N/A'} | {row['title'][:80]}")

# Save
out_path = "data/raw/federal_register_events.csv"
df.to_csv(out_path, index=False)
print(f"\nSaved to {out_path}")
print(f"File size: {__import__('os').path.getsize(out_path):,} bytes")

print("\n=== FEDERAL REGISTER FETCH COMPLETE ===")
