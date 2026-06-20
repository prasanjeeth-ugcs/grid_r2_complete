"""
Diversion Route Planning Engine - ASTRAM AI V2.0
=================================================

Generate alternate routes and barricade placement for corridor closures.
Simplified version using coordinate-based heuristics.

Author: SHIVAPREETHAM ROHITH
Date: June 2026
"""

import math
import random
from typing import Dict, List, Tuple, Optional


CORRIDOR_ROUTES = {
    "Mysore Road": {
        "start": (12.9250, 77.5937),
        "end": (12.9500, 77.5700),
        "parallel_roads": [
            {"name": "Kanakapura Road", "coords": [(12.9400, 77.5500), (12.9550, 77.5650)]},
            {"name": "Chord Road Extension", "coords": [(12.9300, 77.5750), (12.9480, 77.5620)]}
        ]
    },
    "Bellary Road 1": {
        "start": (13.0467, 77.5971),
        "end": (13.0800, 77.6100),
        "parallel_roads": [
            {"name": "BEL Road", "coords": [(13.0500, 77.6000), (13.0750, 77.6150)]},
            {"name": "Hennur Road", "coords": [(13.0450, 77.6500), (13.0700, 77.6600)]}
        ]
    },
    "Hosur Road": {
        "start": (12.9178, 77.6226),
        "end": (12.8456, 77.6603),
        "parallel_roads": [
            {"name": "Bannerghatta Road", "coords": [(12.9072, 77.5931), (12.8500, 77.6000)]},
            {"name": "ORR South", "coords": [(12.8800, 77.6400), (12.8200, 77.6800)]}
        ]
    },
}


class DiversionEngine:
    """Generate diversion routes and barricade placement for closures."""

    def __init__(self):
        """Initialize diversion engine."""
        self.corridor_routes = CORRIDOR_ROUTES

    def plan_diversion(
        self,
        corridor: str,
        closure_coords: Dict[str, Tuple[float, float]],
        k_routes: int = 3
    ) -> Dict:
        """
        Generate alternate routes when a corridor is closed.

        Args:
            corridor: Corridor name (e.g., "Bellary Road 1")
            closure_coords: {"start": (lat, lon), "end": (lat, lon)}
            k_routes: Number of alternate routes (default 3)

        Returns:
            {
                "alternate_routes": [GeoJSON features],
                "travel_time_differences": [+5min, +8min, +12min],
                "barricade_locations": [{lat, lon, type}, ...],
                "affected_area_km2": float,
                "estimated_delay_min": float
            }
        """
        if corridor not in self.corridor_routes:
            return self._generate_generic_diversion(closure_coords, k_routes)

        route_data = self.corridor_routes[corridor]
        closure_start = closure_coords.get("start", route_data["start"])
        closure_end = closure_coords.get("end", route_data["end"])

        alternate_routes = []
        time_differences = []

        for i, parallel in enumerate(route_data["parallel_roads"][:k_routes]):
            route_geojson = self._create_route_geojson(
                parallel["coords"],
                parallel["name"],
                route_type=f"alternate_{i+1}"
            )

            alternate_routes.append(route_geojson)

            distance_km = self._calculate_distance(parallel["coords"][0], parallel["coords"][-1])
            time_diff = self._estimate_time_difference(distance_km, base_speed=30)
            time_differences.append(time_diff)

        barricades = self._suggest_barricade_placement(corridor, closure_start, closure_end)

        affected_area = self._calculate_affected_area(closure_start, closure_end, radius_km=2.0)

        estimated_delay = sum(time_differences) / len(time_differences) if time_differences else 10

        return {
            "corridor": corridor,
            "closure_segment": {
                "start": closure_start,
                "end": closure_end,
                "length_km": self._calculate_distance(closure_start, closure_end)
            },
            "alternate_routes": alternate_routes,
            "travel_time_differences_min": time_differences,
            "barricade_locations": barricades,
            "affected_area_km2": round(affected_area, 2),
            "estimated_avg_delay_min": round(estimated_delay, 1),
            "recommended_route": alternate_routes[0]["properties"]["name"] if alternate_routes else None
        }

    def _generate_generic_diversion(
        self,
        closure_coords: Dict[str, Tuple[float, float]],
        k_routes: int
    ) -> Dict:
        """Generate generic diversion for corridors without specific route data."""
        start = closure_coords.get("start", (12.95, 77.60))
        end = closure_coords.get("end", (12.96, 77.61))

        alternate_routes = []
        time_differences = []

        for i in range(k_routes):
            offset_lat = random.uniform(-0.02, 0.02)
            offset_lon = random.uniform(-0.02, 0.02)

            mid_point = (
                (start[0] + end[0]) / 2 + offset_lat,
                (start[1] + end[1]) / 2 + offset_lon
            )

            coords = [start, mid_point, end]

            route_geojson = self._create_route_geojson(
                coords,
                f"Alternate Route {i+1}",
                route_type=f"alternate_{i+1}"
            )

            alternate_routes.append(route_geojson)

            distance_km = self._calculate_distance(start, end) * (1.2 + i * 0.1)
            time_diff = 5 + i * 3
            time_differences.append(time_diff)

        barricades = self._suggest_barricade_placement("Generic", start, end)

        return {
            "corridor": "Generic",
            "closure_segment": {
                "start": start,
                "end": end,
                "length_km": self._calculate_distance(start, end)
            },
            "alternate_routes": alternate_routes,
            "travel_time_differences_min": time_differences,
            "barricade_locations": barricades,
            "affected_area_km2": 4.0,
            "estimated_avg_delay_min": sum(time_differences) / len(time_differences),
            "recommended_route": alternate_routes[0]["properties"]["name"] if alternate_routes else None
        }

    def _create_route_geojson(
        self,
        coords: List[Tuple[float, float]],
        name: str,
        route_type: str
    ) -> Dict:
        """Create GeoJSON LineString for a route."""
        return {
            "type": "Feature",
            "properties": {
                "name": name,
                "route_type": route_type,
                "color": self._get_route_color(route_type)
            },
            "geometry": {
                "type": "LineString",
                "coordinates": [[lon, lat] for lat, lon in coords]
            }
        }

    def _get_route_color(self, route_type: str) -> str:
        """Get color for route visualization."""
        color_map = {
            "alternate_1": "#10b981",
            "alternate_2": "#f59e0b",
            "alternate_3": "#ef4444",
            "closure": "#6b7280"
        }
        return color_map.get(route_type, "#3b82f6")

    def _suggest_barricade_placement(
        self,
        corridor: str,
        closure_start: Tuple[float, float],
        closure_end: Tuple[float, float]
    ) -> List[Dict]:
        """Identify optimal barricade placement locations."""
        barricades = []

        barricades.append({
            "location": "Closure Entry Point",
            "coordinates": closure_start,
            "latitude": closure_start[0],
            "longitude": closure_start[1],
            "type": "full_closure",
            "count": 4,
            "reason": "Block vehicle entry to closed segment"
        })

        barricades.append({
            "location": "Closure Exit Point",
            "coordinates": closure_end,
            "latitude": closure_end[0],
            "longitude": closure_end[1],
            "type": "full_closure",
            "count": 4,
            "reason": "Block exit from closed segment"
        })

        mid_lat = (closure_start[0] + closure_end[0]) / 2
        mid_lon = (closure_start[1] + closure_end[1]) / 2

        barricades.append({
            "location": "Diversion Junction",
            "coordinates": (mid_lat + 0.005, mid_lon + 0.005),
            "latitude": mid_lat + 0.005,
            "longitude": mid_lon + 0.005,
            "type": "diversion",
            "count": 3,
            "reason": "Redirect traffic to alternate route"
        })

        barricades.append({
            "location": "Pedestrian Safety Zone",
            "coordinates": (mid_lat - 0.005, mid_lon),
            "latitude": mid_lat - 0.005,
            "longitude": mid_lon,
            "type": "pedestrian_safety",
            "count": 2,
            "reason": "Protect pedestrian movement"
        })

        return barricades

    def _calculate_distance(
        self,
        coord1: Tuple[float, float],
        coord2: Tuple[float, float]
    ) -> float:
        """Calculate distance between two coordinates using Haversine formula."""
        lat1, lon1 = coord1
        lat2, lon2 = coord2

        R = 6371.0

        dlat = math.radians(lat2 - lat1)
        dlon = math.radians(lon2 - lon1)

        a = (math.sin(dlat / 2) ** 2 +
             math.cos(math.radians(lat1)) *
             math.cos(math.radians(lat2)) *
             math.sin(dlon / 2) ** 2)

        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

        distance = R * c
        return distance

    def _estimate_time_difference(self, distance_km: float, base_speed: float = 30) -> int:
        """Estimate time difference in minutes."""
        time_hours = distance_km / base_speed
        time_minutes = time_hours * 60
        return int(time_minutes)

    def _calculate_affected_area(
        self,
        center1: Tuple[float, float],
        center2: Tuple[float, float],
        radius_km: float
    ) -> float:
        """Estimate affected area around closure."""
        area = math.pi * (radius_km ** 2)
        return area


_diversion_engine = None


def get_diversion_engine() -> DiversionEngine:
    """Get or create diversion engine instance."""
    global _diversion_engine
    if _diversion_engine is None:
        _diversion_engine = DiversionEngine()
    return _diversion_engine
