"""
Resource Engine — ASTRAM AI V2.0
==================================
Rule-based resource allocation with timeline format and detailed barricade placement.
No ML. Pure rule engine.

Input: impact_class, cause, vehicle_type, corridor_tier, location (optional)
Output: Timeline + Resource counts + Estimated resolution (range) + Barricade placement details
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


def recommend(cause, impact_class, corridor_tier, vehicle_type=None, location=None):
    """
    Generate resource recommendation in timeline format with detailed barricade placement.

    Args:
        cause: Incident cause
        impact_class: Risk class (Critical, High, Medium, Low)
        corridor_tier: Corridor tier (0-3)
        vehicle_type: Vehicle type (optional)
        location: Location coordinates (optional) for barricade placement

    Returns:
        timeline: list of {phase, actions} dicts
        resources: scaled resource counts
        resolution: {median, range} estimated resolution time
        vehicle_note: special note for vehicle type
        barricade_placement: detailed barricade deployment plan
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

    barricade_count = max(0, round(base_resources.get("barricades", 0) * total_mult))

    scaled_resources = {
        "police_units": max(0, round(base_resources.get("police", 0) * total_mult)),
        "tow_trucks": max(0, round(base_resources.get("tow", 0) * total_mult)),
        "barricades": barricade_count,
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

    # Generate detailed barricade placement
    barricade_placement = generate_barricade_placement(
        cause, impact_class, barricade_count, corridor_tier, location
    )

    return {
        "timeline": timeline,
        "resources": scaled_resources,
        "resolution": resolution,
        "vehicle_note": vehicle_note,
        "barricade_placement": barricade_placement,
        "multipliers": {
            "risk_class": f"{impact_class} ({risk_mult}x)",
            "corridor_tier": f"Tier {corridor_tier} ({tier_mult}x)" if corridor_tier > 0 else "Non-corridor (1.0x)",
            "total": f"{total_mult:.1f}x",
        },
    }


def generate_barricade_placement(cause, impact_class, total_barricades, corridor_tier, location=None):
    """
    Generate detailed barricade placement plan.

    Args:
        cause: Incident cause
        impact_class: Risk class
        total_barricades: Total number of barricades
        corridor_tier: Corridor tier
        location: Optional location coordinates

    Returns:
        Detailed barricade deployment plan
    """
    if total_barricades == 0:
        return {
            "total_barricades": 0,
            "placements": [],
            "setup_time_min": 0,
            "deployment_strategy": "No barricades required"
        }

    placements = []

    # Primary placement: Incident site blocking
    primary_count = max(2, round(total_barricades * 0.4))
    placements.append({
        "location_type": "Incident Site - Entry Block",
        "count": primary_count,
        "type": "full_closure" if impact_class in ["Critical", "High"] else "partial_closure",
        "reason": "Block vehicle entry to incident site",
        "priority": 1,
        "deployment_time": "T-0 (immediate)"
    })

    remaining = total_barricades - primary_count

    # Secondary: Diversion points
    if corridor_tier >= 1 and remaining >= 2:
        diversion_count = max(2, round(remaining * 0.5))
        placements.append({
            "location_type": "Upstream Junction - Diversion",
            "count": diversion_count,
            "type": "diversion_signage",
            "reason": "Redirect traffic to alternate route 500m before incident",
            "priority": 2,
            "deployment_time": "T-0 to T+5min"
        })
        remaining -= diversion_count

    # Tertiary: Pedestrian safety or downstream blocking
    if remaining >= 2:
        if cause in ["tree_fall", "water_logging", "protest"]:
            placements.append({
                "location_type": "Pedestrian Safety Zone",
                "count": remaining,
                "type": "pedestrian_safety",
                "reason": "Protect pedestrian movement near incident",
                "priority": 3,
                "deployment_time": "T+5min to T+10min"
            })
        else:
            placements.append({
                "location_type": "Downstream Exit Block",
                "count": remaining,
                "type": "exit_control",
                "reason": "Prevent vehicles from exiting blocked segment",
                "priority": 3,
                "deployment_time": "T+5min to T+10min"
            })

    # Calculate setup time (2 minutes per barricade)
    setup_time = total_barricades * 2

    # Deployment strategy
    if impact_class == "Critical":
        strategy = "Immediate full closure with police escort for barricade deployment"
    elif impact_class == "High":
        strategy = "Phased deployment: Site blocking first, then diversion points"
    else:
        strategy = "Standard deployment: Sequential placement based on priority"

    return {
        "total_barricades": total_barricades,
        "placements": placements,
        "setup_time_min": setup_time,
        "deployment_strategy": strategy,
        "equipment_checklist": [
            f"{total_barricades} traffic barricades",
            f"{len(placements)} deployment crews",
            "Reflective vests for deployment personnel",
            "Caution tape for perimeter marking",
            "Emergency lights if night deployment"
        ]
    }
