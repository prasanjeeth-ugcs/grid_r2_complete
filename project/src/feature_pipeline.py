"""
=============================================================================
 FEATURE PIPELINE — Astram Traffic Impact System
=============================================================================
 Transforms raw CSV into model-ready parquet with:
   - Cleaned categorical/temporal/spatial features
   - Corridor tier assignments
   - DBSCAN geo_cluster_id
   - MiniLM description embeddings (PCA-reduced)
   - Composite impact score (training label)
   - Impact class (4-level binned label)
=============================================================================
 Output: project/model_ready.parquet
=============================================================================
"""

import pandas as pd
import numpy as np
import warnings
import sys
import io
import os

warnings.filterwarnings("ignore")
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

# ─────────────────────────────────────────────────────────────────────────────
# CONFIG
# ─────────────────────────────────────────────────────────────────────────────

DATA_PATH = r"d:\round2 - anti\Astram event data_anonymized - Astram event data_anonymizedb40ac87 (1).csv"
OUTPUT_PATH = r"d:\round2 - anti\project\model_ready.parquet"
EMBEDDING_DIM = 32  # PCA target dimension for description embeddings

# ─────────────────────────────────────────────────────────────────────────────
# DOMAIN LOOKUPS (from project/docs/)
# ─────────────────────────────────────────────────────────────────────────────

CORRIDOR_TIERS = {
    # Tier 1 — Critical Arterials
    "Mysore Road": 1, "Bellary Road 1": 1, "Tumkur Road": 1,
    "Bellary Road 2": 1, "Hosur Road": 1,
    # Tier 2 — Major Corridors
    "ORR North 1": 2, "Old Madras Road": 2, "Magadi Road": 2,
    "ORR East 1": 2, "ORR North 2": 2, "Bannerghatta Road": 2,
    "ORR East 2": 2, "West of Chord Road": 2,
    # Tier 3 — Secondary Corridors
    "ORR West 1": 3, "ORR South 1": 3, "Kanakapura Road": 3,
    "Sarjapur Road": 3, "Hennur Road": 3, "Airport New South Road": 3,
    "ORR West 2": 3, "ORR South 2": 3,
}

# NOTE: CAUSE_SEVERITY_WEIGHTS removed in v3.
# event_cause and priority are NOT used in the label.
# The model must discover their effect from the features.


def get_corridor_tier(corridor):
    if pd.isna(corridor) or corridor == "Non-corridor":
        return 0  # 0 = non-corridor (numeric for ML)
    return CORRIDOR_TIERS.get(corridor, 3)


# ─────────────────────────────────────────────────────────────────────────────
# STEP 1: LOAD & CLEAN
# ─────────────────────────────────────────────────────────────────────────────

print("=" * 70)
print(" FEATURE PIPELINE — Building model_ready.parquet")
print("=" * 70)

print("\n[1/7] Loading and cleaning data...")
df = pd.read_csv(DATA_PATH, low_memory=False)
print(f"  Raw: {df.shape[0]} rows × {df.shape[1]} columns")

# Replace literal NULLs
df.replace("NULL", np.nan, inplace=True)
df.replace("null", np.nan, inplace=True)

# Parse datetime columns
datetime_cols = [
    "start_datetime", "end_datetime", "created_date",
    "modified_datetime", "closed_datetime", "resolved_datetime"
]
for col in datetime_cols:
    if col in df.columns:
        df[col] = pd.to_datetime(df[col], errors="coerce", utc=True)

# Boolean columns
df["requires_road_closure"] = df["requires_road_closure"].map(
    {True: True, False: False, "TRUE": True, "FALSE": False, "true": True, "false": False}
).fillna(False).astype(bool)

df["authenticated"] = df["authenticated"].map(
    {"yes": True, "no": False, True: True, False: False}
).fillna(False).astype(bool)

# Clean coordinates
for col in ["latitude", "longitude"]:
    df[col] = pd.to_numeric(df[col], errors="coerce")

# Clean categoricals
cat_cols = ["event_type", "event_cause", "status", "priority", "corridor",
            "veh_type", "police_station", "zone", "junction"]
for col in cat_cols:
    if col in df.columns:
        df[col] = df[col].astype(str).str.strip()
        df[col] = df[col].replace("nan", np.nan)

# Exclude test_demo events
df = df[df["event_cause"] != "test_demo"].copy()
print(f"  After cleaning (excl. test_demo): {df.shape[0]} rows")


# ─────────────────────────────────────────────────────────────────────────────
# STEP 2: TEMPORAL FEATURES
# ─────────────────────────────────────────────────────────────────────────────

print("[2/7] Engineering temporal features...")

df["hour"] = df["start_datetime"].dt.hour
df["weekday"] = df["start_datetime"].dt.dayofweek  # 0=Mon, 6=Sun
df["month"] = df["start_datetime"].dt.month
df["is_weekend"] = df["weekday"].isin([5, 6]).astype(int)

# Night = 10PM–6AM IST = UTC 16:30–00:30 ≈ UTC hours 17–24, 0
# In UTC hours: night heavy vehicle window
df["is_night"] = df["hour"].apply(
    lambda h: 1 if (h >= 17 or h <= 0) else 0
) if df["hour"].notna().any() else 0

# Cyclical encoding for hour
df["hour_sin"] = np.sin(2 * np.pi * df["hour"] / 24)
df["hour_cos"] = np.cos(2 * np.pi * df["hour"] / 24)

# Cyclical encoding for weekday
df["weekday_sin"] = np.sin(2 * np.pi * df["weekday"] / 7)
df["weekday_cos"] = np.cos(2 * np.pi * df["weekday"] / 7)

# Cyclical encoding for month
df["month_sin"] = np.sin(2 * np.pi * df["month"] / 12)
df["month_cos"] = np.cos(2 * np.pi * df["month"] / 12)

print(f"  Temporal features: hour, weekday, month, is_weekend, is_night + cyclical encodings")


# ─────────────────────────────────────────────────────────────────────────────
# STEP 3: LOCATION FEATURES
# ─────────────────────────────────────────────────────────────────────────────

print("[3/7] Engineering location features...")

# Corridor tier
df["corridor_tier"] = df["corridor"].apply(get_corridor_tier)
df["is_corridor"] = (df["corridor_tier"] > 0).astype(int)

# DBSCAN geo_cluster
from sklearn.cluster import DBSCAN

geo_mask = (
    df["latitude"].notna() & df["longitude"].notna() &
    df["latitude"].between(12.5, 13.5) & df["longitude"].between(77.0, 78.0)
)

coords = df.loc[geo_mask, ["latitude", "longitude"]].values.copy()
coords_scaled = coords.copy()
coords_scaled[:, 0] *= 111000  # lat to meters
coords_scaled[:, 1] *= 111000 * np.cos(np.radians(12.97))  # lng to meters

clusterer = DBSCAN(eps=800, min_samples=30, n_jobs=-1)
cluster_labels = clusterer.fit_predict(coords_scaled)

df["geo_cluster"] = -1  # default: noise
df.loc[geo_mask, "geo_cluster"] = cluster_labels

n_clusters = len(set(cluster_labels)) - (1 if -1 in cluster_labels else 0)
print(f"  DBSCAN clusters: {n_clusters}, noise: {(cluster_labels == -1).sum()}")

# Historical frequency features
station_counts = df["police_station"].value_counts()
df["station_event_count"] = df["police_station"].map(station_counts).fillna(0).astype(int)

junction_counts = df["junction"].value_counts()
df["junction_event_count"] = df["junction"].map(junction_counts).fillna(0).astype(int)

corridor_counts = df["corridor"].value_counts()
df["corridor_event_count"] = df["corridor"].map(corridor_counts).fillna(0).astype(int)

# Lat/Lon bins — finer spatial resolution than DBSCAN (fixes Cluster 0 mega-cluster)
df["lat_bin"] = (df["latitude"] * 100).astype(int)
df["lon_bin"] = (df["longitude"] * 100).astype(int)

print(f"  Location features: corridor_tier, is_corridor, geo_cluster, lat_bin, lon_bin, station/junction/corridor counts")


# ─────────────────────────────────────────────────────────────────────────────
# STEP 4: DESCRIPTION EMBEDDINGS
# ─────────────────────────────────────────────────────────────────────────────

print("[4/7] Generating description embeddings (MiniLM)...")

from sentence_transformers import SentenceTransformer
from sklearn.decomposition import PCA

# Load multilingual model
model = SentenceTransformer("paraphrase-multilingual-MiniLM-L12-v2")
print(f"  Model loaded: paraphrase-multilingual-MiniLM-L12-v2 (384d)")

# Prepare descriptions — fill missing with empty string
descriptions = df["description"].fillna("").astype(str).tolist()

# Encode in batches
print(f"  Encoding {len(descriptions)} descriptions...")
embeddings_full = model.encode(
    descriptions,
    batch_size=128,
    show_progress_bar=True,
    normalize_embeddings=True,
)
print(f"  Raw embeddings shape: {embeddings_full.shape}")

# PCA reduction: 384d → 32d
pca = PCA(n_components=EMBEDDING_DIM, random_state=42)
embeddings_reduced = pca.fit_transform(embeddings_full)
explained_var = pca.explained_variance_ratio_.sum()
print(f"  PCA {embeddings_full.shape[1]}d → {EMBEDDING_DIM}d (explained variance: {explained_var:.1%})")

# Add to dataframe
emb_cols = [f"desc_emb_{i}" for i in range(EMBEDDING_DIM)]
emb_df = pd.DataFrame(embeddings_reduced, index=df.index, columns=emb_cols)
df = pd.concat([df, emb_df], axis=1)

print(f"  Added {EMBEDDING_DIM} embedding columns: desc_emb_0 .. desc_emb_{EMBEDDING_DIM-1}")


# ─────────────────────────────────────────────────────────────────────────────
# STEP 5: IMPACT SCORE (TRAINING LABEL)
# ─────────────────────────────────────────────────────────────────────────────

print("[5/7] Computing impact scores (v3 formula)...")

# Duration proxy — used ONLY for label generation, NEVER as a feature
df["closure_time_hrs"] = (
    df["closed_datetime"] - df["start_datetime"]
).dt.total_seconds() / 3600
df.loc[df["closure_time_hrs"] < 0, "closure_time_hrs"] = np.nan


def compute_impact_score(row):
    """
    Impact Score v3 — Pure outcome-based label.

    ONLY uses:
      closure  = 50 pts  (hard outcome: did the road close?)
      corridor = 30 pts  (where: Tier 1/2/3/non-corridor)
      duration = 20 pts  (how long: post-event duration signal)

    DOES NOT use:
      event_cause  → let the model discover cause effects
      priority     → noisy, nearly a proxy for cause

    This forces the model to learn WHY certain causes/contexts
    lead to high scores, rather than memorizing a formula.
    """
    score = 0.0

    # Component 1: Road closure (0 or 50)
    if row["requires_road_closure"]:
        score += 50

    # Component 2: Corridor tier (0–30)
    tier = row["corridor_tier"]
    tier_scores = {1: 30, 2: 22, 3: 14, 0: 0}
    score += tier_scores.get(tier, 0)

    # Component 3: Duration (0–20)
    # Post-event signal — how long did it take to resolve?
    duration = row.get("closure_time_hrs")
    if pd.notna(duration) and duration > 0:
        if duration > 6:
            score += 20
        elif duration > 2:
            score += 14
        elif duration > 1:
            score += 7

    return min(score, 100)


def score_to_class(score):
    if score >= 65:
        return "Critical"
    elif score >= 40:
        return "High"
    elif score >= 20:
        return "Medium"
    else:
        return "Low"


df["impact_score"] = df.apply(compute_impact_score, axis=1)
df["impact_class"] = df["impact_score"].apply(score_to_class)

# Print distribution
class_dist = df["impact_class"].value_counts()
print(f"\n  Impact Score v3 Distribution:")
print(f"    Mean:   {df['impact_score'].mean():.1f}")
print(f"    Median: {df['impact_score'].median():.1f}")
print(f"    Min:    {df['impact_score'].min():.1f}")
print(f"    Max:    {df['impact_score'].max():.1f}")
print(f"\n  Impact Class Distribution:")
for cls in ["Critical", "High", "Medium", "Low"]:
    count = class_dist.get(cls, 0)
    pct = count / len(df) * 100
    print(f"    {cls:10s}: {count:5d} ({pct:5.1f}%)")

# SAFETY CHECK: closure_time_hrs must NOT be in the feature set
print(f"\n  ⚠ SAFETY: closure_time_hrs is used ONLY for label, NOT exported as feature")


# ─────────────────────────────────────────────────────────────────────────────
# STEP 6: ENCODE CATEGORICALS
# ─────────────────────────────────────────────────────────────────────────────

print("\n[6/7] Encoding categorical features...")

# Label encode event_cause
from sklearn.preprocessing import LabelEncoder

cause_encoder = LabelEncoder()
df["event_cause_encoded"] = cause_encoder.fit_transform(df["event_cause"].fillna("unknown"))
print(f"  event_cause: {len(cause_encoder.classes_)} classes → encoded")

# Label encode event_type
df["event_type_encoded"] = (df["event_type"] == "planned").astype(int)
print(f"  event_type: binary (planned=1, unplanned=0)")

# Label encode veh_type (with NaN → -1)
veh_encoder = LabelEncoder()
veh_filled = df["veh_type"].fillna("unknown")
df["veh_type_encoded"] = veh_encoder.fit_transform(veh_filled)
print(f"  veh_type: {len(veh_encoder.classes_)} classes → encoded")

# Police station frequency encoding (already have station_event_count)
# Corridor already encoded as corridor_tier


# ─────────────────────────────────────────────────────────────────────────────
# STEP 7: SELECT & EXPORT
# ─────────────────────────────────────────────────────────────────────────────

print("[7/7] Selecting final columns and exporting...")

# Define output columns
output_cols = [
    # Identifiers (for traceability, not for modeling)
    "id",

    # Categorical features (raw — keep for analysis)
    "event_cause",
    "event_type",
    "corridor",
    "veh_type",
    "police_station",

    # Encoded categorical features (for ML)
    "event_cause_encoded",
    "event_type_encoded",
    "veh_type_encoded",
    "corridor_tier",
    "is_corridor",
    "geo_cluster",

    # Spatial features
    "latitude",
    "longitude",
    "lat_bin",
    "lon_bin",

    # Temporal features
    "hour",
    "weekday",
    "month",
    "is_weekend",
    "is_night",
    "hour_sin", "hour_cos",
    "weekday_sin", "weekday_cos",
    "month_sin", "month_cos",

    # Boolean features
    "requires_road_closure",
    "authenticated",

    # Historical frequency features
    "station_event_count",
    "junction_event_count",
    "corridor_event_count",

    # NOTE: closure_time_hrs is intentionally EXCLUDED
    # It is post-event data, used only for label generation

    # Description embeddings
    *emb_cols,

    # Target variables (training labels)
    "impact_score",
    "impact_class",
]

# Ensure all columns exist
existing = [c for c in output_cols if c in df.columns]
missing = [c for c in output_cols if c not in df.columns]
if missing:
    print(f"  ⚠ Missing columns (skipped): {missing}")

out = df[existing].copy()

# Convert booleans to int for parquet compatibility
for col in ["requires_road_closure", "authenticated"]:
    if col in out.columns:
        out[col] = out[col].astype(int)

# Save
out.to_parquet(OUTPUT_PATH, index=False, engine="pyarrow")
print(f"\n  ✅ Saved: {OUTPUT_PATH}")
print(f"  Shape: {out.shape[0]} rows × {out.shape[1]} columns")
print(f"  File size: {os.path.getsize(OUTPUT_PATH) / 1024 / 1024:.1f} MB")

# Print column summary
print(f"\n  ── COLUMN SUMMARY ──")
print(f"  Features for ML:       {len(existing) - 3} columns")  # minus id, impact_score, impact_class
print(f"  Embedding dimensions:  {EMBEDDING_DIM}")
print(f"  Target columns:        impact_score (continuous), impact_class (4-class)")

print(f"\n{'='*70}")
print(f" PIPELINE COMPLETE — model_ready.parquet is ready for training")
print(f"{'='*70}")
