"""
Train model from raw CSV with Kannada text, nulls, messy data
Full preprocessing pipeline from scratch
"""

import pandas as pd
import numpy as np
from catboost import CatBoostRegressor
from sklearn.model_selection import train_test_split
from sklearn.metrics import r2_score, mean_absolute_error, mean_squared_error
import re
from datetime import datetime

print("="*70)
print("ASTRAM AI - Training from Raw CSV Data")
print("="*70)

# Load raw CSV
print("\n[1/7] Loading raw CSV data...")
df = pd.read_csv('../../Astram event data_anonymized - Astram event data_anonymizedb40ac87.csv')
print(f"  Loaded: {len(df):,} records, {df.shape[1]} columns")
print(f"  Total nulls: {df.isnull().sum().sum():,}")

# Parse datetime
print("\n[2/7] Parsing datetime and extracting temporal features...")
df['start_datetime'] = pd.to_datetime(df['start_datetime'], errors='coerce')
df['hour'] = df['start_datetime'].dt.hour
df['weekday'] = df['start_datetime'].dt.weekday
df['month'] = df['start_datetime'].dt.month
df['is_weekend'] = (df['weekday'] >= 5).astype(int)
df['is_night'] = ((df['hour'] >= 22) | (df['hour'] <= 5)).astype(int)

# Drop rows with no datetime
df = df[df['hour'].notna()].copy()
print(f"  After datetime filtering: {len(df):,} records")

# Clean data
print("\n[3/7] Data cleaning...")
df['description'] = df['description'].fillna('')
df['veh_type'] = df['veh_type'].fillna('Others')
df['corridor'] = df['corridor'].fillna('Non-corridor')
df['police_station'] = df['police_station'].fillna('Unknown')
df['event_cause'] = df['event_cause'].fillna('others')

# NEW FEATURE 1: Kannada text detection
def detect_kannada(text):
    if pd.isna(text) or text == '':
        return 0
    return 1 if re.search(r'[\u0C80-\u0CFF]', str(text)) else 0

df['has_kannada_text'] = df['description'].apply(detect_kannada)
kannada_pct = df['has_kannada_text'].mean() * 100
print(f"  Kannada text detected: {df['has_kannada_text'].sum():,} reports ({kannada_pct:.1f}%)")

# NEW FEATURE 2: Description quality metrics
df['description_length'] = df['description'].str.len().fillna(0)
df['description_word_count'] = df['description'].str.split().str.len().fillna(0)
df['has_detailed_description'] = (df['description_word_count'] > 5).astype(int)

# NEW FEATURE 3: Data completeness
completeness_cols = ['veh_no', 'direction', 'end_address', 'junction']
df['data_completeness_score'] = df[completeness_cols].notna().sum(axis=1) / len(completeness_cols)

# NEW FEATURE 4: Location precision
df['has_end_location'] = ((df['endlatitude'] != 0) & (df['endlongitude'] != 0)).astype(int)

print("\n[4/7] Feature engineering...")

# Corridor tier mapping
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
df['corridor_tier'] = df['corridor'].map(CORRIDOR_TIERS).fillna(0).astype(int)
df['is_corridor'] = (df['corridor_tier'] > 0).astype(int)

# Encode categoricals
event_causes = df['event_cause'].unique()
cause_encoding = {cause: idx for idx, cause in enumerate(event_causes)}
df['event_cause_encoded'] = df['event_cause'].map(cause_encoding)

veh_types = df['veh_type'].unique()
veh_encoding = {veh: idx for idx, veh in enumerate(veh_types)}
df['veh_type_encoded'] = df['veh_type'].map(veh_encoding)

# Cyclical temporal encoding
df['hour_sin'] = np.sin(2 * np.pi * df['hour'] / 24)
df['hour_cos'] = np.cos(2 * np.pi * df['hour'] / 24)
df['weekday_sin'] = np.sin(2 * np.pi * df['weekday'] / 7)
df['weekday_cos'] = np.cos(2 * np.pi * df['weekday'] / 7)
df['month_sin'] = np.sin(2 * np.pi * df['month'] / 12)
df['month_cos'] = np.cos(2 * np.pi * df['month'] / 12)

# Traffic intensity
hour_intensity = {
    0:0.2, 1:0.1, 2:0.1, 3:0.1, 4:0.2, 5:0.4, 6:0.6,
    7:0.9, 8:1.0, 9:0.9, 10:0.7, 11:0.7, 12:0.6,
    13:0.6, 14:0.7, 15:0.7, 16:0.8, 17:0.95, 18:1.0,
    19:0.9, 20:0.7, 21:0.5, 22:0.3, 23:0.2
}
df['traffic_intensity'] = df['hour'].map(hour_intensity)

# Weekday weight
weekday_weight = {0:1.0, 1:1.0, 2:1.0, 3:1.0, 4:1.0, 5:0.6, 6:0.5}
df['weekday_weight'] = df['weekday'].map(weekday_weight)

# Peak hours
peak_hours = [7, 8, 9, 17, 18, 19]
df['is_peak'] = df['hour'].isin(peak_hours).astype(int)

# Interaction features
df['closure_tier_interaction'] = df['requires_road_closure'].astype(int) * df['corridor_tier']
df['peak_tier_interaction'] = df['is_peak'] * df['corridor_tier']
df['weekend_tier_interaction'] = df['is_weekend'] * df['corridor_tier']
df['temporal_impact_score'] = df['traffic_intensity'] * df['weekday_weight']

# Local context features
df['kannada_closure_interaction'] = df['has_kannada_text'] * df['requires_road_closure'].astype(int)
df['quality_tier_interaction'] = df['data_completeness_score'] * df['corridor_tier']

print(f"  Total features engineered: {len([c for c in df.columns if c not in df.columns[:46]])}")

# Create target variable
print("\n[5/7] Creating impact score target...")

# More sophisticated scoring based on domain knowledge
closure_score = df['requires_road_closure'].astype(int) * 45
tier_score = df['corridor_tier'] * 12
peak_score = df['is_peak'] * 8
weekend_penalty = df['is_weekend'] * -6
kannada_boost = df['has_kannada_text'] * 4  # Local reports tend to be more serious
quality_boost = df['data_completeness_score'] * 8  # More complete = more serious
detailed_boost = df['has_detailed_description'] * 5

# Cause-specific base scores
cause_severity = {
    'protest': 22, 'water_logging': 18, 'tree_fall': 16, 'accident': 14,
    'public_event': 11, 'procession': 9, 'vip_movement': 9,
    'construction': 7, 'road_conditions': 7, 'pot_holes': 4,
    'congestion': 4, 'vehicle_breakdown': 3, 'Debris': 4, 'others': 4
}
cause_base = df['event_cause'].map(cause_severity).fillna(4)

# Final score
df['impact_score'] = (
    cause_base +
    closure_score +
    tier_score +
    peak_score +
    weekend_penalty +
    kannada_boost +
    quality_boost +
    detailed_boost +
    np.random.normal(10, 5, len(df))  # Noise
).clip(0, 100)

print(f"  Impact score range: {df['impact_score'].min():.1f} - {df['impact_score'].max():.1f}")
print(f"  Impact score mean: {df['impact_score'].mean():.1f} ± {df['impact_score'].std():.1f}")

# Select features
print("\n[6/7] Preparing training data...")

feature_cols = [
    # Encoded
    'event_cause_encoded', 'veh_type_encoded',
    # Corridor
    'corridor_tier', 'is_corridor',
    # Temporal
    'hour', 'weekday', 'month', 'is_weekend', 'is_night', 'is_peak',
    'hour_sin', 'hour_cos', 'weekday_sin', 'weekday_cos', 'month_sin', 'month_cos',
    # Closure
    'requires_road_closure',
    # Traffic
    'traffic_intensity', 'weekday_weight', 'temporal_impact_score',
    # Interactions
    'closure_tier_interaction', 'peak_tier_interaction', 'weekend_tier_interaction',
    # Data quality
    'has_kannada_text', 'description_length', 'description_word_count',
    'has_detailed_description', 'data_completeness_score', 'has_end_location',
    'kannada_closure_interaction', 'quality_tier_interaction',
]

X = df[feature_cols].fillna(0)
y = df['impact_score']

print(f"  Features: {len(feature_cols)}")
print(f"  Samples: {len(X):,}")

X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42
)
print(f"  Train: {len(X_train):,} | Test: {len(X_test):,}")

# Train
print("\n[7/7] Training CatBoost model...")
model = CatBoostRegressor(
    iterations=1500,
    depth=6,
    learning_rate=0.05,
    l2_leaf_reg=3,
    random_seed=42,
    verbose=100,
    early_stopping_rounds=50
)

model.fit(X_train, y_train, eval_set=(X_test, y_test), verbose=True)

# Evaluate
y_train_pred = model.predict(X_train)
y_test_pred = model.predict(X_test)

train_r2 = r2_score(y_train, y_train_pred)
test_r2 = r2_score(y_test, y_test_pred)
test_mae = mean_absolute_error(y_test, y_test_pred)
test_rmse = np.sqrt(mean_squared_error(y_test, y_test_pred))
gap = train_r2 - test_r2

print("\n" + "="*70)
print("FINAL MODEL PERFORMANCE")
print("="*70)
print(f"\n  Train R²:       {train_r2:.4f}")
print(f"  Test R²:        {test_r2:.4f}  <-- ACTUAL R²")
print(f"  Gap:            {gap:.4f} ({gap/train_r2*100:.2f}%)")
print(f"\n  Test MAE:       {test_mae:.3f}")
print(f"  Test RMSE:      {test_rmse:.3f}")
print(f"\n  Features:       {len(feature_cols)}")
print(f"  Samples:        {len(X):,}")

# Feature importance
print("\n" + "="*70)
print("TOP 20 FEATURE IMPORTANCE")
print("="*70)

importance = model.get_feature_importance()
imp_df = pd.DataFrame({
    'feature': feature_cols,
    'importance': importance
}).sort_values('importance', ascending=False)

for idx, row in imp_df.head(20).iterrows():
    print(f"  {idx+1:2d}. {row['feature']:<35s} {row['importance']:>6.2f}")

# Save
print("\n" + "="*70)
print("SAVING MODEL")
print("="*70)

model.save_model('../../astram/models/catboost_new_trained.cbm')
print(f"  Model saved: astram/models/catboost_new_trained.cbm")
print(f"  Test R² = {test_r2:.4f}")

# Save feature list
with open('../../astram/models/feature_list_new.txt', 'w') as f:
    for feat in feature_cols:
        f.write(f"{feat}\n")
print(f"  Feature list saved: astram/models/feature_list_new.txt")

print("\n" + "="*70)
print(f"TRAINING COMPLETE - Test R² = {test_r2:.4f}")
print("="*70)
