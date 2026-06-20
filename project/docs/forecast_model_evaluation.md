# Forecast Model Evaluation Report

**Author**: SHIVAPREETHAM ROHITH
**Date**: June 2026
**Model**: CatBoost Regressor for Planned Event Impact Forecasting

## Model Performance

| Metric | Train | Test |
|--------|-------|------|
| MAE | 1.669 | 3.295 |
| RMSE | 2.576 | 4.853 |
| R² | 0.9921 | 0.9721 |

## Target Performance Goals

- ✅ R² > 0.85: **0.9721** ACHIEVED
- ✅ MAE < 5.0: **3.295** ACHIEVED

## Feature Importance (Top 10)

           Feature  Importance
  closure_required   85.865455
     corridor_tier    7.490331
       is_corridor    2.446677
             month    0.731250
          hour_cos    0.480404
       weekday_cos    0.455902
event_type_encoded    0.362579
              hour    0.360379
       weekday_sin    0.321483
           weekday    0.315442

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
2. Add API endpoint `/api/forecast/event/{event_id}`
3. Build frontend Page 4 for event forecasting
4. Validate on real planned events
