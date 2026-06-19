# Dataset Understanding — Astram Traffic Event Data

> **Last Updated**: 2026-06-18
> **Dataset**: Astram Event-Driven Congestion Management Platform — Bengaluru, India
> **File**: `Astram event data_anonymized - Astram event data_anonymizedb40ac87 (1).csv`

---

## 1. Dataset Overview

| Attribute | Value |
|-----------|-------|
| Total Records | **8,173 events** |
| Total Columns | **46** |
| Date Range | Nov 11, 2023 — Apr 08, 2024 (~5 months) |
| Geographic Bounds | Lat: 12.801°N – 13.268°N, Lng: 77.309°E – 77.769°E |
| File Size | 4.3 MB |
| Anonymization | IDs anonymized (FKID, FKUSR, FKN, FKKG patterns) |

### Key KPIs

| KPI | Value |
|-----|-------|
| Dominant Cause | Vehicle Breakdown (59.9%) |
| Unplanned Events | 94.3% |
| Closed/Resolved | 87.7% |
| Median Resolution Time | ~59 minutes |
| Road Closure Rate | 8.3% (676 events) |
| Corridors Covered | 22 |
| Police Stations | 54 |
| Unique Junctions | 294 |

---

## 2. Reliable Feature Set (16 columns, 100% complete)

```
id, event_type, event_cause, latitude, longitude, requires_road_closure,
status, authenticated, modified_datetime, client_id, created_by_id,
last_modified_by_id, police_station, created_date, address, priority
```

## 3. Columns to Drop (>98% empty)

```
map_file, meta_data, comment, direction, route_path
```

## 4. Data Anomalies

1. **Literal "NULL" strings** — must replace with NaN
2. **Zero coordinates as missing** — endlatitude/endlongitude use 0
3. **Mixed case** — "Debris" vs "debris", "Fog / Low Visibility"
4. **3 test_demo records** — exclude from analysis
5. **Mixed-language descriptions** — English + Kannada

---

## 5. Event Cause Distribution

| Cause | Count | Share | Closure Rate | Priority % High |
|-------|-------|-------|-------------|----------------|
| vehicle_breakdown | 4,896 | 59.9% | 4.3% | 75.3% |
| others | 638 | 7.8% | 8.6% | 43.4% |
| pot_holes | 537 | 6.6% | 2.4% | 24.6% |
| construction | 480 | 5.9% | 26.5% | 60.4% |
| water_logging | 458 | 5.6% | 8.5% | 56.8% |
| accident | 365 | 4.5% | 3.0% | 15.3% |
| tree_fall | 284 | 3.5% | 39.4% | 25.7% |
| road_conditions | 170 | 2.1% | 12.4% | 34.1% |
| congestion | 136 | 1.7% | 4.4% | 66.2% |
| public_event | 84 | 1.0% | 46.4% | 55.9% |
| procession | 72 | 0.9% | 26.4% | 33.3% |
| vip_movement | 20 | 0.2% | 80.0% | 90.0% |
| protest | 15 | 0.2% | 40.0% | 13.3% |

---

## 6. Temporal Patterns

- **Peak hour**: UTC 21:00 (2:30 AM IST) — 810 events — heavy vehicle window
- **Morning surge**: UTC 04:00–06:00 (9:30–11:30 AM IST)
- **Deep trough**: UTC 14:00–16:00 (7:30–9:30 PM IST) — only 9–13 events/hr
- **Peak day**: Thursday (16.4%), **Low day**: Monday (11.1%)
- **Peak month**: March 2024 (23.6%)

---

## 7. Spatial Analysis

### Top 5 Police Stations
1. Yelahanka (377), 2. HAL Old Airport (361), 3. Sadashivanagar (302), 4. Byatarayanapura (297), 5. Halasuru Gate (297)

### DBSCAN Clustering Results
- 10 spatial clusters, 86.5% of events clustered
- Cluster 0 (mega-cluster): 5,867 events — central Bengaluru
- Peripheral zones separate cleanly: Whitefield, Magadi Road, ORR West, Bannerghatta (59–85% corridor purity)
- Airport Zone and Electronic City fall into noise (too sparse)

---

## 8. Validation Findings

### Leakage Audit — requires_road_closure
- **VERDICT: SAFE** — set at creation time
- Active events: 10.1% closure rate
- Closed events: 8.0% closure rate
- All 1,007 active events have the field populated
- Same cause-closure rate pattern across all statuses

### Text Field Quality — description
- 83.4% populated (6,813/8,173)
- 79.3% unique (not templated)
- 87.8% mostly English, 12.2% Kannada/code-mixed
- 43.4% contain location keywords
- 27.4% contain severity keywords
- **VERDICT: Strong NLP candidate** — multilingual MiniLM embeddings recommended

### Hotspot Intelligence
- 10 DBSCAN clusters cover 86.5% of events
- Peripheral zones identified without corridor labels
- Inner city needs police_station for fine-grained resolution
- geo_cluster_id recommended as categorical feature

---

## 9. Corridor Analysis

- 62% of events on designated corridors
- Top 3 corridors (Mysore Rd, Bellary Rd 1, Tumkur Rd) = 22.1% of all events
- Vehicle breakdown dominates every corridor
- See `corridor_tiering.md` for tier assignments

---

## 10. Resolution Time

- Median: ~59 min (based on 72 events with resolved_datetime)
- Mean: 4.88 hours (heavy right-skew)
- 51.4% resolved within 1 hour
- 93% resolved within 4 hours
- closure_time_hrs (38.4% coverage) is better proxy than resolution_time_hrs (0.9%)

---

## 11. Vehicle Breakdown Deep-Dive

Top vehicle types in breakdowns (4,896 events):
1. BMTC Bus: 29.9% — public transit, needs depot coordination
2. Heavy Vehicle: 19.7% — needs heavy crane/tow
3. LCV: 13.8% — standard tow
4. Others: 9.2%
5. Private Bus: 7.3% — large tow + passenger transfer

Public transit (BMTC + KSRTC) = 34.4% of all breakdowns.
