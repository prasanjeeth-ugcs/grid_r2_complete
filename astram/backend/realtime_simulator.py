"""
Real-time Incident Simulator - ASTRAM AI V2.0
==============================================

Simulate real-time incident feeds for demo purposes without external dependencies.

Author: SHIVAPREETHAM ROHITH
Date: June 2026
"""

import random
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Optional


class RealtimeSimulator:
    """Simulate real-time incident detection for demo purposes."""

    def __init__(self, historical_data_path: str):
        """
        Initialize simulator with historical data.

        Args:
            historical_data_path: Path to historical incidents parquet file
        """
        self.historical = pd.read_parquet(historical_data_path)
        self.active_incidents = []
        self.incident_counter = 1

    def generate_realistic_incident(self) -> Optional[Dict]:
        """
        Generate a realistic incident based on current time and patterns.

        Returns:
            Incident dict or None if generation fails
        """
        now = datetime.now()
        hour = now.hour
        weekday = now.weekday()

        similar = self.historical[
            (self.historical["hour"] == hour) &
            (self.historical["weekday"] == weekday)
        ]

        if len(similar) == 0:
            similar = self.historical.sample(min(100, len(self.historical)))

        if len(similar) > 0:
            template = similar.sample(1).iloc[0]

            lat_offset = random.uniform(-0.01, 0.01)
            lon_offset = random.uniform(-0.01, 0.01)

            incident = {
                "id": f"LIVE_{now.strftime('%Y%m%d%H%M%S')}_{self.incident_counter}",
                "cause": template["event_cause"],
                "corridor": template["corridor"],
                "latitude": template["latitude"] + lat_offset,
                "longitude": template["longitude"] + lon_offset,
                "vehicle_type": template["veh_type"] if pd.notna(template["veh_type"]) else "Others",
                "closure": bool(template.get("requires_road_closure", False)),
                "timestamp": now.isoformat(),
                "status": "active",
                "source": "realtime_simulator",
                "hour": hour,
                "weekday": weekday
            }

            self.incident_counter += 1
            self.active_incidents.append(incident)

            return incident

        return None

    def get_active_incidents(self, max_age_hours: int = 2) -> List[Dict]:
        """
        Return currently active simulated incidents.

        Args:
            max_age_hours: Maximum age of incidents to include (default 2 hours)

        Returns:
            List of active incident dicts
        """
        cutoff = datetime.now() - timedelta(hours=max_age_hours)

        self.active_incidents = [
            i for i in self.active_incidents
            if datetime.fromisoformat(i["timestamp"]) > cutoff
        ]

        return self.active_incidents

    def resolve_incident(self, incident_id: str) -> bool:
        """
        Mark an incident as resolved.

        Args:
            incident_id: ID of incident to resolve

        Returns:
            True if resolved, False if not found
        """
        for incident in self.active_incidents:
            if incident["id"] == incident_id:
                incident["status"] = "resolved"
                incident["resolved_at"] = datetime.now().isoformat()
                return True
        return False

    def get_incident_stream(self, duration_minutes: int = 60, interval_minutes: int = 5) -> List[Dict]:
        """
        Generate a stream of incidents over a time period.

        Args:
            duration_minutes: Total duration to simulate
            interval_minutes: Average minutes between incidents

        Returns:
            List of simulated incidents
        """
        stream = []
        num_incidents = max(1, duration_minutes // interval_minutes)

        for i in range(num_incidents):
            incident = self.generate_realistic_incident()
            if incident:
                offset = timedelta(minutes=i * interval_minutes)
                incident["timestamp"] = (datetime.now() - timedelta(minutes=duration_minutes) + offset).isoformat()
                stream.append(incident)

        return stream

    def simulate_traffic_conditions(self, corridor: str) -> Dict:
        """
        Simulate current traffic conditions for a corridor.

        Args:
            corridor: Corridor name

        Returns:
            Traffic condition dict
        """
        hour = datetime.now().hour
        weekday = datetime.now().weekday()

        is_rush_hour = hour in [8, 9, 17, 18, 19]
        is_weekend = weekday in [5, 6]

        base_congestion = 30
        if is_rush_hour and not is_weekend:
            base_congestion = 70
        elif is_rush_hour and is_weekend:
            base_congestion = 50
        elif is_weekend:
            base_congestion = 20

        congestion = base_congestion + random.randint(-10, 10)

        corridor_incidents = [
            i for i in self.active_incidents
            if i["corridor"] == corridor
        ]

        if len(corridor_incidents) > 0:
            congestion = min(100, congestion + len(corridor_incidents) * 15)

        if congestion >= 70:
            status = "Heavy"
            color = "red"
        elif congestion >= 40:
            status = "Moderate"
            color = "orange"
        else:
            status = "Light"
            color = "green"

        avg_speed = max(10, 60 - (congestion * 0.5))

        return {
            "corridor": corridor,
            "congestion_level": congestion,
            "status": status,
            "color": color,
            "avg_speed_kmph": round(avg_speed, 1),
            "active_incidents": len(corridor_incidents),
            "timestamp": datetime.now().isoformat()
        }

    def get_system_pulse(self) -> Dict:
        """
        Get overall system pulse metrics.

        Returns:
            System metrics dict
        """
        active = self.get_active_incidents()

        total_active = len(active)
        critical = sum(1 for i in active if i.get("closure", False))

        causes = {}
        for i in active:
            cause = i.get("cause", "unknown")
            causes[cause] = causes.get(cause, 0) + 1

        return {
            "total_active_incidents": total_active,
            "critical_incidents": critical,
            "incident_breakdown": causes,
            "last_incident_time": active[-1]["timestamp"] if active else None,
            "system_status": "Critical" if critical > 2 else ("Warning" if total_active > 5 else "Normal"),
            "timestamp": datetime.now().isoformat()
        }


_simulator = None


def get_simulator(data_path: str = "astram/data/model_ready_v2.parquet") -> RealtimeSimulator:
    """Get or create simulator instance."""
    global _simulator
    if _simulator is None:
        _simulator = RealtimeSimulator(data_path)
    return _simulator
