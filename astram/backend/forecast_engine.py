"""
Forecast Engine - ASTRAM AI V2.0
=================================

Predict impact of planned events 24-72 hours in advance.

Author: SHIVAPREETHAM ROHITH
Date: June 2026
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from catboost import CatBoostRegressor
import os

# Import from existing engines
import sys
sys.path.append(os.path.dirname(__file__))
from model_engine import get_corridor_tier, score_to_class

# Event type encoding (must match training)
EVENT_TYPE_ENCODING = {
    'festival': 0, 'sports': 1, 'rally': 2, 'procession': 3,
    'public_event': 4, 'construction': 5
}


class ForecastEngine:
    """Engine for forecasting planned event impact."""

    def __init__(self):
        """Initialize forecast engine with model and data."""
        self.model = None
        self.planned_events = None
        self.historical_df = None
        self._load_model()
        self._load_data()

    def _load_model(self):
        """Load trained forecast model."""
        model_path = os.path.join(os.path.dirname(__file__), '..', 'models', 'forecast_event_impact.cbm')
        self.model = CatBoostRegressor()
        self.model.load_model(model_path)
        print(f"[ForecastEngine] Loaded forecast model from {model_path}")

    def _load_data(self):
        """Load planned events and historical data."""
        # Load planned events
        events_path = os.path.join(os.path.dirname(__file__), '..', 'data', 'planned_events.csv')
        self.planned_events = pd.read_csv(events_path)

        # Parse datetime
        self.planned_events['datetime'] = pd.to_datetime(
            self.planned_events['date'] + ' ' + self.planned_events['start_time']
        )
        self.planned_events['hour'] = self.planned_events['datetime'].dt.hour
        self.planned_events['weekday'] = self.planned_events['datetime'].dt.weekday
        self.planned_events['month'] = self.planned_events['datetime'].dt.month

        # Load historical data for similarity matching
        hist_path = os.path.join(os.path.dirname(__file__), '..', 'data', 'model_ready_v2.parquet')
        self.historical_df = pd.read_parquet(hist_path)

        print(f"[ForecastEngine] Loaded {len(self.planned_events)} planned events")

    def _build_event_features(self, event):
        """Build feature vector for a planned event."""
        features = {}

        # Event type encoding
        features['event_type_encoded'] = EVENT_TYPE_ENCODING.get(event['event_type'], 4)

        # Corridor features
        features['corridor_tier'] = get_corridor_tier(event['corridor'])
        features['is_corridor'] = 1 if features['corridor_tier'] > 0 else 0

        # Temporal features
        features['hour'] = event['hour']
        features['weekday'] = event['weekday']
        features['month'] = event['month']
        features['is_weekend'] = 1 if event['weekday'] in [5, 6] else 0
        features['is_night'] = 1 if event['hour'] in list(range(22, 24)) + list(range(0, 6)) else 0

        # Cyclical encoding
        features['hour_sin'] = np.sin(2 * np.pi * features['hour'] / 24)
        features['hour_cos'] = np.cos(2 * np.pi * features['hour'] / 24)
        features['weekday_sin'] = np.sin(2 * np.pi * features['weekday'] / 7)
        features['weekday_cos'] = np.cos(2 * np.pi * features['weekday'] / 7)

        # Crowd size features
        features['expected_crowd'] = event['expected_crowd']
        features['crowd_log'] = np.log1p(features['expected_crowd'])
        crowd = features['expected_crowd']
        if crowd <= 10000:
            features['crowd_tier'] = 0
        elif crowd <= 30000:
            features['crowd_tier'] = 1
        elif crowd <= 50000:
            features['crowd_tier'] = 2
        else:
            features['crowd_tier'] = 3

        # Closure requirement
        features['closure_required'] = 1 if event['closure_required'] else 0

        # Corridor event count (from historical data)
        corridor_count = len(self.historical_df[
            self.historical_df['corridor'] == event['corridor']
        ])
        features['corridor_event_count'] = corridor_count if corridor_count > 0 else 100

        return pd.DataFrame([features])

    def _find_similar_historical_events(self, event):
        """Find similar historical events for confidence estimation."""
        # Filter by event type similarity
        similar = self.historical_df[
            self.historical_df['event_type'] == 'planned'
        ].copy()

        # Filter by corridor if available
        if event['corridor'] != 'Non-corridor':
            corridor_similar = similar[similar['corridor'] == event['corridor']]
            if len(corridor_similar) > 0:
                similar = corridor_similar

        # Filter by similar time characteristics
        time_similar = similar[
            (similar['hour'] >= event['hour'] - 2) &
            (similar['hour'] <= event['hour'] + 2)
        ]
        if len(time_similar) > 0:
            similar = time_similar

        return similar

    def _compute_forecast_confidence(self, event, similar_events):
        """Compute confidence level for forecast."""
        count = len(similar_events)

        if count >= 10:
            level = "High"
            reason = f"{count} similar historical events found"
        elif count >= 5:
            level = "Medium"
            reason = f"{count} similar events, moderate historical basis"
        else:
            level = "Low"
            reason = f"Limited historical data ({count} events)"

        return {
            "level": level,
            "matching_count": count,
            "reason": reason
        }

    def _generate_proactive_plan(self, event, predicted_class, predicted_score):
        """Generate proactive resource deployment plan."""
        plan = {
            "pre_deployment_required": predicted_class in ["High", "Critical"],
            "recommended_actions": [],
            "timeline": []
        }

        if predicted_class == "Critical":
            plan["recommended_actions"].extend([
                "Deploy traffic personnel 2 hours before event",
                "Set up barricades at key junctions 1 hour before",
                "Activate traffic diversion plan",
                "Coordinate with event organizers for crowd management",
                "Alert nearby hospitals and emergency services"
            ])
            plan["timeline"].append({
                "time": "T-2 hours",
                "action": "Deploy 8-10 traffic officers to corridor",
                "resources": {"officers": 10, "barricades": 20}
            })
            plan["timeline"].append({
                "time": "T-1 hour",
                "action": "Set up full barricading and signage",
                "resources": {"barricades": 20, "signage": 15}
            })
            plan["timeline"].append({
                "time": "Event start",
                "action": "Monitor and adjust traffic flow",
                "resources": {"officers": 10, "patrol_vehicles": 3}
            })

        elif predicted_class == "High":
            plan["recommended_actions"].extend([
                "Deploy traffic personnel 1 hour before event",
                "Pre-position tow trucks if needed",
                "Monitor traffic flow in real-time",
                "Coordinate with event organizers"
            ])
            plan["timeline"].append({
                "time": "T-1 hour",
                "action": "Deploy 5-6 traffic officers",
                "resources": {"officers": 6, "barricades": 10}
            })
            plan["timeline"].append({
                "time": "Event start",
                "action": "Active traffic management",
                "resources": {"officers": 6, "patrol_vehicles": 2}
            })

        elif predicted_class == "Medium":
            plan["recommended_actions"].extend([
                "Monitor event remotely",
                "Keep rapid response team on standby",
                "Pre-plan diversion routes"
            ])
            plan["timeline"].append({
                "time": "Event start",
                "action": "Monitor from command center",
                "resources": {"officers": 2, "standby_team": 4}
            })

        else:  # Low
            plan["recommended_actions"].append("Standard monitoring")
            plan["timeline"].append({
                "time": "Event time",
                "action": "Routine patrol",
                "resources": {"officers": 1}
            })

        # Add crowd-specific actions
        if event['expected_crowd'] > 50000:
            plan["recommended_actions"].append(
                f"Large crowd ({event['expected_crowd']:,}) - Deploy crowd control barriers"
            )

        # Add closure-specific actions
        if event['closure_required']:
            plan["recommended_actions"].append(
                "Road closure planned - Activate diversion routes in advance"
            )

        return plan

    def predict_event_impact(self, event_id):
        """
        Predict impact for a planned event 24-72h in advance.

        Args:
            event_id: ID of planned event

        Returns:
            dict with forecast details
        """
        # Get event
        event = self.planned_events[
            self.planned_events['event_id'] == event_id
        ].iloc[0].to_dict()

        # Build features
        features = self._build_event_features(event)

        # Predict impact score
        predicted_score = float(self.model.predict(features)[0])
        predicted_score = max(0, min(100, predicted_score))  # Clip to 0-100

        # Convert to risk class
        predicted_class = score_to_class(predicted_score)

        # Find similar historical events
        similar_events = self._find_similar_historical_events(event)

        # Compute confidence
        confidence = self._compute_forecast_confidence(event, similar_events)

        # Generate proactive plan
        proactive_plan = self._generate_proactive_plan(event, predicted_class, predicted_score)

        # Prepare response
        forecast = {
            "event_id": event_id,
            "event_name": event['event_name'],
            "event_type": event['event_type'],
            "event_date": str(event['datetime']),
            "corridor": event['corridor'],
            "location": event['location'],
            "expected_crowd": int(event['expected_crowd']),
            "closure_required": bool(event['closure_required']),
            "predicted_impact_score": round(predicted_score, 1),
            "predicted_risk_class": predicted_class,
            "confidence": confidence,
            "similar_historical_events": {
                "count": len(similar_events),
                "avg_resolution_hours": similar_events['resolution_time_hours'].mean() if len(similar_events) > 0 else None,
                "closure_rate": (similar_events['requires_road_closure'].sum() / len(similar_events) * 100) if len(similar_events) > 0 else None
            },
            "proactive_plan": proactive_plan,
            "forecast_generated_at": datetime.now().isoformat()
        }

        return forecast

    def get_upcoming_events(self, days_ahead=7):
        """
        Get all planned events in next N days with forecasts.

        Args:
            days_ahead: Number of days to look ahead

        Returns:
            list of event forecasts
        """
        today = datetime.now()
        future = today + timedelta(days=days_ahead)

        # Filter upcoming events
        upcoming = self.planned_events[
            (self.planned_events['datetime'] >= today) &
            (self.planned_events['datetime'] <= future)
        ].copy()

        # Sort by date
        upcoming = upcoming.sort_values('datetime')

        # Generate forecasts for each
        forecasts = []
        for _, event in upcoming.iterrows():
            try:
                forecast = self.predict_event_impact(event['event_id'])
                forecasts.append(forecast)
            except Exception as e:
                print(f"Error forecasting event {event['event_id']}: {e}")
                continue

        return forecasts

    def generate_event_briefing(self, date_str):
        """
        Generate daily briefing for planned events.

        Args:
            date_str: Date in 'YYYY-MM-DD' format

        Returns:
            dict with briefing details
        """
        target_date = pd.to_datetime(date_str).date()

        # Filter events on this date
        events_today = self.planned_events[
            self.planned_events['datetime'].dt.date == target_date
        ]

        briefing = {
            "date": date_str,
            "event_count": len(events_today),
            "high_risk_events": [],
            "corridors_affected": events_today['corridor'].unique().tolist(),
            "total_expected_crowd": int(events_today['expected_crowd'].sum()),
            "closures_planned": int(events_today['closure_required'].sum())
        }

        # Generate forecasts for high-risk events
        for _, event in events_today.iterrows():
            forecast = self.predict_event_impact(event['event_id'])
            if forecast['predicted_risk_class'] in ['High', 'Critical']:
                briefing['high_risk_events'].append(forecast)

        # Summary
        if len(briefing['high_risk_events']) > 0:
            briefing['briefing_summary'] = f"{len(briefing['high_risk_events'])} high-risk events require proactive deployment"
        else:
            briefing['briefing_summary'] = "Standard monitoring recommended"

        return briefing

    def get_high_risk_periods(self, corridor=None):
        """
        Identify high-risk time periods based on upcoming events.

        Args:
            corridor: Optional corridor filter

        Returns:
            list of high-risk periods
        """
        # Get next 30 days of events
        forecasts = self.get_upcoming_events(days_ahead=30)

        # Filter by corridor if specified
        if corridor:
            forecasts = [f for f in forecasts if f['corridor'] == corridor]

        # Identify high-risk periods
        high_risk = [
            f for f in forecasts
            if f['predicted_risk_class'] in ['High', 'Critical']
        ]

        # Group by date
        periods = {}
        for forecast in high_risk:
            date = forecast['event_date'][:10]  # Extract date
            if date not in periods:
                periods[date] = []
            periods[date].append(forecast)

        # Format output
        result = [
            {
                "date": date,
                "event_count": len(events),
                "events": events,
                "max_risk_score": max(e['predicted_impact_score'] for e in events)
            }
            for date, events in periods.items()
        ]

        # Sort by risk score
        result.sort(key=lambda x: x['max_risk_score'], reverse=True)

        return result

    def detect_event_conflicts(self, date=None, days_ahead=7):
        """
        Detect conflicts when multiple events occur on the same day or in nearby corridors.

        Args:
            date: Specific date to check (YYYY-MM-DD), or None for upcoming period
            days_ahead: Number of days to look ahead if no date specified

        Returns:
            List of conflict reports with severity and recommendations
        """
        if date:
            target_date = pd.to_datetime(date)
            events_to_check = self.planned_events[
                pd.to_datetime(self.planned_events['date']).dt.date == target_date.date()
            ]
        else:
            # Check upcoming events
            today = pd.Timestamp.now().normalize()
            future = today + pd.Timedelta(days=days_ahead)
            events_to_check = self.planned_events[
                (pd.to_datetime(self.planned_events['date']) >= today) &
                (pd.to_datetime(self.planned_events['date']) <= future)
            ]

        # Group events by date
        conflicts = []

        for event_date in events_to_check['date'].unique():
            day_events = events_to_check[events_to_check['date'] == event_date]

            if len(day_events) <= 1:
                continue  # No conflict if only one event

            # Forecast impact for each event
            forecasts = []
            for _, event in day_events.iterrows():
                forecast = self.predict_event_impact(event['event_id'])
                forecasts.append({
                    'event_id': event['event_id'],
                    'event_name': event['event_name'],
                    'corridor': event['corridor'],
                    'time': event['start_time'],
                    'predicted_impact': forecast['predicted_impact_score'],
                    'risk_class': forecast['predicted_risk_class'],
                    'expected_crowd': event['expected_crowd'],
                    'closure_required': event['closure_required']
                })

            # Analyze conflicts
            conflict_details = {
                'date': event_date,
                'event_count': len(day_events),
                'events': forecasts,
                'total_expected_crowd': sum(f['expected_crowd'] for f in forecasts),
                'conflicts': []
            }

            # Check for same corridor conflicts
            corridors = [f['corridor'] for f in forecasts]
            if len(corridors) != len(set(corridors)):
                conflict_details['conflicts'].append({
                    'type': 'Same Corridor Conflict',
                    'severity': 'Critical',
                    'description': 'Multiple events on the same corridor will cause severe congestion',
                    'recommendation': 'Reschedule one event or prepare extensive diversion routes'
                })

            # Check for overlapping high-risk events
            high_risk_events = [f for f in forecasts if f['risk_class'] in ['High', 'Critical']]
            if len(high_risk_events) >= 2:
                conflict_details['conflicts'].append({
                    'type': 'Multiple High-Risk Events',
                    'severity': 'High',
                    'description': f"{len(high_risk_events)} high-risk events on same day will strain resources",
                    'recommendation': f"Pre-position {len(high_risk_events) * 15} additional officers and {len(high_risk_events) * 25} barricades"
                })

            # Check for closure conflicts
            closure_events = [f for f in forecasts if f['closure_required']]
            if len(closure_events) >= 2:
                conflict_details['conflicts'].append({
                    'type': 'Multiple Road Closures',
                    'severity': 'Critical',
                    'description': f"{len(closure_events)} road closures will significantly disrupt city traffic",
                    'recommendation': 'Coordinate closure timings to avoid overlap if possible'
                })

            # Check for crowd accumulation
            if conflict_details['total_expected_crowd'] > 100000:
                conflict_details['conflicts'].append({
                    'type': 'Excessive Crowd Accumulation',
                    'severity': 'High',
                    'description': f"Total {conflict_details['total_expected_crowd']:,} people expected across events",
                    'recommendation': 'Deploy crowd control units and setup emergency medical facilities'
                })

            # Check for time proximity (events within 2 hours)
            event_times = sorted([pd.to_datetime(f['time']).hour for f in forecasts])
            for i in range(len(event_times) - 1):
                if event_times[i+1] - event_times[i] <= 2:
                    conflict_details['conflicts'].append({
                        'type': 'Time Proximity Conflict',
                        'severity': 'Medium',
                        'description': 'Events occurring within 2 hours of each other',
                        'recommendation': 'Ensure rapid resource redeployment between events'
                    })
                    break

            # Add conflict severity score
            severity_scores = {'Critical': 3, 'High': 2, 'Medium': 1}
            total_severity = sum(severity_scores[c['severity']] for c in conflict_details['conflicts'])
            conflict_details['conflict_severity_score'] = total_severity
            conflict_details['overall_severity'] = (
                'Critical' if total_severity >= 6 else
                'High' if total_severity >= 3 else
                'Medium' if total_severity >= 1 else 'Low'
            )

            conflicts.append(conflict_details)

        # Sort by severity score
        conflicts.sort(key=lambda x: x['conflict_severity_score'], reverse=True)

        return conflicts


# Global instance (singleton pattern)
_forecast_engine = None


def get_forecast_engine():
    """Get or create forecast engine instance."""
    global _forecast_engine
    if _forecast_engine is None:
        _forecast_engine = ForecastEngine()
    return _forecast_engine
