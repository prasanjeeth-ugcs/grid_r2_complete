# ASTRAM AI — Bengaluru Traffic Operational Intelligence Platform

> **Version 2.0 — Proactive Event Forecasting & Management**
>
> An AI-powered traffic intelligence platform that forecasts planned event impact 24-72h in advance, provides real-time weather-based risk alerts, generates diversion routes, and continuously learns from post-event outcomes for Bengaluru's traffic management authorities.

**Flipkart Grid 2.0, Round 2 Submission**
**Problem Statement**: Event-Driven Congestion (Planned & Unplanned) Operational Challenge

---

## Table of Contents

- [Overview](#overview)
- [The Three Questions](#the-three-questions)
- [System Architecture](#system-architecture)
- [Technology Stack](#technology-stack)
- [Data Layer](#data-layer)
- [Backend Engines](#backend-engines)
  - [Feature Engineering Pipeline](#1-feature-engineering-pipeline)
  - [Impact Engine](#2-impact-engine)
  - [Risk Class Engine](#3-risk-class-engine)
  - [Confidence Engine](#4-confidence-engine)
  - [Historical Evidence Engine](#5-historical-evidence-engine)
  - [Resource Planning Engine](#6-resource-planning-engine)
  - [Corridor DNA Engine](#7-corridor-dna-engine)
  - [Corridor Stress Index](#8-corridor-stress-index)
  - [Operational Risk Window](#9-operational-risk-window)
  - [Shift Briefing Engine](#10-shift-briefing-engine)
  - [Transit Chain Flag](#11-transit-chain-flag)
  - [Formula vs AI Engine](#12-formula-vs-ai-engine)
- [API Endpoints](#api-endpoints)
- [Frontend Pages](#frontend-pages)
  - [Page 1: Command Center](#page-1-command-center)
  - [Page 2: Incident Response Copilot](#page-2-incident-response-copilot)
  - [Page 3: Corridor Intelligence](#page-3-corridor-intelligence)
- [Project Structure](#project-structure)
- [Setup & Installation](#setup--installation)
- [Demo Scenario](#demo-scenario)
- [Model Details](#model-details)
- [Precomputed Lookup Tables](#precomputed-lookup-tables)
- [Design Decisions](#design-decisions)

---

## Overview

ASTRAM (Advanced Smart Traffic Response And Management) is a **traffic operational intelligence platform** built for Bengaluru's traffic management authorities. It processes **8,170 historical traffic incidents** collected across Bengaluru's 21 major corridors and 54 police station jurisdictions to deliver real-time incident impact assessment, resource recommendations, and operational pattern intelligence.

The system is **not** a forecasting tool — it does not predict future incidents. Instead, it answers operational questions: *"How bad is this incident?"*, *"What resources do we need?"*, and *"What has historically happened in similar situations?"*.

### Key Numbers

| Metric | Value |
|--------|-------|
| Historical incidents | 8,173 |
| Planned events database | 55 events |
| Corridors monitored | 21 |
| Police stations | 54 |
| Cause categories | 14 |
| Vehicle types | 10 |
| Risk window slots | 168 (7 days × 24 hours) |
| Incident Model R² | 0.9522 |
| Model Features | 36 (enhanced) |
| API Endpoints | 32 |

---

## The Three Questions

The entire system is designed to answer exactly **three operational questions**:

### Q1: How severe is this incident?
**Answered by: Impact Engine (CatBoost Regressor)**

Given an incident's characteristics (cause, corridor, time, vehicle type, closure status), the system predicts an **Impact Score (0–100)** and classifies it into a **Risk Class** (Low / Medium / High / Critical).

### Q2: What should we do about it?
**Answered by: Resource Planning Engine**

Based on the risk class, cause type, and corridor tier, the system generates a **resource deployment timeline** with specific phases (0–15 min, 15–30 min, 30–60 min) and an **estimated resolution time range**.

### Q3: What does Bengaluru's historical behavior tell us?
**Answered by: Operational Intelligence Layer**

The system searches for **similar historical incidents** and provides confidence levels, critical rates, corridor DNA profiles, stress indices, and operational risk windows — all derived from real Bengaluru traffic data.

---

## System Architecture

### Complete System Diagram

```
┌─────────────────────────────────────────────────────────────────────────┐
│                          ASTRAM AI Platform                              │
│                  Proactive Traffic Management System                     │
└─────────────────────────────────────────────────────────────────────────┘
                                    │
        ┌───────────────────────────┼───────────────────────────┐
        │                           │                           │
        ▼                           ▼                           ▼
┌─────────────┐          ┌──────────────────┐        ┌─────────────────┐
│  Data Layer │          │  ML Model Layer  │        │  Real-Time Layer│
└─────────────┘          └──────────────────┘        └─────────────────┘
        │                           │                           │
        ├─ 8,173 Incidents          ├─ CatBoost Model           ├─ Weather API
        ├─ 21 Corridors             │  (36 features)            ├─ Incident Sim
        ├─ Enhanced Features        │  (R²=0.95)                └─ System Pulse
        └─ 76 Total Columns         └─ Precomputed Lookups
                │                           │                           │
                └───────────────┬───────────┴───────────────┬───────────┘
                                │                           │
                                ▼                           ▼
                    ┌─────────────────────┐      ┌──────────────────────┐
                    │  Backend Engines (9)│      │   API Layer (28 EP)  │
                    └─────────────────────┘      └──────────────────────┘
                                │                           │
        ┌───────────────────────┼───────────────────────────┼────────────┐
        │           │            │            │              │            │
        ▼           ▼            ▼            ▼              ▼            ▼
   ┌────────┐  ┌────────┐  ┌─────────┐  ┌────────┐   ┌──────────┐  ┌─────────┐
   │ Model  │  │Forecast│  │ Weather │  │Resource│   │Diversion │  │Feedback │
   │ Engine │  │ Engine │  │ Engine  │  │ Engine │   │  Engine  │  │ Engine  │
   └────────┘  └────────┘  └─────────┘  └────────┘   └──────────┘  └─────────┘
        │           │            │            │              │            │
        └───────────┴────────────┴────────────┴──────────────┴────────────┘
                                         │
                                         ▼
                            ┌──────────────────────────┐
                            │   Frontend Dashboard      │
                            │  ┌────────────────────┐  │
                            │  │ Page 1: Command    │  │
                            │  │         Center     │  │
                            │  ├────────────────────┤  │
                            │  │ Page 2: Incident   │  │
                            │  │         Copilot    │  │
                            │  ├────────────────────┤  │
                            │  │ Page 3: Corridor   │  │
                            │  │         Intel      │  │
                            │  └────────────────────┘  │
                            └──────────────────────────┘
                                         │
                                         ▼
                              ┌────────────────────┐
                              │  Traffic Officers  │
                              │   Decision Making  │
                              └────────────────────┘
```

### Inference Pipeline (Real-Time Incident)

```
User Input (6 fields)
    │
    ├─ Cause: tree_fall
    ├─ Corridor: Bellary Road 1
    ├─ Closure: true
    ├─ Vehicle: Others
    ├─ Hour: 5
    └─ Weekday: Thursday
            │
            ▼
┌───────────────────────────┐
│  Feature Engineering (26) │
│  ─────────────────────── │
│  • hour_sin/cos           │
│  • weekday_sin/cos        │
│  • corridor_tier = 1      │
│  • station_event_count    │
│  • is_night = true        │
│  • requires_closure = 1   │
│  • ... 20 more features   │
└───────────────────────────┘
            │
            ▼
┌───────────────────────────┐
│   CatBoost Model (240KB)  │
│   ───────────────────     │
│   1000 iterations         │
│   depth=6, lr=0.05        │
│   L2_reg=3                │
└───────────────────────────┘
            │
            ▼
    Raw Score: 85.3
            │
            ▼
┌───────────────────────────┐
│    Score Blending         │
│  ─────────────────────    │
│  Find 14 similar cases    │
│  Historical avg: 90.6     │
│  Blend: 0.4×85.3 + 0.6×90.6│
│  = 88.5                   │
└───────────────────────────┘
            │
            ▼
    Impact Score: 88
    Risk Class: Critical
            │
            ├─────────────────────────────┬─────────────────┬──────────────┐
            │                             │                 │              │
            ▼                             ▼                 ▼              ▼
  ┌─────────────────┐        ┌──────────────────┐   ┌──────────┐  ┌──────────┐
  │ Resource Engine │        │Historical Engine │   │ Corridor │  │ Weather  │
  │ ─────────────── │        │ ──────────────── │   │   DNA    │  │   Risk   │
  │ • 6 officers    │        │ • 14 similar     │   │ ──────── │  │ ──────── │
  │ • 12 barricades │        │ • 100% critical  │   │ Tier 1   │  │ No rain  │
  │ • BBMP crew     │        │ • High confidence│   │ 610 inc. │  │ Low risk │
  │ • Timeline      │        │ • Score dist.    │   │ Stress79 │  │          │
  │ • Placement     │        │                  │   │          │  │          │
  └─────────────────┘        └──────────────────┘   └──────────┘  └──────────┘
            │                             │                 │              │
            └─────────────────────────────┴─────────────────┴──────────────┘
                                         │
                                         ▼
                              ┌──────────────────────┐
                              │   JSON Response      │
                              │  {                   │
                              │    impact: 88,       │
                              │    risk: "Critical", │
                              │    resources: {...}, │
                              │    historical: {...},│
                              │    corridor: {...}   │
                              │  }                   │
                              └──────────────────────┘
                                         │
                                         ▼
                              ┌──────────────────────┐
                              │  Frontend Rendering  │
                              │  • Impact ring       │
                              │  • Resource timeline │
                              │  • Barricade map     │
                              │  • Historical charts │
                              └──────────────────────┘
```

### Event Forecasting Pipeline (Proactive)

```
Planned Event Database
    │
    ├─ Diwali Festival
    ├─ Mysore Road
    ├─ 50,000 expected crowd
    ├─ Nov 1, 6 PM
    └─ Closure required
            │
            ▼
┌───────────────────────────┐
│  Feature Engineering (17) │
│  ─────────────────────── │
│  • event_type = festival  │
│  • crowd_log = 10.82      │
│  • closure_required = 1   │
│  • corridor_tier = 1      │
│  • hour_sin/cos           │
│  • ... 12 more features   │
└───────────────────────────┘
            │
            ▼
┌───────────────────────────┐
│ Impact Model (141KB)      │
│ ─────────────────────     │
│ Trained on 8,057 samples  │
│ (Method 6 - Best)         │
│ R² = 0.9522               │
└───────────────────────────┘
            │
            ▼
    Predicted Impact: 87.5
    Risk Class: Critical
    Confidence: High
            │
            ▼
┌───────────────────────────┐
│ Proactive Timeline        │
│ ───────────────────────   │
│ T-48h: Public advisory    │
│ T-24h: Pre-position       │
│ T-2h:  Deploy officers    │
│ T-1h:  Activate diversion │
│ T-0:   Full closure       │
└───────────────────────────┘
            │
            ▼
    Resource Deployment
    24-72h BEFORE Event
```

### Data Flow

1. **Startup**: Load `model_ready.parquet` and `catboost_best.cbm`. Load all precomputed JSON lookup tables.
2. **Incident Input**: User provides cause, corridor, hour, weekday, vehicle type, closure status.
3. **Feature Pipeline**: Transforms input into a 26-dimensional feature vector matching the training schema.
4. **Impact Engine**: CatBoost model predicts a raw impact score.
5. **Score Blending**: Raw model score is blended with historical average from similar incidents using a weighted formula.
6. **Risk Classification**: Blended score is classified into Low/Medium/High/Critical.
7. **Parallel Engines**: Resource timeline, historical evidence, corridor DNA, confidence, and transit chain flag are computed simultaneously.
8. **Response Assembly**: All engine outputs are combined into a single JSON response served to the frontend.

---

## Technology Stack

### Backend

| Component | Technology | Purpose |
|-----------|------------|---------|
| **Web Framework** | [FastAPI](https://fastapi.tiangolo.com/) 0.115+ | Async REST API with automatic OpenAPI docs |
| **ASGI Server** | [Uvicorn](https://www.uvicorn.org/) | High-performance async server |
| **ML Model** | [CatBoost](https://catboost.ai/) Regressor | Gradient boosting for impact score prediction |
| **Data Processing** | [Pandas](https://pandas.pydata.org/) + [NumPy](https://numpy.org/) | Parquet I/O, feature engineering, aggregation |
| **Data Format** | [Apache Parquet](https://parquet.apache.org/) via PyArrow | Columnar storage for fast reads |
| **Validation** | [Pydantic](https://docs.pydantic.dev/) | Request/response schema validation |
| **Language** | Python 3.10+ | Core language |

### Frontend

| Component | Technology | Purpose |
|-----------|------------|---------|
| **Structure** | HTML5 semantic markup | 3-page SPA with client-side routing |
| **Styling** | Vanilla CSS with Custom Properties | Premium dark theme, glassmorphism, animations |
| **Logic** | Vanilla JavaScript (ES6+) | All page logic, API integration, rendering |
| **Charts** | [Chart.js](https://www.chartjs.org/) | Bubble, bar, scatter, and grouped charts |
| **Maps** | [Leaflet](https://leafletjs.com/) + CARTO dark tiles | Interactive incident map of Bengaluru |
| **Typography** | [Inter](https://fonts.google.com/specimen/Inter) + [JetBrains Mono](https://www.jetbrains.com/lp/mono/) | UI text + monospaced data values |

### Data Pipeline (One-time)

| Component | Technology | Purpose |
|-----------|------------|---------|
| **Feature Engineering** | scikit-learn (DBSCAN, LabelEncoder, PCA) | Geo clustering, encoding |
| **Text Embeddings** | sentence-transformers (MiniLM-L12-v2) | Description embeddings (32-dim PCA) |
| **Model Training** | CatBoost with Optuna hyperparameter tuning | Impact score regression |

---

## Data Layer

### Source Data

The raw data is **8,170 anonymized traffic incident records** from Bengaluru's ASTRAM traffic management system, covering approximately 5 months of operations. Each record contains:

- **Incident metadata**: cause, type (planned/unplanned), priority, status
- **Location**: latitude, longitude, corridor, police station, junction, zone
- **Temporal**: start time, end time, created/modified/closed/resolved timestamps
- **Vehicle**: type (BMTC Bus, Heavy Vehicle, Private Car, etc.)
- **Operational**: road closure required, authenticated status
- **Text**: incident description (Kannada/English)

### model_ready.parquet (Training Data)

The feature pipeline transforms raw CSV into a **66-column parquet file** containing:

| Category | Columns | Details |
|----------|---------|---------|
| **Identifiers** | 1 | `id` |
| **Raw Categoricals** | 5 | `event_cause`, `event_type`, `corridor`, `veh_type`, `police_station` |
| **Encoded Categoricals** | 5 | Label-encoded versions for ML |
| **Spatial** | 6 | `latitude`, `longitude`, `lat_bin`, `lon_bin`, `geo_cluster`, `corridor_tier` |
| **Temporal** | 11 | `hour`, `weekday`, `month`, cyclical encodings (sin/cos), `is_weekend`, `is_night` |
| **Boolean** | 2 | `requires_road_closure`, `authenticated` |
| **Frequency** | 3 | `station_event_count`, `junction_event_count`, `corridor_event_count` |
| **Embeddings** | 32 | PCA-reduced MiniLM description embeddings (`desc_emb_0` to `desc_emb_31`) |
| **Targets** | 2 | `impact_score` (continuous 0–100), `impact_class` (4-class) |

### Impact Score Formula (Training Label)

The impact score used to train the model is computed from **three outcome-based components**:

```
Impact Score = Closure (0 or 50) + Corridor Tier (0-30) + Duration (0-20)
```

| Component | Weight | Logic |
|-----------|--------|-------|
| **Road Closure** | 50 pts | Binary: did the road close? |
| **Corridor Tier** | 0–30 pts | Tier 1 = 30, Tier 2 = 22, Tier 3 = 14, Non-corridor = 0 |
| **Duration** | 0–20 pts | Post-event resolution time: >6h = 20, >2h = 14, >1h = 7 |

> **Design Decision**: `event_cause` and `priority` are intentionally **excluded** from the label formula. This forces the model to *discover* why certain causes lead to high scores from the features, rather than memorizing a deterministic rule.

---

## Backend Engines

### 1. Feature Engineering Pipeline

**File**: [model_engine.py](astram/backend/model_engine.py) → `build_feature_vector()`

Transforms 6 user inputs into a 26-dimensional feature vector matching the exact training schema:

| Step | Input | Output |
|------|-------|--------|
| **Step 1** | Corridor name | `corridor_tier` (1/2/3/0), `is_corridor` |
| **Step 2** | Hour | `hour_sin`, `hour_cos` via `sin(2πh/24)`, `cos(2πh/24)` |
| **Step 3** | Hour | `rush_hour_flag` (7–10, 16–20), `night_flag` (22–5) |
| **Step 4** | (internal) | `station_event_count` from historical frequency lookup |
| **Step 5** | Corridor | `corridor_event_count` from historical frequency lookup |
| **Step 6** | (internal) | `geo_cluster`, `lat_bin`, `lon_bin` defaults |

#### Corridor Tier Mapping

```
Tier 1 (Critical Arterials):  Mysore Road, Bellary Road 1, Tumkur Road, Bellary Road 2, Hosur Road
Tier 2 (Major Corridors):     ORR North 1, Old Madras Road, Magadi Road, ORR East 1, ORR North 2,
                               Bannerghatta Road, ORR East 2, West of Chord Road
Tier 3 (Secondary):           ORR West 1, ORR South 1, Kanakapura Road, Sarjapur Road, Hennur Road,
                               Airport New South Road, ORR West 2, ORR South 2
Tier 0:                        Non-corridor (local roads)
```

---

### 2. Impact Engine

**File**: [model_engine.py](astram/backend/model_engine.py) → `predict_impact()`

- **Model**: CatBoost Regressor (`catboost_best.cbm`, 240 KB frozen model)
- **Input**: 26-feature vector from the Feature Pipeline
- **Output**: Raw impact score (0–100 range)
- **No retraining**: Model is frozen. Same weights at every prediction.

The raw model output is then **blended** with historical context in [app.py](astram/backend/app.py):

```python
# If many similar historical incidents exist, blend with their average
if similar_count > 10:
    blended = model_score × 0.4 + historical_average × 0.6
elif similar_count > 5:
    blended = model_score × 0.5 + historical_average × 0.5
else:
    blended = model_score

# Rule-based adjustments
if closure:     blended += 15
if tier == 1:   blended += 10
if tier == 2:   blended += 5
```

---

### 3. Risk Class Engine

**File**: [model_engine.py](astram/backend/model_engine.py) → `score_to_class()`

Converts the blended impact score into a risk classification:

| Score Range | Risk Class | Color |
|-------------|------------|-------|
| 0 – 25 | **Low** | 🟢 Green |
| 25 – 50 | **Medium** | 🟡 Amber |
| 50 – 75 | **High** | 🟠 Orange |
| 75 – 100 | **Critical** | 🔴 Red |

---

### 4. Confidence Engine

**File**: [historical_engine.py](astram/backend/historical_engine.py) → `compute_confidence()`

Measures **prediction trust** by counting how many historical incidents match the current scenario's key characteristics.

**Matching criteria**: `cause` + `corridor_tier` + `closure`

| Matching Count | Confidence Level |
|----------------|-----------------|
| ≥ 30 | **High** — Strong historical basis |
| 10 – 29 | **Medium** — Moderate evidence |
| < 10 | **Low** — Limited historical data |

---

### 5. Historical Evidence Engine

**File**: [historical_engine.py](astram/backend/historical_engine.py) → `find_similar_incidents()`

Searches the historical index for incidents with matching characteristics.

**Input**: cause, corridor_tier, closure
**Output**:

| Field | Description |
|-------|-------------|
| `count` | Number of similar incidents found |
| `critical_rate` | Percentage that were Critical |
| `average_score` | Mean impact score |
| `score_distribution` | Count per risk class {Low, Medium, High, Critical} |
| `top_examples` | Up to 5 sample incidents with details |

**Fallback logic**:
1. Try: `cause + corridor_tier + closure` (most specific)
2. If < 5 results: relax to `cause + corridor_tier`
3. If < 3 results: relax to `cause` only

---

### 6. Resource Planning Engine

**File**: [resource_engine.py](astram/backend/resource_engine.py) → `recommend()`

**No ML**. Pure rule-based engine.

**Input**: cause, impact_class, corridor_tier, vehicle_type

**Output** — Timeline format:

```
Tree Fall:
  0–15 min:  Police Units, Area Barricading
  15–30 min: BBMP Tree Crew
  30–60 min: Barricades, Traffic Diversion

Estimated Resolution: Median 1.2h, Range 0.4h–4.0h
```

**Resource scaling**: Resources are multiplied based on risk class and corridor tier:

| Factor | Multiplier |
|--------|-----------|
| Critical risk | 2.0× |
| High risk | 1.5× |
| Tier 1 corridor | 1.5× |
| Tier 2 corridor | 1.25× |

**Resolution estimates** are always displayed as a **range**, never a single number:

| Cause | Median | Range |
|-------|--------|-------|
| Vehicle Breakdown | 0.5h | 0.5h – 1.0h |
| Tree Fall | 1.2h | 0.4h – 4.0h |
| Accident | 2.0h | 1.0h – 3.0h |
| Water Logging | 3.0h | 2.0h – 8.0h |
| Construction | 12.0h | 4.0h – 48.0h |
| Protest | 5.0h | 2.0h – 12.0h |

---

### 7. Corridor DNA Engine

**File**: [corridor_engine.py](astram/backend/corridor_engine.py) → `get_corridor_dna()`

Precomputed profile for each of the 21 corridors:

| Field | Example (Bellary Road 1) |
|-------|-------------------------|
| Tier | 1 |
| Total Incidents | 610 |
| Dominant Cause | Vehicle Breakdown |
| Peak Hour | 4 AM |
| Closure Rate | 5.4% |
| Critical Rate | 5.4% |
| Station | Sadashivanagar |
| Stress Index | 79.1 |

---

### 8. Corridor Stress Index

**File**: [corridor_engine.py](astram/backend/corridor_engine.py) → `get_stress_index()`

Signature metric combining three normalized dimensions:

```
Stress Index = 0.4 × normalized_frequency
             + 0.4 × normalized_avg_impact
             + 0.2 × normalized_closure_rate

Scale: 0–100
```

Each dimension is normalized to 0–1 relative to the highest corridor, then combined with the above weights and scaled to 0–100.

**Top corridors by stress**:

| Corridor | Stress Index |
|----------|-------------|
| Mysore Road | ~98.7 |
| Bellary Road 1 | ~79.1 |
| Tumkur Road | ~66.3 |

Used in: **Page 1** (stress bar) and **Page 3** (leaderboard chart).

---

### 9. Operational Risk Window

**File**: [corridor_engine.py](astram/backend/corridor_engine.py) → `get_risk_window()`

Precomputed grid of **168 slots** (7 weekdays × 24 hours), each containing:

| Field | Description |
|-------|-------------|
| `event_count` | Historical incidents in that slot |
| `critical_rate` | % that were Critical |
| `avg_impact` | Mean impact score |
| `top_corridors` | Top 3 corridors by incident count |
| `top_causes` | Top 3 causes by incident count |

**No forecasting language** — this is purely historical pattern data.

**Example**: Thursday 5 AM → 467 incidents, Top Corridor: Bellary Road 1, Top Cause: Vehicle Breakdown, Critical Rate: 6.6%

---

### 10. Shift Briefing Engine

**File**: [corridor_engine.py](astram/backend/corridor_engine.py) → `get_shift_briefing()`

Aggregates risk window data into three operational shifts:

| Shift | Hours |
|-------|-------|
| **Morning** | 06:00 – 14:00 |
| **Evening** | 14:00 – 22:00 |
| **Night** | 22:00 – 06:00 |

**Output**: stress_level (High/Elevated/Normal), total_events, critical_rate, top_corridors, top_causes.

---

### 11. Transit Chain Flag

**File**: [historical_engine.py](astram/backend/historical_engine.py) → `check_transit_chain()`

A unique detection feature that triggers when:

```
vehicle_breakdown  AND  (BMTC OR KSRTC bus)  AND  Tier 1 corridor
```

**Output when triggered**:
- Bus type (BMTC/KSRTC)
- Historical case count (530 cases in data)
- Estimated cumulative passenger disruption
- Advisory: depot coordination recommended

---

### 12. Formula vs AI Engine

**File**: [model_engine.py](astram/backend/model_engine.py) → `compute_operational_baseline()`

The most important **storytelling component**. Splits the prediction explanation into two parts:

#### Operational Baseline (Deterministic)

A formula any human could compute:

```
Road Closure     +35
Tier 1 Corridor  +30
Cause Severity   +18  (tree_fall)
Night Hours       -5
─────────────────────
Baseline          78
```

#### Historical Pattern Intelligence

**NOT fake SHAP values**. Shows real historical data:

```
14 Similar Historical Incidents
Average Historical Impact: 90.6
AI Predicted: 88

"The AI learned that incidents with these characteristics
historically evolve into high-severity events."
```

---

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/api/predict` | Full incident analysis — all engines combined |
| `GET` | `/api/city-pulse` | Command Center data: KPIs + map + feed + stress bar |
| `GET` | `/api/risk-window` | 168-slot operational risk window grid |
| `GET` | `/api/shift-briefing` | Current shift briefing |
| `GET` | `/api/corridor/{name}` | Single corridor DNA profile |
| `POST` | `/api/similar-incidents` | Historical similarity search |
| `GET` | `/api/station-intelligence` | All 54 stations with stats |
| `GET` | `/api/corridor-intelligence` | Page 3 chart datasets |
| `GET` | `/api/metadata` | Available options for frontend selectors |

### `/api/predict` — Full Request/Response

**Request**:
```json
{
    "cause": "tree_fall",
    "corridor": "Bellary Road 1",
    "closure": true,
    "vehicle_type": "Others",
    "hour": 5,
    "weekday": 3
}
```

**Response** (key fields):
```json
{
    "impact_score": 88.0,
    "risk_class": "Critical",
    "confidence": { "level": "Medium", "matching_count": 14 },
    "resource_plan": {
        "timeline": [...],
        "resources": { "police_units": 6, "barricades": 12, "diversion_required": true },
        "resolution": { "median": "1.2h", "range": "0.4h–4.0h" }
    },
    "historical_evidence": {
        "count": 14,
        "critical_rate": 100.0,
        "average_score": 90.6,
        "score_distribution": { "Low": 0, "Medium": 0, "High": 0, "Critical": 14 }
    },
    "formula_vs_ai": {
        "operational_baseline": { "baseline_score": 78, "components": [...] },
        "historical_pattern": { "similar_count": 14, "average_historical_impact": 90.6, "narrative": "..." }
    },
    "corridor_dna": { "corridor": "Bellary Road 1", "total_incidents": 610, "stress_index": 79.1, ... },
    "transit_chain": { "triggered": false }
}
```

---

## Frontend Pages

### Page 1: Command Center

City-wide operational overview with 6 sections:

| Section | Component | Data Source |
|---------|-----------|-------------|
| **KPI Strip** | 4 stat cards (total incidents, critical, closures, avg impact) | `/api/city-pulse` |
| **Corridor Stress Bar** | Animated horizontal bar chart, sorted by stress index | `/api/city-pulse` → `stress_bar` |
| **Operational Risk Window** | 168-cell heatmap (weekday × hour), current slot highlighted | `/api/risk-window` |
| **Shift Briefing** | Current shift panel (Morning/Evening/Night) with stress level | `/api/shift-briefing` |
| **Historical Feed** | Scrollable incident list, clickable → navigates to Page 2 | `/api/city-pulse` → `feed` |
| **Incident Map** | Leaflet map with CARTO dark tiles, color-coded by risk class | `/api/city-pulse` → `map_events` |

### Page 2: Incident Response Copilot

The **main demo page** — interactive incident analysis with 8 panels:

| Panel | Description |
|-------|-------------|
| **A: Impact Assessment** | Animated score ring (0–100), risk class badge, confidence indicator |
| **B: Resolution Estimate** | Median + range display (never single number) |
| **C: Resource Timeline** | Visual phase-based timeline (0–15 min → 15–30 min → 30–60 min) |
| **D: Historical Evidence** | Similar count, critical rate, avg score, score distribution bar |
| **E: Formula vs AI** | Split panel: operational baseline formula vs AI narrative |
| **F: Corridor DNA** | 6-stat mini-profile of selected corridor (conditional — hidden for Non-corridor) |
| **G: Transit Chain Flag** | Red alert banner (conditional — only for BMTC/KSRTC + Tier 1 + breakdown) |
| **H: What-If Toggle** | Toggle closure ON/OFF, shows score delta and class change |

### Page 3: Corridor Intelligence

Answers 5 strategic questions:

| Question | Visualization | Chart Type |
|----------|--------------|------------|
| Where should resources be pre-positioned? | Corridor × Hour incident density | Bubble chart |
| Which causes create closures? | Closure rate by cause type | Horizontal bar |
| Which corridors create the most burden? | Stress Index leaderboard | Horizontal bar |
| Which stations are overloaded? | Event count vs avg impact scatter | Scatter (Halasuru Gate highlighted) |
| Fleet demand intelligence | Tow trucks/day + officers/day per corridor | Grouped bar |

---

## Project Structure

```
astram/
├── backend/
│   ├── __init__.py
│   ├── app.py                    # FastAPI application (9 endpoints)
│   ├── model_engine.py           # Feature Pipeline + Impact Engine + Risk Class + Formula vs AI
│   ├── historical_engine.py      # Confidence + Historical Evidence + Transit Chain
│   ├── resource_engine.py        # Resource Timeline + Resolution Estimates
│   ├── corridor_engine.py        # Corridor DNA + Stress Index + Risk Window + Shift Briefing + Stations
│   ├── precompute_lookups.py     # One-time script to generate lookup tables
│   └── lookup_tables/
│       ├── corridor_dna.json         # 21 corridor profiles
│       ├── stress_index.json         # Corridor stress scores
│       ├── risk_window.json          # 168 weekday×hour slots
│       ├── station_intelligence.json # 54 station profiles
│       ├── resource_mapping.json     # 14 cause type → timeline + resolution
│       └── historical_index.parquet  # 8,170 records for similarity search
├── data/
│   ├── model_ready.parquet       # 8,170 × 66 training/inference dataset
│   └── raw_events.csv            # Original anonymized CSV
├── models/
│   └── catboost_best.cbm         # Frozen CatBoost model (240 KB)
├── frontend/
│   ├── index.html                # 3-page SPA structure
│   ├── css/
│   │   └── styles.css            # Premium dark theme design system
│   ├── js/
│   │   └── app.js                # All page logic, charts, renderers
│   └── assets/
├── requirements.txt              # Python dependencies
└── run.bat                       # Windows startup script
```

---

## Setup & Installation

### Prerequisites

- Python 3.10 or higher
- pip package manager

### Install Dependencies

```bash
cd astram
pip install -r requirements.txt
```

Required packages: `fastapi`, `uvicorn[standard]`, `pandas`, `numpy`, `catboost`, `pyarrow`, `pydantic`

### Generate Lookup Tables (One-time)

```bash
python -X utf8 backend/precompute_lookups.py
```

This reads `data/model_ready.parquet` and generates 6 JSON lookup files + 1 parquet index in `backend/lookup_tables/`.

### Start the Server

```bash
# Option 1: Direct
cd astram
python -m uvicorn backend.app:app --host 0.0.0.0 --port 5000

# Option 2: Batch file (Windows)
run.bat
```

### Access the Dashboard

Open **http://localhost:5000** in your browser.

---

## Demo Scenario

The canonical demo follows this exact script:

### Setup
- **When**: Thursday, 5:30 AM
- **What**: Tree Fall
- **Where**: Bellary Road 1
- **Road Closure**: Yes

### Expected Flow

```
1. Impact Score: 88 → Critical
2. 14 Similar Historical Incidents
3. Historical Average Impact: 90.6
4. Operational Baseline: 78 (Road Closure +35, Tier 1 +30, Cause +18, Night -5)
5. Resource Timeline: Police → BBMP Crew → Barricades/Diversion
6. Resolution: Median 1.2h, Range 0.4h–4.0h
7. Corridor DNA: 610 incidents, Stress 79.1

What-If Toggle (Closure OFF):
8. Score drops to 65 → High (Critical → High)

Navigate to Page 1:
9. Risk Window shows Thursday 5AM slot highlighted
10. Bellary Road 1 appears in stress bar

Navigate to Page 3:
11. Corridor Intelligence shows full analytical view
```

### Transit Chain Demo
- Change to: Vehicle Breakdown + BMTC Bus + Bellary Road 1
- Transit Chain Flag triggers: 530 historical cases, depot coordination advised

---

## Model Details

### CatBoost Regressor

| Parameter | Value |
|-----------|-------|
| Model type | CatBoostRegressor |
| File | `models/catboost_final_best.cbm` (141 KB) |
| Status | **Production Ready** — Method 6 |
| Features | 36 numeric features |
| Target | `impact_score` (continuous, 0–100) |
| R² Score | 0.9522 |
| MAE | 3.241 |
| Train-Test Gap | 0.39% (excellent) |

### Feature Importance (Training)

The model learned that the most important features are:
1. `requires_road_closure` — Binary closure flag
2. `corridor_tier` — Corridor importance level
3. `corridor_event_count` — Historical incident frequency
4. `hour_sin` / `hour_cos` — Time of day (cyclical)
5. `event_cause_encoded` — Type of incident
6. `station_event_count` — Station-level historical load

### Why Score Blending?

The raw CatBoost model predictions cluster in the 0–50 range due to the training distribution (mean score ~22). To produce more operationally meaningful scores:

1. We blend the model output with the **historical average** from similar incidents
2. We add **rule-based adjustments** for closure (+15), tier (+10/+5), and cause severity
3. This produces scores that span the full 0–100 range and align with operational intuition

---

## Precomputed Lookup Tables

All lookup tables are generated once by `precompute_lookups.py` and loaded into memory at server startup:

| Table | Records | Size | Purpose |
|-------|---------|------|---------|
| `corridor_dna.json` | 21 | ~4 KB | Per-corridor profiles |
| `stress_index.json` | 21 | ~2 KB | Stress scores |
| `risk_window.json` | 168 | ~45 KB | Weekday × hour grid |
| `station_intelligence.json` | 54 | ~12 KB | Per-station profiles |
| `resource_mapping.json` | 14 | ~5 KB | Cause → timeline mapping |
| `historical_index.parquet` | 8,170 | ~120 KB | Similarity search index |

---

## Design Decisions

### Why FastAPI over Flask?
- Async support for concurrent requests
- Automatic request validation with Pydantic
- Built-in OpenAPI/Swagger documentation at `/docs`
- Better performance for I/O-bound workloads

### Why No SHAP?
The V1.0 architecture explicitly forbids "fake SHAP" or "invented deltas". Instead, we use:
- **Operational Baseline**: A deterministic formula any human can verify
- **Historical Pattern Intelligence**: Real statistics from similar incidents
- This approach is more honest and operationally useful than feature attribution values

### Why Precomputed Lookups?
- Zero runtime computation for Corridor DNA, Stress Index, Risk Window, Station Intelligence
- Sub-millisecond response times for these endpoints
- Data only changes when the parquet is updated (not during runtime)

### Why Score Blending?
- The raw CatBoost model is accurate (R²=0.93) but its predictions cluster in the lower range
- Blending with historical averages anchors predictions to observed real-world outcomes
- Rule-based adjustments for closure/tier ensure operational factors have guaranteed impact

### Why No Forecasting?
- The architecture explicitly states: *"No forecasting language"*
- All data shown is historical — "this is what happened", not "this is what will happen"
- This avoids liability issues and overpromising prediction capabilities

---

## License

Internal use — Bengaluru Traffic Management Authority.

---

*Built with CatBoost, FastAPI, and historical intelligence from 8,170 real Bengaluru traffic incidents.*
