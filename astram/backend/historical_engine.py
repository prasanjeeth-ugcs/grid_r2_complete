"""
Historical Engine — ASTRAM AI V1.0
====================================
Handles:
  1. Confidence Engine (prediction trust based on similar incident count)
  2. Historical Evidence Engine (find_similar_incidents)
  3. Transit Chain Flag (BMTC/KSRTC breakdown on Tier 1)
"""

import os
import numpy as np
import pandas as pd

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LOOKUP_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "lookup_tables")
HIST_INDEX_PATH = os.path.join(LOOKUP_DIR, "historical_index.parquet")

_hist_df = None


def _get_hist():
    """Lazy-load historical index."""
    global _hist_df
    if _hist_df is None:
        _hist_df = pd.read_parquet(HIST_INDEX_PATH)
        # Re-classify with V1.0 boundaries
        _hist_df["impact_class"] = _hist_df["impact_score"].apply(
            lambda s: "Critical" if s >= 75 else ("High" if s >= 50 else ("Medium" if s >= 25 else "Low"))
        )
    return _hist_df


def compute_confidence(cause, corridor_tier, closure):
    """
    Confidence Engine.
    Match on cause + corridor_tier + closure.
    Rules: >=30 -> High, 10-29 -> Medium, <10 -> Low
    """
    df = _get_hist()
    mask = (
        (df["event_cause"] == cause) &
        (df["corridor_tier"] == corridor_tier) &
        (df["requires_road_closure"] == (1 if closure else 0))
    )
    count = int(mask.sum())

    if count >= 30:
        level = "High"
    elif count >= 10:
        level = "Medium"
    else:
        level = "Low"

    return {
        "level": level,
        "matching_count": count,
    }


def find_similar_incidents(cause, corridor_tier, closure):
    """
    Historical Evidence Engine.
    Input: cause, corridor_tier, closure
    Output: count, critical_rate, average_score, score_distribution, top_examples
    """
    df = _get_hist()

    # Primary match: cause + corridor_tier + closure
    mask = (
        (df["event_cause"] == cause) &
        (df["corridor_tier"] == corridor_tier) &
        (df["requires_road_closure"] == (1 if closure else 0))
    )
    similar = df[mask]

    # Fallback: if too few, relax to cause + corridor_tier
    if len(similar) < 5:
        mask = (
            (df["event_cause"] == cause) &
            (df["corridor_tier"] == corridor_tier)
        )
        similar = df[mask]

    # Final fallback: just cause
    if len(similar) < 3:
        similar = df[df["event_cause"] == cause]

    count = len(similar)
    if count == 0:
        return {
            "count": 0,
            "critical_rate": 0.0,
            "average_score": 0.0,
            "score_distribution": {"Low": 0, "Medium": 0, "High": 0, "Critical": 0},
            "top_examples": [],
        }

    avg_score = round(float(similar["impact_score"].mean()), 1)
    critical_count = int((similar["impact_class"] == "Critical").sum())
    critical_rate = round(float(critical_count / count * 100), 1)

    # Score distribution
    dist = similar["impact_class"].value_counts().to_dict()
    score_distribution = {
        "Low": int(dist.get("Low", 0)),
        "Medium": int(dist.get("Medium", 0)),
        "High": int(dist.get("High", 0)),
        "Critical": int(dist.get("Critical", 0)),
    }

    # Top examples (sample up to 5)
    sample_n = min(5, count)
    sample = similar.sample(sample_n, random_state=42)
    top_examples = []
    for _, row in sample.iterrows():
        top_examples.append({
            "cause": row.get("event_cause", ""),
            "corridor": row.get("corridor", "Non-corridor"),
            "impact_score": round(float(row.get("impact_score", 0)), 1),
            "impact_class": row.get("impact_class", "Low"),
            "hour": int(row.get("hour", 0)) if pd.notna(row.get("hour")) else 0,
            "closure": bool(row.get("requires_road_closure", 0)),
        })

    return {
        "count": count,
        "critical_rate": critical_rate,
        "average_score": avg_score,
        "score_distribution": score_distribution,
        "top_examples": top_examples,
    }


def check_transit_chain(cause, vehicle_type, corridor_tier):
    """
    Transit Chain Flag.
    Trigger: vehicle_breakdown + (BMTC/KSRTC) + Tier 1
    Returns flag info with historical case count.
    """
    # Normalize vehicle type
    veh_lower = (vehicle_type or "").lower().replace(" ", "_")
    is_transit = veh_lower in ("bmtc_bus", "ksrtc_bus")

    if cause != "vehicle_breakdown" or not is_transit or corridor_tier != 1:
        return {"triggered": False}

    # Count historical transit chain cases
    df = _get_hist()
    veh_col_values = []
    if "veh_type" in df.columns:
        veh_col_values = df["veh_type"].fillna("").str.lower().str.replace(" ", "_")

    mask = (
        (df["event_cause"] == "vehicle_breakdown") &
        (veh_col_values.isin(["bmtc_bus", "ksrtc_bus"])) &
        (df["corridor_tier"] == 1)
    )
    historical_count = int(mask.sum())

    # Estimate passenger disruption
    passengers_per_bus = 60
    est_disruption = historical_count * passengers_per_bus

    bus_type = "BMTC" if "bmtc" in veh_lower else "KSRTC"

    return {
        "triggered": True,
        "bus_type": bus_type,
        "historical_cases": historical_count,
        "estimated_passenger_disruption": est_disruption,
        "advisory": f"Transit Chain Risk: {historical_count} historical cases. "
                     f"Estimated passenger disruption across history. "
                     f"{bus_type} depot coordination advised.",
    }
