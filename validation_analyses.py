"""
=============================================================================
 VALIDATION ANALYSES — Pre-Modeling Integrity Checks
=============================================================================
 Analysis 1: Leakage Audit (requires_road_closure timing)
 Analysis 2: Text Field Quality (description samples + stats)
 Analysis 3: Spatial Hotspots (HDBSCAN clustering)
=============================================================================
"""

import pandas as pd
import numpy as np
import sys, io, warnings
warnings.filterwarnings("ignore")
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

# ─────────────────────────────────────────────────────────────────────────────
# DATA LOADING (same pipeline as EDA)
# ─────────────────────────────────────────────────────────────────────────────

DATA_PATH = r"d:\round2 - anti\Astram event data_anonymized - Astram event data_anonymizedb40ac87 (1).csv"

df = pd.read_csv(DATA_PATH, low_memory=False)
df.replace("NULL", np.nan, inplace=True)
df.replace("null", np.nan, inplace=True)

datetime_cols = [
    "start_datetime", "end_datetime", "created_date",
    "modified_datetime", "closed_datetime", "resolved_datetime"
]
for col in datetime_cols:
    if col in df.columns:
        df[col] = pd.to_datetime(df[col], errors="coerce", utc=True)

df["requires_road_closure"] = df["requires_road_closure"].map(
    {True: True, False: False, "TRUE": True, "FALSE": False, "true": True, "false": False}
)

cat_cols = ["event_type", "event_cause", "status", "priority", "corridor",
            "veh_type", "police_station", "zone", "junction"]
for col in cat_cols:
    if col in df.columns:
        df[col] = df[col].astype(str).str.strip()
        df[col] = df[col].replace("nan", np.nan)

for col in ["latitude", "longitude"]:
    df[col] = pd.to_numeric(df[col], errors="coerce")

print("=" * 80)
print(" VALIDATION ANALYSES — Pre-Modeling Integrity Checks")
print("=" * 80)
print(f"  Loaded: {df.shape[0]} rows × {df.shape[1]} columns\n")


# =============================================================================
# ANALYSIS 1: LEAKAGE AUDIT
# =============================================================================

print("=" * 80)
print(" ANALYSIS 1: LEAKAGE AUDIT — requires_road_closure Timing")
print("=" * 80)

# ── 1A: Feature availability table ──
print("""
┌─────────────────────────┬──────────────────────┬──────────────────────┐
│ Column                  │ Available at Start?  │ Available After?     │
├─────────────────────────┼──────────────────────┼──────────────────────┤
│ event_cause             │ ✅ YES               │                      │
│ event_type              │ ✅ YES               │                      │
│ corridor                │ ✅ YES               │                      │
│ latitude / longitude    │ ✅ YES               │                      │
│ police_station          │ ✅ YES               │                      │
│ address                 │ ✅ YES               │                      │
│ priority                │ ✅ YES               │                      │
│ start_datetime          │ ✅ YES               │                      │
│ created_date            │ ✅ YES               │                      │
│ authenticated           │ ✅ YES               │                      │
├─────────────────────────┼──────────────────────┼──────────────────────┤
│ requires_road_closure   │ ❓ UNDER AUDIT       │ ❓ UNDER AUDIT       │
├─────────────────────────┼──────────────────────┼──────────────────────┤
│ closed_datetime         │ ❌ NO                │ ✅ After closure     │
│ status                  │ ❌ NO (changes)      │ ✅ Final state       │
│ resolved_datetime       │ ❌ NO                │ ✅ After resolution  │
│ closed_by_id            │ ❌ NO                │ ✅ After closure     │
│ modified_datetime       │ ❌ NO (changes)      │ ✅ Final value       │
│ description             │ ❓ MIXED             │ ❓ May be updated    │
└─────────────────────────┴──────────────────────┴──────────────────────┘
""")

# ── 1B: When is requires_road_closure set? ──
# Key diagnostic: check if road closure correlates with fields only known AFTER the event
print("  ── Diagnostic 1B: requires_road_closure timing signals ──\n")

closure_true = df[df["requires_road_closure"] == True]
closure_false = df[df["requires_road_closure"] == False]

print(f"  Road closure = TRUE:  {len(closure_true):,} events ({len(closure_true)/len(df)*100:.1f}%)")
print(f"  Road closure = FALSE: {len(closure_false):,} events ({len(closure_false)/len(df)*100:.1f}%)")

# Check: do ALL events have requires_road_closure populated (even active ones)?
active_events = df[df["status"] == "active"]
active_with_closure = active_events["requires_road_closure"].notna().sum()
active_closure_true = (active_events["requires_road_closure"] == True).sum()
print(f"\n  Active (unclosed) events: {len(active_events)}")
print(f"    └─ have requires_road_closure filled: {active_with_closure}/{len(active_events)}")
print(f"    └─ requires_road_closure = TRUE:      {active_closure_true}/{len(active_events)}")

# Check: is road_closure set at creation time?
# If report_delay is ~0 AND road_closure is filled, it was set at creation
df["report_delay_sec"] = (df["created_date"] - df["start_datetime"]).dt.total_seconds()
# For closure events, compare: was road_closure set BEFORE closed_datetime?
# Proxy: if modified_datetime == created_date for closure=True events, it was set at creation
closure_events = df[df["requires_road_closure"] == True].copy()

# Check if closure_true events have closed_datetime populated
closure_has_closed_dt = closure_events["closed_datetime"].notna().sum()
closure_has_resolved_dt = closure_events["resolved_datetime"].notna().sum()
print(f"\n  Among requires_road_closure=TRUE ({len(closure_events)} events):")
print(f"    └─ has closed_datetime:   {closure_has_closed_dt}/{len(closure_events)} ({closure_has_closed_dt/len(closure_events)*100:.1f}%)")
print(f"    └─ has resolved_datetime: {closure_has_resolved_dt}/{len(closure_events)} ({closure_has_resolved_dt/len(closure_events)*100:.1f}%)")
print(f"    └─ status=active:         {(closure_events['status']=='active').sum()}")
print(f"    └─ status=closed:         {(closure_events['status']=='closed').sum()}")
print(f"    └─ status=resolved:       {(closure_events['status']=='resolved').sum()}")

# ── 1C: CRITICAL TEST ──
# If requires_road_closure is known at incident creation, then active events should also have it.
# If it's only set post-assessment, active events would have it = False disproportionately.
print(f"\n  ── CRITICAL TEST: Road closure rate by event status ──")
status_closure = df.groupby("status")["requires_road_closure"].agg(["sum", "count", "mean"]).reset_index()
status_closure.columns = ["Status", "Closure_True", "Total", "Rate"]
for _, row in status_closure.iterrows():
    print(f"    {row['Status']:12s}: {int(row['Closure_True']):4d}/{int(row['Total']):5d} = {row['Rate']*100:.1f}%")

# ── 1D: Check if planned events always have road_closure known ──
print(f"\n  ── Planned vs Unplanned road closure rates ──")
type_closure = df.groupby("event_type")["requires_road_closure"].agg(["sum", "count", "mean"]).reset_index()
type_closure.columns = ["Type", "Closure_True", "Total", "Rate"]
for _, row in type_closure.iterrows():
    print(f"    {row['Type']:12s}: {int(row['Closure_True']):4d}/{int(row['Total']):5d} = {row['Rate']*100:.1f}%")

# ── 1E: Cause × Closure breakdown for active events ──
print(f"\n  ── Road closure rate by cause — ACTIVE events only ──")
active_closure = active_events.groupby("event_cause")["requires_road_closure"].agg(["sum", "count", "mean"]).reset_index()
active_closure.columns = ["Cause", "Closure_True", "Total", "Rate"]
active_closure = active_closure.sort_values("Rate", ascending=False)
for _, row in active_closure.iterrows():
    if row['Total'] >= 3:
        print(f"    {row['Cause']:25s}: {int(row['Closure_True']):3d}/{int(row['Total']):4d} = {row['Rate']*100:.1f}%")

# ── 1F: VERDICT ──
# If active events have similar closure rates to closed events by cause, then road_closure 
# is set at creation time (safe to use as input). If active events are all False, it's post-hoc.
active_rate = active_events["requires_road_closure"].mean() * 100
closed_rate = df[df["status"] == "closed"]["requires_road_closure"].mean() * 100
print(f"\n  ┌──────────────────────────────────────────────────────────────┐")
print(f"  │ VERDICT:                                                     │")
print(f"  │   Active events closure rate:  {active_rate:5.1f}%                       │")
print(f"  │   Closed events closure rate:  {closed_rate:5.1f}%                       │")
if abs(active_rate - closed_rate) < 3.0:
    print(f"  │   → SIMILAR rates → road_closure is set AT CREATION         │")
    print(f"  │   → SAFE to use as INPUT feature                            │")
    verdict_1 = "SAFE"
elif active_rate < closed_rate * 0.5:
    print(f"  │   → Active rate << Closed rate → LIKELY set POST-HOC        │")
    print(f"  │   → LEAKAGE RISK — should be PREDICTION TARGET not input    │")
    verdict_1 = "LEAKAGE"
else:
    print(f"  │   → Rates differ but not dramatically                       │")
    print(f"  │   → CAUTION — further investigation needed                  │")
    verdict_1 = "CAUTION"
print(f"  └──────────────────────────────────────────────────────────────┘\n")


# =============================================================================
# ANALYSIS 2: TEXT FIELD QUALITY — description
# =============================================================================

print("\n" + "=" * 80)
print(" ANALYSIS 2: TEXT FIELD QUALITY — description column")
print("=" * 80)

desc = df["description"].dropna()
total_with_desc = len(desc)
total_events = len(df)
print(f"\n  Populated: {total_with_desc:,}/{total_events:,} ({total_with_desc/total_events*100:.1f}%)")

# ── 2A: Basic statistics ──
desc_lengths = desc.str.len()
desc_words = desc.str.split().str.len()
print(f"\n  ── Character length stats ──")
print(f"    Mean:   {desc_lengths.mean():.0f} chars")
print(f"    Median: {desc_lengths.median():.0f} chars")
print(f"    Min:    {desc_lengths.min():.0f} chars")
print(f"    Max:    {desc_lengths.max():.0f} chars")
print(f"    P25:    {desc_lengths.quantile(0.25):.0f} chars")
print(f"    P75:    {desc_lengths.quantile(0.75):.0f} chars")

print(f"\n  ── Word count stats ──")
print(f"    Mean:   {desc_words.mean():.1f} words")
print(f"    Median: {desc_words.median():.0f} words")
print(f"    Min:    {desc_words.min():.0f} words")
print(f"    Max:    {desc_words.max():.0f} words")

# ── 2B: Language detection ──
# Simple heuristic: if >50% ASCII characters, likely English
def is_mostly_english(text):
    if pd.isna(text) or len(text) == 0:
        return False
    ascii_chars = sum(1 for c in text if ord(c) < 128)
    return ascii_chars / len(text) > 0.7

english_mask = desc.apply(is_mostly_english)
english_count = english_mask.sum()
non_english_count = len(desc) - english_count
print(f"\n  ── Language breakdown ──")
print(f"    Mostly English (>70% ASCII): {english_count:,} ({english_count/len(desc)*100:.1f}%)")
print(f"    Mostly non-English/Kannada:  {non_english_count:,} ({non_english_count/len(desc)*100:.1f}%)")

# ── 2C: 30 random samples ──
print(f"\n  ── 30 RANDOM DESCRIPTION SAMPLES ──")
print(f"  {'─'*72}")
np.random.seed(42)
samples = desc.sample(30, random_state=42)
for i, (idx, text) in enumerate(samples.items(), 1):
    cause = df.loc[idx, "event_cause"] if pd.notna(df.loc[idx, "event_cause"]) else "?"
    closure = "🔴CLOSURE" if df.loc[idx, "requires_road_closure"] == True else ""
    # Truncate very long texts
    display = text[:120] + "..." if len(text) > 120 else text
    # Replace newlines
    display = display.replace("\n", " ").replace("\r", "")
    print(f"  [{i:2d}] [{cause:20s}] {closure}")
    print(f"       {display}")
    print()

# ── 2D: Template detection ──
print(f"\n  ── Template / Repetition Analysis ──")
# Check for most common descriptions
desc_normalized = desc.str.lower().str.strip()
top_descs = desc_normalized.value_counts().head(15)
print(f"  Top 15 most repeated descriptions:")
for text, count in top_descs.items():
    display = text[:80] + "..." if len(str(text)) > 80 else text
    print(f"    {count:4d}x: {display}")

unique_ratio = desc_normalized.nunique() / len(desc_normalized)
print(f"\n  Unique descriptions: {desc_normalized.nunique():,}/{len(desc_normalized):,} ({unique_ratio*100:.1f}%)")

# ── 2E: Location clue detection ──
print(f"\n  ── Location Clues in Descriptions ──")
location_keywords = [
    "road", "junction", "signal", "flyover", "bridge", "circle", "cross",
    "bus stop", "metro", "station", "highway", "near", "opposite", "towards",
    "silk board", "kr pura", "yelahanka", "majestic", "airport", "ring road",
    "outer ring", "inner ring", "orr", "whitefield", "electronic city",
    "hosur", "mysore", "tumkur", "bellary", "bannerghatta"
]
desc_lower = desc.str.lower()
location_hits = sum(desc_lower.str.contains(kw, na=False).sum() for kw in location_keywords)
descs_with_location = sum(
    desc_lower.str.contains("|".join(location_keywords), na=False, regex=True)
)
print(f"  Descriptions containing location keywords: {descs_with_location:,}/{len(desc):,} ({descs_with_location/len(desc)*100:.1f}%)")

# ── 2F: Severity clue detection ──
print(f"\n  ── Severity Clues in Descriptions ──")
severity_keywords = [
    "block", "jam", "stuck", "heavy", "severe", "major", "accident",
    "fatal", "injur", "dead", "critical", "emergency", "urgent", "fire",
    "overturn", "collision", "pile", "damage", "broken", "leak",
    "flood", "submerge", "crane", "tow", "rescue"
]
descs_with_severity = sum(
    desc_lower.str.contains("|".join(severity_keywords), na=False, regex=True)
)
print(f"  Descriptions containing severity keywords: {descs_with_severity:,}/{len(desc):,} ({descs_with_severity/len(desc)*100:.1f}%)")

# ── 2G: Verdict ──
print(f"\n  ┌──────────────────────────────────────────────────────────────┐")
print(f"  │ VERDICT — Description Field Quality:                        │")
print(f"  │   Populated:    {total_with_desc/total_events*100:.1f}%                                     │")
print(f"  │   Unique ratio: {unique_ratio*100:.1f}%                                     │")
print(f"  │   English:      {english_count/len(desc)*100:.1f}%                                     │")
print(f"  │   Location:     {descs_with_location/len(desc)*100:.1f}%  contain location keywords        │")
print(f"  │   Severity:     {descs_with_severity/len(desc)*100:.1f}%  contain severity keywords        │")
if unique_ratio > 0.5 and descs_with_location / len(desc) > 0.3:
    print(f"  │                                                            │")
    print(f"  │   → STRONG NLP CANDIDATE                                   │")
    print(f"  │   → MiniLM embeddings recommended                          │")
    print(f"  │   → Mixed-language challenge — consider multilingual model  │")
elif unique_ratio > 0.3:
    print(f"  │                                                            │")
    print(f"  │   → MODERATE NLP CANDIDATE                                 │")
    print(f"  │   → Worth trying embeddings, but template dilution risk    │")
else:
    print(f"  │                                                            │")
    print(f"  │   → WEAK NLP CANDIDATE — too many templates                │")
    print(f"  │   → Keyword extraction may outperform embeddings           │")
print(f"  └──────────────────────────────────────────────────────────────┘\n")


# =============================================================================
# ANALYSIS 3: SPATIAL HOTSPOTS — HDBSCAN / DBSCAN Clustering
# =============================================================================

print("\n" + "=" * 80)
print(" ANALYSIS 3: SPATIAL HOTSPOTS — HDBSCAN Clustering")
print("=" * 80)

# Filter to valid Bengaluru coordinates
geo = df[["latitude", "longitude", "event_cause", "requires_road_closure", "corridor", "police_station"]].dropna(subset=["latitude", "longitude"]).copy()
geo = geo[(geo["latitude"].between(12.5, 13.5)) & (geo["longitude"].between(77.0, 78.0))]
print(f"\n  Events with valid coordinates: {len(geo):,}")

# Try HDBSCAN first, fallback to DBSCAN
try:
    from sklearn.cluster import HDBSCAN as HDBSCANCluster
    print("  Using: sklearn.cluster.HDBSCAN")
    
    coords = geo[["latitude", "longitude"]].values
    # Convert to approximate meters for eps: ~111km per degree
    coords_scaled = coords.copy()
    coords_scaled[:, 0] *= 111000  # lat to meters
    coords_scaled[:, 1] *= 111000 * np.cos(np.radians(12.97))  # lng to meters at Bengaluru latitude
    
    clusterer = HDBSCANCluster(
        min_cluster_size=50,
        min_samples=10,
        cluster_selection_epsilon=500,  # 500m radius
    )
    geo["cluster_id"] = clusterer.fit_predict(coords_scaled)
    method_used = "HDBSCAN"
    
except (ImportError, Exception) as e:
    print(f"  HDBSCAN not available ({e}), falling back to DBSCAN...")
    from sklearn.cluster import DBSCAN
    
    coords = geo[["latitude", "longitude"]].values
    coords_scaled = coords.copy()
    coords_scaled[:, 0] *= 111000
    coords_scaled[:, 1] *= 111000 * np.cos(np.radians(12.97))
    
    clusterer = DBSCAN(
        eps=800,       # 800 meters
        min_samples=30,
        n_jobs=-1
    )
    geo["cluster_id"] = clusterer.fit_predict(coords_scaled)
    method_used = "DBSCAN"

n_clusters = geo[geo["cluster_id"] >= 0]["cluster_id"].nunique()
noise_count = (geo["cluster_id"] == -1).sum()
clustered_count = (geo["cluster_id"] >= 0).sum()

print(f"\n  Method: {method_used}")
print(f"  Clusters found: {n_clusters}")
print(f"  Clustered events: {clustered_count:,} ({clustered_count/len(geo)*100:.1f}%)")
print(f"  Noise (unclustered): {noise_count:,} ({noise_count/len(geo)*100:.1f}%)")

# ── 3A: Cluster summary table ──
print(f"\n  ── TOP SPATIAL HOTSPOTS ──")
print(f"  {'─'*95}")
print(f"  {'Cluster':>8s} | {'Events':>7s} | {'Lat':>8s} | {'Lng':>8s} | {'Top Cause':20s} | {'Closure%':>8s} | {'Top Corridor':20s} | {'Top Station':20s}")
print(f"  {'─'*95}")

cluster_stats = []
for cid in sorted(geo[geo["cluster_id"] >= 0]["cluster_id"].unique()):
    cluster = geo[geo["cluster_id"] == cid]
    n = len(cluster)
    lat_center = cluster["latitude"].mean()
    lng_center = cluster["longitude"].mean()
    top_cause = cluster["event_cause"].mode().iloc[0] if len(cluster["event_cause"].mode()) > 0 else "?"
    closure_rate = cluster["requires_road_closure"].mean() * 100
    top_corridor = cluster["corridor"].mode().iloc[0] if len(cluster["corridor"].dropna().mode()) > 0 else "?"
    top_station = cluster["police_station"].mode().iloc[0] if len(cluster["police_station"].dropna().mode()) > 0 else "?"
    
    cluster_stats.append({
        "cluster_id": cid,
        "event_count": n,
        "lat_center": lat_center,
        "lng_center": lng_center,
        "top_cause": top_cause,
        "closure_rate": closure_rate,
        "top_corridor": top_corridor,
        "top_station": top_station,
    })

# Sort by event count descending
cluster_stats = sorted(cluster_stats, key=lambda x: -x["event_count"])

for cs in cluster_stats[:25]:  # Show top 25 clusters
    print(f"  {cs['cluster_id']:>8d} | {cs['event_count']:>7d} | {cs['lat_center']:8.4f} | {cs['lng_center']:8.4f} | {cs['top_cause']:20s} | {cs['closure_rate']:7.1f}% | {cs['top_corridor'][:20]:20s} | {cs['top_station'][:20]:20s}")

# ── 3B: Known Zone Identification ──
print(f"\n\n  ── ZONE IDENTIFICATION (can we find known zones without corridor labels?) ──\n")

known_zones = {
    "Airport Zone":      {"lat_range": (13.15, 13.30), "lng_range": (77.55, 77.75)},
    "Silk Board Zone":   {"lat_range": (12.91, 12.93), "lng_range": (77.59, 77.63)},
    "Yelahanka Zone":    {"lat_range": (13.08, 13.18), "lng_range": (77.53, 77.62)},
    "KR Puram Zone":     {"lat_range": (12.98, 13.03), "lng_range": (77.65, 77.73)},
    "Electronic City":   {"lat_range": (12.83, 12.87), "lng_range": (77.64, 77.70)},
    "Majestic/CBD":      {"lat_range": (12.96, 12.99), "lng_range": (77.56, 77.60)},
    "Whitefield Zone":   {"lat_range": (12.95, 13.00), "lng_range": (77.72, 77.78)},
}

for zone_name, bounds in known_zones.items():
    lat_lo, lat_hi = bounds["lat_range"]
    lng_lo, lng_hi = bounds["lng_range"]
    
    zone_events = geo[
        (geo["latitude"].between(lat_lo, lat_hi)) & 
        (geo["longitude"].between(lng_lo, lng_hi))
    ]
    
    if len(zone_events) == 0:
        print(f"  {zone_name:20s}: No events in bounding box")
        continue
    
    # Find which clusters intersect this zone
    zone_clusters = zone_events[zone_events["cluster_id"] >= 0]["cluster_id"].unique()
    n_events = len(zone_events)
    top_cause = zone_events["event_cause"].mode().iloc[0] if len(zone_events["event_cause"].mode()) > 0 else "?"
    closure_rate = zone_events["requires_road_closure"].mean() * 100
    top_station = zone_events["police_station"].mode().iloc[0] if len(zone_events["police_station"].dropna().mode()) > 0 else "?"
    
    cluster_str = ",".join(str(c) for c in sorted(zone_clusters)[:5]) if len(zone_clusters) > 0 else "no cluster"
    
    print(f"  {zone_name:20s}: {n_events:4d} events | clusters=[{cluster_str}] | top_cause={top_cause} | closure={closure_rate:.1f}% | station={top_station}")

# ── 3C: Do clusters emerge without corridor labels? ──
print(f"\n  ── CLUSTER QUALITY CHECK: Corridor homogeneity ──\n")
print(f"  If clusters are corridor-homogeneous, spatial clustering captures corridor structure.\n")

for cs in cluster_stats[:10]:
    cid = cs["cluster_id"]
    cluster = geo[geo["cluster_id"] == cid]
    corridor_dist = cluster["corridor"].value_counts()
    top_2 = corridor_dist.head(2)
    total = len(cluster)
    top1_pct = (top_2.iloc[0] / total * 100) if len(top_2) >= 1 else 0
    top1_name = top_2.index[0] if len(top_2) >= 1 else "?"
    top2_str = f"#{top_2.index[1]}={top_2.iloc[1]}" if len(top_2) >= 2 else ""
    print(f"    Cluster {cid:3d} ({total:4d} events): {top1_name[:25]:25s} = {top1_pct:.0f}% | {top2_str}")

# ── 3D: Verdict ──
print(f"\n  ┌──────────────────────────────────────────────────────────────┐")
print(f"  │ VERDICT — Spatial Hotspot Analysis:                         │")
print(f"  │   Clusters found: {n_clusters:3d}                                      │")
print(f"  │   Clustered:      {clustered_count/len(geo)*100:.1f}%                                    │")
if n_clusters >= 5:
    print(f"  │                                                            │")
    print(f"  │   → HOTSPOT INTELLIGENCE CONFIRMED                         │")
    print(f"  │   → Spatial clusters recover corridor/zone structure        │")
    print(f"  │   → geo_cluster feature recommended for modeling            │")
else:
    print(f"  │                                                            │")
    print(f"  │   → WEAK clustering — data may be too diffuse              │")
    print(f"  │   → Consider using lat/lng directly or geo-binning          │")
print(f"  └──────────────────────────────────────────────────────────────┘\n")


# =============================================================================
# COMBINED VERDICT
# =============================================================================
print("\n" + "=" * 80)
print(" COMBINED VALIDATION VERDICT")
print("=" * 80)
print(f"""
  ┌─────────────────────────────────────────────────────────────────────────┐
  │ Analysis 1 — Leakage Audit:                                           │
  │   requires_road_closure verdict: {verdict_1:8s}                              │
  │                                                                       │
  │ Analysis 2 — Text Quality:                                            │
  │   {total_with_desc/total_events*100:.1f}% populated, {unique_ratio*100:.1f}% unique, {english_count/len(desc)*100:.1f}% English                 │
  │   NLP embeddings: {'RECOMMENDED' if unique_ratio > 0.5 else 'MAYBE':12s}                                      │
  │                                                                       │
  │ Analysis 3 — Spatial Hotspots:                                        │
  │   {n_clusters} clusters from {method_used}                                          │
  │   Hotspot intelligence: {'YES ✅' if n_clusters >= 5 else 'WEAK ⚠️':8s}                                    │
  └─────────────────────────────────────────────────────────────────────────┘

  ── ARCHITECTURE IMPLICATIONS ──

  IF road_closure is SET AT CREATION → use as input feature
  IF road_closure is SET POST-HOC   → PREDICT it (binary classifier)
     Then chain: predict closure → use prediction in risk model

  Description embeddings → MiniLM-L6 or multilingual-MiniLM
  Spatial clusters → geo_cluster_id as categorical feature
""")

print("\nDone. All validation analyses complete.")
