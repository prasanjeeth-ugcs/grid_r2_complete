"""
Precompute Lookup Tables — ASTRAM AI V1.0
==========================================
Reads model_ready.parquet and generates all lookup JSON files.
Run once before starting the server.

Output: astram/backend/lookup_tables/
  - corridor_dna.json
  - stress_index.json
  - risk_window.json
  - station_intelligence.json
  - resource_mapping.json
  - historical_index.parquet
"""

import os
import json
import numpy as np
import pandas as pd

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_PATH = os.path.join(BASE_DIR, "data", "model_ready.parquet")
OUTPUT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "lookup_tables")

# Corridor Tiers
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

# New risk class boundaries (V1.0)
def score_to_class(score):
    if score >= 75:
        return "Critical"
    elif score >= 50:
        return "High"
    elif score >= 25:
        return "Medium"
    else:
        return "Low"


def main():
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    
    print("=" * 60)
    print("  ASTRAM AI — Precomputing Lookup Tables")
    print("=" * 60)
    
    df = pd.read_parquet(DATA_PATH)
    df["corridor"] = df["corridor"].fillna("Non-corridor")
    
    # Re-classify with new boundaries
    df["impact_class"] = df["impact_score"].apply(score_to_class)
    
    print(f"  Loaded: {len(df)} records")
    print(f"  Corridors: {df['corridor'].nunique()}")
    print(f"  Stations: {df['police_station'].nunique()}")
    
    # ─── 1. CORRIDOR DNA ─────────────────────────────────────────────
    print("\n[1/6] Computing Corridor DNA...")
    
    corridor_dna = {}
    for corridor, grp in df[df["corridor"] != "Non-corridor"].groupby("corridor"):
        tier = CORRIDOR_TIERS.get(corridor, 3)
        total = len(grp)
        closure_rate = float(grp["requires_road_closure"].mean() * 100)
        critical_count = int((grp["impact_class"] == "Critical").sum())
        critical_rate = float(critical_count / total * 100) if total > 0 else 0.0
        
        # Dominant cause
        cause_counts = grp["event_cause"].value_counts()
        dominant_cause = cause_counts.index[0] if len(cause_counts) > 0 else "unknown"
        
        # Peak hour
        hour_counts = grp["hour"].value_counts()
        peak_hour = int(hour_counts.index[0]) if len(hour_counts) > 0 else 10
        
        # Station (most common)
        station_counts = grp["police_station"].value_counts()
        station = station_counts.index[0] if len(station_counts) > 0 else "Unknown"
        
        corridor_dna[corridor] = {
            "corridor": corridor,
            "tier": tier,
            "total_incidents": total,
            "closure_rate": round(closure_rate, 1),
            "critical_rate": round(critical_rate, 1),
            "critical_count": critical_count,
            "dominant_cause": dominant_cause,
            "peak_hour": peak_hour,
            "station": station,
            "avg_impact": round(float(grp["impact_score"].mean()), 1),
        }
    
    with open(os.path.join(OUTPUT_DIR, "corridor_dna.json"), "w") as f:
        json.dump(corridor_dna, f, indent=2)
    print(f"  → corridor_dna.json ({len(corridor_dna)} corridors)")
    
    # ─── 2. STRESS INDEX ──────────────────────────────────────────────
    print("[2/6] Computing Corridor Stress Index...")
    
    stress_data = {}
    corridors_with_data = df[df["corridor"] != "Non-corridor"].groupby("corridor")
    
    # Get raw values for normalization
    freqs = {}
    avg_impacts = {}
    closure_rates = {}
    
    for corridor, grp in corridors_with_data:
        freqs[corridor] = len(grp)
        avg_impacts[corridor] = float(grp["impact_score"].mean())
        closure_rates[corridor] = float(grp["requires_road_closure"].mean())
    
    # Normalize each dimension to 0-1
    max_freq = max(freqs.values()) if freqs else 1
    max_impact = max(avg_impacts.values()) if avg_impacts else 1
    max_closure = max(closure_rates.values()) if closure_rates else 1
    
    for corridor in freqs:
        norm_freq = freqs[corridor] / max_freq if max_freq > 0 else 0
        norm_impact = avg_impacts[corridor] / max_impact if max_impact > 0 else 0
        norm_closure = closure_rates[corridor] / max_closure if max_closure > 0 else 0
        
        # Formula: 0.4 × freq + 0.4 × impact + 0.2 × closure
        stress = (0.4 * norm_freq + 0.4 * norm_impact + 0.2 * norm_closure) * 100
        
        stress_data[corridor] = {
            "corridor": corridor,
            "stress_index": round(stress, 1),
            "frequency": freqs[corridor],
            "avg_impact": round(avg_impacts[corridor], 1),
            "closure_rate": round(closure_rates[corridor] * 100, 1),
        }
    
    with open(os.path.join(OUTPUT_DIR, "stress_index.json"), "w") as f:
        json.dump(stress_data, f, indent=2)
    print(f"  → stress_index.json ({len(stress_data)} corridors)")
    
    # Also add stress_index back into corridor_dna
    for corridor in corridor_dna:
        if corridor in stress_data:
            corridor_dna[corridor]["stress_index"] = stress_data[corridor]["stress_index"]
        else:
            corridor_dna[corridor]["stress_index"] = 0.0
    
    with open(os.path.join(OUTPUT_DIR, "corridor_dna.json"), "w") as f:
        json.dump(corridor_dna, f, indent=2)
    
    # ─── 3. RISK WINDOW ──────────────────────────────────────────────
    print("[3/6] Computing Operational Risk Window (168 slots)...")
    
    risk_window = []
    weekday_names = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
    
    for weekday in range(7):
        for hour in range(24):
            mask = (df["weekday"] == weekday) & (df["hour"] == hour)
            slot = df[mask]
            
            count = len(slot)
            critical_count = int((slot["impact_class"] == "Critical").sum())
            critical_rate = round(float(critical_count / count * 100), 1) if count > 0 else 0.0
            avg_impact = round(float(slot["impact_score"].mean()), 1) if count > 0 else 0.0
            
            # Top corridors
            if count > 0:
                top_corr = slot[slot["corridor"] != "Non-corridor"]["corridor"].value_counts().head(3)
                top_corridors = [{"corridor": c, "count": int(n)} for c, n in top_corr.items()]
                
                top_cause = slot["event_cause"].value_counts().head(3)
                top_causes = [{"cause": c, "count": int(n)} for c, n in top_cause.items()]
            else:
                top_corridors = []
                top_causes = []
            
            risk_window.append({
                "weekday": weekday,
                "weekday_name": weekday_names[weekday],
                "hour": hour,
                "event_count": count,
                "critical_rate": critical_rate,
                "critical_count": critical_count,
                "avg_impact": avg_impact,
                "top_corridors": top_corridors,
                "top_causes": top_causes,
            })
    
    with open(os.path.join(OUTPUT_DIR, "risk_window.json"), "w") as f:
        json.dump(risk_window, f, indent=2)
    print(f"  → risk_window.json ({len(risk_window)} slots)")
    
    # ─── 4. STATION INTELLIGENCE ──────────────────────────────────────
    print("[4/6] Computing Station Intelligence...")
    
    station_intel = {}
    for station, grp in df.groupby("police_station"):
        if pd.isna(station) or str(station).strip() == "":
            continue
        
        total = len(grp)
        critical_count = int((grp["impact_class"] == "Critical").sum())
        critical_rate = round(float(critical_count / total * 100), 1) if total > 0 else 0.0
        avg_impact = round(float(grp["impact_score"].mean()), 1)
        
        top_causes = grp["event_cause"].value_counts().head(3)
        top_corridors = grp[grp["corridor"] != "Non-corridor"]["corridor"].value_counts().head(3)
        
        station_intel[station] = {
            "station": station,
            "event_count": total,
            "critical_count": critical_count,
            "critical_rate": critical_rate,
            "avg_impact": avg_impact,
            "closure_rate": round(float(grp["requires_road_closure"].mean() * 100), 1),
            "top_causes": [{"cause": c, "count": int(n)} for c, n in top_causes.items()],
            "top_corridors": [{"corridor": c, "count": int(n)} for c, n in top_corridors.items()],
        }
    
    with open(os.path.join(OUTPUT_DIR, "station_intelligence.json"), "w") as f:
        json.dump(station_intel, f, indent=2)
    print(f"  → station_intelligence.json ({len(station_intel)} stations)")
    
    # ─── 5. RESOURCE MAPPING ─────────────────────────────────────────
    print("[5/6] Computing Resource Mapping...")
    
    resource_mapping = {
        "tree_fall": {
            "timeline": [
                {"phase": "0-15 min", "actions": ["Police Units", "Area Barricading"]},
                {"phase": "15-30 min", "actions": ["BBMP Tree Crew"]},
                {"phase": "30-60 min", "actions": ["Barricades", "Traffic Diversion"]},
            ],
            "resolution": {"median": "1.2h", "range": "0.4h–4.0h"},
            "resources": {"police": 2, "barricades": 4, "crew": "BBMP Tree Crew", "tow": 0, "diversion": True},
        },
        "vehicle_breakdown": {
            "timeline": [
                {"phase": "0-15 min", "actions": ["Police Unit"]},
                {"phase": "15-30 min", "actions": ["Tow Truck"]},
            ],
            "resolution": {"median": "0.5h", "range": "0.5h–1.0h"},
            "resources": {"police": 1, "barricades": 0, "crew": "None", "tow": 1, "diversion": False},
        },
        "accident": {
            "timeline": [
                {"phase": "0-15 min", "actions": ["Police Units (2)", "Ambulance"]},
                {"phase": "15-30 min", "actions": ["Tow Truck", "Barricades"]},
                {"phase": "30-60 min", "actions": ["Investigation Team", "Traffic Diversion"]},
            ],
            "resolution": {"median": "2.0h", "range": "1.0h–3.0h"},
            "resources": {"police": 2, "barricades": 2, "crew": "Accident Investigation", "tow": 1, "diversion": True},
        },
        "water_logging": {
            "timeline": [
                {"phase": "0-15 min", "actions": ["Police Unit", "Barricading"]},
                {"phase": "15-60 min", "actions": ["BWSSB Drainage Team"]},
                {"phase": "Ongoing", "actions": ["Traffic Diversion"]},
            ],
            "resolution": {"median": "3.0h", "range": "2.0h–8.0h"},
            "resources": {"police": 1, "barricades": 2, "crew": "BWSSB Drainage Team", "tow": 0, "diversion": True},
        },
        "construction": {
            "timeline": [
                {"phase": "0-15 min", "actions": ["Police Unit", "Barricading"]},
                {"phase": "Ongoing", "actions": ["BBMP Oversight", "Traffic Diversion"]},
            ],
            "resolution": {"median": "12.0h", "range": "4.0h–48.0h"},
            "resources": {"police": 1, "barricades": 5, "crew": "BBMP Oversight", "tow": 0, "diversion": True},
        },
        "pot_holes": {
            "timeline": [
                {"phase": "0-15 min", "actions": ["Barricading"]},
                {"phase": "15-60 min", "actions": ["BBMP Road Crew"]},
            ],
            "resolution": {"median": "2.0h", "range": "1.0h–4.0h"},
            "resources": {"police": 0, "barricades": 2, "crew": "BBMP Road Crew", "tow": 0, "diversion": False},
        },
        "public_event": {
            "timeline": [
                {"phase": "Pre-event", "actions": ["Police Units (4)", "Barricading (8)"]},
                {"phase": "During", "actions": ["Traffic Diversion", "Crowd Control"]},
            ],
            "resolution": {"median": "6.0h", "range": "4.0h–12.0h"},
            "resources": {"police": 4, "barricades": 8, "crew": "Event Management", "tow": 0, "diversion": True},
        },
        "procession": {
            "timeline": [
                {"phase": "Pre-event", "actions": ["Police Units (3)", "Route Barricading"]},
                {"phase": "During", "actions": ["Escort", "Traffic Diversion"]},
            ],
            "resolution": {"median": "3.0h", "range": "2.0h–6.0h"},
            "resources": {"police": 3, "barricades": 5, "crew": "None", "tow": 0, "diversion": True},
        },
        "vip_movement": {
            "timeline": [
                {"phase": "Pre-event", "actions": ["Police Units (5)", "Route Clearance"]},
                {"phase": "During", "actions": ["Escort", "Full Diversion"]},
            ],
            "resolution": {"median": "2.0h", "range": "1.0h–4.0h"},
            "resources": {"police": 5, "barricades": 8, "crew": "None", "tow": 0, "diversion": True},
        },
        "protest": {
            "timeline": [
                {"phase": "0-15 min", "actions": ["Police Units (6)", "Barricading"]},
                {"phase": "During", "actions": ["Crowd Control", "Full Diversion"]},
            ],
            "resolution": {"median": "5.0h", "range": "2.0h–12.0h"},
            "resources": {"police": 6, "barricades": 8, "crew": "None", "tow": 0, "diversion": True},
        },
        "road_conditions": {
            "timeline": [
                {"phase": "0-15 min", "actions": ["Police Unit", "Barricading"]},
                {"phase": "15-60 min", "actions": ["BBMP Road Crew"]},
            ],
            "resolution": {"median": "3.0h", "range": "2.0h–8.0h"},
            "resources": {"police": 1, "barricades": 2, "crew": "BBMP Road Crew", "tow": 0, "diversion": False},
        },
        "congestion": {
            "timeline": [
                {"phase": "0-15 min", "actions": ["Police Unit"]},
                {"phase": "15-30 min", "actions": ["Signal Override / Manual Control"]},
            ],
            "resolution": {"median": "1.5h", "range": "1.0h–3.0h"},
            "resources": {"police": 1, "barricades": 0, "crew": "None", "tow": 0, "diversion": False},
        },
        "Debris": {
            "timeline": [
                {"phase": "0-15 min", "actions": ["Police Unit", "Barricading"]},
                {"phase": "15-30 min", "actions": ["BBMP Cleanup Crew"]},
            ],
            "resolution": {"median": "1.0h", "range": "0.5h–2.0h"},
            "resources": {"police": 1, "barricades": 2, "crew": "BBMP Cleanup Crew", "tow": 0, "diversion": False},
        },
        "others": {
            "timeline": [
                {"phase": "0-15 min", "actions": ["Police Unit"]},
                {"phase": "15-30 min", "actions": ["Assessment & Dispatch"]},
            ],
            "resolution": {"median": "2.0h", "range": "1.0h–4.0h"},
            "resources": {"police": 1, "barricades": 1, "crew": "Standard", "tow": 0, "diversion": False},
        },
    }
    
    with open(os.path.join(OUTPUT_DIR, "resource_mapping.json"), "w") as f:
        json.dump(resource_mapping, f, indent=2)
    print(f"  → resource_mapping.json ({len(resource_mapping)} cause types)")
    
    # ─── 6. HISTORICAL INDEX ─────────────────────────────────────────
    print("[6/6] Building Historical Index...")
    
    hist_cols = [
        "event_cause", "corridor", "corridor_tier",
        "requires_road_closure", "impact_score", "impact_class",
        "hour", "weekday", "veh_type", "police_station",
    ]
    existing_cols = [c for c in hist_cols if c in df.columns]
    hist_df = df[existing_cols].copy()
    hist_df.to_parquet(os.path.join(OUTPUT_DIR, "historical_index.parquet"), index=False)
    print(f"  → historical_index.parquet ({len(hist_df)} records)")
    
    print("\n" + "=" * 60)
    print("  ✅ All lookup tables generated successfully")
    print(f"  Output: {OUTPUT_DIR}")
    print("=" * 60)


if __name__ == "__main__":
    main()
