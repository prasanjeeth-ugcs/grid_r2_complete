# Corridor Tiering

> **Last Updated**: 2026-06-18

---

## Tier 1 — Critical Arterials (>290 events)

| Corridor | Events | Share | Strategic Note |
|---|---|---|---|
| Mysore Road | 743 | 9.1% | Southwest gateway, heavy commercial |
| Bellary Road 1 | 610 | 7.5% | Airport corridor (north), VIP route |
| Tumkur Road | 458 | 5.6% | Northwest industrial, truck-heavy |
| Bellary Road 2 | 379 | 4.6% | Airport corridor (inner), accident-prone |
| Hosur Road | 298 | 3.6% | Southeast IT corridor, pothole issues |

**5 corridors, 2,488 events (30.4%). Impact multiplier: 1.50×**

## Tier 2 — Major Corridors (160–275 events)

| Corridor | Events | Share |
|---|---|---|
| ORR North 1 | 275 | 3.4% |
| Old Madras Road | 263 | 3.2% |
| Magadi Road | 245 | 3.0% |
| ORR East 1 | 244 | 3.0% |
| ORR North 2 | 235 | 2.9% |
| Bannerghatta Road | 209 | 2.6% |
| ORR East 2 | 187 | 2.3% |
| West of Chord Road | 174 | 2.1% |

**8 corridors, 1,832 events (22.4%). Impact multiplier: 1.25×**

## Tier 3 — Secondary Corridors (<160 events)

| Corridor | Events | Share |
|---|---|---|
| ORR West 1 | 168 | 2.1% |
| ORR South 1 | 105 | 1.3% |
| Kanakapura Road | 89 | 1.1% |
| Sarjapur Road | 73 | 0.9% |
| Hennur Road | 61 | 0.7% |
| Airport New South Road | 47 | 0.6% |
| ORR West 2 | 38 | 0.5% |
| ORR South 2 | 30 | 0.4% |

**8 corridors, 611 events (7.5%). Impact multiplier: 1.10×**

## Non-Corridor

**3,124 events (38.2%). Impact multiplier: 1.00×**

## Implementation

```python
CORRIDOR_TIERS = {
    "Mysore Road": 1, "Bellary Road 1": 1, "Tumkur Road": 1,
    "Bellary Road 2": 1, "Hosur Road": 1,
    "ORR North 1": 2, "Old Madras Road": 2, "Magadi Road": 2,
    "ORR East 1": 2, "ORR North 2": 2, "Bannerghatta Road": 2,
    "ORR East 2": 2, "West of Chord Road": 2,
    "ORR West 1": 3, "ORR South 1": 3, "Kanakapura Road": 3,
    "Sarjapur Road": 3, "Hennur Road": 3, "Airport New South Road": 3,
    "ORR West 2": 3, "ORR South 2": 3,
}

TIER_MULTIPLIER = {1: 1.50, 2: 1.25, 3: 1.10, None: 1.00}

def get_corridor_tier(corridor):
    if pd.isna(corridor) or corridor == "Non-corridor":
        return None
    return CORRIDOR_TIERS.get(corridor, 3)
```
