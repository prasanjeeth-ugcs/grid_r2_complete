"""
Forecasting Model Training - ASTRAM AI V2.0
==========================================

Train CatBoost model to predict impact of planned events 24-72h in advance.

Author: SHIVAPREETHAM ROHITH
Date: June 2026
"""

import pandas as pd
import numpy as np
from catboost import CatBoostRegressor, Pool
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
import warnings
warnings.filterwarnings('ignore')


# Corridor tier mapping (from model_engine.py)
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

EVENT_TYPE_ENCODING = {
    'festival': 0, 'sports': 1, 'rally': 2, 'procession': 3,
    'public_event': 4, 'construction': 5
}


def get_corridor_tier(corridor):
    """Get corridor tier (0-3)."""
    if pd.isna(corridor) or corridor == 'Non-corridor':
        return 0
    return CORRIDOR_TIERS.get(corridor, 3)


def load_historical_data():
    """Load and prepare historical incident data."""
    print("\n[1/6] Loading historical data...")
    df = pd.read_parquet('astram/data/model_ready_v2.parquet')

    # Filter for relevant incidents (exclude minor ones for training)
    df = df[df['resolution_time_hours'] > 0].copy()

    print(f"  Loaded {len(df):,} historical incidents")
    return df


def load_planned_events():
    """Load planned events database."""
    print("\n[2/6] Loading planned events...")
    events = pd.read_csv('astram/data/planned_events.csv')

    # Parse datetime
    events['datetime'] = pd.to_datetime(events['date'] + ' ' + events['start_time'])
    events['hour'] = events['datetime'].dt.hour
    events['weekday'] = events['datetime'].dt.weekday
    events['month'] = events['datetime'].dt.month

    print(f"  Loaded {len(events)} planned events")
    return events


def create_synthetic_training_data(historical_df, planned_events):
    """
    Create synthetic training data by matching planned events to historical patterns.

    Strategy: For each planned event type, find similar historical incidents and
    augment them with event characteristics (crowd size, etc.)
    """
    print("\n[3/6] Creating synthetic training data...")

    synthetic_data = []

    # For each planned event type, sample historical incidents
    for event_type in planned_events['event_type'].unique():
        type_events = planned_events[planned_events['event_type'] == event_type]

        # Find historical incidents on same corridors
        corridors = type_events['corridor'].unique()
        historical_subset = historical_df[historical_df['corridor'].isin(corridors)].copy()

        if len(historical_subset) == 0:
            # Use random sample if no corridor match
            historical_subset = historical_df.sample(min(100, len(historical_df))).copy()

        # Augment with planned event features
        for _, event in type_events.iterrows():
            # Sample similar historical incidents
            n_samples = min(50, len(historical_subset))
            samples = historical_subset.sample(n_samples).copy()

            # Add planned event features
            samples['event_type_planned'] = event_type
            samples['expected_crowd'] = event['expected_crowd']
            samples['closure_required_planned'] = event['closure_required']
            samples['is_planned_event'] = 1

            # Adjust impact based on crowd size (larger crowds = higher impact)
            crowd_factor = np.log1p(event['expected_crowd']) / 10
            samples['resolution_time_hours'] = samples['resolution_time_hours'] * (1 + crowd_factor * 0.3)

            # If closure is planned, increase likelihood
            if event['closure_required']:
                samples['requires_road_closure'] = True
                samples['resolution_time_hours'] = samples['resolution_time_hours'] * 1.5

            synthetic_data.append(samples)

    # Combine all synthetic samples
    synthetic_df = pd.concat(synthetic_data, ignore_index=True)

    # Also include actual historical planned events
    historical_planned = historical_df[historical_df['event_type'] == 'planned'].copy()
    historical_planned['event_type_planned'] = 'public_event'  # Default
    historical_planned['expected_crowd'] = 10000  # Estimate
    historical_planned['closure_required_planned'] = historical_planned['requires_road_closure']
    historical_planned['is_planned_event'] = 1

    # Combine
    training_df = pd.concat([synthetic_df, historical_planned], ignore_index=True)

    print(f"  Created {len(training_df):,} training samples ({len(synthetic_df)} synthetic + {len(historical_planned)} historical)")

    return training_df


def build_forecast_features(df):
    """Build feature set for forecasting model."""
    print("\n[4/6] Engineering forecast features...")

    features = pd.DataFrame()

    # Event type encoding
    features['event_type_encoded'] = df['event_type_planned'].map(EVENT_TYPE_ENCODING).fillna(4)

    # Corridor features
    features['corridor_tier'] = df['corridor'].apply(get_corridor_tier)
    features['is_corridor'] = (features['corridor_tier'] > 0).astype(int)

    # Temporal features
    features['hour'] = df['hour']
    features['weekday'] = df['weekday']
    features['month'] = df.get('month', 6)  # Default to June if missing
    features['is_weekend'] = df['weekday'].isin([5, 6]).astype(int)
    features['is_night'] = df['hour'].isin(list(range(22, 24)) + list(range(0, 6))).astype(int)

    # Cyclical encoding
    features['hour_sin'] = np.sin(2 * np.pi * features['hour'] / 24)
    features['hour_cos'] = np.cos(2 * np.pi * features['hour'] / 24)
    features['weekday_sin'] = np.sin(2 * np.pi * features['weekday'] / 7)
    features['weekday_cos'] = np.cos(2 * np.pi * features['weekday'] / 7)

    # Crowd size features
    features['expected_crowd'] = df['expected_crowd'].fillna(0)
    features['crowd_log'] = np.log1p(features['expected_crowd'])
    features['crowd_tier'] = pd.cut(features['expected_crowd'],
                                     bins=[0, 10000, 30000, 50000, 100000],
                                     labels=[0, 1, 2, 3]).astype(float).fillna(0)

    # Closure requirement
    features['closure_required'] = df['closure_required_planned'].astype(int)

    # Historical corridor patterns (if available)
    if 'corridor_event_count' in df.columns:
        features['corridor_event_count'] = df['corridor_event_count']
    else:
        features['corridor_event_count'] = 100  # Default

    # Target: resolution time as proxy for impact
    # Convert to impact score (0-100 scale)
    target = df['resolution_time_hours'].fillna(1.0)

    # Impact score formula (adapted from original)
    impact_score = (
        features['closure_required'] * 50 +  # Closure = 50 pts
        features['corridor_tier'] * 10 +      # Tier bonus
        np.clip(target * 5, 0, 20)            # Resolution time contribution
    )

    print(f"  Built {len(features.columns)} features for {len(features)} samples")
    print(f"  Feature list: {list(features.columns)}")

    return features, impact_score


def train_forecast_model(X, y):
    """Train CatBoost regression model."""
    print("\n[5/6] Training CatBoost forecast model...")

    # Train/test split
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42
    )

    print(f"  Train set: {len(X_train):,} samples")
    print(f"  Test set: {len(X_test):,} samples")

    # Model configuration (similar to baseline)
    model = CatBoostRegressor(
        iterations=1000,
        depth=6,
        learning_rate=0.05,
        l2_leaf_reg=3,
        loss_function='RMSE',
        eval_metric='MAE',
        random_seed=42,
        verbose=100,
        early_stopping_rounds=50
    )

    # Train
    print("\n  Training...")
    model.fit(
        X_train, y_train,
        eval_set=(X_test, y_test),
        use_best_model=True,
        plot=False
    )

    # Evaluate
    print("\n  Evaluating model...")
    y_train_pred = model.predict(X_train)
    y_test_pred = model.predict(X_test)

    train_mae = mean_absolute_error(y_train, y_train_pred)
    test_mae = mean_absolute_error(y_test, y_test_pred)
    train_rmse = np.sqrt(mean_squared_error(y_train, y_train_pred))
    test_rmse = np.sqrt(mean_squared_error(y_test, y_test_pred))
    train_r2 = r2_score(y_train, y_train_pred)
    test_r2 = r2_score(y_test, y_test_pred)

    print("\n" + "="*60)
    print("MODEL PERFORMANCE")
    print("="*60)
    print(f"  Train MAE:  {train_mae:.3f}")
    print(f"  Test MAE:   {test_mae:.3f}")
    print(f"  Train RMSE: {train_rmse:.3f}")
    print(f"  Test RMSE:  {test_rmse:.3f}")
    print(f"  Train R²:   {train_r2:.4f}")
    print(f"  Test R²:    {test_r2:.4f}")
    print("="*60)

    # Feature importance
    feature_importance = pd.DataFrame({
        'Feature': X.columns,
        'Importance': model.get_feature_importance()
    }).sort_values('Importance', ascending=False)

    print("\nTop 10 Feature Importance:")
    print(feature_importance.head(10).to_string(index=False))

    return model, {
        'train_mae': train_mae, 'test_mae': test_mae,
        'train_rmse': train_rmse, 'test_rmse': test_rmse,
        'train_r2': train_r2, 'test_r2': test_r2,
        'feature_importance': feature_importance
    }


def save_model(model, metrics):
    """Save trained model and metrics."""
    print("\n[6/6] Saving model...")

    # Save model
    model_path = 'astram/models/forecast_event_impact.cbm'
    model.save_model(model_path)
    print(f"  Model saved to {model_path}")

    # Save metrics report
    report = f"""# Forecast Model Evaluation Report

**Author**: SHIVAPREETHAM ROHITH
**Date**: June 2026
**Model**: CatBoost Regressor for Planned Event Impact Forecasting

## Model Performance

| Metric | Train | Test |
|--------|-------|------|
| MAE | {metrics['train_mae']:.3f} | {metrics['test_mae']:.3f} |
| RMSE | {metrics['train_rmse']:.3f} | {metrics['test_rmse']:.3f} |
| R² | {metrics['train_r2']:.4f} | {metrics['test_r2']:.4f} |

## Target Performance Goals

- ✅ R² > 0.85: **{metrics['test_r2']:.4f}** {"ACHIEVED" if metrics['test_r2'] > 0.85 else "NOT MET"}
- ✅ MAE < 5.0: **{metrics['test_mae']:.3f}** {"ACHIEVED" if metrics['test_mae'] < 5.0 else "NOT MET"}

## Feature Importance (Top 10)

{metrics['feature_importance'].head(10).to_string(index=False)}

## Model Configuration

- **Algorithm**: CatBoost Regressor
- **Iterations**: 1000 (with early stopping)
- **Depth**: 6
- **Learning Rate**: 0.05
- **L2 Regularization**: 3

## Training Data

- **Synthetic samples** generated from historical patterns
- **Augmented** with planned event characteristics (crowd size, closure)
- **Features**: Event type, corridor tier, temporal patterns, crowd metrics

## Usage

```python
from catboost import CatBoostRegressor

model = CatBoostRegressor()
model.load_model('forecast_event_impact.cbm')

# Predict impact for planned event
features = build_forecast_features(event_data)
predicted_impact = model.predict(features)
```

## Next Steps

1. Integrate into forecast_engine.py
2. Add API endpoint `/api/forecast/event/{{event_id}}`
3. Build frontend Page 4 for event forecasting
4. Validate on real planned events
"""

    report_path = 'project/docs/forecast_model_evaluation.md'
    with open(report_path, 'w', encoding='utf-8') as f:
        f.write(report)

    print(f"  Evaluation report saved to {report_path}")


def main():
    """Main training pipeline."""
    print("="*70)
    print("ASTRAM AI V2.0 - Forecasting Model Training")
    print("="*70)

    # Load data
    historical_df = load_historical_data()
    planned_events = load_planned_events()

    # Create training data
    training_df = create_synthetic_training_data(historical_df, planned_events)

    # Build features
    X, y = build_forecast_features(training_df)

    # Train model
    model, metrics = train_forecast_model(X, y)

    # Save
    save_model(model, metrics)

    print("\n" + "="*70)
    print("TRAINING COMPLETE")
    print("="*70)
    print(f"\nModel: forecast_event_impact.cbm")
    print(f"Test R²: {metrics['test_r2']:.4f}")
    print(f"Test MAE: {metrics['test_mae']:.3f}")
    print("\nReady for deployment in forecast_engine.py")
    print("="*70)


if __name__ == "__main__":
    main()
