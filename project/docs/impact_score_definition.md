# Impact Score Definition

> **Current Version**: v2
> **Last Updated**: 2026-06-18
> **Purpose**: Define the composite impact score used as training label for Module 1

---

## Design Philosophy

The impact score is a **training label**, not a feature. It encodes "how impactful was this incident?" from outcome signals. The ML model then learns to **predict** this score from input features at inference time.

**Why not rule-based classification?**
- Rules map cause→class (e.g., "tree_fall → High"). A dictionary does this.
- ML must add value by learning **contextual interactions** (cause × time × location × description).
- The model differentiates **within** the same cause category based on context.

---

## Version History

### Impact Score v1 (KILLED)

Rule-based classification. Direct cause→class mapping.

```
tree_fall → High
vip_movement → Critical
vehicle_breakdown + corridor → Medium
```

**Killed because**: The model just learns a lookup table. No AI value-add.

---

### Impact Score v2 (CURRENT)

Composite score from outcome signals. Adjusted weights to reduce priority dominance.

**Weight rationale**: `priority` is noisy — 75.3% of breakdowns are "High" priority despite being routine. It's nearly a proxy for cause, not an independent severity signal. Reduce its weight. Lean on harder outcome signals: closure, corridor, duration.

#### Formula

| Component | Points | Signal |
|-----------|--------|--------|
| Road closure | **35** | Hard outcome — did the road actually close? |
| Corridor tier | **30** | Tier 1=30, Tier 2=22, Tier 3=14, Non-corridor=0 |
| Duration | **15** | >6h=15, 2–6h=10, 1–2h=5 |
| Cause severity | **10** | Data-driven weight from historical closure rates |
| Priority | **10** | Officer judgment (downweighted — noisy) |

**Total range**: 0–100

#### Cause Severity Weights (0–10)

Based on historical closure rates, not opinion:

| Cause | Weight | Closure Rate |
|-------|--------|-------------|
| vip_movement | 10 | 80.0% |
| public_event | 9 | 46.4% |
| protest | 9 | 40.0% |
| tree_fall | 8 | 39.4% |
| procession | 7 | 26.4% |
| construction | 7 | 26.5% |
| road_conditions | 5 | 12.4% |
| water_logging | 5 | 8.5% |
| congestion | 3 | 4.4% |
| vehicle_breakdown | 2 | 4.3% |
| accident | 2 | 3.0% |
| pot_holes | 1 | 2.4% |
| others | 2 | 8.6% |
| Debris | 2 | 8.3% |

#### Binning to Risk Classes

| Class | Score Range | Expected % |
|-------|------------|-----------|
| 🔴 Critical | 65–100 | ~5–8% |
| 🟠 High | 40–64 | ~20–25% |
| 🟡 Medium | 20–39 | ~30–35% |
| 🟢 Low | 0–19 | ~35–40% |

#### Implementation

```python
def compute_impact_score(row):
    score = 0.0

    # Component 1: Road closure (0 or 35)
    if row["requires_road_closure"]:
        score += 35

    # Component 2: Corridor tier (0–30)
    tier = get_corridor_tier(row.get("corridor"))
    tier_scores = {1: 30, 2: 22, 3: 14, None: 0}
    score += tier_scores.get(tier, 0)

    # Component 3: Duration (0–15)
    duration = row.get("closure_time_hrs")
    if pd.notna(duration) and duration > 0:
        if duration > 6:
            score += 15
        elif duration > 2:
            score += 10
        elif duration > 1:
            score += 5

    # Component 4: Cause severity (0–10)
    cause_weights = {
        "vip_movement": 10, "public_event": 9, "protest": 9,
        "tree_fall": 8, "procession": 7, "construction": 7,
        "road_conditions": 5, "water_logging": 5,
        "congestion": 3, "vehicle_breakdown": 2, "accident": 2,
        "pot_holes": 1, "others": 2, "Debris": 2,
    }
    score += cause_weights.get(row["event_cause"], 2)

    # Component 5: Priority (0 or 10)
    if row["priority"] == "High":
        score += 10

    return min(score, 100)


def score_to_class(score):
    if score >= 65:
        return "Critical"
    elif score >= 40:
        return "High"
    elif score >= 20:
        return "Medium"
    else:
        return "Low"
```

---

## What the AI Learns That Rules Can't

The model's input features include signals the label formula **does not use**:

| Feature | Value-Add |
|---------|-----------|
| Hour of day | 2AM breakdown (heavy vehicle window) ≠ 2PM breakdown |
| Day of week | Thursday events 48% more frequent than Monday |
| Description embeddings | "traffic blocked both sides" vs "no problem sir" |
| Lat/lng + geo_cluster | Silk Board junction ≠ residential lane |
| Junction history | Repeat hotspot junctions escalate faster |
| Vehicle type | BMTC bus on Bellary Road ≠ auto on side street |
| Police station load | Yelahanka (377 events) has stretched resources |
| Interaction effects | construction × night × Tier 1 corridor |

**The model differentiates within the same cause category.** Two tree falls, same `event_cause`, different predictions based on context. That's value a lookup table cannot provide.
