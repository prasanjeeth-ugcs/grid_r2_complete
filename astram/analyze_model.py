import pandas as pd
import numpy as np
import sys
sys.path.insert(0, 'd:/round2 - anti/astram')
from backend.model_engine import model, FEATURE_COLS

df = pd.read_parquet('d:/round2 - anti/astram/data/model_ready.parquet')

# Predict on actual training data
X = df[FEATURE_COLS]
preds = np.array(model.predict(X))
print('=== Model predictions on TRAINING data ===')
print(f'  Mean:   {preds.mean():.3f}')
print(f'  Std:    {preds.std():.3f}')
print(f'  Min:    {preds.min():.3f}')
print(f'  Max:    {preds.max():.3f}')
print(f'  p50:    {np.percentile(preds, 50):.3f}')
print(f'  p90:    {np.percentile(preds, 90):.3f}')
print()

# Compare to actual
print('=== Actual impact_score ===')
actual = df['impact_score'].values
print(f'  Mean:   {actual.mean():.3f}')
print(f'  Std:    {actual.std():.3f}')
print()

# Check a few high-score rows from training data
high_score = df[df['impact_score'] >= 65].head(5)
print('=== High-score training examples ===')
for _, row in high_score.iterrows():
    feats = row[FEATURE_COLS].values
    pred = float(model.predict(pd.DataFrame([row[FEATURE_COLS]])))
    print(f'  actual={row["impact_score"]:.0f}  predicted={pred:.2f}  cause={row["event_cause"]}  corridor={row["corridor"]}  closure={row["requires_road_closure"]}  tier={row["corridor_tier"]}')

print()

# Check feature importance
fi = model.get_feature_importance()
print('=== Feature Importance (Top 10) ===')
for i in np.argsort(fi)[::-1][:10]:
    print(f'  {FEATURE_COLS[i]:30s}: {fi[i]:.2f}')
