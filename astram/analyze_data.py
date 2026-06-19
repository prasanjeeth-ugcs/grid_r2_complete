import pandas as pd
import numpy as np

df = pd.read_parquet('d:/round2 - anti/astram/data/model_ready.parquet')

print('=== impact_score stats ===')
print(df['impact_score'].describe())
print()

print('=== impact_class distribution ===')
print(df['impact_class'].value_counts())
print()

print('=== Score percentiles ===')
for p in [10, 25, 50, 75, 90, 95, 99]:
    print(f'  p{p}: {df["impact_score"].quantile(p/100):.1f}')
print()

print('=== event_cause values ===')
print(df['event_cause'].unique())
print()

print('=== corridor_tier distribution ===')
print(df['corridor_tier'].value_counts().sort_index())
print()

print('=== requires_road_closure ===')
print(df['requires_road_closure'].value_counts())
print()

print('=== Scores by class ===')
print(df.groupby('impact_class')['impact_score'].describe())
print()

# Test predictions with different combos
from catboost import CatBoostRegressor
import sys
sys.path.insert(0, 'd:/round2 - anti/astram')
from backend.model_engine import predict, CAUSE_ENCODING, VEH_ENCODING

print('=== CAUSE_ENCODING ===')
print(CAUSE_ENCODING)
print()
print('=== VEH_ENCODING ===')
print(VEH_ENCODING)
print()

# Test various scenarios
tests = [
    {"event_cause": "tree_fall", "corridor": "Bellary Road 1", "requires_road_closure": True, "hour": 5, "weekday": 3},
    {"event_cause": "accident", "corridor": "Mysore Road", "requires_road_closure": True, "hour": 8, "weekday": 1},
    {"event_cause": "vip_movement", "corridor": "Hosur Road", "requires_road_closure": True, "hour": 10, "weekday": 0},
    {"event_cause": "vehicle_breakdown", "corridor": "Non-corridor", "requires_road_closure": False, "hour": 14, "weekday": 4},
    {"event_cause": "protest", "corridor": "Tumkur Road", "requires_road_closure": True, "hour": 12, "weekday": 2},
    {"event_cause": "water_logging", "corridor": "Bellary Road 2", "requires_road_closure": True, "hour": 6, "weekday": 5},
]

print('=== Prediction tests ===')
for t in tests:
    r = predict(t)
    print(f'  {t["event_cause"]:20s} | {t["corridor"]:20s} | closure={t["requires_road_closure"]} | score={r["score"]:5.1f} | class={r["impact_class"]}')
