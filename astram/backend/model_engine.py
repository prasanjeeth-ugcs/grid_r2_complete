"""
Model Engine — ASTRAM AI V1.0
==============================
Handles:
  1. Feature Pipeline (build feature vector from input)
  2. Impact Engine (CatBoost prediction)
  3. Risk Class Engine (score -> class with V1.0 boundaries)
  4. Formula vs AI Engine (operational baseline + historical pattern narrative)
"""

import os
import numpy as np
import pandas as pd
from catboost import CatBoostRegressor, Pool

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MODEL_PATH = os.path.join(BASE_DIR, "models", "catboost_best.cbm")
DATA_PATH = os.path.join(BASE_DIR, "data", "model_ready.parquet")

# --- Corridor Tiers ---
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

CORRIDORS = list(CORRIDOR_TIERS.keys()) + ["Non-corridor"]

EVENT_CAUSES = [
    "vehicle_breakdown", "accident", "tree_fall", "water_logging",
    "construction", "pot_holes", "road_conditions", "public_event",
    "procession", "vip_movement", "protest", "congestion", "others", "Debris"
]

VEH_DISPLAY_MAP = {
    "BMTC Bus": "bmtc_bus", "Heavy Vehicle": "heavy_vehicle",
    "LCV": "lcv", "Others": "others", "Private Bus": "private_bus",
    "Private Car": "private_car", "KSRTC Bus": "ksrtc_bus",
    "Taxi": "taxi", "Auto": "auto", "Truck": "truck",
}
VEH_TYPES = list(VEH_DISPLAY_MAP.keys())

# Cause severity baseline for Formula engine
CAUSE_SEVERITY = {
    "protest": 25, "water_logging": 20, "tree_fall": 18, "accident": 15,
    "public_event": 12, "procession": 10, "vip_movement": 10,
    "construction": 8, "road_conditions": 8, "pot_holes": 5,
    "congestion": 5, "vehicle_breakdown": 3, "Debris": 5, "others": 5,
}

# --- Feature config matching training pipeline ---
FEATURE_COLS = [
    "event_cause_encoded", "event_type_encoded", "veh_type_encoded",
    "corridor_tier", "is_corridor", "geo_cluster",
    "latitude", "longitude", "lat_bin", "lon_bin",
    "hour", "weekday", "month", "is_weekend", "is_night",
    "hour_sin", "hour_cos", "weekday_sin", "weekday_cos",
    "month_sin", "month_cos",
    "requires_road_closure", "authenticated",
    "station_event_count", "junction_event_count", "corridor_event_count",
]

# Build encoder mappings from training data
_df = pd.read_parquet(DATA_PATH)
CAUSE_ENCODING = dict(zip(_df["event_cause"], _df["event_cause_encoded"]))
VEH_ENCODING = dict(zip(_df["veh_type"].fillna("unknown"), _df["veh_type_encoded"]))
STATION_FREQ = _df.groupby("police_station")["station_event_count"].first().to_dict()
CORRIDOR_FREQ = _df.groupby("corridor")["corridor_event_count"].first().to_dict()
POLICE_STATIONS = sorted(_df["police_station"].dropna().unique().tolist())

# --- Load model ---
model = CatBoostRegressor()
model.load_model(MODEL_PATH)
print(f"[ModelEngine] Loaded CatBoost from {MODEL_PATH}")
print(f"[ModelEngine] Feature count: {len(FEATURE_COLS)}")


def get_corridor_tier(corridor):
    """Map corridor name to tier number."""
    if pd.isna(corridor) or corridor in ("Non-corridor", None, ""):
        return 0
    return CORRIDOR_TIERS.get(corridor, 3)


# --- V1.0 Risk Class Boundaries ---
def score_to_class(score):
    """Convert impact score to risk class (V1.0 boundaries)."""
    if score >= 75:
        return "Critical"
    elif score >= 50:
        return "High"
    elif score >= 25:
        return "Medium"
    else:
        return "Low"


def build_feature_vector(cause, corridor, closure, vehicle_type, hour, weekday=3):
    """
    Feature Pipeline: Build a feature vector from incident parameters.
    Steps match spec: tier mapping -> temporal -> flags -> station/corridor lookup -> geo
    """
    # Step 1: Corridor tier
    tier = get_corridor_tier(corridor)

    # Step 2: Temporal cyclical features
    hour_sin = float(np.sin(2 * np.pi * hour / 24))
    hour_cos = float(np.cos(2 * np.pi * hour / 24))
    weekday_sin = float(np.sin(2 * np.pi * weekday / 7))
    weekday_cos = float(np.cos(2 * np.pi * weekday / 7))

    # Step 3: Flags
    rush_hour_flag = 1 if (7 <= hour <= 10) or (16 <= hour <= 20) else 0
    night_flag = 1 if (hour >= 22 or hour <= 5) else 0

    # Translate vehicle type
    veh = VEH_DISPLAY_MAP.get(vehicle_type, vehicle_type) if vehicle_type else "others"
    if isinstance(veh, str):
        veh = veh.lower().replace(" ", "_")

    row = {
        "event_cause_encoded": CAUSE_ENCODING.get(cause, CAUSE_ENCODING.get("others", 6)),
        "event_type_encoded": 0,  # unplanned
        "veh_type_encoded": VEH_ENCODING.get(veh, VEH_ENCODING.get("others", 5)),
        "corridor_tier": tier,
        "is_corridor": 1 if tier > 0 else 0,
        "geo_cluster": 0,
        "latitude": 12.97,
        "longitude": 77.59,
        "lat_bin": 1297,
        "lon_bin": 7759,
        "hour": hour,
        "weekday": weekday,
        "month": 6,
        "is_weekend": 1 if weekday in [5, 6] else 0,
        "is_night": night_flag,
        "hour_sin": hour_sin,
        "hour_cos": hour_cos,
        "weekday_sin": weekday_sin,
        "weekday_cos": weekday_cos,
        "month_sin": float(np.sin(2 * np.pi * 6 / 12)),
        "month_cos": float(np.cos(2 * np.pi * 6 / 12)),
        "requires_road_closure": 1 if closure else 0,
        "authenticated": 1,
        "station_event_count": 50,
        "junction_event_count": 10,
        "corridor_event_count": CORRIDOR_FREQ.get(corridor, 0),
    }

    return pd.DataFrame([row])[FEATURE_COLS]


def predict_impact(cause, corridor, closure, vehicle_type, hour, weekday=3):
    """
    Impact Engine: Predict impact score using frozen CatBoost model.
    Returns raw score + risk class.
    """
    X = build_feature_vector(cause, corridor, closure, vehicle_type, hour, weekday)
    raw = model.predict(X)
    raw_arr = np.asarray(raw)
    raw_scalar = float(raw_arr.flat[0])

    # The model outputs a score — scale to 0-100 range
    # Model was trained with scores 0-100, but raw predictions may cluster
    score = max(0.0, min(100.0, raw_scalar))
    risk_class = score_to_class(score)

    return {
        "impact_score": round(score, 1),
        "risk_class": risk_class,
        "raw_model_output": round(raw_scalar, 2),
    }


def compute_operational_baseline(cause, corridor, closure, hour):
    """
    Formula vs AI Engine: Deterministic operational baseline.
    Shows the formula-based score that a human could compute.
    """
    baseline = 0
    components = []

    # Road Closure component
    if closure:
        baseline += 35
        components.append({"factor": "Road Closure", "delta": "+35"})

    # Corridor Tier component
    tier = get_corridor_tier(corridor)
    tier_scores = {1: 30, 2: 20, 3: 10, 0: 0}
    tier_delta = tier_scores.get(tier, 0)
    if tier_delta > 0:
        components.append({"factor": f"Tier {tier} Corridor", "delta": f"+{tier_delta}"})
        baseline += tier_delta

    # Cause Severity component
    cause_delta = CAUSE_SEVERITY.get(cause, 5)
    components.append({"factor": f"Cause Severity ({cause})", "delta": f"+{cause_delta}"})
    baseline += cause_delta

    # Rush hour boost
    if (7 <= hour <= 10) or (16 <= hour <= 20):
        components.append({"factor": "Rush Hour", "delta": "+5"})
        baseline += 5

    # Night reduction
    if hour >= 22 or hour <= 5:
        components.append({"factor": "Night Hours", "delta": "-5"})
        baseline -= 5

    baseline = max(0, min(100, baseline))

    return {
        "baseline_score": baseline,
        "components": components,
    }


def get_metadata():
    """Return available options for the frontend selectors."""
    return {
        "corridors": CORRIDORS,
        "event_causes": EVENT_CAUSES,
        "veh_types": VEH_TYPES,
        "stations": POLICE_STATIONS,
    }
