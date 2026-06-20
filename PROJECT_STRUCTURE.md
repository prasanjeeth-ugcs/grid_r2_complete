# ASTRAM AI - Project Structure

**Flipkart Grid 2.0, Round 2 Submission**

---

## Folder Organization

### `/astram` - Production System
The complete, deployable traffic management platform.

```
astram/
├── backend/
│   ├── app.py                    # FastAPI server (28 API endpoints)
│   ├── model_engine.py           # Impact prediction engine
│   ├── forecast_engine.py        # Event forecasting engine
│   ├── weather_engine.py         # Weather & water logging risk
│   ├── realtime_simulator.py    # Real-time incident simulator
│   ├── diversion_engine.py       # Route planning engine
│   ├── feedback_engine.py        # Post-event learning
│   ├── historical_engine.py      # Historical pattern search
│   ├── resource_engine.py        # Resource allocation
│   ├── corridor_engine.py        # Corridor intelligence
│   ├── precompute_lookups.py     # Lookup table generator
│   └── lookup_tables/            # Precomputed JSON indices
├── data/
│   ├── model_ready_v2.parquet    # Training data (8,173 incidents × 62 features)
│   ├── planned_events.csv        # Event database (20 planned events)
│   └── raw_events.csv            # Original incident data
├── models/
│   ├── catboost_best.cbm         # Incident impact model
│   └── forecast_event_impact.cbm # Event forecasting model
├── frontend/
│   ├── index.html                # 3-page SPA
│   ├── css/styles.css            # Dark theme UI
│   └── js/app.js                 # Page logic + charts
└── run.bat                       # Windows launcher
```

**To run**:
```bash
cd astram
python -m uvicorn backend.app:app --host 0.0.0.0 --port 5000
```

---

### `/project` - Development Workspace
Research, training, and analysis artifacts.

```
project/
├── src/
│   ├── enhanced_preprocessing_v2.py  # Data preprocessing pipeline
│   └── train_forecast.py             # Forecast model training
├── notebooks/
│   └── 02_eda_analysis.ipynb         # Comprehensive EDA (7 sections)
└── docs/
    └── forecast_model_evaluation.md  # Model metrics report
```

---

### `/docs` - Documentation
```
docs/
├── problem-statement.md              # Problem statement
└── walkthrough.md                    # Demo scenarios & API guide
```

---

## Why Two Folders?

- **astram/** = Production system (what runs)
- **project/** = Development workspace (how it was built)

This separation keeps the production system clean while preserving the full development workflow for evaluation.

---

## Key Features

- **28 API endpoints** covering incident analysis, event forecasting, real-time weather, diversion planning, and feedback
- **9 backend engines** for comprehensive traffic management intelligence
- **2 CatBoost models** for incident impact prediction and event forecasting
- **Proactive forecasting** of planned events 24-72h in advance
- **Real-time weather integration** with water logging risk assessment
- **Diversion route planning** with coordinate-based routing
- **Post-event learning** with model drift detection

---

*Built with CatBoost, FastAPI, and intelligence from 8,173 real Bengaluru traffic incidents + 20 planned events.*
