# ASTRAM Command Center

**AI-Powered Traffic Incident Management for Bengaluru**

## Architecture

```
Officer reports incident → AI estimates impact → AI recommends resources → Control room dashboard
```

| Module | Description | Tech |
|---|---|---|
| Impact Engine | Predict severity score (0–100) | CatBoost Regressor (R²=0.926) |
| Risk Forecast | Corridor risk by time/day | Historical pattern aggregation |
| Resource Copilot | Deployment recommendations | Rule engine × risk multipliers |
| Explainability | SHAP + what-if counterfactuals | CatBoost native SHAP |

## Quick Start

### Option 1: One-click
```
Double-click run.bat
```

### Option 2: Manual
```bash
# Install dependencies
python -m pip install -r requirements.txt

# Start server
python backend/app.py
```

Then open: **http://localhost:5000**

## Pages

1. **Executive Overview** — Active incidents, city heatmap, corridor risks
2. **Risk Forecast** — Predict risk for any corridor + time
3. **Incident Simulator** — ★ The demo page. Simulate any incident.
4. **Resource Copilot** — AI resource deployment recommendations
5. **Explainability** — SHAP explanations + what-if counterfactuals

## Model Metrics

| Metric | Value |
|---|---|
| R² | 0.9259 |
| MAE | 3.404 |
| RMSE | 5.158 |
| Macro F1 | 0.8546 |
| Weighted F1 | 0.8949 |

## Folder Structure

```
astram/
├── backend/
│   ├── app.py               # Flask API server
│   ├── model_engine.py       # CatBoost + SHAP
│   ├── forecast_engine.py    # Corridor forecasting
│   └── resource_engine.py    # Resource recommendations
├── frontend/
│   ├── index.html            # Dashboard shell
│   ├── css/styles.css        # Dark theme
│   └── js/                   # Page modules
├── data/
│   ├── model_ready.parquet   # Processed dataset
│   └── raw_events.csv        # Source data
├── models/
│   └── catboost_best.cbm     # Frozen model
├── requirements.txt
├── run.bat
└── README.md
```
