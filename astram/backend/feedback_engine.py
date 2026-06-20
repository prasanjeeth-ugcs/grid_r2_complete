"""
Feedback Engine - ASTRAM AI V2.0
=================================

Post-event learning and model performance monitoring.
Logs predictions vs actual outcomes for continuous improvement.

Author: SHIVAPREETHAM ROHITH
Date: June 2026
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import os


class FeedbackEngine:
    """Post-event learning and prediction quality monitoring."""

    def __init__(self, log_path: str = "astram/data/predictions_log.parquet"):
        """
        Initialize feedback engine.

        Args:
            log_path: Path to predictions log parquet file
        """
        self.log_path = log_path
        self.logs = self._load_logs()

    def _load_logs(self) -> pd.DataFrame:
        """Load existing prediction logs or create empty DataFrame."""
        if os.path.exists(self.log_path):
            try:
                return pd.read_parquet(self.log_path)
            except Exception as e:
                print(f"Error loading logs: {e}")
                return self._create_empty_log()
        else:
            return self._create_empty_log()

    def _create_empty_log(self) -> pd.DataFrame:
        """Create empty log DataFrame with schema."""
        return pd.DataFrame(columns=[
            "timestamp", "prediction_id", "cause", "corridor", "corridor_tier",
            "closure", "vehicle_type", "hour", "weekday",
            "predicted_impact", "predicted_class", "confidence_level",
            "actual_impact", "actual_class", "actual_resolution_time",
            "error_abs", "error_pct", "class_correct"
        ])

    def _save_logs(self):
        """Save logs to disk."""
        try:
            os.makedirs(os.path.dirname(self.log_path), exist_ok=True)
            self.logs.to_parquet(self.log_path, index=False)
        except Exception as e:
            print(f"Error saving logs: {e}")

    def log_prediction(
        self,
        prediction: Dict,
        actual_outcome: Optional[Dict] = None
    ) -> str:
        """
        Log a prediction for later evaluation.

        Args:
            prediction: Prediction dict from /api/predict
            actual_outcome: Actual outcome dict (optional, can be added later)

        Returns:
            prediction_id for future reference
        """
        prediction_id = f"PRED_{datetime.now().strftime('%Y%m%d%H%M%S%f')}"

        record = {
            "timestamp": datetime.now(),
            "prediction_id": prediction_id,
            "cause": prediction.get("cause", "unknown"),
            "corridor": prediction.get("corridor", "Non-corridor"),
            "corridor_tier": prediction.get("corridor_tier", 0),
            "closure": prediction.get("closure", False),
            "vehicle_type": prediction.get("vehicle_type", "Others"),
            "hour": prediction.get("hour", 0),
            "weekday": prediction.get("weekday", 0),
            "predicted_impact": prediction.get("impact_score", 0),
            "predicted_class": prediction.get("risk_class", "Low"),
            "confidence_level": prediction.get("confidence", {}).get("level", "Medium"),
            "actual_impact": actual_outcome.get("impact_score") if actual_outcome else None,
            "actual_class": actual_outcome.get("risk_class") if actual_outcome else None,
            "actual_resolution_time": actual_outcome.get("resolution_time") if actual_outcome else None,
            "error_abs": None,
            "error_pct": None,
            "class_correct": None
        }

        if actual_outcome:
            predicted = record["predicted_impact"]
            actual = record["actual_impact"]
            if predicted and actual:
                record["error_abs"] = abs(predicted - actual)
                record["error_pct"] = (abs(predicted - actual) / actual * 100) if actual > 0 else 0
                record["class_correct"] = (record["predicted_class"] == record["actual_class"])

        self.logs = pd.concat([self.logs, pd.DataFrame([record])], ignore_index=True)
        self._save_logs()

        return prediction_id

    def update_actual_outcome(
        self,
        prediction_id: str,
        actual_outcome: Dict
    ) -> bool:
        """
        Update a logged prediction with actual outcome.

        Args:
            prediction_id: ID from log_prediction()
            actual_outcome: Actual outcome data

        Returns:
            True if updated, False if prediction_id not found
        """
        mask = self.logs["prediction_id"] == prediction_id

        if not mask.any():
            return False

        idx = self.logs[mask].index[0]

        self.logs.at[idx, "actual_impact"] = actual_outcome.get("impact_score")
        self.logs.at[idx, "actual_class"] = actual_outcome.get("risk_class")
        self.logs.at[idx, "actual_resolution_time"] = actual_outcome.get("resolution_time")

        predicted = self.logs.at[idx, "predicted_impact"]
        actual = self.logs.at[idx, "actual_impact"]

        if predicted and actual:
            self.logs.at[idx, "error_abs"] = abs(predicted - actual)
            self.logs.at[idx, "error_pct"] = (abs(predicted - actual) / actual * 100) if actual > 0 else 0
            self.logs.at[idx, "class_correct"] = (
                self.logs.at[idx, "predicted_class"] == self.logs.at[idx, "actual_class"]
            )

        self._save_logs()
        return True

    def calculate_model_drift(self, window_days: int = 30) -> Dict:
        """
        Detect if model performance is degrading over time.

        Args:
            window_days: Days to analyze (default 30)

        Returns:
            Drift analysis dict
        """
        cutoff = datetime.now() - timedelta(days=window_days)
        recent = self.logs[self.logs["timestamp"] > cutoff]

        recent_with_actuals = recent[recent["actual_impact"].notna()].copy()

        if len(recent_with_actuals) < 10:
            return {
                "status": "insufficient_data",
                "count": len(recent_with_actuals),
                "message": f"Need at least 10 predictions with outcomes, have {len(recent_with_actuals)}"
            }

        mae = recent_with_actuals["error_abs"].mean()
        mape = recent_with_actuals["error_pct"].mean()
        class_accuracy = recent_with_actuals["class_correct"].mean() * 100

        drift_threshold_mae = 5.0
        drift_threshold_accuracy = 70.0

        drift_detected = (mae > drift_threshold_mae) or (class_accuracy < drift_threshold_accuracy)

        return {
            "status": "drift_detected" if drift_detected else "model_healthy",
            "window_days": window_days,
            "predictions_analyzed": len(recent_with_actuals),
            "mae": round(mae, 2),
            "mape": round(mape, 2),
            "class_accuracy_pct": round(class_accuracy, 1),
            "drift_detected": drift_detected,
            "recommendation": "Consider model retraining" if drift_detected else "Model performing well",
            "thresholds": {
                "mae_threshold": drift_threshold_mae,
                "accuracy_threshold": drift_threshold_accuracy
            }
        }

    def generate_feedback_report(self) -> Dict:
        """
        Generate comprehensive post-event learning insights.

        Returns:
            Feedback report dict
        """
        total_predictions = len(self.logs)
        with_outcomes = self.logs[self.logs["actual_impact"].notna()]
        total_with_outcomes = len(with_outcomes)

        if total_with_outcomes == 0:
            return {
                "total_predictions": total_predictions,
                "predictions_with_outcomes": 0,
                "message": "No predictions with actual outcomes yet"
            }

        avg_error = with_outcomes["error_abs"].mean()
        avg_error_pct = with_outcomes["error_pct"].mean()

        accuracy_by_class = with_outcomes.groupby("predicted_class")["class_correct"].apply(
            lambda x: (x.sum() / len(x) * 100) if len(x) > 0 else 0
        ).to_dict()

        best_corridors = with_outcomes[with_outcomes["corridor"] != "Non-corridor"].groupby("corridor")["error_abs"].mean().sort_values().head(5).to_dict()

        weak_spots = self._identify_weak_spots(with_outcomes)

        temporal_performance = with_outcomes.groupby("hour")["error_abs"].mean().to_dict()

        return {
            "total_predictions": total_predictions,
            "predictions_with_outcomes": total_with_outcomes,
            "overall_metrics": {
                "mean_absolute_error": round(avg_error, 2),
                "mean_percentage_error": round(avg_error_pct, 2),
                "overall_class_accuracy_pct": round(with_outcomes["class_correct"].mean() * 100, 1)
            },
            "accuracy_by_risk_class": {k: round(v, 1) for k, v in accuracy_by_class.items()},
            "best_performing_corridors": {k: round(v, 2) for k, v in best_corridors.items()},
            "temporal_performance_by_hour": {int(k): round(v, 2) for k, v in temporal_performance.items()},
            "areas_for_improvement": weak_spots,
            "data_quality": {
                "outcome_reporting_rate": round(total_with_outcomes / total_predictions * 100, 1) if total_predictions > 0 else 0,
                "total_logged": total_predictions
            }
        }

    def _identify_weak_spots(self, with_outcomes: pd.DataFrame) -> List[Dict]:
        """Identify areas where model performance is weakest."""
        weak_spots = []

        cause_errors = with_outcomes.groupby("cause")["error_abs"].agg(["mean", "count"])
        cause_errors = cause_errors[cause_errors["count"] >= 3]

        if len(cause_errors) > 0:
            worst_cause = cause_errors["mean"].idxmax()
            worst_error = cause_errors.loc[worst_cause, "mean"]

            if worst_error > 7.0:
                weak_spots.append({
                    "category": "cause",
                    "value": worst_cause,
                    "avg_error": round(worst_error, 2),
                    "count": int(cause_errors.loc[worst_cause, "count"]),
                    "recommendation": f"Review and retrain for {worst_cause} incidents"
                })

        closure_errors = with_outcomes.groupby("closure")["error_abs"].mean()
        if True in closure_errors.index and closure_errors[True] > 8.0:
            weak_spots.append({
                "category": "closure_events",
                "value": "Road closure cases",
                "avg_error": round(closure_errors[True], 2),
                "recommendation": "Improve closure impact estimation"
            })

        night_mask = with_outcomes["hour"].isin(list(range(22, 24)) + list(range(0, 6)))
        if night_mask.sum() >= 5:
            night_error = with_outcomes[night_mask]["error_abs"].mean()
            day_error = with_outcomes[~night_mask]["error_abs"].mean()

            if night_error > day_error * 1.5:
                weak_spots.append({
                    "category": "temporal",
                    "value": "Night hours (22:00-6:00)",
                    "avg_error": round(night_error, 2),
                    "recommendation": "Add nighttime-specific features"
                })

        return weak_spots


_feedback_engine = None


def get_feedback_engine(log_path: str = "astram/data/predictions_log.parquet") -> FeedbackEngine:
    """Get or create feedback engine instance."""
    global _feedback_engine
    if _feedback_engine is None:
        _feedback_engine = FeedbackEngine(log_path)
    return _feedback_engine
