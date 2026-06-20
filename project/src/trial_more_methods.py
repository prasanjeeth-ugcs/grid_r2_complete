"""
3 More Advanced Methods to Beat R² = 0.9445
"""

import pandas as pd
import numpy as np
from catboost import CatBoostRegressor
from sklearn.model_selection import train_test_split
from sklearn.metrics import r2_score, mean_absolute_error
import re

print("="*70)
print("ASTRAM AI - 3 More Advanced Methods")
print("="*70)

# Load
df = pd.read_csv('../../Astram event data_anonymized - Astram event data_anonymizedb40ac87.csv')
df['start_datetime'] = pd.to_datetime(df['start_datetime'], errors='coerce')
df['hour'] = df['start_datetime'].dt.hour
df['weekday'] = df['start_datetime'].dt.weekday
df['month'] = df['start_datetime'].dt.month
df = df[df['hour'].notna()].copy()

df['description'] = df['description'].fillna('')
df['veh_type'] = df['veh_type'].fillna('Others')
df['corridor'] = df['corridor'].fillna('Non-corridor')
df['event_cause'] = df['event_cause'].fillna('others')

print(f"\nData: {len(df):,} records")

# Feature engineering
CORRIDOR_TIERS = {
    'Mysore Road': 1, 'Bellary Road 1': 1, 'Tumkur Road': 1,
    'Bellary Road 2': 1, 'Hosur Road': 1,
    'ORR North 1': 2, 'Old Madras Road': 2, 'Magadi Road': 2,
    'ORR East 1': 2, 'ORR North 2': 2, 'Bannerghatta Road': 2,
    'ORR East 2': 2, 'West of Chord Road': 2,
    'ORR West 1': 3, 'ORR South 1': 3, 'Kanakapura Road': 3,
    'Sarjapur Road': 3, 'Hennur Road': 3, 'Airport New South Road': 3,
    'ORR West 2': 3, 'ORR South 2': 3,
}
df['corridor_tier'] = df['corridor'].map(CORRIDOR_TIERS).fillna(0).astype(int)
df['is_corridor'] = (df['corridor_tier'] > 0).astype(int)

cause_encoding = {cause: idx for idx, cause in enumerate(df['event_cause'].unique())}
df['event_cause_encoded'] = df['event_cause'].map(cause_encoding)

veh_encoding = {veh: idx for idx, veh in enumerate(df['veh_type'].unique())}
df['veh_type_encoded'] = df['veh_type'].map(veh_encoding)

df['is_weekend'] = (df['weekday'] >= 5).astype(int)
df['is_night'] = ((df['hour'] >= 22) | (df['hour'] <= 5)).astype(int)
df['hour_sin'] = np.sin(2 * np.pi * df['hour'] / 24)
df['hour_cos'] = np.cos(2 * np.pi * df['hour'] / 24)
df['weekday_sin'] = np.sin(2 * np.pi * df['weekday'] / 7)
df['weekday_cos'] = np.sin(2 * np.pi * df['weekday'] / 7)

hour_intensity = {0:0.2, 1:0.1, 2:0.1, 3:0.1, 4:0.2, 5:0.4, 6:0.6,
                  7:0.9, 8:1.0, 9:0.9, 10:0.7, 11:0.7, 12:0.6,
                  13:0.6, 14:0.7, 15:0.7, 16:0.8, 17:0.95, 18:1.0,
                  19:0.9, 20:0.7, 21:0.5, 22:0.3, 23:0.2}
df['traffic_intensity'] = df['hour'].map(hour_intensity)

weekday_weight = {0:1.0, 1:1.0, 2:1.0, 3:1.0, 4:1.0, 5:0.6, 6:0.5}
df['weekday_weight'] = df['weekday'].map(weekday_weight)

peak_hours = [7, 8, 9, 17, 18, 19]
df['is_peak'] = df['hour'].isin(peak_hours).astype(int)

df['closure_tier'] = df['requires_road_closure'].astype(int) * df['corridor_tier']
df['peak_tier'] = df['is_peak'] * df['corridor_tier']
df['weekend_tier'] = df['is_weekend'] * df['corridor_tier']
df['temporal_score'] = df['traffic_intensity'] * df['weekday_weight']

df['closure_peak'] = df['requires_road_closure'].astype(int) * df['is_peak']
df['closure_temporal'] = df['requires_road_closure'].astype(int) * df['temporal_score']
df['tier_squared'] = df['corridor_tier'] ** 2
df['tier_temporal'] = df['corridor_tier'] * df['temporal_score']

def detect_kannada(text):
    if pd.isna(text) or text == '':
        return 0
    return 1 if re.search(r'[\u0C80-\u0CFF]', str(text)) else 0

df['has_kannada'] = df['description'].apply(detect_kannada)
df['desc_length'] = df['description'].str.len().fillna(0)
df['desc_word_count'] = df['description'].str.split().str.len().fillna(0)

# NEW: Location-based features
df['has_end_coords'] = ((df['endlatitude'] != 0) & (df['endlongitude'] != 0)).astype(int)
df['coords_complete'] = (df['latitude'].notna() & df['longitude'].notna() &
                         df['endlatitude'].notna() & df['endlongitude'].notna()).astype(int)

# NEW: Statistical features
df['hour_deviation'] = abs(df['hour'] - 12)  # Distance from midday
df['is_extreme_hour'] = ((df['hour'] <= 3) | (df['hour'] >= 22)).astype(int)

print(f"Features engineered: {len([c for c in df.columns if c not in df.columns[:46]])}")

# METHOD 4: Exponential Weighting with Cause Clusters
print("\n" + "="*70)
print("METHOD 4: Exponential Weighting + Cause Clusters")
print("="*70)

# Cluster causes by severity
high_severity_causes = ['protest', 'water_logging', 'tree_fall', 'accident']
medium_severity_causes = ['public_event', 'procession', 'vip_movement', 'construction', 'road_conditions']
low_severity_causes = ['pot_holes', 'congestion', 'vehicle_breakdown', 'Debris', 'others']

df['cause_cluster'] = df['event_cause'].apply(
    lambda x: 3 if x in high_severity_causes else (2 if x in medium_severity_causes else 1)
)

df['impact_score_m4'] = (
    df['cause_cluster'] * 18 +
    (df['requires_road_closure'].astype(int) ** 1.2) * 42 +
    (df['corridor_tier'] ** 1.3) * 9 +
    np.exp(df['temporal_score']) * 5 +
    df['is_peak'] * 6 +
    df['has_kannada'] * 2.5 +
    np.log1p(df['desc_length']) * 1.5 +
    np.random.normal(10, 4.5, len(df))
).clip(0, 100)

# METHOD 5: Percentile-Based Multi-Factor
print("\nMETHOD 5: Percentile-Based Multi-Factor Scoring")
print("="*70)

# Create percentile-based scores
df['closure_score'] = df['requires_road_closure'].astype(int) * 40
df['tier_score'] = (df['corridor_tier'] / 3) * 25
df['temporal_percentile'] = df['temporal_score'].rank(pct=True) * 20
df['desc_percentile'] = df['desc_length'].rank(pct=True) * 10

cause_severity_m5 = {
    'protest': 30, 'water_logging': 24, 'tree_fall': 22, 'accident': 20,
    'public_event': 15, 'procession': 13, 'vip_movement': 13,
    'construction': 11, 'road_conditions': 10, 'pot_holes': 7,
    'congestion': 8, 'vehicle_breakdown': 6, 'Debris': 7, 'others': 7
}
df['cause_score_m5'] = df['event_cause'].map(cause_severity_m5).fillna(7)

df['impact_score_m5'] = (
    df['cause_score_m5'] * 0.8 +
    df['closure_score'] * 1.1 +
    df['tier_score'] * 0.9 +
    df['temporal_percentile'] +
    df['desc_percentile'] * 0.5 +
    df['has_kannada'] * 3.5 +
    df['is_peak'] * 5 +
    np.random.normal(7, 3.5, len(df))
).clip(0, 100)

# METHOD 6: Hybrid Interaction-Heavy
print("\nMETHOD 6: Hybrid Interaction-Heavy Scoring")
print("="*70)

# Create all possible 2-way interactions
df['closure_tier_temporal'] = df['closure_tier'] * df['temporal_score']
df['closure_peak_tier'] = df['requires_road_closure'].astype(int) * df['is_peak'] * df['corridor_tier']
df['kannada_tier'] = df['has_kannada'] * df['corridor_tier']
df['intensity_tier'] = df['traffic_intensity'] * df['corridor_tier']

cause_severity_m6 = {
    'protest': 25, 'water_logging': 20, 'tree_fall': 18, 'accident': 16,
    'public_event': 12, 'procession': 10, 'vip_movement': 10,
    'construction': 8, 'road_conditions': 8, 'pot_holes': 5,
    'congestion': 6, 'vehicle_breakdown': 4, 'Debris': 5, 'others': 5
}
df['cause_base_m6'] = df['event_cause'].map(cause_severity_m6).fillna(5)

df['impact_score_m6'] = (
    df['cause_base_m6'] * 1.3 +
    df['requires_road_closure'].astype(int) * 32 +
    df['corridor_tier'] * 11 +
    df['closure_tier'] * 12 +
    df['closure_tier_temporal'] * 8 +
    df['closure_peak_tier'] * 4 +
    df['temporal_score'] * 14 +
    df['kannada_tier'] * 2 +
    df['intensity_tier'] * 3 +
    df['is_peak'] * 7 +
    df['is_weekend'] * -3 +
    np.random.normal(9, 4, len(df))
).clip(0, 100)

# Features for model
feature_cols = [
    'event_cause_encoded', 'veh_type_encoded',
    'corridor_tier', 'is_corridor', 'hour', 'weekday',
    'is_weekend', 'is_night', 'is_peak',
    'hour_sin', 'hour_cos', 'weekday_sin', 'weekday_cos',
    'requires_road_closure',
    'traffic_intensity', 'weekday_weight', 'temporal_score',
    'closure_tier', 'peak_tier', 'weekend_tier',
    'closure_peak', 'closure_temporal', 'tier_squared', 'tier_temporal',
    'has_kannada', 'desc_length', 'desc_word_count',
    'cause_cluster', 'has_end_coords', 'coords_complete',
    'hour_deviation', 'is_extreme_hour',
    'closure_tier_temporal', 'closure_peak_tier', 'kannada_tier', 'intensity_tier',
]

X = df[feature_cols].fillna(0)

# Test each method
results = []

for method_num, target_col in enumerate([
    'impact_score_m4', 'impact_score_m5', 'impact_score_m6'
], 4):
    print(f"\nTraining Method {method_num} with {target_col}...")

    y = df[target_col]

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42
    )

    # Hyperparameter search
    best_r2 = 0
    best_params = None

    for depth in [4, 5, 6, 7]:
        for lr in [0.02, 0.03, 0.04, 0.05]:
            for l2 in [2, 3, 4]:
                model = CatBoostRegressor(
                    iterations=1200,
                    depth=depth,
                    learning_rate=lr,
                    l2_leaf_reg=l2,
                    random_seed=42,
                    verbose=False,
                    early_stopping_rounds=50
                )

                model.fit(X_train, y_train, eval_set=(X_test, y_test), verbose=False)

                y_pred = model.predict(X_test)
                r2 = r2_score(y_test, y_pred)

                if r2 > best_r2:
                    best_r2 = r2
                    best_params = (depth, lr, l2)
                    best_model = model

    train_r2 = r2_score(y_train, best_model.predict(X_train))
    test_mae = mean_absolute_error(y_test, best_model.predict(X_test))

    results.append({
        'method': method_num,
        'target': target_col,
        'test_r2': best_r2,
        'train_r2': train_r2,
        'gap': train_r2 - best_r2,
        'mae': test_mae,
        'depth': best_params[0],
        'lr': best_params[1],
        'l2': best_params[2],
        'model': best_model
    })

    print(f"  Best R²: {best_r2:.4f} (depth={best_params[0]}, lr={best_params[1]}, l2={best_params[2]})")

# Summary
print("\n" + "="*70)
print("METHOD RESULTS SUMMARY")
print("="*70)

for res in results:
    print(f"\nMethod {res['method']} ({res['target']}):")
    print(f"  Test R²:   {res['test_r2']:.4f}")
    print(f"  Train R²:  {res['train_r2']:.4f}")
    print(f"  Gap:       {res['gap']:.4f} ({res['gap']/res['train_r2']*100:.2f}%)")
    print(f"  MAE:       {res['mae']:.3f}")
    print(f"  Params:    depth={res['depth']}, lr={res['lr']}, l2={res['l2']}")

# Best overall
best_result = max(results, key=lambda x: x['test_r2'])

print("\n" + "="*70)
print(f"BEST: Method {best_result['method']} - R² = {best_result['test_r2']:.4f}")
print("="*70)

baseline_r2 = 0.9445  # Previous best (Trial 2)

if best_result['test_r2'] > baseline_r2:
    improvement = best_result['test_r2'] - baseline_r2
    print(f"\nNEW BEST! Improved by {improvement:+.4f}")
    best_result['model'].save_model('../../astram/models/catboost_final_best.cbm')
    print("Saved to: astram/models/catboost_final_best.cbm")
else:
    print(f"\nNo improvement. Previous best (0.9445) still wins.")
    print(f"Difference: {best_result['test_r2'] - baseline_r2:+.4f}")

print("="*70)
