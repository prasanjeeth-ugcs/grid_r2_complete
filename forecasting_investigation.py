"""
=============================================================================
 ASTRAM — Pre-Modeling Investigation: Forecasting Feasibility Analysis
=============================================================================
 Analyses A–F + Timeline Reconstruction Check
=============================================================================
"""

import pandas as pd
import numpy as np
import warnings, sys, io

# Force UTF-8 output on Windows
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

warnings.filterwarnings("ignore")

DATA_PATH = r"d:\round2 - anti\Astram event data_anonymized - Astram event data_anonymizedb40ac87 (1).csv"

# ─── LOAD & CLEAN ───
df = pd.read_csv(DATA_PATH, low_memory=False)
df.replace("NULL", np.nan, inplace=True)
df.replace("null", np.nan, inplace=True)

dt_cols = ["start_datetime","end_datetime","created_date","modified_datetime","closed_datetime","resolved_datetime"]
for c in dt_cols:
    if c in df.columns:
        df[c] = pd.to_datetime(df[c], errors="coerce", utc=True)

df["requires_road_closure"] = df["requires_road_closure"].map(
    {True:True, False:False, "TRUE":True, "FALSE":False, "true":True, "false":False}
)

for c in ["endlatitude","endlongitude","latitude","longitude"]:
    df[c] = pd.to_numeric(df[c], errors="coerce")
for c in ["endlatitude","endlongitude"]:
    df.loc[df[c]==0, c] = np.nan

cat_cols = ["event_type","event_cause","status","priority","corridor","veh_type","police_station","zone","junction"]
for c in cat_cols:
    if c in df.columns:
        df[c] = df[c].astype(str).str.strip().replace("nan", np.nan)

df["hour_of_day"] = df["start_datetime"].dt.hour
df["day_of_week"] = df["start_datetime"].dt.day_name()
df["date"] = df["start_datetime"].dt.date
df["month"] = df["start_datetime"].dt.month
df["is_corridor"] = df["corridor"].apply(lambda x: False if pd.isna(x) or x=="Non-corridor" else True)

SEP = "=" * 80
SUB = "-" * 80

# ═════════════════════════════════════════════════════════════════════════════
# A. CORRIDOR × TIME MATRIX
# ═════════════════════════════════════════════════════════════════════════════
print(f"\n{SEP}")
print("  A. CORRIDOR x HOUR-OF-DAY MATRIX")
print(f"{SEP}\n")

ct_corridor_hour = pd.crosstab(df["corridor"], df["hour_of_day"])
# Show top 15 corridors
top_corridors = df["corridor"].value_counts().head(15).index.tolist()
ct_top = ct_corridor_hour.loc[ct_corridor_hour.index.isin(top_corridors)]
ct_top = ct_top.reindex(top_corridors)

print("Top 15 Corridors x Hour (UTC):\n")
print(ct_top.to_string())

# Peak hours per corridor
print(f"\n{SUB}")
print("Peak Hours per Corridor (UTC -> IST):")
print(f"{SUB}")
for corr in top_corridors:
    row = ct_corridor_hour.loc[corr]
    peak_h = int(row.idxmax())
    peak_count = int(row.max())
    ist_h = (peak_h + 5) % 24  # Approximate IST
    ist_str = f"{ist_h:02d}:{30 if peak_h != ist_h - 5 else 0:02d}"
    print(f"  {corr:25s} -> Peak UTC {peak_h:02d}:00 (IST ~{(peak_h+5)%24:02d}:30) = {peak_count} events")

# ═════════════════════════════════════════════════════════════════════════════
# B. EVENT CAUSE × TIME MATRIX
# ═════════════════════════════════════════════════════════════════════════════
print(f"\n\n{SEP}")
print("  B. EVENT CAUSE x HOUR-OF-DAY MATRIX")
print(f"{SEP}\n")

ct_cause_hour = pd.crosstab(df["event_cause"], df["hour_of_day"])
print(ct_cause_hour.to_string())

print(f"\n{SUB}")
print("Peak Hours per Event Cause (UTC -> IST):")
print(f"{SUB}")
for cause in ct_cause_hour.index:
    row = ct_cause_hour.loc[cause]
    peak_h = int(row.idxmax())
    peak_count = int(row.max())
    total = int(row.sum())
    # Find top 3 hours
    top3 = row.nlargest(3)
    top3_str = ", ".join([f"UTC {int(h):02d}(IST ~{(int(h)+5)%24:02d}:30)={int(v)}" for h,v in top3.items()])
    print(f"  {cause:25s} -> Peak: {top3_str}  | Total: {total}")

# Night vs Day analysis for vehicle_breakdown
print(f"\n{SUB}")
print("Vehicle Breakdown: Night (UTC 18-05 / IST 23:30-10:30) vs Day:")
print(f"{SUB}")
bd = df[df["event_cause"] == "vehicle_breakdown"]
bd_night = bd[bd["hour_of_day"].isin(list(range(18,24)) + list(range(0,6)))]
bd_day = bd[~bd["hour_of_day"].isin(list(range(18,24)) + list(range(0,6)))]
print(f"  Night events: {len(bd_night)} ({len(bd_night)/len(bd)*100:.1f}%)")
print(f"  Day events:   {len(bd_day)} ({len(bd_day)/len(bd)*100:.1f}%)")

# Water logging by month
print(f"\n{SUB}")
print("Water Logging by Month:")
print(f"{SUB}")
wl = df[df["event_cause"] == "water_logging"]
wl_monthly = wl["month"].value_counts().sort_index()
month_names = {1:"Jan",2:"Feb",3:"Mar",4:"Apr",5:"May",6:"Jun",7:"Jul",8:"Aug",9:"Sep",10:"Oct",11:"Nov",12:"Dec"}
for m, count in wl_monthly.items():
    print(f"  {month_names.get(int(m),'?'):5s}: {count:4d} events {'*' * (count // 10)}")

# ═════════════════════════════════════════════════════════════════════════════
# C. CLOSURE PROBABILITY BY CORRIDOR
# ═════════════════════════════════════════════════════════════════════════════
print(f"\n\n{SEP}")
print("  C. CLOSURE PROBABILITY BY CORRIDOR")
print(f"{SEP}\n")

closure_corr = df.groupby("corridor")["requires_road_closure"].agg(["mean","sum","count"]).reset_index()
closure_corr.columns = ["Corridor", "Closure Rate", "Closures", "Total"]
closure_corr["Closure Rate"] = (closure_corr["Closure Rate"] * 100).round(1)
closure_corr = closure_corr.sort_values("Closure Rate", ascending=False)

print(f"{'Corridor':30s} {'Rate':>8s} {'Closures':>10s} {'Total':>8s}")
print(SUB)
for _, r in closure_corr.iterrows():
    bar = '#' * int(r['Closure Rate'] / 2)
    print(f"  {r['Corridor']:28s} {r['Closure Rate']:>6.1f}% {int(r['Closures']):>8d} {int(r['Total']):>8d}  {bar}")

# ═════════════════════════════════════════════════════════════════════════════
# D. CLOSURE PROBABILITY BY VEHICLE TYPE
# ═════════════════════════════════════════════════════════════════════════════
print(f"\n\n{SEP}")
print("  D. CLOSURE PROBABILITY BY VEHICLE TYPE")
print(f"{SEP}\n")

closure_veh = df.dropna(subset=["veh_type"]).groupby("veh_type")["requires_road_closure"].agg(["mean","sum","count"]).reset_index()
closure_veh.columns = ["Vehicle Type", "Closure Rate", "Closures", "Total"]
closure_veh["Closure Rate"] = (closure_veh["Closure Rate"] * 100).round(1)
closure_veh = closure_veh.sort_values("Closure Rate", ascending=False)

print(f"{'Vehicle Type':25s} {'Rate':>8s} {'Closures':>10s} {'Total':>8s}")
print(SUB)
for _, r in closure_veh.iterrows():
    bar = '#' * int(r['Closure Rate'] / 2)
    print(f"  {r['Vehicle Type']:23s} {r['Closure Rate']:>6.1f}% {int(r['Closures']):>8d} {int(r['Total']):>8d}  {bar}")

# ═════════════════════════════════════════════════════════════════════════════
# E. PRIORITY × CORRIDOR
# ═════════════════════════════════════════════════════════════════════════════
print(f"\n\n{SEP}")
print("  E. PRIORITY x CORRIDOR CROSS-TAB")
print(f"{SEP}\n")

ct_corr_prio = pd.crosstab(df["corridor"], df["priority"])
ct_corr_prio["Total"] = ct_corr_prio.sum(axis=1)
ct_corr_prio["High%"] = (ct_corr_prio.get("High", 0) / ct_corr_prio["Total"] * 100).round(1)
ct_corr_prio = ct_corr_prio.sort_values("Total", ascending=False).head(22)

print(f"{'Corridor':30s} {'High':>6s} {'Low':>6s} {'Total':>7s} {'High%':>7s}")
print(SUB)
for corr, row in ct_corr_prio.iterrows():
    high_val = int(row.get("High", 0))
    low_val = int(row.get("Low", 0))
    total_val = int(row["Total"])
    high_pct = float(row["High%"])
    indicator = "***" if high_pct > 80 else "**" if high_pct > 60 else "*" if high_pct > 40 else ""
    print(f"  {corr:28s} {high_val:>6d} {low_val:>6d} {total_val:>7d} {high_pct:>6.1f}% {indicator}")

# ═════════════════════════════════════════════════════════════════════════════
# F. EVENT CAUSE × VEHICLE TYPE
# ═════════════════════════════════════════════════════════════════════════════
print(f"\n\n{SEP}")
print("  F. EVENT CAUSE x VEHICLE TYPE CROSS-TAB")
print(f"{SEP}\n")

ct_cause_veh = pd.crosstab(df["event_cause"], df["veh_type"])
print(ct_cause_veh.to_string())

# Show which event causes have vehicle data
print(f"\n{SUB}")
print("Vehicle Data Coverage by Event Cause:")
print(f"{SUB}")
for cause in df["event_cause"].value_counts().index:
    total = len(df[df["event_cause"]==cause])
    with_veh = df[(df["event_cause"]==cause) & (df["veh_type"].notna())].shape[0]
    pct = with_veh / total * 100
    bar = '#' * int(pct / 5)
    print(f"  {cause:25s} {with_veh:>5d}/{total:>5d} ({pct:>5.1f}%) {bar}")


# ═════════════════════════════════════════════════════════════════════════════
# G. THE BIG QUESTION: CAN WE RECONSTRUCT A TIMELINE?
# ═════════════════════════════════════════════════════════════════════════════
print(f"\n\n{'#' * 80}")
print("  G. TIMELINE RECONSTRUCTION FEASIBILITY")
print(f"{'#' * 80}\n")

# Filter to events with valid start_datetime and corridor
timeline_df = df.dropna(subset=["start_datetime"]).copy()
timeline_df = timeline_df[timeline_df["corridor"].notna()]
timeline_df = timeline_df.sort_values(["corridor", "start_datetime"])

print("--- Overview ---")
print(f"  Events with valid timestamp: {len(timeline_df)}")
print(f"  Corridors: {timeline_df['corridor'].nunique()}")
print(f"  Date range: {timeline_df['start_datetime'].min()} to {timeline_df['start_datetime'].max()}")

# Per-corridor timeline density
print(f"\n{SUB}")
print("  CORRIDOR TIMELINE DENSITY")
print(f"{SUB}\n")

print(f"{'Corridor':30s} {'Events':>7s} {'Days':>6s} {'Evt/Day':>8s} {'Med Gap':>10s} {'Min Gap':>10s} {'Max Gap':>10s} {'Forecastable?':>14s}")
print(SUB)

corridor_timeline_stats = []
for corr in timeline_df["corridor"].value_counts().head(22).index:
    sub = timeline_df[timeline_df["corridor"] == corr].sort_values("start_datetime")
    if len(sub) < 5:
        continue
    
    # Time gaps between consecutive events
    gaps = sub["start_datetime"].diff().dropna()
    gaps_hours = gaps.dt.total_seconds() / 3600
    
    # Date span
    date_span = (sub["start_datetime"].max() - sub["start_datetime"].min()).days + 1
    events_per_day = len(sub) / max(date_span, 1)
    
    med_gap = gaps_hours.median()
    min_gap = gaps_hours.min()
    max_gap = gaps_hours.max()
    mean_gap = gaps_hours.mean()
    
    # Forecastability assessment
    # If median gap < 24h and events/day >= 1, strong forecastability
    if events_per_day >= 2 and med_gap < 24:
        forecastable = "STRONG"
    elif events_per_day >= 1 and med_gap < 48:
        forecastable = "MODERATE"
    elif events_per_day >= 0.5:
        forecastable = "WEAK"
    else:
        forecastable = "INSUFFICIENT"
    
    corridor_timeline_stats.append({
        "corridor": corr,
        "events": len(sub),
        "days": date_span,
        "events_per_day": events_per_day,
        "med_gap": med_gap,
        "min_gap": min_gap,
        "max_gap": max_gap,
        "mean_gap": mean_gap,
        "forecastable": forecastable,
    })
    
    print(f"  {corr:28s} {len(sub):>7d} {date_span:>6d} {events_per_day:>7.1f} {med_gap:>8.1f}h {min_gap:>8.1f}h {max_gap:>8.1f}h  {forecastable}")

# Daily event counts per corridor (for time-series)
print(f"\n\n{SUB}")
print("  DAILY EVENT COUNTS — TOP 5 CORRIDORS (Sample: Last 30 days)")
print(f"{SUB}\n")

top5_corr = [s["corridor"] for s in sorted(corridor_timeline_stats, key=lambda x: x["events"], reverse=True)[:5] if s["corridor"] != "Non-corridor"][:5]

for corr in top5_corr:
    sub = timeline_df[timeline_df["corridor"] == corr].copy()
    sub["date"] = sub["start_datetime"].dt.date
    daily = sub.groupby("date").size()
    
    # Show last 30 days
    last30 = daily.tail(30)
    print(f"\n  {corr} (last 30 days of data):")
    print(f"  {'Date':12s} {'Count':>6s}  Sparkline")
    print(f"  {'-'*40}")
    for dt, count in last30.items():
        bar = '|' * count
        print(f"  {str(dt):12s} {count:>6d}  {bar}")
    
    print(f"  Summary: mean={daily.mean():.1f}/day, std={daily.std():.1f}, min={daily.min()}, max={daily.max()}")

# ─── Inter-event time analysis ───
print(f"\n\n{SUB}")
print("  INTER-EVENT TIME DISTRIBUTION (All corridors combined)")
print(f"{SUB}\n")

all_gaps = []
for corr in timeline_df["corridor"].unique():
    sub = timeline_df[timeline_df["corridor"] == corr].sort_values("start_datetime")
    gaps = sub["start_datetime"].diff().dropna().dt.total_seconds() / 3600
    all_gaps.extend(gaps.values)

all_gaps = pd.Series(all_gaps)
print(f"  Total inter-event gaps analyzed: {len(all_gaps):,}")
print(f"  Mean gap:   {all_gaps.mean():.2f} hours")
print(f"  Median gap: {all_gaps.median():.2f} hours")
print(f"  Std:        {all_gaps.std():.2f} hours")
print(f"  P25:        {all_gaps.quantile(0.25):.2f} hours")
print(f"  P75:        {all_gaps.quantile(0.75):.2f} hours")
print(f"  P95:        {all_gaps.quantile(0.95):.2f} hours")

# Gap distribution buckets
bins = [0, 0.5, 1, 2, 4, 8, 12, 24, 48, 96, float('inf')]
labels = ["<30min", "30m-1h", "1-2h", "2-4h", "4-8h", "8-12h", "12-24h", "1-2d", "2-4d", ">4d"]
gap_buckets = pd.cut(all_gaps, bins=bins, labels=labels)
gap_dist = gap_buckets.value_counts().reindex(labels)

print(f"\n  Inter-Event Gap Distribution:")
print(f"  {'Bucket':12s} {'Count':>8s} {'%':>8s}  Bar")
print(f"  {'-'*50}")
for label, count in gap_dist.items():
    pct = count / len(all_gaps) * 100
    bar = '#' * int(pct / 2)
    print(f"  {label:12s} {count:>8d} {pct:>7.1f}%  {bar}")

# ─── Autocorrelation check ───
print(f"\n\n{SUB}")
print("  AUTOCORRELATION CHECK (Can past events predict future events?)")
print(f"{SUB}\n")

for corr in top5_corr[:5]:
    sub = timeline_df[timeline_df["corridor"] == corr].copy()
    sub["date"] = sub["start_datetime"].dt.date
    daily = sub.groupby("date").size()
    
    # Reindex to fill missing days with 0
    full_range = pd.date_range(daily.index.min(), daily.index.max())
    daily = daily.reindex(full_range, fill_value=0)
    
    if len(daily) < 14:
        continue
    
    # Manual autocorrelation for lags 1-7
    print(f"  {corr}:")
    lags_str = []
    for lag in [1, 2, 3, 7]:
        if len(daily) > lag:
            ac = daily.autocorr(lag=lag)
            strength = "STRONG" if abs(ac) > 0.5 else "moderate" if abs(ac) > 0.3 else "weak"
            lags_str.append(f"Lag-{lag}: {ac:+.3f} ({strength})")
    print(f"    {' | '.join(lags_str)}")

# ─── SIMULTANEOUS EVENTS (Overlapping events on same corridor) ───
print(f"\n\n{SUB}")
print("  SIMULTANEOUS EVENTS CHECK (Multiple active events on same corridor)")
print(f"{SUB}\n")

for corr in top5_corr[:5]:
    sub = timeline_df[timeline_df["corridor"] == corr].copy()
    sub["date"] = sub["start_datetime"].dt.date
    
    # Count events on same day
    daily = sub.groupby("date").size()
    multi_days = (daily > 1).sum()
    max_same_day = daily.max()
    
    print(f"  {corr:28s}: {multi_days} days with >1 event (max {max_same_day} in a single day)")

# ═════════════════════════════════════════════════════════════════════════════
# FINAL VERDICT
# ═════════════════════════════════════════════════════════════════════════════
print(f"\n\n{'#' * 80}")
print("  FORECASTING FEASIBILITY VERDICT")
print(f"{'#' * 80}\n")

strong = sum(1 for s in corridor_timeline_stats if s["forecastable"] == "STRONG")
moderate = sum(1 for s in corridor_timeline_stats if s["forecastable"] == "MODERATE")
weak = sum(1 for s in corridor_timeline_stats if s["forecastable"] == "WEAK")
insuf = sum(1 for s in corridor_timeline_stats if s["forecastable"] == "INSUFFICIENT")

print(f"  Corridor Forecastability Assessment:")
print(f"    STRONG (>=2 evt/day, gap<24h):     {strong} corridors")
print(f"    MODERATE (>=1 evt/day, gap<48h):    {moderate} corridors")
print(f"    WEAK (>=0.5 evt/day):               {weak} corridors")
print(f"    INSUFFICIENT (<0.5 evt/day):        {insuf} corridors")
print(f"    Total assessed:                     {len(corridor_timeline_stats)} corridors")

print(f"\n  Timeline Reconstruction:")
can_forecast = strong + moderate
total_assessed = len(corridor_timeline_stats)
if can_forecast >= 5:
    print(f"    VERDICT: YES - Timeline CAN be reconstructed for {can_forecast}/{total_assessed} corridors")
    print(f"    APPROACH: Time-series forecasting is VIABLE")
    print(f"    -> Daily event count prediction per corridor")
    print(f"    -> Hourly event probability by corridor x cause")
    print(f"    -> Sequence modeling: Incident T -> Incident T+1 gap prediction")
elif can_forecast >= 2:
    print(f"    VERDICT: PARTIAL - Timeline possible for {can_forecast}/{total_assessed} corridors")
    print(f"    APPROACH: Hybrid model recommended")
    print(f"    -> Forecasting for top corridors")
    print(f"    -> Risk classification for remaining corridors")
else:
    print(f"    VERDICT: NO - Data too sparse for reliable timeline forecasting")
    print(f"    APPROACH: Stick with risk prediction (classification)")

print(f"\n  Recommended Strategy:")
print(f"    1. Forecasting layer: Predict daily event counts per corridor (top {strong + moderate})")
print(f"    2. Risk classification: 4-level risk for individual events")
print(f"    3. Combined: Forecast -> triggers proactive resource deployment")
print(f"       Event occurs -> Risk prediction -> Resource recommendation")
print()
