# 🚦 Astram — Bengaluru Traffic Event Data: Exploratory Data Analysis

> **Problem Statement**: How can historical and real-time data be used to forecast event-related traffic impact and recommend optimal manpower, barricading, and diversion plans?

> **Dataset**: Astram Event-Driven Congestion Management Platform — Bengaluru, India

---

## Table of Contents

- [1. Dataset Overview](#1-dataset-overview)
- [2. Data Schema & Column Dictionary](#2-data-schema--column-dictionary)
- [3. Data Quality Report](#3-data-quality-report)
- [4. Univariate Analysis](#4-univariate-analysis)
- [5. Temporal Patterns](#5-temporal-patterns)
- [6. Geospatial Analysis](#6-geospatial-analysis)
- [7. Corridor & Zone Analysis](#7-corridor--zone-analysis)
- [8. Vehicle Breakdown Deep-Dive](#8-vehicle-breakdown-deep-dive)
- [9. Resolution Time Analysis](#9-resolution-time-analysis)
- [10. Road Closure Analysis](#10-road-closure-analysis)
- [11. Bivariate & Cross-Tabulation Insights](#11-bivariate--cross-tabulation-insights)
- [12. Feature Engineering Recommendations](#12-feature-engineering-recommendations)
- [13. Key Findings Summary](#13-key-findings-summary)
- [14. Recommendations for Modules 1–5](#14-recommendations-for-modules-15)
- [15. Appendix](#15-appendix)
- **Pre-Modeling Investigation**
- [16. Forecasting Feasibility](#16-pre-modeling-investigation-forecasting-feasibility)
- [17. Analysis A: Corridor × Hour-of-Day](#17-analysis-a-corridor--hour-of-day-matrix)
- [18. Analysis B: Event Cause × Hour-of-Day](#18-analysis-b-event-cause--hour-of-day-matrix)
- [19. Analysis C & D: Closure Probability](#19-analysis-c--d-closure-probability)
- [20. Analysis E: Priority × Corridor](#20-analysis-e-priority--corridor)
- [21. Analysis F: Event Cause × Vehicle Type](#21-analysis-f-event-cause--vehicle-type)
- [22. Analysis G: Timeline Reconstruction](#22-analysis-g-timeline-reconstruction--forecasting-feasibility)
- [FINAL VERDICT: Forecasting Feasibility](#final-verdict-forecasting-feasibility)

---

## 1. Dataset Overview

| Attribute | Value |
|-----------|-------|
| **Source** | Astram Traffic Event Management Platform |
| **City** | Bengaluru, Karnataka, India |
| **Format** | CSV (UTF-8) |
| **File Size** | 4.3 MB |
| **Total Records** | 8,173 events |
| **Total Columns** | 46 (raw) |
| **Date Range** | November 11, 2023 — April 08, 2024 (~5 months) |
| **Geographic Bounds** | Lat: 12.801°N – 13.268°N, Lng: 77.309°E – 77.769°E |
| **Anonymization** | IDs anonymized (FKID, FKUSR, FKN, FKKG patterns) |

### At-a-Glance KPIs

| KPI | Value |
|-----|-------|
| Total Events | **8,173** |
| Dominant Cause | **Vehicle Breakdown (59.9%)** |
| Unplanned Events | **94.3%** (7,706 of 8,173) |
| Closed/Resolved Events | **87.7%** (7,166) |
| Median Resolution Time | **0.98 hours** (~59 minutes) |
| Mean Resolution Time | **4.88 hours** (heavy right-skew) |
| Road Closure Rate | **8.3%** (676 events) |
| Rush Hour Share | **25.4%** of events during 8–10 AM & 5–8 PM |
| Designated Corridors Covered | **22 corridors** |
| Police Stations Involved | **54 stations** |
| Unique Junctions Logged | **294 junctions** |
| Authenticated Reports | **87.7%** |

---

## 2. Data Schema & Column Dictionary

### Column Groups

The 46 columns fall into 8 functional groups:

#### Identity & Classification (6 columns)
| Column | Type | Description | Completeness |
|--------|------|-------------|-------------|
| `id` | String | Anonymized event ID (FKID format) | 100% |
| `event_type` | Categorical | `planned` (5.7%) or `unplanned` (94.3%) | 100% |
| `event_cause` | Categorical | 17 distinct causes (see §4.1) | 100% |
| `priority` | Categorical | `High` (61.5%) or `Low` (38.4%) | 100% |
| `status` | Categorical | `closed` / `active` / `resolved` | 100% |
| `authenticated` | Boolean | Whether report was authenticated | 100% |

#### Location — Start Point (5 columns)
| Column | Type | Description | Completeness |
|--------|------|-------------|-------------|
| `latitude` | Float | Start latitude | 100% |
| `longitude` | Float | Start longitude | 100% |
| `address` | String | Geocoded start address | 100% |
| `police_station` | String | Nearest police station (54 unique) | 100% |
| `corridor` | Categorical | Traffic corridor name (22 unique) | 99.8% |

#### Location — End Point / Resolution (6 columns)
| Column | Type | Description | Completeness |
|--------|------|-------------|-------------|
| `endlatitude` | Float | End latitude (0 = missing) | 8.4% |
| `endlongitude` | Float | End longitude (0 = missing) | 8.4% |
| `end_address` | String | Geocoded end address | 8.4% |
| `resolved_at_address` | String | Resolution location address | 0.9% |
| `resolved_at_latitude` | Float | Resolution latitude | 0.9% |
| `resolved_at_longitude` | Float | Resolution longitude | 0.9% |

#### Temporal (6 columns)
| Column | Type | Description | Completeness |
|--------|------|-------------|-------------|
| `start_datetime` | Datetime (UTC) | Event start time | 98.6% |
| `end_datetime` | Datetime (UTC) | Planned end time | 5.8% |
| `created_date` | Datetime (UTC) | Record creation time | 100% |
| `modified_datetime` | Datetime (UTC) | Last modification time | 100% |
| `closed_datetime` | Datetime (UTC) | Event closure time | 38.4% |
| `resolved_datetime` | Datetime (UTC) | Event resolution time | 0.9% |

#### Vehicle Information (5 columns)
| Column | Type | Description | Completeness |
|--------|------|-------------|-------------|
| `veh_type` | Categorical | Vehicle type (10 categories) | 59.8% |
| `veh_no` | String | Anonymized vehicle number | 59.8% |
| `cargo_material` | String | Cargo type for trucks | 3.4% |
| `reason_breakdown` | String | Breakdown reason | 3.4% |
| `age_of_truck` | Numeric | Truck manufacture year | 3.4% |

#### Road & Infrastructure (4 columns)
| Column | Type | Description | Completeness |
|--------|------|-------------|-------------|
| `requires_road_closure` | Boolean | Whether road closure was needed | 100% |
| `direction` | String | Traffic direction affected | 0.5% |
| `description` | String | Free-text description (mixed English/Kannada) | 83.4% |
| `junction` | String | Nearest junction name (294 unique) | 30.7% |

#### Administrative & Users (10 columns)
| Column | Type | Description | Completeness |
|--------|------|-------------|-------------|
| `client_id` | Numeric | Client identifier | 100% |
| `created_by_id` | String | User who created the report | 100% |
| `last_modified_by_id` | String | Last modifier | 100% |
| `assigned_to_police_id` | String | Assigned police officer | 1.6% |
| `citizen_accident_id` | String | Citizen report link | 1.6% |
| `closed_by_id` | String | User who closed the event | 38.4% |
| `resolved_by_id` | String | User who resolved the event | 0.9% |
| `kgid` | String | KGID identifier | 96.8% |
| `gba_identifier` | String | GBA area identifier | 42.1% |
| `zone` | Categorical | Administrative zone (10 zones) | 42.1% |

#### Unused / Empty (4 columns)
| Column | Type | Description | Completeness |
|--------|------|-------------|-------------|
| `map_file` | — | Always NULL | 0% |
| `route_path` | — | Almost always NULL | 1.7% |
| `comment` | — | Always NULL | 0% |
| `meta_data` | — | Always NULL | 0% |

---

## 3. Data Quality Report

### 3.1 Missingness Summary

#### Fully Populated Columns (0% missing) — Safe for modeling
```
id, event_type, event_cause, latitude, longitude, requires_road_closure,
status, authenticated, modified_datetime, client_id, created_by_id,
last_modified_by_id, police_station, created_date, address, priority
```
**16 columns** are 100% complete — these form the reliable feature set.

#### Columns with Significant Missing Data

| Column | Missing % | Missing Count | Impact |
|--------|-----------|---------------|--------|
| `map_file` | 100.0% | 8,173 | ❌ Drop — completely empty |
| `meta_data` | 100.0% | 8,173 | ❌ Drop — completely empty |
| `comment` | 100.0% | 8,173 | ❌ Drop — completely empty |
| `direction` | 99.5% | 8,132 | ❌ Drop — nearly empty |
| `resolved_datetime` | 99.1% | 8,101 | ⚠️ Only 72 events have resolution timestamps |
| `resolved_at_address` | 99.1% | 8,101 | ⚠️ Paired with resolved_datetime |
| `resolved_by_id` | 99.1% | 8,101 | ⚠️ Paired with resolved_datetime |
| `assigned_to_police_id` | 98.4% | 8,042 | ⚠️ Very sparse |
| `citizen_accident_id` | 98.4% | 8,042 | ⚠️ Very sparse |
| `route_path` | 98.3% | 8,034 | ❌ Drop — nearly empty |
| `age_of_truck` | 96.6% | 7,895 | ⚠️ Only 278 values |
| `cargo_material` | 96.6% | 7,895 | ⚠️ Only 278 values |
| `reason_breakdown` | 96.6% | 7,895 | ⚠️ Only 278 values |
| `end_datetime` | 94.2% | 7,700 | ⚠️ Only for planned events |
| `end_address` | 91.6% | 7,488 | ⚠️ Only for multi-point events |
| `endlatitude` | 91.6% | 7,488 | ⚠️ Paired with end_address |
| `endlongitude` | 91.6% | 7,488 | ⚠️ Paired with end_address |
| `junction` | 69.3% | 5,661 | ⚠️ Available for ~31% events |
| `closed_datetime` | 61.6% | 5,033 | ⚠️ Only for closed events |
| `closed_by_id` | 61.6% | 5,033 | ⚠️ Paired with closed_datetime |
| `zone` | 57.9% | 4,734 | ⚠️ Available for ~42% events |
| `gba_identifier` | 57.9% | 4,734 | ⚠️ Paired with zone |
| `veh_no` | 40.2% | 3,284 | ⚠️ For vehicle-related events only |
| `veh_type` | 40.2% | 3,284 | ⚠️ For vehicle-related events only |
| `description` | 16.6% | 1,358 | ✅ Mostly available |

### 3.2 Data Anomalies Identified

1. **Literal NULL strings**: The dataset uses `"NULL"` as text instead of proper null values — requires replacement with `NaN` during loading
2. **Zero coordinates as missing**: `endlatitude`/`endlongitude` use `0` to represent missing values — must be converted to `NaN`
3. **Mixed case in event causes**: `"Debris"` vs `"debris"` and `"Fog / Low Visibility"` exist as separate categories — need normalization
4. **`test_demo` events**: 3 test records exist in the data — should be excluded from analysis
5. **Mixed-language descriptions**: The `description` field contains both English and Kannada text — complicates NLP analysis
6. **Massive resolution time outliers**: Maximum resolution time is 149.38 hours (~6.2 days), while median is just 0.98 hours
7. **Only 72 events have `resolved_datetime`**: This limits resolution time analysis to <1% of data; `closed_datetime` (38.4% available) is a better proxy for duration estimation

### 3.3 Columns Recommended to Drop

```
map_file, meta_data, comment, direction, route_path
```
These 5 columns are >98% empty and provide no analytical value.

---

## 4. Univariate Analysis

### 4.1 Event Cause Distribution

Vehicle breakdown overwhelmingly dominates with nearly **60% of all events**:

| Rank | Event Cause | Count | Share |
|------|------------|-------|-------|
| 1 | **vehicle_breakdown** | 4,896 | 59.9% |
| 2 | others | 638 | 7.8% |
| 3 | pot_holes | 537 | 6.6% |
| 4 | construction | 480 | 5.9% |
| 5 | water_logging | 458 | 5.6% |
| 6 | accident | 365 | 4.5% |
| 7 | tree_fall | 284 | 3.5% |
| 8 | road_conditions | 170 | 2.1% |
| 9 | congestion | 136 | 1.7% |
| 10 | public_event | 84 | 1.0% |
| 11 | procession | 72 | 0.9% |
| 12 | vip_movement | 20 | 0.2% |
| 13 | protest | 15 | 0.2% |
| 14 | Debris | 12 | 0.1% |
| 15 | test_demo | 3 | <0.1% |
| 16 | Fog / Low Visibility | 2 | <0.1% |
| 17 | debris | 1 | <0.1% |

**Key Insight**: The top 3 causes (breakdown, others, potholes) account for **74.3%** of all events. For the ML model (Module 1), this means a significant class imbalance challenge — vehicle breakdowns will dominate training data.

### 4.2 Event Type

| Type | Count | Share |
|------|-------|-------|
| **Unplanned** | 7,706 | 94.3% |
| Planned | 467 | 5.7% |

**Key Insight**: Almost all events are **reactive**, not proactive. The system is overwhelmingly used for unplanned incident logging. Planned events (construction, public events, VIP movements) are a small fraction.

### 4.3 Event Status

| Status | Count | Share |
|--------|-------|-------|
| **Closed** | 7,095 | 86.8% |
| Active | 1,007 | 12.3% |
| Resolved | 71 | 0.9% |

**Key Insight**: 86.8% of events have been closed. The distinction between "closed" and "resolved" is unclear from the data — only 71 events are marked "resolved" while 7,095 are "closed". For modeling, treat both as "completed". The 12.3% active events may represent snapshot timing or stale records.

### 4.4 Priority

| Priority | Count | Share |
|----------|-------|-------|
| **High** | 5,030 | 61.5% |
| Low | 3,141 | 38.4% |

**Key Insight**: The binary priority system skews toward "High" (61.5%). This is too coarse for the 4-level risk prediction needed in Module 1 — we need to engineer a more granular target variable using additional signals (road closure, event cause, corridor type).

---

## 5. Temporal Patterns

### 5.1 Hourly Distribution

The data shows a **strong bimodal pattern** aligned with Bengaluru's traffic rhythms:

| Hour (UTC) | Events | Bengaluru Local (UTC+5:30) | Period |
|------------|--------|---------------------------|--------|
| 00:00 | 418 | 5:30 AM | Early Morning |
| 01:00 | 381 | 6:30 AM | Morning Rush Start |
| 02:00 | 387 | 7:30 AM | Morning Rush |
| 03:00 | 372 | 8:30 AM | Morning Rush |
| 04:00 | 558 | 9:30 AM | Morning Rush Peak |
| 05:00 | 661 | 10:30 AM | Late Morning |
| 06:00 | 660 | 11:30 AM | Midday |
| 07:00 | 480 | 12:30 PM | Midday |
| 08:00 | 327 | 1:30 PM | Afternoon |
| 09:00 | 160 | 2:30 PM | Afternoon |
| 10:00 | 68 | 3:30 PM | Afternoon Lull |
| 11:00 | 68 | 4:30 PM | Pre-Evening |
| 12:00 | 63 | 5:30 PM | Evening Rush Start |
| 13:00 | 33 | 6:30 PM | Evening Rush |
| 14:00 | 13 | 7:30 PM | Evening Rush |
| 15:00 | **9** | 8:30 PM | **← Minimum** |
| 16:00 | 9 | 9:30 PM | Night |
| 17:00 | 34 | 10:30 PM | Night |
| 18:00 | 228 | 11:30 PM | Late Night |
| 19:00 | 578 | 12:30 AM | After Midnight |
| 20:00 | 681 | 1:30 AM | Night (trucks enter) |
| 21:00 | **810** | 2:30 AM | **← Maximum** |
| 22:00 | 564 | 3:30 AM | Early Morning |
| 23:00 | 495 | 4:30 AM | Early Morning |

**Key Insights**:
- **Peak at UTC 21:00 (2:30 AM IST)** with 810 events — this correlates with **heavy vehicle movement windows** when trucks are allowed on Bengaluru roads (typically after 10 PM)
- **Morning surge from UTC 04:00–06:00 (9:30 AM–11:30 AM IST)** — post-morning-rush reporting wave
- **Deep trough at UTC 14:00–16:00 (7:30–9:30 PM IST)** — only 9–13 events/hour during evening rush paradoxically, likely due to shift changes or reporting delays
- **Implication for Module 2**: Time-of-day weighting must account for the **nighttime heavy vehicle surge**, not just traditional rush hours

### 5.2 Day-of-Week Distribution

| Day | Events | Share |
|-----|--------|-------|
| **Thursday** | 1,343 | 16.4% |
| Tuesday | 1,245 | 15.2% |
| Friday | 1,245 | 15.2% |
| Saturday | 1,223 | 15.0% |
| Wednesday | 1,162 | 14.2% |
| Sunday | 930 | 11.4% |
| **Monday** | 909 | **11.1% ← Minimum** |

**Key Insight**: Events are fairly evenly distributed across the week, with a slight mid-week peak (Thursday) and a Monday/Sunday dip. Weekends (26.3%) are slightly lower than proportional (28.6%), but not dramatically.

### 5.3 Monthly Distribution

| Month | Events | Share |
|-------|--------|-------|
| **March 2024** | 1,931 | **23.6% ← Peak** |
| December 2023 | 1,746 | 21.4% |
| January 2024 | 1,446 | 17.7% |
| February 2024 | 1,340 | 16.4% |
| November 2023 | 972 | 11.9% |
| April 2024 | 622 | 7.6% |

**Key Insight**: March 2024 has the highest event count — could indicate pre-monsoon infrastructure issues, election season activity, or increased field reporting. April shows low counts likely because the data ends on April 8th (partial month). The November 2023 count is also low as data starts on Nov 11th.

---

## 6. Geospatial Analysis

### 6.1 Geographic Coverage

| Metric | Value |
|--------|-------|
| **Latitude Range** | 12.801°N – 13.268°N |
| **Longitude Range** | 77.309°E – 77.769°E |
| **Approximate Area** | ~52 km (N-S) × ~50 km (E-W) |
| **Center** | ~12.97°N, 77.59°E (central Bengaluru) |

The data covers the full Bengaluru metropolitan area, extending from **Electronic City** in the south to **Devanahalli Airport** in the north, and from **Kengeri** in the west to **Whitefield** in the east.

### 6.2 Top 15 Police Stations by Event Load

| Rank | Police Station | Events | Share |
|------|---------------|--------|-------|
| 1 | **Yelahanka** | 377 | 4.6% |
| 2 | HAL Old Airport | 361 | 4.4% |
| 3 | Sadashivanagar | 302 | 3.7% |
| 4 | Byatarayanapura | 297 | 3.6% |
| 5 | Halasuru Gate | 297 | 3.6% |
| 6 | Yeshwanthpura | 280 | 3.4% |
| 7 | Hennuru | 276 | 3.4% |
| 8 | Kodigehalli | 272 | 3.3% |
| 9 | Banaswadi | 245 | 3.0% |
| 10 | K.R. Pura | 228 | 2.8% |
| 11 | Kamakshipalya | 224 | 2.7% |
| 12 | No Police Station | 219 | 2.7% |
| 13 | Cubbon Park | 212 | 2.6% |
| 14 | Jalahalli | 197 | 2.4% |
| 15 | Chamarajpet | 192 | 2.3% |

**Key Insight**: The top 15 stations handle **52.5%** of all events. Yelahanka leads — likely due to the airport corridor and heavy vehicle traffic. The "No Police Station" entry (219 events) indicates geocoding gaps.

### 6.3 Zone-wise Distribution

*Available for 42.1% of events (3,439 records with zone data):*

| Zone | Events | Share (of zoned) |
|------|--------|-----------------|
| **Central Zone 2** | 623 | 18.1% |
| West Zone 1 | 433 | 12.6% |
| North Zone 2 | 413 | 12.0% |
| West Zone 2 | 358 | 10.4% |
| South Zone 2 | 354 | 10.3% |
| North Zone 1 | 318 | 9.2% |
| Central Zone 1 | 269 | 7.8% |
| East Zone 1 | 253 | 7.4% |
| South Zone 1 | 233 | 6.8% |
| East Zone 2 | 190 | 5.5% |

**Key Insight**: Central Zone 2 has the highest density, consistent with CBD congestion patterns. The west and north zones are also heavily affected, correlating with the Tumkur Road and Bellary Road corridors.

---

## 7. Corridor & Zone Analysis

### 7.1 Top 15 Corridors by Event Count

| Rank | Corridor | Events | Share | Top Cause |
|------|----------|--------|-------|-----------|
| 1 | **Non-corridor** | 3,124 | 38.2% | — |
| 2 | **Mysore Road** | 743 | 9.1% | Vehicle Breakdown (565) |
| 3 | **Bellary Road 1** | 610 | 7.5% | Vehicle Breakdown (449) |
| 4 | **Tumkur Road** | 458 | 5.6% | Vehicle Breakdown (383) |
| 5 | Bellary Road 2 | 379 | 4.6% | Vehicle Breakdown (269) |
| 6 | Hosur Road | 298 | 3.6% | Vehicle Breakdown (170) |
| 7 | ORR North 1 | 275 | 3.4% | — |
| 8 | Old Madras Road | 263 | 3.2% | — |
| 9 | Magadi Road | 245 | 3.0% | — |
| 10 | ORR East 1 | 244 | 3.0% | — |
| 11 | ORR North 2 | 235 | 2.9% | — |
| 12 | Bannerghatta Road | 209 | 2.6% | — |
| 13 | ORR East 2 | 187 | 2.3% | — |
| 14 | West of Chord Road | 174 | 2.1% | — |
| 15 | ORR West 1 | 168 | 2.1% | — |

### 7.2 Corridor vs Non-Corridor Split

| Category | Events | Share |
|----------|--------|-------|
| **On designated corridor** | 5,049 | 61.8% |
| Non-corridor | 3,124 | 38.2% |

**Key Insight**: Nearly **62%** of events occur on designated corridors, where they have the highest traffic impact. The top 3 corridors (Mysore Rd, Bellary Rd 1, Tumkur Rd) alone account for **22.1%** of all events. Vehicle breakdown is the dominant cause on every single major corridor.

### 7.3 Corridor Top Causes (Top 5 Corridors)

| Corridor | #1 Cause | #2 Cause | #3 Cause |
|----------|----------|----------|----------|
| **Mysore Road** | Vehicle Breakdown (565) | Others (62) | Water Logging (41) |
| **Bellary Road 1** | Vehicle Breakdown (449) | Others (53) | Accident (20) |
| **Tumkur Road** | Vehicle Breakdown (383) | Others (33) | Accident (16) |
| **Bellary Road 2** | Vehicle Breakdown (269) | Accident (42) | Others (23) |
| **Hosur Road** | Vehicle Breakdown (170) | Potholes (60) | Others (19) |

**Key Insight**: Vehicle breakdowns dominate every corridor. Bellary Road 2 has a notably higher accident proportion. Hosur Road stands out for pothole issues (60 events), suggesting infrastructure deterioration on that corridor.

---

## 8. Vehicle Breakdown Deep-Dive

Vehicle breakdowns (4,896 events, 59.9%) are the most impactful event category. Here's the vehicle type distribution:

### 8.1 Vehicle Type Distribution (Breakdown Events Only)

| Rank | Vehicle Type | Count | Share (of breakdowns) |
|------|-------------|-------|----------------------|
| 1 | **BMTC Bus** | 1,466 | 29.9% |
| 2 | Heavy Vehicle | 965 | 19.7% |
| 3 | LCV (Light Commercial) | 678 | 13.8% |
| 4 | Others | 449 | 9.2% |
| 5 | Private Bus | 359 | 7.3% |
| 6 | Private Car | 345 | 7.0% |
| 7 | Truck | 276 | 5.6% |
| 8 | KSRTC Bus | 217 | 4.4% |
| 9 | Taxi | 95 | 1.9% |
| 10 | Auto | 37 | 0.8% |

*Note: ~9 vehicle type values were missing (0.2% of breakdowns)*

### 8.2 Key Vehicle Insights

- **Public transit (BMTC + KSRTC) accounts for 34.4%** of all breakdowns — 1,683 public bus breakdowns in 5 months
- **Heavy vehicles + trucks = 25.3%** — significant contributor, especially during nighttime hours when truck entry is permitted
- **Commercial vehicles (LCV + Truck + Heavy) = 39.2%** — the largest category when combined
- **Private vehicles (Car + Taxi + Auto) = 9.7%** — smallest share, suggesting private vehicle breakdowns are either less frequent or less reported

**Implication for Module 3 (Resources)**: BMTC bus breakdowns likely need coordination with BMTC depot for replacement buses, while heavy vehicle breakdowns need crane/towing arrangements. Different vehicle types require different resource responses.

---

## 9. Resolution Time Analysis

### 9.1 Resolution Time Statistics

*Based on 72 events with `resolved_datetime` populated (0.9% of dataset):*

| Statistic | Value |
|-----------|-------|
| Count | 72 events |
| Mean | 4.88 hours |
| **Median** | **0.98 hours (~59 min)** |
| 25th Percentile | 0.60 hours (~36 min) |
| 75th Percentile | 1.52 hours (~91 min) |
| 95th Percentile | 10.84 hours |
| Maximum | 149.38 hours (~6.2 days) |

### 9.2 Closure Time Statistics (Alternative Duration Proxy)

*Based on events with `closed_datetime` populated (38.4% of dataset):*

| Statistic | Value |
|-----------|-------|
| Median | 1.08 hours |
| Mean | 105.98 hours |

**Key Insight**: The massive gap between median (1.08h) and mean (105.98h) for closure time indicates **extreme outliers** — some events were closed days or weeks later during bulk cleanup operations. The median is a much better central tendency measure.

### 9.3 Duration Categories

| Duration | Count | Share (of resolved) |
|----------|-------|-------------------|
| < 1 hour | 37 | 51.4% |
| 1–4 hours | 30 | 41.7% |
| 4–12 hours | 1 | 1.4% |
| > 12 hours | 4 | 5.6% |

**Key Insight**: Over half of events are resolved within an hour, and 93% within 4 hours. The 4 outlier events (>12 hours) likely represent complex incidents or administrative delays.

> ⚠️ **Important caveat**: Resolution time analysis is based on only 72 events (0.9% of data). Closure time (38.4% coverage) should be used as the primary duration proxy for Module 2 scoring.

---

## 10. Road Closure Analysis

### 10.1 Overall Road Closure Rate

| Metric | Value |
|--------|-------|
| Events requiring road closure | **676** |
| Closure rate | **8.3%** |
| Events without closure | 7,497 (91.7%) |

### 10.2 Road Closure Rate by Event Cause

| Event Cause | Closures | Total | Closure Rate |
|-------------|----------|-------|-------------|
| **vip_movement** | 16 | 20 | **80.0%** |
| **public_event** | 39 | 84 | **46.4%** |
| **protest** | 6 | 15 | **40.0%** |
| **tree_fall** | 112 | 284 | **39.4%** |
| **construction** | 127 | 480 | **26.5%** |
| **procession** | 19 | 72 | **26.4%** |
| road_conditions | 21 | 170 | 12.4% |
| others | 55 | 638 | 8.6% |
| water_logging | 39 | 458 | 8.5% |
| Debris | 1 | 12 | 8.3% |
| congestion | 6 | 136 | 4.4% |
| vehicle_breakdown | 210 | 4,896 | 4.3% |
| accident | 11 | 365 | 3.0% |
| pot_holes | 13 | 537 | 2.4% |

### 10.3 Key Road Closure Insights

- **VIP movements have the highest closure rate (80%)** — nearly all VIP events require road closure. Despite being rare (20 events), they have disproportionate impact
- **Tree falls cause the most closures in absolute terms** alongside construction (112 and 127 closures respectively)
- **Vehicle breakdowns have low closure rate (4.3%)** individually, but due to sheer volume they account for **210 closures** — the third highest in absolute terms
- **Accidents surprisingly have only 3.0% closure rate** — most accidents don't block the road entirely

**Implication for Module 1**: `requires_road_closure` is a strong signal for distinguishing Critical/High risk events. Combined with `event_cause`, it creates highly predictive feature interactions.

### 10.4 Resolution Time by Road Closure

| Road Closure | Median Resolution (hrs) |
|-------------|------------------------|
| Yes | 0.77 |
| No | 1.00 |

**Surprising finding**: Events WITH road closure actually resolve **faster** (median 0.77h vs 1.00h). This suggests that road closures trigger a more urgent response, leading to quicker resolution. However, this is based on the limited resolution time data (72 events).

---

## 11. Bivariate & Cross-Tabulation Insights

### 11.1 Event Cause × Priority

| Event Cause | High | Low | High % |
|-------------|------|-----|--------|
| vehicle_breakdown | 3,688 | 1,208 | 75.3% |
| others | 277 | 361 | 43.4% |
| pot_holes | 132 | 405 | 24.6% |
| construction | 290 | 190 | 60.4% |
| water_logging | 260 | 198 | 56.8% |
| accident | 56 | 309 | 15.3% |
| tree_fall | 73 | 211 | 25.7% |
| road_conditions | 58 | 112 | 34.1% |
| congestion | 90 | 46 | 66.2% |
| public_event | 47 | 37 | 55.9% |
| procession | 24 | 48 | 33.3% |
| vip_movement | 18 | 2 | 90.0% |
| protest | 2 | 13 | 13.3% |

**Key Insights**:
- **VIP movements** are almost always High priority (90.0%)
- **Vehicle breakdowns** are predominantly High priority (75.3%) — this makes sense as they directly block traffic
- **Accidents** are surprisingly Low priority dominant (84.7%) — likely because most accidents in the dataset are minor/already cleared
- **Potholes** and **tree falls** are mostly Low priority — they're infrastructure issues rather than active traffic disruptions

### 11.2 Top Event Cause by Corridor

Vehicle breakdown dominates every major corridor (as shown in §7.3), but secondary causes vary:
- **Hosur Road**: Potholes are the #2 issue (suggests road quality problems)
- **Bellary Road 2**: Accidents are #2 (suggests a high-speed corridor with safety concerns)
- **Mysore Road**: Water logging is #3 (drainage infrastructure issue)

---

## 12. Feature Engineering Recommendations

Based on the EDA findings, these derived features should be created for Modules 1–5:

### 12.1 Temporal Features

| Feature | Derivation | Purpose |
|---------|-----------|---------|
| `hour_of_day` | Extract from `start_datetime` | Temporal pattern capture |
| `day_of_week` | Extract from `start_datetime` | Weekday/weekend patterns |
| `month` | Extract from `start_datetime` | Seasonal effects |
| `is_weekend` | Saturday/Sunday flag | Binary temporal feature |
| `is_rush_hour` | 8–10 AM or 5–8 PM IST | Traffic volume proxy |
| `is_night` | 10 PM – 6 AM IST | Heavy vehicle window |
| `hour_sin`, `hour_cos` | Cyclical encoding of hour | Better ML representation |

### 12.2 Duration Features

| Feature | Derivation | Purpose |
|---------|-----------|---------|
| `closure_time_hrs` | `closed_datetime - start_datetime` | Primary duration proxy (38.4% coverage) |
| `resolution_time_hrs` | `resolved_datetime - start_datetime` | Secondary duration (0.9% coverage) |
| `report_delay_min` | `created_date - start_datetime` | Reporting latency |
| `duration_category` | Binned: <1h, 1-4h, 4-12h, >12h | Categorical duration |

### 12.3 Location Features

| Feature | Derivation | Purpose |
|---------|-----------|---------|
| `is_corridor` | corridor ≠ "Non-corridor" | Binary corridor flag |
| `corridor_event_frequency` | Historical event count per corridor | Corridor risk level |
| `station_event_frequency` | Historical event count per police station | Station load indicator |
| `junction_repeat_count` | Count of past events at same junction | Repeat hotspot indicator |
| `geo_cluster` | K-means clustering on lat/lng | Spatial grouping |

### 12.4 Engineered Target Variable (for Module 1)

Since the dataset only has binary priority (High/Low), the 4-level risk target should be constructed:

| Risk Level | Rule |
|-----------|------|
| **Critical** | `road_closure=TRUE` AND `priority=High` AND `is_corridor=TRUE` |
| **High** | `priority=High` AND `is_corridor=TRUE` AND `road_closure=FALSE` |
| **Medium** | `priority=High` AND `is_corridor=FALSE` |
| **Low** | `priority=Low` |

### 12.5 Impact Score Components (for Module 2)

| Component | Source | Calculation |
|-----------|--------|-------------|
| Priority Weight | `priority` | High=0.7, Low=0.3 |
| Duration Factor | `closure_time_hrs` | Percentile rank normalized to 0–1 |
| Historical Frequency | Junction/corridor count | Count / max_count |
| Corridor Risk | Corridor event density | Events_per_corridor / max_events |
| Time-of-Day Weight | `hour_of_day` | Night(heavy vehicles)=1.0, Rush=0.8, Midday=0.5, Off-peak=0.2 |

---

## 13. Key Findings Summary

### Finding 1: Vehicle Breakdowns Dominate (59.9%)
Nearly 3 out of every 5 events are vehicle breakdowns. BMTC buses alone account for 30% of breakdowns. This single event cause should be the primary focus of the prediction model, and the resource engine should have optimized response templates for breakdowns.

### Finding 2: Nighttime Heavy Vehicle Surge
The peak event hour is **UTC 21:00 (2:30 AM IST)** with 810 events — driven by heavy vehicle movement windows. Traditional rush-hour weighting won't capture this. The impact scoring model must separately weight the nighttime freight movement window.

### Finding 3: 94.3% Events Are Unplanned
The system is overwhelmingly reactive. Only 467 events (5.7%) were planned. This validates the need for a predictive system (Module 1) that can anticipate disruptions before they cascade.

### Finding 4: Resolution is Fast but Skewed
Median resolution time is ~59 minutes, but the mean is ~5 hours. A small number of events take days to resolve. The resource recommendation engine should trigger escalation protocols for events exceeding 2-hour thresholds.

### Finding 5: Road Closures are Rare but Impactful
Only 8.3% of events require road closure, but they're concentrated in VIP movements (80%), public events (46.4%), and tree falls (39.4%). Road closure is a strong binary predictor for the risk classification model.

### Finding 6: Top 3 Corridors Handle 22% of Events
Mysore Road (743), Bellary Road 1 (610), and Tumkur Road (458) are the most disruption-prone corridors. Module 4 should have pre-computed diversion routes ready for these corridors at all times.

### Finding 7: Uneven Police Station Load
The top station (Yelahanka: 377 events) handles 4.2× the load of the median station. Resource allocation (Module 3) should factor in station capacity and rebalance deployments.

### Finding 8: Critical Data Gaps
- Only **0.9%** of events have proper resolution timestamps
- **57.9%** lack zone classification
- **69.3%** lack junction mapping
- Vehicle details exist for only **59.8%** of events

These gaps mean Module 1 features should rely primarily on the 16 fully-populated columns.

---

## 14. Recommendations for Modules 1–5

### Module 1: Event Risk Prediction

| Recommendation | Rationale |
|---------------|-----------|
| Use the 16 fully-populated columns as primary features | Data completeness ensures no imputation bias |
| Engineer 4-level target from `priority` + `road_closure` + `event_cause` + `is_corridor` | Binary priority is too coarse for 4-class prediction |
| Apply SMOTE or class weighting | Vehicle breakdown dominance (60%) creates severe class imbalance |
| Use cyclical encoding for hour/day features | Time is circular, linear encoding loses midnight-continuity |
| Include `is_night` (10 PM–6 AM) as a feature | Nighttime heavy vehicle surge is a major event driver |

### Module 2: Congestion Impact Score

| Recommendation | Rationale |
|---------------|-----------|
| Weight nighttime (10 PM–6 AM) heavy vehicle hours at 1.0 | Peak events occur at 2:30 AM, not traditional rush hours |
| Use median (1h) not mean (5h) for baseline duration | Mean is skewed by extreme outliers |
| Use `closure_time_hrs` as duration proxy | 38.4% coverage vs 0.9% for resolution time |
| Multiply corridor risk by junction repeat frequency | Some junctions have chronic repeat events |
| Cap score at 100 using min-max on composite | Ensures interpretable 0–100 range |

### Module 3: Resource Recommendation

| Recommendation | Rationale |
|---------------|-----------|
| Build separate templates for BMTC breakdowns | 30% of all breakdowns — need BMTC depot coordination |
| Heavy vehicle breakdowns need crane/towing | 25% of breakdowns involve heavy vehicles/trucks |
| Tree fall events need BBMP crew | 39.4% road closure rate — second highest absolute closures |
| VIP movements need maximum resources by default | 80% closure rate, 90% High priority |
| Police stations with >300 events/5mo need additional staffing | Yelahanka, HAL, Sadashivanagar are over-loaded |

### Module 4: Diversion Routing

| Recommendation | Rationale |
|---------------|-----------|
| Pre-compute diversions for Mysore Road, Bellary Road 1 & 2, Tumkur Road | Top 4 corridors with 2,190 combined events |
| Include ORR segments (North 1&2, East 1&2, West 1) as priority routes | ORR handles 1,109 events combined |
| Factor in time-of-day for route capacity | Nighttime routes have different capacity than daytime |
| Store top-3 alternates per corridor segment | Reduces real-time computation |

### Module 5: Command Center Dashboard

| Recommendation | Rationale |
|---------------|-----------|
| Color-code by 4-level risk (red/orange/yellow/green) | Instant visual triage for operators |
| Default map center: 12.97°N, 77.59°E, zoom 11 | Covers full Bengaluru metro area |
| Add police station load indicators | Enables workload rebalancing in real-time |
| Include historical hotspot overlay | 294 junctions provide dense event history |
| Support corridor-level filtering | 22 corridors allow focused analysis |

---

## 15. Appendix

### A. File Inventory

| File | Description |
|------|-------------|
| `Astram event data_anonymized...csv` | Raw dataset (4.3 MB, 8,173 rows × 46 columns) |
| `eda_astram.py` | Python EDA script with full data pipeline |
| `eda_dashboard.html` | Interactive Plotly dashboard (optional reference) |
| `README.md` | This document |

### B. Technology Stack

| Tool | Version | Purpose |
|------|---------|---------|
| Python | 3.14 | Primary language |
| pandas | 3.0.3 | Data manipulation |
| plotly | 6.8.0 | Interactive visualizations |
| numpy | 2.4.6 | Numerical operations |

### C. Data Refresh Notes

- Dataset spans **Nov 11, 2023 – Apr 8, 2024** (~5 months)
- November 2023 and April 2024 are partial months
- Full months: December 2023, January–March 2024
- For time-series analysis, restrict to Dec 2023–Mar 2024 for complete monthly comparisons

### D. Glossary

| Term | Definition |
|------|-----------|
| **BMTC** | Bangalore Metropolitan Transport Corporation (city buses) |
| **KSRTC** | Karnataka State Road Transport Corporation (inter-city buses) |
| **ORR** | Outer Ring Road |
| **LCV** | Light Commercial Vehicle |
| **BWSSB** | Bangalore Water Supply and Sewerage Board |
| **BBMP** | Bruhat Bengaluru Mahanagara Palike (city municipal corporation) |
| **CBD** | Central Business District |
| **IST** | Indian Standard Time (UTC+5:30) |
| **GBA** | Greater Bengaluru Area |

---

## 16. Pre-Modeling Investigation: Forecasting Feasibility

> **The single most important question before writing any model:**
> *Can we reconstruct a timeline per corridor — Event T → Event T+1 → Event T+2 — to enable forecasting?*

---

## 17. Analysis A: Corridor × Hour-of-Day Matrix

### Peak Hours per Corridor

| Corridor | Peak Hour (UTC) | Peak Hour (IST) | Peak Count | Total Events |
|----------|----------------|-----------------|------------|-------------|
| **Non-corridor** | 21:00 | ~02:30 AM | 339 | 3,064 |
| **Mysore Road** | 06:00 | ~11:30 AM | 74 | 728 |
| **Bellary Road 1** | 04:00 | ~09:30 AM | 52 | 607 |
| **Tumkur Road** | 21:00 | ~02:30 AM | 44 | 458 |
| **Bellary Road 2** | 20:00 | ~01:30 AM | 42 | 379 |
| **Hosur Road** | 05:00 | ~10:30 AM | 46 | 297 |
| **ORR North 1** | 19:00 | ~00:30 AM | 35 | 274 |
| **Old Madras Road** | 19:00 | ~00:30 AM | 25 | 257 |
| **Magadi Road** | 06:00 | ~11:30 AM | 31 | 243 |
| **ORR East 1** | 21:00 | ~02:30 AM | 26 | 242 |
| **ORR North 2** | 05:00 | ~10:30 AM | 34 | 235 |
| **Bannerghatta Road** | 22:00 | ~03:30 AM | 40 | 208 |
| **ORR East 2** | 21:00 | ~02:30 AM | 57 | 183 |
| **West of Chord Road** | 05:00 | ~10:30 AM | 21 | 172 |
| **ORR West 1** | 21:00 | ~02:30 AM | 31 | 166 |

### Key Pattern: Two Distinct Corridor Clusters

**Cluster 1 — Nighttime Peaks (IST 00:30–03:30 AM):**
Tumkur Road, Bellary Road 2, ORR North 1, Old Madras Road, ORR East 1, Bannerghatta Road, ORR East 2, ORR West 1, Non-corridor

→ These are **heavy vehicle corridors** where truck/freight movement peaks after 10 PM IST when entry restrictions lift.

**Cluster 2 — Morning Peaks (IST 09:30–11:30 AM):**
Mysore Road, Bellary Road 1, Hosur Road, Magadi Road, ORR North 2, West of Chord Road

→ These are **commuter corridors** where breakdowns peak during morning commute and late-morning reporting waves.

**Implication for Module 2**: Time-of-day weighting must be **corridor-specific**, not a single global schedule. A breakdown at 2 AM on Tumkur Road is HIGH impact (peak traffic), while 2 AM on Mysore Road is LOW impact (off-peak).

---

## 18. Analysis B: Event Cause × Hour-of-Day Matrix

### Peak Hours per Event Cause

| Event Cause | Peak Hour (IST) | Top 3 Hours (UTC=count) | Total |
|------------|-----------------|------------------------|-------|
| **vehicle_breakdown** | ~01:30 AM | UTC 20=451, UTC 21=440, UTC 19=391 | 4,896 |
| **others** | ~00:30 AM | UTC 19=65, UTC 21=60, UTC 20=52 | 638 |
| **pot_holes** | ~03:30 AM | UTC 22=112, UTC 21=84, UTC 05=64 | 537 |
| **construction** | ~02:30 AM | UTC 21=85, UTC 20=73, UTC 19=34 | 480 |
| **water_logging** | ~11:30 AM | UTC 06=116, UTC 07=92, UTC 05=48 | 458 |
| **accident** | ~04:30 AM | UTC 23=69, UTC 03=23, UTC 04=22 | 365 |
| **tree_fall** | ~11:30 AM | UTC 06=42, UTC 07=40, UTC 08=32 | 284 |
| **road_conditions** | ~02:30 AM | UTC 21=37, UTC 22=16, UTC 05=14 | 170 |
| **congestion** | ~09:30 AM | UTC 04=32, UTC 05=20, UTC 06=12 | 136 |
| **public_event** | ~11:30 AM | UTC 06=5, UTC 13=5, UTC 03=4 | 84 |
| **procession** | ~10:30 AM | UTC 05=11, UTC 21=9, UTC 04=8 | 72 |

### Hypothesis Confirmation

**Hypothesis: "Heavy vehicle breakdowns peak at night"**

| Period | Breakdown Events | Share |
|--------|-----------------|-------|
| **Night (IST 23:30–11:30)** | **3,824** | **78.1%** |
| Day (IST 11:30–23:30) | 1,072 | 21.9% |

**CONFIRMED.** Nearly **4 out of 5 vehicle breakdowns** occur during the nighttime heavy vehicle window. This is the single strongest temporal signal in the dataset.

**Hypothesis: "Water logging peaks during rainfall periods"**

| Month | Water Logging Events |
|-------|---------------------|
| November 2023 | 18 |
| December 2023 | 20 |
| January 2024 | 45 |
| February 2024 | 26 |
| **March 2024** | **230** |
| **April 2024** | **119** |

**CONFIRMED.** March–April sees a **massive 12x spike** in water logging (230+119=349 events vs. ~27/month in Nov-Feb). March is pre-monsoon season in Bengaluru with early thunderstorms. This is a strong seasonal feature.

### Cause-Specific Temporal Patterns

1. **Accidents peak at IST ~04:30 AM** (UTC 23:00 = 69 events) — late-night/early-morning hours with lower visibility and potential drowsy driving
2. **Tree falls peak at IST ~11:30 AM** — daytime, likely reported during morning inspections or after overnight storms
3. **Congestion peaks at IST ~09:30 AM** — classic morning rush hour
4. **Potholes peak at IST ~03:30 AM** — nighttime reporting by field staff on patrol
5. **Construction events peak at IST ~02:30 AM** — nighttime construction work on major corridors

---

## 19. Analysis C & D: Closure Probability

### C. Road Closure Rate by Corridor

| Corridor | Closure Rate | Closures | Total |
|----------|-------------|----------|-------|
| **Non-corridor** | **12.1%** | 378 | 3,124 |
| Varthur Road | 11.7% | 9 | 77 |
| CBD 1 | 11.5% | 3 | 26 |
| **Mysore Road** | **11.0%** | **82** | 743 |
| Airport New South Road | 10.4% | 7 | 67 |
| ORR North 1 | 8.0% | 22 | 275 |
| Old Airport Road | 7.9% | 6 | 76 |
| ORR East 1 | 7.4% | 18 | 244 |
| CBD 2 | 6.7% | 7 | 104 |
| West of Chord Road | 6.3% | 11 | 174 |
| IRR (Thanisandra road) | 6.3% | 6 | 95 |
| Hennur Main Road | 6.2% | 6 | 96 |
| Hosur Road | 5.7% | 17 | 298 |
| Bellary Road 1 | 5.4% | 33 | 610 |
| Old Madras Road | 4.6% | 12 | 263 |
| ORR North 2 | 4.3% | 10 | 235 |
| Magadi Road | 4.1% | 10 | 245 |
| Bannerghatta Road | 3.3% | 7 | 209 |
| Bellary Road 2 | 3.2% | 12 | 379 |
| ORR West 1 | 3.0% | 5 | 168 |
| **Tumkur Road** | **2.6%** | **12** | 458 |
| ORR East 2 | 1.6% | 3 | 187 |

**Key Insight**: Non-corridor roads have the **highest closure rate (12.1%)** — likely because smaller roads are more easily fully blocked. Among major corridors, Mysore Road (11.0%) has notably high closure rate, while Tumkur Road (2.6%) and ORR East 2 (1.6%) rarely require closures.

### D. Road Closure Rate by Vehicle Type

| Vehicle Type | Closure Rate | Closures | Total |
|-------------|-------------|----------|-------|
| **Auto** | **10.8%** | 4 | 37 |
| Private Bus | 5.6% | 20 | 359 |
| Truck | 5.4% | 15 | 276 |
| **BMTC Bus** | **5.0%** | **73** | 1,466 |
| Heavy Vehicle | 4.2% | 41 | 965 |
| Private Car | 4.1% | 14 | 345 |
| Others | 3.6% | 16 | 449 |
| LCV | 2.7% | 18 | 678 |
| KSRTC Bus | 2.3% | 5 | 217 |
| Taxi | 2.1% | 2 | 95 |

**Key Insight**: Autos have the highest per-event closure rate (10.8%), likely because they break down in narrow lanes that fully block traffic. In absolute terms, **BMTC buses cause the most closures (73)** — expected given their volume. LCVs and taxis rarely cause road closures.

---

## 20. Analysis E: Priority × Corridor

| Corridor | High | Low | Total | High % | Signal |
|----------|------|-----|-------|--------|--------|
| **Non-corridor** | **0** | **3,122** | 3,122 | **0.0%** | — |
| Mysore Road | 741 | 2 | 743 | 99.7% | ★★★ |
| Bellary Road 1 | 610 | 0 | 610 | 100.0% | ★★★ |
| Tumkur Road | 454 | 4 | 458 | 99.1% | ★★★ |
| Bellary Road 2 | 379 | 0 | 379 | 100.0% | ★★★ |
| Hosur Road | 298 | 0 | 298 | 100.0% | ★★★ |
| ORR North 1 | 275 | 0 | 275 | 100.0% | ★★★ |
| Old Madras Road | 263 | 0 | 263 | 100.0% | ★★★ |
| Magadi Road | 245 | 0 | 245 | 100.0% | ★★★ |
| ORR East 1 | 244 | 0 | 244 | 100.0% | ★★★ |
| ORR North 2 | 235 | 0 | 235 | 100.0% | ★★★ |
| Bannerghatta Road | 209 | 0 | 209 | 100.0% | ★★★ |
| ORR East 2 | 187 | 0 | 187 | 100.0% | ★★★ |
| West of Chord Road | 174 | 0 | 174 | 100.0% | ★★★ |
| ORR West 1 | 168 | 0 | 168 | 100.0% | ★★★ |
| CBD 2 | 104 | 0 | 104 | 100.0% | ★★★ |

**CRITICAL DISCOVERY**: Priority is **perfectly correlated with corridor assignment**:
- **Every event on a designated corridor = High priority** (99.1–100%)
- **Every Non-corridor event = Low priority** (100%)

This means `priority` is **NOT an independent feature** — it's a deterministic function of `corridor`. For Module 1, we should NOT use both `priority` and `is_corridor` as separate features — they carry identical information. The 4-level risk target must be engineered from other signals.

---

## 21. Analysis F: Event Cause × Vehicle Type

### Cross-Tab Results

| Event Cause | Auto | BMTC | Heavy Veh. | KSRTC | LCV | Others | Pvt Bus | Pvt Car | Taxi | Truck |
|------------|------|------|-----------|-------|-----|--------|---------|---------|------|-------|
| **vehicle_breakdown** | 37 | 1,466 | 965 | 217 | 678 | 449 | 359 | 345 | 95 | 276 |
| All other causes | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |

### Vehicle Data Coverage by Event Cause

| Event Cause | With Vehicle Data | Total | Coverage |
|------------|------------------|-------|----------|
| **vehicle_breakdown** | 4,887 | 4,896 | **99.8%** |
| others | 0 | 638 | 0.0% |
| pot_holes | 0 | 537 | 0.0% |
| construction | 0 | 480 | 0.0% |
| water_logging | 0 | 458 | 0.0% |
| accident | 0 | 365 | 0.0% |
| tree_fall | 0 | 284 | 0.0% |
| *All remaining* | 0 | 500 | 0.0% |

**CRITICAL DISCOVERY**: Vehicle type data (`veh_type`, `veh_no`) is recorded **EXCLUSIVELY for vehicle breakdowns** and for zero other event causes. This means:
- `veh_type` is NOT a general feature — it's a breakdown-specific attribute
- For the ML model, `veh_type` should only be used in a **sub-model** for breakdown severity, not in the main risk classifier
- Accident events (365) have **no vehicle data at all** — a significant gap for accident-related resource planning

---

## 22. Analysis G: Timeline Reconstruction & Forecasting Feasibility

### THE VERDICT

### Corridor Timeline Density

| Corridor | Events | Days Span | Events/Day | Median Gap | Forecastable? |
|----------|--------|----------|-----------|-----------|---------------|
| **Non-corridor** | 3,064 | 151 | **20.3** | 0.4h | **STRONG** |
| **Mysore Road** | 728 | 151 | **4.8** | 2.1h | **STRONG** |
| **Bellary Road 1** | 607 | 151 | **4.0** | 2.7h | **STRONG** |
| **Tumkur Road** | 458 | 151 | **3.0** | 3.9h | **STRONG** |
| **Bellary Road 2** | 379 | 151 | **2.5** | 4.4h | **STRONG** |
| **Hosur Road** | 297 | 148 | **2.0** | 3.5h | **STRONG** |
| ORR North 1 | 274 | 151 | 1.8 | 7.2h | MODERATE |
| Old Madras Road | 257 | 150 | 1.7 | 6.0h | MODERATE |
| Magadi Road | 243 | 149 | 1.6 | 9.1h | MODERATE |
| ORR East 1 | 242 | 147 | 1.6 | 5.5h | MODERATE |
| ORR North 2 | 235 | 150 | 1.6 | 11.3h | MODERATE |
| Bannerghatta Road | 208 | 149 | 1.4 | 4.7h | MODERATE |
| ORR East 2 | 183 | 146 | 1.3 | 17.3h | MODERATE |
| West of Chord Road | 172 | 148 | 1.2 | 14.8h | MODERATE |
| ORR West 1 | 166 | 150 | 1.1 | 13.2h | MODERATE |
| CBD 2 | 98 | 151 | 0.6 | 22.7h | WEAK |
| IRR (Thanisandra road) | 95 | 150 | 0.6 | 22.5h | WEAK |
| Hennur Main Road | 94 | 143 | 0.7 | 22.7h | WEAK |
| Varthur Road | 75 | 147 | 0.5 | 27.6h | WEAK |
| Old Airport Road | 74 | 149 | 0.5 | 26.7h | INSUFFICIENT |
| Airport New South Road | 63 | 146 | 0.4 | 23.1h | INSUFFICIENT |
| CBD 1 | 25 | 145 | 0.2 | 45.7h | INSUFFICIENT |

### Forecastability Assessment

| Rating | Criteria | Corridors | Count |
|--------|---------|-----------|-------|
| **STRONG** | ≥2 events/day, median gap <24h | Non-corridor, Mysore Rd, Bellary Rd 1, Tumkur Rd, Bellary Rd 2, Hosur Rd | **6** |
| **MODERATE** | ≥1 event/day, median gap <48h | ORR North 1&2, Old Madras, Magadi, ORR East 1&2, Bannerghatta, W. Chord, ORR West 1 | **9** |
| **WEAK** | ≥0.5 events/day | CBD 2, IRR, Hennur Main, Varthur | **4** |
| **INSUFFICIENT** | <0.5 events/day | Old Airport, Airport New South, CBD 1 | **3** |

### Inter-Event Gap Distribution (All Corridors)

| Gap Duration | Count | Share |
|-------------|-------|-------|
| **< 30 minutes** | **2,481** | **31.0%** |
| 30 min – 1 hour | 883 | 11.0% |
| 1 – 2 hours | 897 | 11.2% |
| 2 – 4 hours | 781 | 9.7% |
| 4 – 8 hours | 621 | 7.7% |
| 8 – 12 hours | 432 | 5.4% |
| 12 – 24 hours | 1,007 | 12.6% |
| 1 – 2 days | 495 | 6.2% |
| 2 – 4 days | 236 | 2.9% |
| > 4 days | 99 | 1.2% |

**53.2%** of consecutive events on the same corridor occur within **2 hours** of each other. This indicates **event clustering** — incidents tend to cascade or occur in bursts.

### Daily Event Counts (Top Corridors, Last 30 Days)

**Mysore Road**: mean 4.9/day, std 3.1, range 1–19
```
2024-03-29: |||||||||||||||  (15)
2024-04-06: |||||||||||||||||  (17)
2024-03-26: ||||||||||||  (12)
2024-04-03: ||||||||||||  (12)
2024-03-11: |||||||||||  (11)
```

**Bellary Road 1**: mean 4.2/day, std 2.7, range 1–19
```
2024-03-26: |||||||||||  (11)
2024-03-16: ||||||||  (8)
2024-03-30: ||||||||  (8)
2024-04-07: ||||||||  (8)
```

**Tumkur Road**: mean 3.1/day, std 1.9, range 1–11
```
2024-04-03: ||||||||  (8)
2024-03-30: |||||||  (7)
```

### Autocorrelation Analysis

| Corridor | Lag-1 | Lag-2 | Lag-3 | Lag-7 | Verdict |
|----------|-------|-------|-------|-------|---------|
| Mysore Road | +0.103 | -0.003 | +0.107 | +0.132 | Weak |
| Bellary Road 1 | +0.008 | +0.002 | +0.041 | -0.033 | Weak |
| Tumkur Road | +0.048 | -0.033 | -0.046 | -0.108 | Weak |
| Bellary Road 2 | -0.047 | +0.034 | -0.242 | +0.020 | Weak |

**Autocorrelation is weak across all corridors** (all values <0.15 for lag-1). This means:
- Tomorrow's event count is **NOT strongly predictable** from today's count alone
- Pure ARIMA/time-series models will have limited accuracy
- **BUT**: The high event density (2-5/day on top corridors) still supports **hourly probability models** and **Poisson-based event rate forecasting**

### Simultaneous Events (Multiple Active on Same Corridor)

| Corridor | Days with >1 Event | Max Events in a Day |
|----------|--------------------|-------------------|
| Mysore Road | 133 days | 19 |
| Bellary Road 1 | 124 days | 19 |
| Tumkur Road | 121 days | 11 |
| Bellary Road 2 | 94 days | 12 |

Multi-event days are the **norm, not the exception** — Mysore Road has >1 event on **88% of days** with data.

---

## FINAL VERDICT: Forecasting Feasibility

### **YES — Timeline CAN be reconstructed for 15 out of 22 corridors.**

| Layer | Feasibility | Approach |
|-------|-------------|----------|
| **Daily event count forecasting** | **VIABLE** for 15 corridors | Poisson regression or count-based models (events/day per corridor) |
| **Hourly event probability** | **VIABLE** for top 6 corridors | Time-of-day × corridor probability matrix |
| **Pure time-series (ARIMA)** | **WEAK** | Low autocorrelation — limited standalone value |
| **Risk classification** | **STRONG** for all events | Event-level 4-class prediction using features |

### Recommended Hybrid Strategy

```
┌─────────────────────────────────────────────────────────┐
│  LAYER 1: FORECASTING                                   │
│  Predict daily event counts per corridor                │
│  → "Mysore Road expects ~5 events tomorrow"             │
│  → Triggers proactive resource pre-positioning          │
├─────────────────────────────────────────────────────────┤
│  LAYER 2: RISK CLASSIFICATION (Module 1)                │
│  When event occurs → Predict risk level                 │
│  → Low / Medium / High / Critical                       │
│  → Uses event_cause + corridor + hour + road_closure    │
├─────────────────────────────────────────────────────────┤
│  LAYER 3: IMPACT SCORING (Module 2)                     │
│  Composite KPI 0-100                                    │
│  → Corridor-specific time weighting (NOT global)        │
│  → Nighttime weight for freight corridors               │
├─────────────────────────────────────────────────────────┤
│  LAYER 4: RESOURCE + DIVERSION (Modules 3-4)            │
│  Resource recommendation + alternate routes             │
│  → Triggered by Layers 1-3                              │
└─────────────────────────────────────────────────────────┘
```

### Critical Design Decisions Uncovered

1. **Priority = Corridor** → Do not use both as features; they're redundant
2. **Vehicle type = Breakdown only** → Use as sub-model feature, not main classifier input
3. **Time weighting must be corridor-specific** → Tumkur Road peaks at 2:30 AM, Bellary Road 1 peaks at 9:30 AM
4. **Breakdowns are 78% nighttime** → Nighttime is the primary event window, not rush hour
5. **Water logging is seasonal** → March–April 12x spike; include month/season as features
6. **Event clustering is real** → 53% of events follow within 2 hours of the previous on same corridor
7. **Forecasting + Classification is stronger than classification alone** → Forecast enables proactive deployment

---

*Updated: June 17, 2026 | Data: 8,173 events | Phase 0 Complete — Ready for Module 1*
