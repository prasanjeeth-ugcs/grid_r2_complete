"""
Corridor Engine — ASTRAM AI V1.0
===================================
Handles:
  1. Corridor DNA (per-corridor profiles)
  2. Corridor Stress Index (signature metric)
  3. Operational Risk Window (168-slot grid)
  4. Shift Briefing (Morning/Evening/Night)
  5. Station Intelligence (all 54 stations)
"""

import os
import json
import pandas as pd

LOOKUP_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "lookup_tables")

# Caches
_corridor_dna = None
_stress_index = None
_risk_window = None
_station_intel = None


def _load_json(filename):
    path = os.path.join(LOOKUP_DIR, filename)
    with open(path, "r") as f:
        return json.load(f)


def get_corridor_dna(corridor_name=None):
    """Get Corridor DNA. If corridor_name given, return single entry."""
    global _corridor_dna
    if _corridor_dna is None:
        _corridor_dna = _load_json("corridor_dna.json")

    if corridor_name:
        return _corridor_dna.get(corridor_name, None)
    return _corridor_dna


def get_stress_index():
    """Get Corridor Stress Index (all corridors, sorted by stress)."""
    global _stress_index
    if _stress_index is None:
        _stress_index = _load_json("stress_index.json")

    # Sort by stress_index descending
    sorted_items = sorted(
        _stress_index.values(),
        key=lambda x: x["stress_index"],
        reverse=True
    )
    return sorted_items


def get_risk_window(weekday=None, hour=None):
    """
    Get Operational Risk Window.
    168 slots (7 weekdays x 24 hours).
    Optionally filter by weekday and/or hour.
    """
    global _risk_window
    if _risk_window is None:
        _risk_window = _load_json("risk_window.json")

    if weekday is not None and hour is not None:
        # Return specific slot
        for slot in _risk_window:
            if slot["weekday"] == weekday and slot["hour"] == hour:
                return slot
        return None

    if weekday is not None:
        return [s for s in _risk_window if s["weekday"] == weekday]

    if hour is not None:
        return [s for s in _risk_window if s["hour"] == hour]

    return _risk_window


def get_shift_briefing(current_hour=None):
    """
    Shift Briefing Engine.
    Morning: 6-14, Evening: 14-22, Night: 22-6
    Returns stress level, top corridors, top causes, critical rate for current shift.
    """
    global _risk_window
    if _risk_window is None:
        _risk_window = _load_json("risk_window.json")

    # Determine current shift
    if current_hour is None:
        import datetime
        current_hour = datetime.datetime.now().hour

    if 6 <= current_hour < 14:
        shift_name = "Morning"
        shift_hours = list(range(6, 14))
    elif 14 <= current_hour < 22:
        shift_name = "Evening"
        shift_hours = list(range(14, 22))
    else:
        shift_name = "Night"
        shift_hours = list(range(22, 24)) + list(range(0, 6))

    # Aggregate all slots in this shift across all weekdays
    shift_slots = [s for s in _risk_window if s["hour"] in shift_hours]

    total_events = sum(s["event_count"] for s in shift_slots)
    total_critical = sum(s["critical_count"] for s in shift_slots)
    critical_rate = round(total_critical / total_events * 100, 1) if total_events > 0 else 0.0
    avg_impact = round(
        sum(s["avg_impact"] * s["event_count"] for s in shift_slots if s["event_count"] > 0) /
        total_events, 1
    ) if total_events > 0 else 0.0

    # Aggregate top corridors across shift
    corridor_counts = {}
    cause_counts = {}
    for s in shift_slots:
        for tc in s.get("top_corridors", []):
            corridor_counts[tc["corridor"]] = corridor_counts.get(tc["corridor"], 0) + tc["count"]
        for tc in s.get("top_causes", []):
            cause_counts[tc["cause"]] = cause_counts.get(tc["cause"], 0) + tc["count"]

    top_corridors = sorted(corridor_counts.items(), key=lambda x: x[1], reverse=True)[:5]
    top_causes = sorted(cause_counts.items(), key=lambda x: x[1], reverse=True)[:5]

    # Stress level
    if avg_impact >= 40 or critical_rate >= 10:
        stress_level = "High"
    elif avg_impact >= 25 or critical_rate >= 5:
        stress_level = "Elevated"
    else:
        stress_level = "Normal"

    return {
        "shift_name": shift_name,
        "shift_hours": f"{shift_hours[0]:02d}:00 - {(shift_hours[-1]+1) % 24:02d}:00",
        "stress_level": stress_level,
        "total_events": total_events,
        "critical_rate": critical_rate,
        "avg_impact": avg_impact,
        "top_corridors": [{"corridor": c, "count": n} for c, n in top_corridors],
        "top_causes": [{"cause": c, "count": n} for c, n in top_causes],
    }


def get_station_intelligence():
    """Get intelligence for all 54 stations."""
    global _station_intel
    if _station_intel is None:
        _station_intel = _load_json("station_intelligence.json")
    return _station_intel
