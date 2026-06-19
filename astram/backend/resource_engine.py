"""
Resource Engine — ASTRAM AI V1.0
==================================
Rule-based resource allocation with timeline format.
No ML. Pure rule engine.

Input: impact_class, cause, vehicle_type, corridor_tier
Output: Timeline + Resource counts + Estimated resolution (range)
"""

import os
import json

LOOKUP_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "lookup_tables")

_resource_map = None


def _get_resource_map():
    """Load resource mapping from precomputed JSON."""
    global _resource_map
    if _resource_map is None:
        path = os.path.join(LOOKUP_DIR, "resource_mapping.json")
        with open(path, "r") as f:
            _resource_map = json.load(f)
    return _resource_map


# Risk class multipliers for resource scaling
RISK_MULTIPLIER = {"Critical": 2.0, "High": 1.5, "Medium": 1.0, "Low": 0.7}
TIER_MULTIPLIER = {0: 1.0, 1: 1.5, 2: 1.25, 3: 1.1}

# Vehicle-specific notes
VEH_NOTES = {
    "bmtc_bus": "Coordinate BMTC depot for replacement bus",
    "ksrtc_bus": "Coordinate KSRTC depot for replacement bus",
    "heavy_vehicle": "Heavy-duty crane/tow required",
    "truck": "Heavy-duty crane + cargo transfer vehicle",
    "private_bus": "Large tow truck + passenger transfer",
}

# Map display names to internal keys
VEH_DISPLAY_TO_INTERNAL = {
    "BMTC Bus": "bmtc_bus", "KSRTC Bus": "ksrtc_bus",
    "Heavy Vehicle": "heavy_vehicle", "Truck": "truck",
    "Private Bus": "private_bus",
}


def recommend(cause, impact_class, corridor_tier, vehicle_type=None):
    """
    Generate resource recommendation in timeline format.

    Returns:
        timeline: list of {phase, actions} dicts
        resources: scaled resource counts
        resolution: {median, range} estimated resolution time
        vehicle_note: special note for vehicle type
    """
    rmap = _get_resource_map()
    entry = rmap.get(cause, rmap.get("others", {}))

    # Timeline (directly from mapping)
    timeline = entry.get("timeline", [])

    # Resolution estimate (range, never single number)
    resolution = entry.get("resolution", {"median": "2.0h", "range": "1.0h-4.0h"})

    # Base resources
    base_resources = entry.get("resources", {
        "police": 1, "barricades": 1, "crew": "Standard", "tow": 0, "diversion": False
    })

    # Scale by risk class and corridor tier
    risk_mult = RISK_MULTIPLIER.get(impact_class, 1.0)
    tier_mult = TIER_MULTIPLIER.get(corridor_tier, 1.0)
    total_mult = risk_mult * tier_mult

    scaled_resources = {
        "police_units": max(0, round(base_resources.get("police", 0) * total_mult)),
        "tow_trucks": max(0, round(base_resources.get("tow", 0) * total_mult)),
        "barricades": max(0, round(base_resources.get("barricades", 0) * total_mult)),
        "special_team": base_resources.get("crew", "None"),
        "diversion_required": base_resources.get("diversion", False),
    }

    # If risk is Critical or High and diversion isn't set, override
    if impact_class in ("Critical", "High") and corridor_tier >= 1:
        scaled_resources["diversion_required"] = True

    # Vehicle-specific note
    veh_key = vehicle_type
    if vehicle_type in VEH_DISPLAY_TO_INTERNAL:
        veh_key = VEH_DISPLAY_TO_INTERNAL[vehicle_type]
    vehicle_note = VEH_NOTES.get(veh_key, "") if veh_key else ""

    return {
        "timeline": timeline,
        "resources": scaled_resources,
        "resolution": resolution,
        "vehicle_note": vehicle_note,
        "multipliers": {
            "risk_class": f"{impact_class} ({risk_mult}x)",
            "corridor_tier": f"Tier {corridor_tier} ({tier_mult}x)" if corridor_tier > 0 else "Non-corridor (1.0x)",
            "total": f"{total_mult:.1f}x",
        },
    }
