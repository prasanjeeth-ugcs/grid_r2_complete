# Validation Findings

> **Last Updated**: 2026-06-18
> **Purpose**: Pre-modeling integrity checks before building the feature pipeline

---

## Analysis 1: Leakage Audit — `requires_road_closure`

### Question
When is `requires_road_closure` recorded? If it's set post-assessment, we cannot use it as an input feature — we must predict it.

### Method
Compared closure rates across event statuses. If the field is post-hoc, active (unclosed) events would be disproportionately FALSE.

### Results

| Status | Closure=TRUE | Total | Rate |
|--------|-------------|-------|------|
| active | 102 | 1,007 | 10.1% |
| closed | 569 | 7,095 | 8.0% |
| resolved | 5 | 71 | 7.0% |

- 1,007/1,007 active events have the field populated (100%)
- Cause-level closure rates for active events match overall dataset rates exactly

### Verdict
**SAFE** — `requires_road_closure` is set at creation time. Use as input feature. No architecture change needed.

---

## Analysis 2: Text Field Quality — `description`

### Stats

| Metric | Value |
|--------|-------|
| Populated | 6,813/8,173 (83.4%) |
| Unique ratio | 79.3% |
| English (>70% ASCII) | 87.8% |
| Kannada/code-mixed | 12.2% |
| Median length | 40 chars |
| Location keywords present | 43.4% |
| Severity keywords present | 27.4% |

### Top Repeated Descriptions
- "starting problem" (139×)
- "vehicle breakdown" (49×)
- "break down" (43×)
- "breakdown" (36×)
- "potholes" (29×)

### Key Observations
1. Descriptions are officer-written, not auto-generated
2. Rich with location context (junctions, landmarks, directions)
3. Severity explicitly stated ("no problem for traffic" vs "traffic blocked")
4. Misspellings common ("Disel prablam", "cluth plate")
5. 12.2% Kannada — needs multilingual model

### Verdict
**STRONG NLP CANDIDATE** — MiniLM embeddings recommended. Use `paraphrase-multilingual-MiniLM-L12-v2` for English+Kannada handling.

---

## Analysis 3: Spatial Hotspots — DBSCAN

### Config
- Method: DBSCAN (eps=800m, min_samples=30)
- Coordinate scaling: lat×111km, lng×111km×cos(12.97°)

### Results
- 10 clusters found
- 86.5% of events clustered (7,069/8,173)
- 13.5% noise (1,104)

### Zone Identification Without Corridor Labels

| Zone | Events | Cluster | Closure% |
|------|--------|---------|----------|
| Airport | 93 | no cluster | 1.1% |
| Silk Board | 323 | Cluster 0 | 6.8% |
| Yelahanka | 373 | Cluster 0 | 3.5% |
| KR Puram | 454 | Cluster 0 | 10.8% |
| Electronic City | 68 | no cluster | 1.5% |
| Majestic/CBD | 970 | Cluster 0 | 13.4% |
| Whitefield | 117 | Clusters 1,9 | 3.4% |

### Limitations
- Cluster 0 is a mega-cluster (5,867 events) — too coarse for inner city
- Airport and Electronic City fall into noise
- Need police_station for inner-city granularity

### Verdict
**HOTSPOT INTELLIGENCE CONFIRMED** — Use `geo_cluster_id` as feature, augment with `police_station` for inner-city resolution.
