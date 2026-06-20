# ASTRAM AI V2.0 - Project Structure

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
│   ├── forecast_engine.py        # Event forecasting engine (NEW V2.0)
│   ├── weather_engine.py         # Weather & water logging (NEW V2.0)
│   ├── realtime_simulator.py    # Real-time incident simulator (NEW V2.0)
│   ├── diversion_engine.py       # Route planning engine (NEW V2.0)
│   ├── feedback_engine.py        # Post-event learning (NEW V2.0)
│   ├── historical_engine.py      # Historical pattern search
│   ├── resource_engine.py        # Resource allocation (ENHANCED V2.0)
│   ├── corridor_engine.py        # Corridor intelligence
│   ├── precompute_lookups.py     # Lookup table generator
│   └── lookup_tables/            # Precomputed JSON indices
├── data/
│   ├── model_ready_v2.parquet    # Enhanced training data (8,173 × 62)
│   ├── planned_events.csv        # Event database (20 events)
│   └── raw_events.csv            # Original incident data
├── models/
│   ├── catboost_best.cbm         # Incident impact model (240 KB)
│   └── forecast_event_impact.cbm # Event forecasting model (216 KB, NEW V2.0)
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

**Purpose**: EDA, feature engineering, model training, and evaluation reports.

---

### `/docs` - Documentation
```
docs/
├── problem-statement.md              # Flipkart Grid 2.0 problem statement
└── walkthrough.md                    # V2.0 demo scenarios & API guide
```

---

## Why Two Folders?

- **astram/** = What judges will run and demo (production-ready)
- **project/** = How we built it (research & training process)

This separation keeps the production system clean while preserving the full development workflow for evaluation.

---

## Key Files Summary

| File | Purpose | Size |
|------|---------|------|
| `astram/backend/app.py` | Main API server (28 endpoints) | ~1,200 lines |
| `astram/data/model_ready_v2.parquet` | Training data with 16 new V2.0 features | 1.6 MB |
| `astram/models/forecast_event_impact.cbm` | Event forecasting model (R²=0.9721) | 216 KB |
| `project/notebooks/02_eda_analysis.ipynb` | Comprehensive EDA with visualizations | ~400 KB |
| `docs/walkthrough.md` | Complete V2.0 walkthrough | 450+ lines |

---

## V1.0 vs V2.0 Changes

**V1.0** (Reactive):
- 13 API endpoints
- 4 backend engines
- 1 CatBoost model
- Static historical data only

**V2.0** (Proactive):
- 28 API endpoints (+115%)
- 9 backend engines (+5 new)
- 2 CatBoost models (+event forecasting)
- Real-time weather integration
- Diversion route planning
- Post-event feedback loop
- Problem alignment: **6.5/10 → 9.5/10**

---

*Built with CatBoost, FastAPI, and intelligence from 8,173 real Bengaluru traffic incidents + 20 planned events.*
