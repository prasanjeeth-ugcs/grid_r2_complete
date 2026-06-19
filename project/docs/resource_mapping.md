# Resource Mapping — Module 3 Foundation

> **Last Updated**: 2026-06-18

---

## Resource Matrix

| Event Cause | Tow Truck | Police Units | Barricades | BBMP/Fire Crew | Diversion | Est. Duration |
|---|---|---|---|---|---|---|
| vehicle_breakdown | ✅ Yes | 1 | 0 | No | Maybe | 30–60 min |
| accident | ✅ Yes | 2 | 2 | Maybe | Maybe | 1–3 hrs |
| tree_fall | No | 2 | 4 | ✅ BBMP tree crew | ✅ Yes | 2–6 hrs |
| water_logging | No | 1 | 2 | ✅ BWSSB pump crew | Maybe | 2–8 hrs |
| construction | No | 1 | 4–6 | ✅ BBMP oversight | ✅ Yes | 4–48 hrs |
| pot_holes | No | 0 | 2 | ✅ BBMP road crew | No | 1–4 hrs |
| road_conditions | No | 1 | 2 | ✅ BBMP road crew | Maybe | 2–8 hrs |
| public_event | No | 3–5 | 6–10 | No | ✅ Yes | 4–12 hrs |
| procession | No | 3–4 | 4–6 | No | ✅ Yes | 2–6 hrs |
| vip_movement | No | 4–6 | 6–10 | No | ✅ Yes | 1–4 hrs |
| protest | No | 4–8 | 6–10 | No | ✅ Yes | 2–12 hrs |
| congestion | No | 1–2 | 0 | No | Maybe | 1–3 hrs |
| others | Maybe | 1 | 0–2 | Maybe | Maybe | 1–4 hrs |
| Debris | No | 1 | 2 | ✅ BBMP cleanup | Maybe | 1–2 hrs |

## Vehicle-Specific Sub-Rules (breakdowns)

| Vehicle Type | % of Breakdowns | Special Resource |
|---|---|---|
| BMTC Bus | 29.9% | BMTC depot coordination for replacement bus |
| Heavy Vehicle | 19.7% | Heavy-duty crane/tow |
| Truck | 5.6% | Heavy-duty crane + cargo transfer |
| LCV | 13.8% | Standard tow truck |
| Private Bus | 7.3% | Large tow + passenger transfer |
| Private Car | 7.0% | Standard tow truck |
| KSRTC Bus | 4.4% | KSRTC depot coordination |
| Taxi/Auto | 2.7% | Standard tow / self-push |

## Numeric Encoding

```python
RESOURCE_MAP = {
    "vehicle_breakdown":  {"tow": 1, "police": 1, "barricades": 0, "crew": 0, "diversion": 0.3},
    "accident":           {"tow": 1, "police": 2, "barricades": 2, "crew": 0.5, "diversion": 0.4},
    "tree_fall":          {"tow": 0, "police": 2, "barricades": 4, "crew": 1, "diversion": 1.0},
    "water_logging":      {"tow": 0, "police": 1, "barricades": 2, "crew": 1, "diversion": 0.5},
    "construction":       {"tow": 0, "police": 1, "barricades": 5, "crew": 1, "diversion": 1.0},
    "pot_holes":          {"tow": 0, "police": 0, "barricades": 2, "crew": 1, "diversion": 0.0},
    "road_conditions":    {"tow": 0, "police": 1, "barricades": 2, "crew": 1, "diversion": 0.4},
    "public_event":       {"tow": 0, "police": 4, "barricades": 8, "crew": 0, "diversion": 1.0},
    "procession":         {"tow": 0, "police": 3, "barricades": 5, "crew": 0, "diversion": 1.0},
    "vip_movement":       {"tow": 0, "police": 5, "barricades": 8, "crew": 0, "diversion": 1.0},
    "protest":            {"tow": 0, "police": 6, "barricades": 8, "crew": 0, "diversion": 1.0},
    "congestion":         {"tow": 0, "police": 1, "barricades": 0, "crew": 0, "diversion": 0.3},
    "others":             {"tow": 0.3, "police": 1, "barricades": 1, "crew": 0.3, "diversion": 0.3},
    "Debris":             {"tow": 0, "police": 1, "barricades": 2, "crew": 1, "diversion": 0.4},
}
```

## Scaling Factors

- **Corridor tier**: Tier 1 = 1.5×, Tier 2 = 1.25×, Tier 3 = 1.1×, Non-corridor = 1.0×
- **Rush hour**: 1.3× during 8–10 AM or 5–8 PM IST
- **Risk class escalation**: Critical = 2.0×, High = 1.5×, Medium = 1.0×, Low = 0.7×
