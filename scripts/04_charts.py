"""
Script: 04_charts.py
Purpose: Generate 6 publication-quality PNG charts from real Census + BLS data.
Charts:
  1. chart_01_tariff_exposure_heatmap.png    - Chapter x Country tariff exposure heatmap
  2. chart_02_country_exposure_bar.png       - Country total exposure bar chart
  3. chart_03_scenario_comparison.png        - Scenario exposure comparison (grouped bar)
  4. chart_04_monthly_trends.png             - Monthly import trend lines (4 countries)
  5. chart_05_bls_price_index.png            - BLS import price index over time
  6. chart_06_risk_quadrant.png              - Risk quadrant: import value vs tariff rate
"""

import pandas as pd
import numpy as np
import matplotlib
matplotlib.use("Agg")  # non-interactive backend
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import seaborn as sns
import os

print("=" * 60)
print("PHASE 4: CHART GENERATION")
print("=" * 60)
print()

# Output directory
os.makedirs("charts", exist_ok=True)

# Style configuration
DARK_BG = "#0d1117"
NAVY   = "#0f1929"
AMBER  = "#f5a623"
GOLD   = "#d4962b"
RED    = "#e05c5c"
GREEN  = "#4caf7d"
BLUE   = "#4a9edd"
PURPLE = "#9b72cf"
GRAY   = "#8b949e"
WHITE  = "#e6edf3"
COLORS = [AMBER, BLUE, GREEN, PURPLE, RED, "#78dce8"]
COUNTRY_COLORS = {"China": RED, "Vietnam": AMBER, "India": BLUE, "Mexico": GREEN}

plt.rcParams.update({
    "figure.facecolor": DARK_BG,
    "axes.facecolor": NAVY,
    "axes.edgecolor": "#30363d",
    "axes.labelcolor": WHITE,
    "xtick.color": GRAY,
    "ytick.color": GRAY,
    "text.color": WHITE,
    "grid.color": "#21262d",
    "grid.linewidth": 0.5,
    "font.family": "DejaVu Sans",
    "font.size": 11,
    "axes.titlesize": 14,
    "axes.titleweight": "bold",
    "axes.titlepad": 14,
})

# ----------------------------------------------------------------
# CHART 1: Tariff Exposure Heatmap (Chapter x Country)
# ----------------------------------------------------------------
print("--- Chart 1: Tariff Exposure Heatmap ---")

chap = pd.read_csv("data/processed/chapter_summary.csv")

# Top 20 chapters by total exposure
top_chaps = (
    chap.groupby("chapter_clean")["tariff_exposure_B"]
    .sum()
    .sort_values(ascending=False)
    .head(20)
    .index.tolist()
)
chap_filt = chap[chap["chapter_clean"].isin(top_chaps)]
pivot = chap_filt.pivot_table(
    index="chapter_clean",
    columns="country_clean",
    values="tariff_exposure_B",
    aggfunc="sum",
    fill_value=0,
)
# Reorder rows by total
pivot = pivot.loc[
    pivot.sum(axis=1).sort_values(ascending=False).index
]
pivot.index = [f"HS {str(i).zfill(2)}" for i in pivot.index]

fig, ax = plt.subplots(figsize=(12, 8))
fig.patch.set_facecolor(DARK_BG)
ax.set_facecolor(NAVY)

sns.heatmap(
    pivot,
    ax=ax,
    cmap="YlOrRd",
    annot=True,
    fmt=".1f",
    linewidths=0.3,
    linecolor="#21262d",
    cbar_kws={"label": "Tariff Exposure ($B)"},
    annot_kws={"size": 8, "color": "black"},
)
ax.set_title("Tariff Exposure Heatmap: Top 20 HS Chapters by Country ($B)", pad=16, color=WHITE, fontsize=13)
ax.set_xlabel("Country", color=WHITE)
ax.set_ylabel("HS Chapter", color=WHITE)
ax.tick_params(colors=WHITE)
cbar = ax.collections[0].colorbar
cbar.ax.tick_params(colors=GRAY, labelsize=9)
cbar.set_label("Tariff Exposure ($B)", color=GRAY)

fig.tight_layout()
path1 = "charts/chart_01_tariff_exposure_heatmap.png"
fig.savefig(path1, dpi=150, bbox_inches="tight", facecolor=DARK_BG)
plt.close()
print(f"Saved: {path1} ({os.path.getsize(path1):,} bytes)")
print()

# ----------------------------------------------------------------
# CHART 2: Country Total Exposure Bar Chart
# ----------------------------------------------------------------
print("--- Chart 2: Country Exposure Bar Chart ---")

cs = pd.read_csv("data/processed/country_summary.csv")
cs = cs.sort_values("tariff_exposure_B", ascending=True)

fig, ax = plt.subplots(figsize=(10, 6))
fig.patch.set_facecolor(DARK_BG)
ax.set_facecolor(NAVY)

colors = [COUNTRY_COLORS.get(c, GRAY) for c in cs["country_clean"]]
bars = ax.barh(cs["country_clean"], cs["tariff_exposure_B"], color=colors, edgecolor="#21262d", height=0.55)

for bar, val in zip(bars, cs["tariff_exposure_B"]):
    ax.text(
        bar.get_width() + 0.5,
        bar.get_y() + bar.get_height() / 2,
        f"${val:.1f}B",
        va="center", ha="left", color=WHITE, fontsize=11, fontweight="bold",
    )

# Also show import value as reference
for i, (_, row) in enumerate(cs.iterrows()):
    ax.text(
        -2,
        i,
        f"Import: ${row['import_value_B']:.0f}B",
        va="center", ha="right", color=GRAY, fontsize=9,
    )

ax.set_title("Total Tariff Exposure by Country (2023, $B)", color=WHITE)
ax.set_xlabel("Tariff Exposure ($B)", color=WHITE)
ax.set_xlim(-30, cs["tariff_exposure_B"].max() * 1.2)
ax.axvline(0, color="#30363d", linewidth=1)
ax.grid(axis="x", alpha=0.3)
ax.spines["top"].set_visible(False)
ax.spines["right"].set_visible(False)

# Risk tier labels
tier_map = dict(zip(cs["country_clean"], cs["risk_tier"]))
tier_colors = {"Critical": RED, "High": AMBER, "Medium": BLUE, "Low": GREEN}
for i, country in enumerate(cs["country_clean"]):
    tier = tier_map[country]
    ax.text(
        cs["tariff_exposure_B"].max() * 1.05,
        i,
        tier,
        va="center", ha="left", color=tier_colors.get(tier, GRAY), fontsize=9, fontweight="bold",
    )

fig.tight_layout()
path2 = "charts/chart_02_country_exposure_bar.png"
fig.savefig(path2, dpi=150, bbox_inches="tight", facecolor=DARK_BG)
plt.close()
print(f"Saved: {path2} ({os.path.getsize(path2):,} bytes)")
print()

# ----------------------------------------------------------------
# CHART 3: Scenario Comparison (Grouped Bar)
# ----------------------------------------------------------------
print("--- Chart 3: Scenario Comparison ---")

sc_raw = pd.read_csv("outputs/q3_scenario_comparison.csv")
pivot_sc = sc_raw.pivot_table(
    index="country", columns="scenario", values="total_exposure_B", aggfunc="sum"
)
pivot_sc = pivot_sc[["baseline", "escalation", "relief"]]  # order columns
pivot_sc = pivot_sc.reindex(["China", "Vietnam", "India", "Mexico"])

x = np.arange(len(pivot_sc))
width = 0.25

fig, ax = plt.subplots(figsize=(12, 6))
fig.patch.set_facecolor(DARK_BG)
ax.set_facecolor(NAVY)

sc_colors = {"baseline": AMBER, "escalation": RED, "relief": GREEN}
sc_labels = {"baseline": "Baseline", "escalation": "Escalation (+25%)", "relief": "Relief (-10%)"}

bars_list = []
for i, (sc_key, sc_col) in enumerate(pivot_sc.items()):
    bars = ax.bar(
        x + (i - 1) * width,
        sc_col.values,
        width,
        label=sc_labels[sc_key],
        color=sc_colors[sc_key],
        edgecolor="#21262d",
        alpha=0.9,
    )
    bars_list.append(bars)
    for bar in bars:
        ax.text(
            bar.get_x() + bar.get_width() / 2,
            bar.get_height() + 0.5,
            f"${bar.get_height():.1f}B",
            ha="center", va="bottom", color=WHITE, fontsize=8.5,
        )

ax.set_title("Tariff Exposure: Scenario Comparison by Country ($B)", color=WHITE)
ax.set_xlabel("Country", color=WHITE)
ax.set_ylabel("Tariff Exposure ($B)", color=WHITE)
ax.set_xticks(x)
ax.set_xticklabels(pivot_sc.index, color=WHITE)
ax.legend(facecolor=NAVY, edgecolor="#30363d", labelcolor=WHITE, fontsize=10)
ax.grid(axis="y", alpha=0.3)
ax.spines["top"].set_visible(False)
ax.spines["right"].set_visible(False)

fig.tight_layout()
path3 = "charts/chart_03_scenario_comparison.png"
fig.savefig(path3, dpi=150, bbox_inches="tight", facecolor=DARK_BG)
plt.close()
print(f"Saved: {path3} ({os.path.getsize(path3):,} bytes)")
print()

# ----------------------------------------------------------------
# CHART 4: Monthly Import Trends (Line Chart - 4 Countries)
# ----------------------------------------------------------------
print("--- Chart 4: Monthly Import Trends ---")

mt = pd.read_csv("data/processed/monthly_trends.csv")

fig, ax = plt.subplots(figsize=(13, 6))
fig.patch.set_facecolor(DARK_BG)
ax.set_facecolor(NAVY)

for country in ["China", "Mexico", "Vietnam", "India"]:
    sub = mt[mt["intended_country"] == country].sort_values("month_num")
    vals = sub["total_import_value"].values / 1e9
    months = sub["month_num"].values
    color = COUNTRY_COLORS[country]
    ax.plot(months, vals, marker="o", markersize=5, linewidth=2, color=color, label=country)
    # Annotate last point
    ax.annotate(
        f"{country}\n${vals[-1]:.1f}B",
        xy=(months[-1], vals[-1]),
        xytext=(12.3, vals[-1]),
        color=color,
        fontsize=9,
        va="center",
    )

ax.set_title("Monthly Import Value by Country - Jan to Dec 2023 ($B)\nSource: U.S. Census Bureau", color=WHITE)
ax.set_xlabel("Month (2023)", color=WHITE)
ax.set_ylabel("Import Value ($B)", color=WHITE)
ax.set_xticks(range(1, 13))
ax.set_xticklabels(["Jan","Feb","Mar","Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec"], color=GRAY)
ax.set_xlim(1, 14)
ax.legend(facecolor=NAVY, edgecolor="#30363d", labelcolor=WHITE, fontsize=10, loc="upper left")
ax.grid(alpha=0.3)
ax.spines["top"].set_visible(False)
ax.spines["right"].set_visible(False)

fig.tight_layout()
path4 = "charts/chart_04_monthly_trends.png"
fig.savefig(path4, dpi=150, bbox_inches="tight", facecolor=DARK_BG)
plt.close()
print(f"Saved: {path4} ({os.path.getsize(path4):,} bytes)")
print()

# ----------------------------------------------------------------
# CHART 5: BLS Import Price Index Over Time
# ----------------------------------------------------------------
print("--- Chart 5: BLS Import Price Index ---")

bls = pd.read_csv("data/processed/bls_trends.csv")
bls_series = {
    "EIUIR":    ("All Imports", WHITE),
    "EIUIR100": ("Industrial Supplies", AMBER),
    "EIUIR300": ("Capital Goods", BLUE),
    "EIUIR400": ("Consumer Goods", GREEN),
}

# Use row index as x-axis (BLS period is annual-ish, no month granularity)
fig, ax = plt.subplots(figsize=(13, 6))
fig.patch.set_facecolor(DARK_BG)
ax.set_facecolor(NAVY)

for sid, (label, color) in bls_series.items():
    sub = bls[bls["series_id"] == sid].reset_index(drop=True)
    ax.plot(sub.index, sub["value"], linewidth=2, color=color, label=f"{sid} - {label}")
    # Mark spikes
    spikes = sub[sub["spike"] == True]
    ax.scatter(spikes.index, spikes["value"], color=color, marker="^", s=60, zorder=5, alpha=0.7)

ax.set_title("BLS Import Price Index by Category (2020-2025)\nTriangles indicate MoM spikes > 0.5%  |  Source: Bureau of Labor Statistics", color=WHITE)
ax.set_xlabel("Observation Index", color=WHITE)
ax.set_ylabel("Price Index (Base: 2000=100)", color=WHITE)
ax.legend(facecolor=NAVY, edgecolor="#30363d", labelcolor=WHITE, fontsize=10)
ax.grid(alpha=0.3)
ax.spines["top"].set_visible(False)
ax.spines["right"].set_visible(False)

fig.tight_layout()
path5 = "charts/chart_05_bls_price_index.png"
fig.savefig(path5, dpi=150, bbox_inches="tight", facecolor=DARK_BG)
plt.close()
print(f"Saved: {path5} ({os.path.getsize(path5):,} bytes)")
print()

# ----------------------------------------------------------------
# CHART 6: Risk Quadrant (Import Value vs Tariff Exposure)
# ----------------------------------------------------------------
print("--- Chart 6: Risk Quadrant ---")

hs10 = pd.read_csv("data/processed/hs10_with_risk.csv")

# Aggregate by country for scatter
cs2 = pd.read_csv("data/processed/country_summary.csv")

tier_colors_map = {"Critical": RED, "High": AMBER, "Medium": BLUE, "Low": GREEN}

fig, ax = plt.subplots(figsize=(10, 7))
fig.patch.set_facecolor(DARK_BG)
ax.set_facecolor(NAVY)

for _, row in cs2.iterrows():
    country = row["country_clean"]
    tier = row["risk_tier"]
    color = tier_colors_map.get(tier, GRAY)
    imp = row["import_value_B"]
    exp = row["tariff_exposure_B"]
    risk = row["risk_score"]

    ax.scatter(imp, exp, s=risk * 120, color=color, alpha=0.8, edgecolors="white", linewidths=1.5, zorder=5)
    ax.annotate(
        f"{country}\n${imp:.0f}B imports\n${exp:.1f}B exposure\nRisk: {risk}",
        xy=(imp, exp),
        xytext=(imp + 8, exp + 2),
        color=WHITE,
        fontsize=9.5,
        fontweight="bold",
        arrowprops=dict(arrowstyle="->", color=GRAY, lw=1),
    )

# Quadrant lines (medians)
med_imp = cs2["import_value_B"].median()
med_exp = cs2["tariff_exposure_B"].median()
ax.axvline(med_imp, color=GRAY, linewidth=1, linestyle="--", alpha=0.5)
ax.axhline(med_exp, color=GRAY, linewidth=1, linestyle="--", alpha=0.5)

# Quadrant labels
ax.text(med_imp * 0.1, med_exp * 1.4, "Low Volume\nHigh Risk", color=GRAY, fontsize=9, alpha=0.7)
ax.text(med_imp * 1.3, med_exp * 1.4, "High Volume\nHigh Risk", color=RED, fontsize=9, alpha=0.8, fontweight="bold")
ax.text(med_imp * 0.1, med_exp * 0.1, "Low Volume\nLow Risk", color=GREEN, fontsize=9, alpha=0.7)
ax.text(med_imp * 1.3, med_exp * 0.1, "High Volume\nLow Risk", color=GRAY, fontsize=9, alpha=0.7)

# Legend
patches = [
    mpatches.Patch(color=RED, label="Critical"),
    mpatches.Patch(color=AMBER, label="High"),
    mpatches.Patch(color=BLUE, label="Medium"),
    mpatches.Patch(color=GREEN, label="Low"),
]
ax.legend(handles=patches, title="Risk Tier", facecolor=NAVY, edgecolor="#30363d",
          labelcolor=WHITE, title_fontsize=9, fontsize=9, loc="lower right")

ax.set_title("Risk Quadrant: Import Value vs Tariff Exposure by Country\nBubble size = risk score  |  Source: U.S. Census Bureau 2023", color=WHITE)
ax.set_xlabel("Total Import Value ($B)", color=WHITE)
ax.set_ylabel("Total Tariff Exposure ($B)", color=WHITE)
ax.grid(alpha=0.3)
ax.spines["top"].set_visible(False)
ax.spines["right"].set_visible(False)

fig.tight_layout()
path6 = "charts/chart_06_risk_quadrant.png"
fig.savefig(path6, dpi=150, bbox_inches="tight", facecolor=DARK_BG)
plt.close()
print(f"Saved: {path6} ({os.path.getsize(path6):,} bytes)")
print()

# ----------------------------------------------------------------
# SUMMARY
# ----------------------------------------------------------------
print("=" * 60)
print("PHASE 4 COMPLETE - ALL 6 CHARTS SAVED")
print("=" * 60)
charts_saved = [path1, path2, path3, path4, path5, path6]
for p in charts_saved:
    sz = os.path.getsize(p)
    print(f"  {p}: {sz:,} bytes")
print()
print("=== DONE ===")
