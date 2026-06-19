# ASTRAM AI V1.0 — Complete Architecture Rebuild

Full rebuild of the ASTRAM platform per the **Final Frozen Architecture V1.0** specification. The system answers 3 questions:
1. **How severe is this incident?** → Impact Engine (CatBoost)
2. **What should we do about it?** → Resource Planning Engine  
3. **What does Bengaluru's history tell us?** → Operational Intelligence Layer

## Current State

The existing codebase in `d:\round2 - anti\astram\` has:
- **Flask** backend (switching to **FastAPI** per spec)
- **model_engine.py** with SHAP-based explanations (removing SHAP, switching to Formula vs AI narrative)
- **forecast_engine.py** (removing entirely — no forecasting, only historical patterns)
- **historical_engine.py** (basic similarity — needs full rebuild with proper matching logic)
- **resource_engine.py** (close to spec — needs timeline format)
- Parquet with 8,170 rows, 66 columns, 54 stations, frozen CatBoost model at `models/catboost_best.cbm`
- Frontend with 3 pages but missing: Corridor DNA, Stress Index, Risk Window, Shift Briefing, Transit Chain, Station Intelligence

> [!IMPORTANT]
> **Risk class boundaries are changing**: Old = `{0-20: Low, 20-40: Medium, 40-65: High, 65+: Critical}` → New = `{0-25: Low, 25-50: Medium, 50-75: High, 75+: Critical}`. This will affect all displays and the demo scenario.

> [!WARNING]  
> **The parquet has `impact_score` computed with old boundaries** (closure=50, tier=30, duration=20). The spec says scores go 0-100 but the current model's raw predictions are concentrated in the 0-50 range. We will use the frozen CatBoost model as-is and apply the new risk class boundaries to its output.

## Open Questions

> [!IMPORTANT]
> 1. **Demo scenario target**: The spec wants Thursday 5:30AM Tree Fall at Bellary Road 1 with closure → Impact Score **88**, Class **Critical**, **14 similar incidents**, historical avg **90.6**. The current model may not produce exactly 88. Should I keep the demo override logic (hardcode ~88 for this specific scenario) or let the model produce whatever it produces?
>
> 2. **Transit Chain Flag**: The spec mentions BMTC/KSRTC bus breakdown on Tier 1 → "530 historical cases". The actual data has ~4,896 vehicle breakdowns total. Should the 530 number be computed from actual data or hardcoded for demo?
>
> 3. **Station column**: The spec references `station` as a feature but the parquet has `police_station`. I'll map `police_station` → `station` in the lookup tables. Confirm?

---

## Proposed Changes

### Phase 1: Data Layer — Precomputed Lookup Tables

All lookup tables precomputed once from `model_ready.parquet` and saved as JSON. Loaded at startup.

#### [NEW] [precompute_lookups.py](file:///d:/round2%20-%20anti/astram/backend/precompute_lookups.py)

Script that reads `model_ready.parquet` and generates all lookup JSON files:

- **`corridor_dna.json`** — One entry per corridor: tier, total_incidents, closure_rate, critical_rate, dominant_cause, peak_hour, station, stress_index
- **`stress_index.json`** — One score per corridor: `0.4×norm_freq + 0.4×norm_avg_impact + 0.2×norm_closure_rate`, scale 0-100
- **`risk_window.json`** — 168 combinations (7 weekdays × 24 hours): event_count, critical_rate, top_corridors, top_causes, avg_impact
- **`station_intelligence.json`** — All 54 stations: event_count, top_causes, top_corridors, critical_rate, avg_impact
- **`resource_mapping.json`** — Rule engine: cause → timeline + estimated resolution
- **`historical_index.parquet`** — Similarity search index: cause, corridor_tier, closure, impact_score, impact_class

#### [NEW] [lookup_tables/](file:///d:/round2%20-%20anti/astram/backend/lookup_tables/) (directory)

Output directory for all 6 JSON files + 1 parquet.

---

### Phase 2: Backend Engines (FastAPI)

#### [DELETE] [forecast_engine.py](file:///d:/round2%20-%20anti/astram/backend/forecast_engine.py)

Removed entirely. No forecasting. Only historical patterns.

---

#### [MODIFY] [app.py](file:///d:/round2%20-%20anti/astram/backend/app.py)

Complete rewrite from Flask to **FastAPI**:
- `POST /predict` — Full incident analysis (impact + risk + confidence + resources + historical evidence + corridor DNA + transit flag)
- `GET /city-pulse` — Overview KPIs, map events, live feed
- `GET /risk-window` — 168-slot risk window data (optionally filtered by weekday/hour)
- `GET /shift-briefing` — Current shift briefing (Morning/Evening/Night)
- `GET /corridor/{name}` — Single corridor DNA
- `POST /similar-incidents` — Historical similarity search
- `GET /station-intelligence` — All 54 stations
- Static file serving for frontend

---

#### [MODIFY] [model_engine.py](file:///d:/round2%20-%20anti/astram/backend/model_engine.py)

Simplified to only:
1. **Feature Pipeline** — Build feature vector matching training schema (6 steps from spec)
2. **Impact Engine** — CatBoost prediction → impact_score (0-100)
3. **Risk Class Engine** — New boundaries: 0-25 Low, 25-50 Medium, 50-75 High, 75-100 Critical
4. **Formula vs AI Engine** — Operational Baseline (deterministic rules) vs Historical Pattern Intelligence (NOT SHAP, show similar incident stats)

Remove: SHAP explanation, `_estimate_confidence`, old `score_to_class`, `whatif` (moved to predict endpoint)

---

#### [MODIFY] [historical_engine.py](file:///d:/round2%20-%20anti/astram/backend/historical_engine.py)

Full rebuild:
1. **Confidence Engine** — Match on `cause + corridor_tier + closure`, count matches: ≥30=High, 10-29=Medium, <10=Low
2. **Historical Evidence Engine** — `find_similar_incidents()`: returns count, critical_rate, average_score, score_distribution, top_examples
3. **Transit Chain Flag** — vehicle_breakdown + (BMTC/KSRTC) + Tier 1 → flag with historical case count

---

#### [MODIFY] [resource_engine.py](file:///d:/round2%20-%20anti/astram/backend/resource_engine.py)

Restructure output to **timeline format**:
```
Tree Fall:
  0-15 min: Police Units
  15-30 min: BBMP Crew
  30-60 min: Barricades, Diversion
```

Add **Expected Resolution Estimate** (historical pattern, show range not single number):
```
Tree Fall: 1.2h median, 0.4h-4.0h range
```

---

#### [NEW] [corridor_engine.py](file:///d:/round2%20-%20anti/astram/backend/corridor_engine.py)

New engine handling:
1. **Corridor DNA** — Load from `corridor_dna.json`, serve per-corridor profiles
2. **Corridor Stress Index** — Load from `stress_index.json`, signature metric for Pages 1 & 3
3. **Risk Window** — Load from `risk_window.json`, 168-slot grid
4. **Shift Briefing** — Compute from risk window: Morning (6-14), Evening (14-22), Night (22-6)
5. **Station Intelligence** — Load from `station_intelligence.json`

---

### Phase 3: Frontend — Complete UI Rebuild

#### [MODIFY] [index.html](file:///d:/round2%20-%20anti/astram/frontend/index.html)

Complete rebuild with all 3 pages matching spec sections 17-19:

**Page 1: Command Center** (6 sections)
1. KPI Strip — Active incidents, Critical count, Road closures, Avg impact
2. Corridor Stress Bar — Horizontal bar chart of stress index per corridor
3. Operational Risk Window — Heatmap grid (weekday × hour), highlights current slot
4. Shift Briefing — Current shift panel (Morning/Evening/Night) with stress level, top corridors, top causes
5. Historical Feed — Clickable incident list → navigates to Page 2 with auto-populate
6. Incident Map — Leaflet map with Bengaluru incidents, color by risk class

**Page 2: Incident Response Copilot** (8 panels)
- Panel A: Impact Assessment (score ring, class badge, confidence indicator)
- Panel B: Resolution Estimate (range display, median + range)
- Panel C: Resource Timeline (visual timeline with phases)
- Panel D: Historical Evidence (similar count, critical rate, avg score, score distribution mini chart)
- Panel E: Formula vs AI (Operational Baseline calculation vs Historical Pattern Intelligence narrative)
- Panel F: Corridor DNA (mini profile of selected corridor)
- Panel G: Transit Chain Flag (conditional — only shown for BMTC/KSRTC + Tier 1 + breakdown)
- Panel H: What-If Toggle (closure ON/OFF, re-runs prediction)

**Page 3: Corridor Intelligence** (5 questions)
- Q1: Resource positioning → Heatmap (corridor × hour)
- Q2: Closure causes → Closure rate chart
- Q3: Most burden → Stress Index Leaderboard
- Q4: Station overload → Station scatter plot (highlight Halasuru Gate)
- Q5: Fleet Demand → Tow trucks/day, Officers/day per corridor

---

#### [MODIFY] [styles.css](file:///d:/round2%20-%20anti/astram/frontend/css/styles.css)

Complete CSS rewrite:
- Premium dark theme with glassmorphism
- Design system with CSS custom properties
- Risk class color palette (Critical=red, High=orange, Medium=amber, Low=green)
- Timeline visualization styles
- Heatmap grid CSS
- Score ring animations
- Stress bar components
- Responsive grid layouts
- Smooth micro-animations and transitions

---

#### [MODIFY] [app.js](file:///d:/round2%20-%20anti/astram/frontend/js/app.js)

Complete JS rewrite:
- FastAPI endpoint integration (new URL paths)
- Page 1: Risk Window heatmap renderer, Stress bar chart, Shift briefing panel, Live feed with click-to-copilot
- Page 2: Full copilot with all 8 panels, What-If toggle logic, Formula vs AI renderer, Transit chain conditional display
- Page 3: 5 intelligence charts (heatmap, closure bar, stress leaderboard, station scatter, fleet demand)
- Chart.js for all visualizations
- Animated score ring, confidence indicators, timeline renderer

---

### Phase 4: Requirements & Config

#### [MODIFY] [requirements.txt](file:///d:/round2%20-%20anti/astram/requirements.txt)

Update dependencies:
```
fastapi
uvicorn[standard]
pandas
numpy
catboost
pyarrow
```

Remove: flask, flask-cors, sentence-transformers (not needed at runtime)

#### [MODIFY] [run.bat](file:///d:/round2%20-%20anti/astram/run.bat)

Update to use uvicorn instead of python app.py.

---

## Verification Plan

### Automated Tests
```bash
# 1. Precompute lookups
python astram/backend/precompute_lookups.py

# 2. Start server
cd astram && uvicorn backend.app:app --host 0.0.0.0 --port 5000

# 3. Test all endpoints
curl http://localhost:5000/api/city-pulse
curl -X POST http://localhost:5000/api/predict -d '{"cause":"tree_fall","corridor":"Bellary Road 1","closure":true,"vehicle_type":"others","hour":5,"weekday":3}'
curl http://localhost:5000/api/risk-window
curl http://localhost:5000/api/shift-briefing
curl http://localhost:5000/api/corridor/Bellary%20Road%201
curl -X POST http://localhost:5000/api/similar-incidents -d '{"cause":"tree_fall","corridor_tier":1,"closure":true}'
curl http://localhost:5000/api/station-intelligence
```

### Manual Verification
- Run the demo scenario: Thursday 5:30 AM, Tree Fall, Bellary Road 1, Road Closure ON
- Verify impact score ≈ 88, Critical class, 14+ similar incidents
- Toggle What-If (closure OFF) → verify class drops to High
- Navigate all 3 pages, verify all panels render correctly
- Check stress index bar on Page 1 shows Mysore Road ≈ 98.7
- Verify risk window highlights Thursday 5 AM slot
- Check transit chain flag shows for BMTC bus breakdown on Tier 1

---

## Build Order

| Phase | What | Files |
|-------|------|-------|
| **1** | Precompute lookup tables | `precompute_lookups.py`, `lookup_tables/*.json` |
| **2a** | Core engines | `model_engine.py`, `historical_engine.py`, `resource_engine.py` |
| **2b** | New engines | `corridor_engine.py` |
| **2c** | FastAPI app | `app.py` (delete `forecast_engine.py`) |
| **3a** | CSS design system | `styles.css` |
| **3b** | Page 2 (Copilot) | `index.html`, `app.js` |
| **3c** | Page 1 (Command Center) | `index.html`, `app.js` |
| **3d** | Page 3 (Intelligence) | `index.html`, `app.js` |
| **4** | Polish + verify | `run.bat`, `requirements.txt`, end-to-end testing |
