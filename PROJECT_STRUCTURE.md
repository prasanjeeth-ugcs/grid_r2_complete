# ASTRAM AI - Project Structure

Clean, organized codebase for Flipkart Grid 2.0 submission.

---

## Root Directory

```
grid_r2_complete/
├── 📄 README.md                    # Main documentation (starts here)
├── 📄 QUICK_START.md               # Get running in 2 minutes
├── 📄 DOCUMENTATION.md             # Index of all docs
├── 📄 DOCKER_GUIDE.md              # Docker deployment guide
├── 📄 VIDEO_DEMO_SCRIPT.md         # 2-minute demo walkthrough
├── 📄 PROJECT_STRUCTURE.md         # This file
│
├── 🐳 Dockerfile                   # Docker build configuration
├── 🐳 docker-compose.yml           # Docker Compose setup
├── 📦 requirements.txt             # Python dependencies
│
├── 📊 Astram event data_anonymized - *.csv  # 8,173 incidents (raw)
│
└── 📁 astram/                      # Main application directory
    ├── 📁 backend/                 # Backend API (FastAPI)
    ├── 📁 frontend/                # Web interface
    ├── 📁 models/                  # Trained ML models
    ├── 📁 data/                    # Processed data (generated)
    └── 📁 scripts/                 # Utility scripts
```

---

## Backend Directory (`astram/backend/`)

```
astram/backend/
├── app.py                          # Main FastAPI app (27 endpoints)
├── model_engine.py                 # CatBoost ML model engine
├── historical_engine.py            # Historical pattern analysis
├── resource_engine.py              # Resource planning
├── corridor_engine.py              # Corridor analytics
├── forecast_engine.py              # Forecasting capabilities
├── weather_engine.py               # Weather integration
├── realtime_simulator.py           # Real-time simulation
├── diversion_engine.py             # Route planning
├── feedback_engine.py              # Prediction feedback
├── precompute_lookups.py           # Generate lookup tables
│
└── lookup_tables/                  # Precomputed data (6 files)
    ├── corridor_dna.json           # 21 corridors
    ├── stress_index.json           # Stress scores
    ├── risk_window.json            # 168 time slots
    ├── station_intelligence.json   # 54 police stations
    ├── resource_mapping.json       # 14 incident types
    └── historical_index.parquet    # 8,173 records
```

---

## Frontend Directory (`astram/frontend/`)

```
astram/frontend/
├── index.html                      # 3-page web interface
├── css/
│   └── styles.css                  # Styling
└── js/
    └── app.js                      # Frontend logic
```

**Pages:**
1. Command Center - City-wide overview
2. Response Copilot - AI predictions (main feature)
3. Corridor Intelligence - Strategic analytics

---

## Scripts Directory (`astram/scripts/`)

```
astram/scripts/
└── preprocess_data.py              # Data preprocessing pipeline
```

**Purpose:** Generates 72-column feature dataset from raw CSV
- Temporal features (hour, weekday, cyclical)
- Spatial features (corridors, tiers, clusters)
- Categorical encoding
- Impact score calculation

---

## Models Directory (`astram/models/`)

```
astram/models/
└── catboost_best.cbm               # Trained CatBoost model (240KB)
```

**Model Stats:**
- Algorithm: CatBoost Gradient Boosting
- R² Score: 0.9522 (95.22% accuracy)
- Training: 6,500 incidents
- Features: 72 engineered features

---

## Data Directory (`astram/data/`)

**Generated during build/setup** - excluded from git

```
astram/data/
└── model_ready.parquet             # 8,173 incidents with 72 features
```

**Note:** Old data files (model_ready_v2.parquet, enhanced_features_data.csv) excluded via `.dockerignore`

---

## Documentation Files

| File | Purpose | For |
|------|---------|-----|
| README.md | Complete system docs | Technical reviewers |
| QUICK_START.md | 2-minute setup | Everyone |
| DOCKER_GUIDE.md | Deployment guide | DevOps |
| VIDEO_DEMO_SCRIPT.md | Demo walkthrough | Presentation |
| DOCUMENTATION.md | Docs index | Navigation |
| PROJECT_STRUCTURE.md | This file | Understanding layout |

---

## Build Process

### Docker Build Stages

1. **Base Image** - Python 3.9-slim
2. **Dependencies** - Install from requirements.txt
3. **Copy Code** - Copy astram/ directory
4. **Copy Data** - Copy raw CSV file
5. **Preprocess** - Run preprocessing pipeline:
   - `astram/scripts/preprocess_data.py` (generate features)
   - `astram/backend/precompute_lookups.py` (generate lookups)
6. **Expose Port** - Port 5000
7. **Start Server** - Uvicorn FastAPI

**Total build time:** ~8-10 minutes
**Image size:** ~1.9GB

---

## API Endpoints (27 Total)

### Core Prediction
- `POST /api/predict` - Impact prediction

### City Overview
- `GET /api/city-pulse` - KPIs and map data
- `GET /api/metadata` - Corridors, causes, vehicles

### Intelligence
- `GET /api/corridor-intelligence` - Analytics
- `GET /api/shift-briefing` - Operational brief
- `GET /api/risk-window` - 168-slot heatmap

### Forecasting (5 endpoints)
- `GET /api/forecast/upcoming`
- `GET /api/forecast/high-risk-periods`
- `GET /api/forecast/briefing`
- `GET /api/forecast/event/{event_id}`
- `GET /api/forecast/conflicts`

### Real-time (5 endpoints)
- `GET /api/realtime/incidents/active`
- `POST /api/realtime/incidents/generate`
- `GET /api/realtime/system-pulse`
- `GET /api/realtime/traffic/{corridor}`
- `GET /api/realtime/weather/{corridor}`

### Others
- `GET /api/corridor/{name}`
- `GET /api/station-intelligence`
- `GET /api/similar-incidents`
- `POST /api/diversion/plan`
- `POST /api/feedback/log`
- `POST /api/feedback/update/{prediction_id}`
- `GET /api/feedback/drift`
- `GET /api/feedback/report`
- `GET /api/analytics/prediction-breakdown`
- `GET /api/analytics/risk-heatmap`

**Interactive docs:** http://localhost:5000/docs

---

## File Sizes

| Item | Size |
|------|------|
| Docker Image | ~1.9GB |
| CatBoost Model | 240KB |
| Raw CSV | ~4.4MB |
| Processed Parquet | ~1.3MB |
| Lookup Tables | ~500KB total |
| Source Code | ~500KB |

---

## Key Technologies

- **ML**: CatBoost 1.2.2
- **Backend**: FastAPI 0.108, Python 3.9
- **Frontend**: Vanilla JS, Leaflet.js, Chart.js
- **Data**: Pandas 2.1.4, PyArrow 14.0.2
- **Deployment**: Docker, Docker Compose

---

## Development Workflow

### Local Development
```bash
# Install dependencies
pip install -r requirements.txt

# Preprocess data
python astram/scripts/preprocess_data.py
python astram/backend/precompute_lookups.py

# Run server
python -m uvicorn astram.backend.app:app --reload --port 5000
```

### Docker Development
```bash
# Build
docker-compose build

# Run
docker-compose up -d

# Logs
docker-compose logs -f

# Stop
docker-compose down
```

---

## Clean Codebase

**Removed unnecessary files:**
- ❌ simple_app.py (simplified version)
- ❌ astram/frontend/simple/ (old frontend)
- ❌ docker-push.sh (instructions now in docs)

**Organized structure:**
- ✅ Scripts in `astram/scripts/`
- ✅ All docs in root
- ✅ Clean separation of concerns

---

**ASTRAM AI** - Clean, production-ready codebase
*Flipkart Grid 2.0, Round 2 Submission*
