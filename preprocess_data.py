"""
ASTRAM AI - Data Preprocessing Pipeline
Generates all required feature columns for the full application
"""

import pandas as pd
import numpy as np
import os
from sklearn.preprocessing import LabelEncoder

print("=" * 60)
print("ASTRAM AI - Data Preprocessing")
print("=" * 60)

# Paths
CSV_PATH = "Astram event data_anonymized - Astram event data_anonymizedb40ac87.csv"
OUTPUT_PATH = "astram/data/model_ready.parquet"

# Corridor tiers
CORRIDOR_TIERS = {
    "Mysore Road": 1, "Bellary Road 1": 1, "Tumkur Road": 1,
    "Bellary Road 2": 1, "Hosur Road": 1,
    "ORR North 1": 2, "Old Madras Road": 2, "Magadi Road": 2,
    "ORR East 1": 2, "ORR North 2": 2, "Bannerghatta Road": 2,
    "ORR East 2": 2, "West of Chord Road": 2,
    "ORR West 1": 3, "ORR South 1": 3, "Kanakapura Road": 3,
    "Sarjapur Road": 3, "Hennur Road": 3, "Airport New South Road": 3,
    "ORR West 2": 3, "ORR South 2": 3,
}

# Load data
print(f"\nLoading: {CSV_PATH}")
df = pd.read_csv(CSV_PATH)
print(f"Loaded {len(df)} records")

# Parse datetime
df["start_datetime"] = pd.to_datetime(df["start_datetime"], errors="coerce")
df["end_datetime"] = pd.to_datetime(df["end_datetime"], errors="coerce")

# Temporal features
df["hour"] = df["start_datetime"].dt.hour
df["weekday"] = df["start_datetime"].dt.dayofweek
df["month"] = df["start_datetime"].dt.month
df["is_weekend"] = (df["weekday"] >= 5).astype(int)
df["is_night"] = ((df["hour"] < 6) | (df["hour"] > 22)).astype(int)

# Cyclical encoding
df["hour_sin"] = np.sin(2 * np.pi * df["hour"] / 24)
df["hour_cos"] = np.cos(2 * np.pi * df["hour"] / 24)
df["weekday_sin"] = np.sin(2 * np.pi * df["weekday"] / 7)
df["weekday_cos"] = np.cos(2 * np.pi * df["weekday"] / 7)
df["month_sin"] = np.sin(2 * np.pi * df["month"] / 12)
df["month_cos"] = np.cos(2 * np.pi * df["month"] / 12)

# Corridor features
df["corridor"] = df["corridor"].fillna("Non-corridor")
df["corridor_tier"] = df["corridor"].apply(lambda x: CORRIDOR_TIERS.get(x, 0) if pd.notna(x) and x != "Non-corridor" else 0)
df["is_corridor"] = (df["corridor"] != "Non-corridor").astype(int)

# Label encoding for categorical features
le_cause = LabelEncoder()
le_event = LabelEncoder()
le_veh = LabelEncoder()

df["event_cause_encoded"] = le_cause.fit_transform(df["event_cause"].fillna("others"))
df["event_type_encoded"] = le_event.fit_transform(df["event_type"].fillna("unknown"))
df["veh_type_encoded"] = le_veh.fit_transform(df["veh_type"].fillna("unknown"))

# Geographic clustering (simple binning)
df["lat_bin"] = pd.cut(df["latitude"], bins=10, labels=False).fillna(0).astype(int)
df["lon_bin"] = pd.cut(df["longitude"], bins=10, labels=False).fillna(0).astype(int)
df["geo_cluster"] = df["lat_bin"] * 10 + df["lon_bin"]

# Frequency features
station_counts = df.groupby("police_station").size()
df["station_event_count"] = df["police_station"].map(station_counts).fillna(0).astype(int)

junction_counts = df.groupby("junction").size()
df["junction_event_count"] = df["junction"].map(junction_counts).fillna(0).astype(int)

corridor_counts = df.groupby("corridor").size()
df["corridor_event_count"] = df["corridor"].map(corridor_counts).fillna(0).astype(int)

# Impact score calculation (simplified formula)
df["duration_minutes"] = (df["end_datetime"] - df["start_datetime"]).dt.total_seconds() / 60
df["duration_minutes"] = df["duration_minutes"].fillna(df["duration_minutes"].median())

# Base impact calculation
cause_severity = {
    "protest": 25, "water_logging": 20, "tree_fall": 18, "accident": 15,
    "public_event": 12, "procession": 10, "vip_movement": 10,
    "construction": 8, "road_conditions": 8, "pot_holes": 5,
    "congestion": 5, "vehicle_breakdown": 3, "Debris": 5, "others": 5,
}

df["base_severity"] = df["event_cause"].map(cause_severity).fillna(5)
df["impact_score"] = df["base_severity"].copy()

# Adjust for road closure
df["impact_score"] = df["impact_score"] + (df["requires_road_closure"].astype(int) * 15)

# Adjust for corridor tier
df["impact_score"] = df["impact_score"] + (df["corridor_tier"] * 5)

# Adjust for peak hours
is_peak = ((df["hour"] >= 7) & (df["hour"] <= 9)) | ((df["hour"] >= 17) & (df["hour"] <= 19))
df["impact_score"] = df["impact_score"] + (is_peak.astype(int) * 10)

# Adjust for duration
df["impact_score"] = df["impact_score"] + (df["duration_minutes"] / 10).clip(0, 20)

# Ensure range 0-100
df["impact_score"] = df["impact_score"].clip(0, 100)

# Impact class
def score_to_class(score):
    if score >= 75:
        return "Critical"
    elif score >= 50:
        return "High"
    elif score >= 25:
        return "Medium"
    else:
        return "Low"

df["impact_class"] = df["impact_score"].apply(score_to_class)

# Convert authenticated to numeric
df["authenticated"] = (df["authenticated"] == "yes").astype(int)

# Save
os.makedirs(os.path.dirname(OUTPUT_PATH), exist_ok=True)
df.to_parquet(OUTPUT_PATH, index=False)

print(f"\nGenerated features:")
print(f"  - Temporal: hour, weekday, month, is_weekend, is_night")
print(f"  - Cyclical: hour_sin/cos, weekday_sin/cos, month_sin/cos")
print(f"  - Corridor: corridor_tier, is_corridor")
print(f"  - Encoded: event_cause_encoded, event_type_encoded, veh_type_encoded")
print(f"  - Geographic: lat_bin, lon_bin, geo_cluster")
print(f"  - Frequency: station_event_count, junction_event_count, corridor_event_count")
print(f"  - Impact: impact_score, impact_class")
print(f"\nSaved to: {OUTPUT_PATH}")
print(f"Total columns: {len(df.columns)}")
print("=" * 60)
