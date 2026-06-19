# ASTRAM AI V1.0 — Architecture Rebuild Walkthrough

Complete rebuild of the Bengaluru Traffic Operational Intelligence Platform per the Final Frozen Architecture V1.0 specification.

## What Changed

### Backend: Flask → FastAPI

| Old | New | Purpose |
|-----|-----|---------|
| Flask + flask-cors | FastAPI + uvicorn | Modern async API framework |
| `forecast_engine.py` | **Deleted** | No forecasting, only historical patterns |
| SHAP-based explanations | Formula vs AI narrative | Deterministic baseline + historical pattern intelligence |
| Old risk boundaries (20/40/65) | New boundaries (25/50/75) | V1.0 spec alignment |

### Files Created/Modified

#### Backend ([astram/backend/](file:///d:/round2%20-%20anti/astram/backend/))

| File | Action | Purpose |
|------|--------|---------|
| [app.py](file:///d:/round2%20-%20anti/astram/backend/app.py) | Rewritten | FastAPI with 7 endpoints |
| [model_engine.py](file:///d:/round2%20-%20anti/astram/backend/model_engine.py) | Rewritten | Feature Pipeline + Impact Engine + Risk Class + Formula vs AI |
| [historical_engine.py](file:///d:/round2%20-%20anti/astram/backend/historical_engine.py) | Rewritten | Confidence + Historical Evidence + Transit Chain Flag |
| [resource_engine.py](file:///d:/round2%20-%20anti/astram/backend/resource_engine.py) | Rewritten | Timeline format + Resolution ranges |
| [corridor_engine.py](file:///d:/round2%20-%20anti/astram/backend/corridor_engine.py) | **New** | Corridor DNA + Stress Index + Risk Window + Shift Briefing + Station Intel |
| [precompute_lookups.py](file:///d:/round2%20-%20anti/astram/backend/precompute_lookups.py) | **New** | Generates all 6 lookup tables |
| `forecast_engine.py` | **Deleted** | Removed forecasting |

#### Lookup Tables ([astram/backend/lookup_tables/](file:///d:/round2%20-%20anti/astram/backend/lookup_tables/))

| File | Contents |
|------|----------|
| `corridor_dna.json` | 21 corridor profiles (tier, incidents, closure rate, dominant cause, stress index) |
| `stress_index.json` | Corridor stress scores (0.4×freq + 0.4×impact + 0.2×closure) |
| `risk_window.json` | 168 slots (7 weekdays × 24 hours) with event counts, critical rates |
| `station_intelligence.json` | 54 police stations with event counts, top causes |
| `resource_mapping.json` | 14 cause types with timelines and resolution estimates |
| `historical_index.parquet` | 8,170 records for similarity search |

#### Frontend ([astram/frontend/](file:///d:/round2%20-%20anti/astram/frontend/))

| File | Changes |
|------|---------|
| [index.html](file:///d:/round2%20-%20anti/astram/frontend/index.html) | 3 full pages with all panels per spec |
| [css/styles.css](file:///d:/round2%20-%20anti/astram/frontend/css/styles.css) | Premium dark theme, glassmorphism, animations |
| [js/app.js](file:///d:/round2%20-%20anti/astram/frontend/js/app.js) | All page logic, charts, renderers |

---

## API Endpoints

| Method | Endpoint | Purpose |
|--------|----------|---------|
| `POST` | `/api/predict` | Full incident analysis (all engines combined) |
| `GET` | `/api/city-pulse` | KPIs + map events + feed + stress bar |
| `GET` | `/api/risk-window` | 168-slot operational risk window |
| `GET` | `/api/shift-briefing` | Current shift (Morning/Evening/Night) |
| `GET` | `/api/corridor/{name}` | Single corridor DNA |
| `POST` | `/api/similar-incidents` | Historical similarity search |
| `GET` | `/api/station-intelligence` | All 54 stations |
| `GET` | `/api/corridor-intelligence` | Page 3 chart data |
| `GET` | `/api/metadata` | Frontend selector options |

---

## 3 Pages Implemented

### Page 1: Command Center
1. **KPI Strip** — Total incidents, critical count, road closures, avg impact
2. **Corridor Stress Bar** — Animated horizontal bars sorted by stress index
3. **Operational Risk Window** — 168-cell heatmap with current-slot highlight
4. **Shift Briefing** — Morning/Evening/Night with stress level, top corridors/causes
5. **Historical Feed** — Clickable incidents → auto-populate Page 2
6. **Incident Map** — Leaflet dark map with color-coded markers

### Page 2: Incident Response Copilot
- **Panel A**: Impact score ring + risk class badge + confidence indicator
- **Panel B**: Resolution estimate (median + range, never single number)
- **Panel C**: Resource timeline (phase-based visual timeline)
- **Panel D**: Historical evidence (count, critical rate, avg score, distribution bar)
- **Panel E**: Formula vs AI (operational baseline components vs AI narrative)
- **Panel F**: Corridor DNA (6-stat grid for selected corridor)
- **Panel G**: Transit Chain Flag (conditional — BMTC/KSRTC + Tier 1 + breakdown)
- **Panel H**: What-If toggle (closure ON/OFF with delta display)

### Page 3: Corridor Intelligence
- **Q1**: Bubble heatmap (corridor × hour)
- **Q2**: Closure rate horizontal bar by cause
- **Q3**: Stress Index leaderboard (sorted bar chart)
- **Q4**: Station scatter (event count vs avg impact, Halasuru Gate highlighted)
- **Q5**: Fleet demand (tow trucks/day + officers/day per corridor)

---

## Verification Results

### Demo Scenario: Thursday 5:30 AM, Tree Fall, Bellary Road 1, Closure ON

| Metric | Expected | Actual |
|--------|----------|--------|
| Impact Score | 88 | **88.0** ✅ |
| Risk Class | Critical | **Critical** ✅ |
| Similar Incidents | 14 | **14** ✅ |
| Historical Avg | 90.6 | **90.6** ✅ |
| Operational Baseline | 78 | **78** ✅ |
| Confidence | Medium (14 matches) | **Medium** ✅ |

### What-If Toggle (Closure OFF)
| Metric | Expected | Actual |
|--------|----------|--------|
| Risk Class Change | Critical → High | **Critical → High** ✅ |
| Score | ~65 | **65.0** ✅ |

### Transit Chain Flag (BMTC Bus + Tier 1)
| Metric | Expected | Actual |
|--------|----------|--------|
| Triggered | True | **True** ✅ |
| Historical Cases | ~530 | **530** ✅ |

### All 7+ Endpoints
All returning HTTP 200 with correct data structures.

---

## How to Run

```bash
# 1. Precompute lookup tables (only needed once)
python -X utf8 astram/backend/precompute_lookups.py

# 2. Start the server
cd astram
python -m uvicorn backend.app:app --host 0.0.0.0 --port 5000

# 3. Open browser
# http://localhost:5000
```

Or use the batch file:
```bash
astram/run.bat
```
