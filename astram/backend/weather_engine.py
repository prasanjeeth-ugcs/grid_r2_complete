"""
Weather Engine - ASTRAM AI V2.0
================================

Real-time weather data integration for water logging risk assessment
and incident correlation.

Author: SHIVAPREETHAM ROHITH
Date: June 2026
"""

import requests
from datetime import datetime, timedelta
from functools import lru_cache
from typing import Dict, List, Optional


CORRIDOR_CENTERS = {
    "Mysore Road": {"lat": 12.9250, "lon": 77.5937},
    "Bellary Road 1": {"lat": 13.0467, "lon": 77.5971},
    "Tumkur Road": {"lat": 13.0262, "lon": 77.5442},
    "Bellary Road 2": {"lat": 13.0800, "lon": 77.6100},
    "Hosur Road": {"lat": 12.9178, "lon": 77.6226},
    "ORR North 1": {"lat": 13.0403, "lon": 77.6186},
    "Old Madras Road": {"lat": 12.9716, "lon": 77.6412},
    "Magadi Road": {"lat": 12.9716, "lon": 77.5396},
    "ORR East 1": {"lat": 12.9698, "lon": 77.7499},
    "ORR North 2": {"lat": 13.0524, "lon": 77.5428},
    "Bannerghatta Road": {"lat": 12.9072, "lon": 77.5931},
    "ORR East 2": {"lat": 12.9800, "lon": 77.7500},
    "West of Chord Road": {"lat": 12.9789, "lon": 77.5993},
    "ORR West 1": {"lat": 12.9786, "lon": 77.5632},
    "ORR South 1": {"lat": 12.8500, "lon": 77.6500},
    "Kanakapura Road": {"lat": 12.9400, "lon": 77.5500},
    "Sarjapur Road": {"lat": 12.9100, "lon": 77.7200},
    "Hennur Road": {"lat": 13.0450, "lon": 77.6500},
    "Airport New South Road": {"lat": 13.0284, "lon": 77.6400},
    "ORR West 2": {"lat": 12.9600, "lon": 77.5300},
    "ORR South 2": {"lat": 12.8200, "lon": 77.6800},
}


class WeatherEngine:
    """Real-time weather data and water logging risk assessment."""

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or "demo"
        self.base_url = "https://api.openweathermap.org/data/2.5"
        self.cache_ttl = 900

    @lru_cache(maxsize=100)
    def get_current_weather(self, lat: float, lon: float) -> Optional[Dict]:
        """
        Get current weather for a location.

        Args:
            lat: Latitude
            lon: Longitude

        Returns:
            Weather data dict or None if API fails
        """
        if self.api_key == "demo":
            return self._get_mock_weather(lat, lon)

        try:
            response = requests.get(
                f"{self.base_url}/weather",
                params={
                    "lat": lat,
                    "lon": lon,
                    "appid": self.api_key,
                    "units": "metric"
                },
                timeout=5
            )

            if response.status_code == 200:
                data = response.json()
                return {
                    "condition": data["weather"][0]["main"],
                    "description": data["weather"][0]["description"],
                    "temp_celsius": data["main"]["temp"],
                    "humidity": data["main"]["humidity"],
                    "rain_1h_mm": data.get("rain", {}).get("1h", 0),
                    "visibility_m": data.get("visibility", 10000),
                    "timestamp": datetime.now().isoformat()
                }
        except Exception as e:
            print(f"Weather API error: {e}")
            return None

    def get_forecast_5day(self, lat: float, lon: float) -> List[Dict]:
        """
        Get 5-day forecast (3-hour intervals).

        Args:
            lat: Latitude
            lon: Longitude

        Returns:
            List of forecast data dicts
        """
        if self.api_key == "demo":
            return self._get_mock_forecast(lat, lon)

        try:
            response = requests.get(
                f"{self.base_url}/forecast",
                params={
                    "lat": lat,
                    "lon": lon,
                    "appid": self.api_key,
                    "units": "metric"
                },
                timeout=5
            )

            if response.status_code == 200:
                data = response.json()
                forecasts = []
                for item in data["list"]:
                    forecasts.append({
                        "datetime": item["dt_txt"],
                        "condition": item["weather"][0]["main"],
                        "temp": item["main"]["temp"],
                        "rain_prob": item.get("pop", 0),
                        "rain_3h_mm": item.get("rain", {}).get("3h", 0)
                    })
                return forecasts
        except Exception as e:
            print(f"Forecast API error: {e}")
            return []

    def check_water_logging_risk(self, corridor: str, forecast_hours: int = 6) -> Dict:
        """
        Predict water logging risk based on rain forecast.

        Args:
            corridor: Corridor name
            forecast_hours: Hours ahead to analyze (default 6)

        Returns:
            Risk assessment dict
        """
        corridor_coords = CORRIDOR_CENTERS.get(corridor)
        if not corridor_coords:
            return {
                "corridor": corridor,
                "risk": "Unknown",
                "reason": "Corridor not found"
            }

        forecast = self.get_forecast_5day(corridor_coords["lat"], corridor_coords["lon"])

        if not forecast:
            return {
                "corridor": corridor,
                "risk": "Unknown",
                "reason": "Weather data unavailable"
            }

        num_intervals = min(forecast_hours // 3, len(forecast))
        total_rain = sum(f.get("rain_3h_mm", 0) for f in forecast[:num_intervals])

        risk = "Low"
        if total_rain > 50:
            risk = "Critical"
        elif total_rain > 25:
            risk = "High"
        elif total_rain > 10:
            risk = "Medium"

        return {
            "corridor": corridor,
            "risk_level": risk,
            "total_rain_mm": round(total_rain, 1),
            "forecast_hours": forecast_hours,
            "recommendation": self._generate_rain_recommendation(risk, total_rain),
            "confidence": self._calculate_rain_confidence(forecast[:num_intervals])
        }

    def _generate_rain_recommendation(self, risk: str, rain_mm: float) -> str:
        """Generate recommendation based on rain forecast."""
        if risk == "Critical":
            return f"URGENT: Deploy water pumps and barricades. Expected {rain_mm:.1f}mm rain - severe water logging likely."
        elif risk == "High":
            return f"Deploy preventive measures. {rain_mm:.1f}mm rain forecast - moderate water logging risk."
        elif risk == "Medium":
            return f"Monitor closely. {rain_mm:.1f}mm rain expected - minor pooling possible."
        else:
            return "Normal operations. Low rain forecast."

    def _calculate_rain_confidence(self, forecast_items: List[Dict]) -> str:
        """Calculate confidence level based on forecast data quality."""
        if not forecast_items:
            return "Low"

        avg_prob = sum(f.get("rain_prob", 0) for f in forecast_items) / len(forecast_items)

        if avg_prob > 0.7:
            return "High"
        elif avg_prob > 0.4:
            return "Medium"
        else:
            return "Low"

    def _get_mock_weather(self, lat: float, lon: float) -> Dict:
        """Generate mock weather data for demo mode."""
        import random
        hour = datetime.now().hour

        is_monsoon = datetime.now().month in [6, 7, 8, 9]
        rain_chance = 0.6 if is_monsoon else 0.2

        conditions = ["Clear", "Clouds", "Rain"] if random.random() < rain_chance else ["Clear", "Clouds"]

        return {
            "condition": random.choice(conditions),
            "description": "Simulated weather data",
            "temp_celsius": random.uniform(20, 35),
            "humidity": random.uniform(40, 90),
            "rain_1h_mm": random.uniform(0, 10) if random.random() < rain_chance else 0,
            "visibility_m": random.randint(5000, 10000),
            "timestamp": datetime.now().isoformat()
        }

    def _get_mock_forecast(self, lat: float, lon: float) -> List[Dict]:
        """Generate mock forecast data for demo mode."""
        import random
        forecasts = []
        now = datetime.now()

        for i in range(40):
            dt = now + timedelta(hours=i * 3)
            is_monsoon = dt.month in [6, 7, 8, 9]
            rain_prob = random.uniform(0.3, 0.8) if is_monsoon else random.uniform(0, 0.3)

            forecasts.append({
                "datetime": dt.strftime("%Y-%m-%d %H:%M:%S"),
                "condition": "Rain" if rain_prob > 0.6 else "Clouds",
                "temp": random.uniform(22, 32),
                "rain_prob": rain_prob,
                "rain_3h_mm": random.uniform(0, 20) if rain_prob > 0.5 else 0
            })

        return forecasts


_weather_engine = None


def get_weather_engine(api_key: Optional[str] = None) -> WeatherEngine:
    """Get or create weather engine instance."""
    global _weather_engine
    if _weather_engine is None:
        _weather_engine = WeatherEngine(api_key)
    return _weather_engine
