"""
=============================================================================
 EXPERIMENT 4 — CatBoost Regressor WITHOUT requires_road_closure
=============================================================================
 The hardest test: can the model predict impact severity
 without knowing whether the road was closed?
 
 If yes → "The model learns severity from context, not from the label formula."
=============================================================================
"""

import pandas as pd
import numpy as np
import sys, io, warnings

warnings.filterwarnings("ignore")
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

from sklearn.model_selection import StratifiedKFold
from sklearn.metrics import (
    classification_report, confusion_matrix,
    f1_score, mean_absolute_error, mean_squared_error, r2_score
)
from catboost import CatBoostRegressor

# ─────────────────────────────────────────────────────────────────────────────
# LOAD
# ─────────────────────────────────────────────────────────────────────────────

DATA_PATH = r"d:\round2 - anti\project\model_ready.parquet"
df = pd.read_parquet(DATA_PATH)

print("=" * 70)
print(" EXPERIMENT 4: CatBoost Regressor — WITHOUT requires_road_closure")
print("=" * 70)
print(f"\n  Loaded: {df.shape[0]} rows × {df.shape[1]} columns")

# ─────────────────────────────────────────────────────────────────────────────
# FEATURE SETUP
# ─────────────────────────────────────────────────────────────────────────────

EXCLUDE_COLS = [
    "id",
    "event_cause", "event_type", "corridor", "veh_type", "police_station",
    "impact_score", "impact_class",
    # THE KEY EXCLUSION:
    "requires_road_closure",
]

# Also exclude NLP embeddings (they didn't help in Exp2)
EMBEDDING_COLS = [c for c in df.columns if c.startswith("desc_emb_")]

FEATURE_COLS = [
    c for c in df.columns
    if c not in EXCLUDE_COLS and c not in EMBEDDING_COLS
]

CLASS_ORDER = ["Low", "Medium", "High", "Critical"]
class_to_int = {c: i for i, c in enumerate(CLASS_ORDER)}

y_score = df["impact_score"]
y_class_int = df["impact_class"].map(class_to_int)

print(f"\n  Features: {len(FEATURE_COLS)} (NO requires_road_closure, NO embeddings)")
print(f"  Excluded feature: requires_road_closure (50% of label weight)")
for c in FEATURE_COLS:
    print(f"    {c}")

# ─────────────────────────────────────────────────────────────────────────────
# ALSO RUN EXP3-REPLAY (with closure) FOR DIRECT COMPARISON
# ─────────────────────────────────────────────────────────────────────────────

FEATURE_COLS_WITH_CLOSURE = FEATURE_COLS + ["requires_road_closure"]

def score_to_class(score):
    if score >= 65:
        return "Critical"
    elif score >= 40:
        return "High"
    elif score >= 20:
        return "Medium"
    else:
        return "Low"


def run_regression(name, feature_cols):
    print(f"\n{'─'*70}")
    print(f"  {name}")
    print(f"{'─'*70}")
    print(f"  Features: {len(feature_cols)} | Target: impact_score")

    X = df[feature_cols].copy()
    for col in X.columns:
        if X[col].dtype in ('float64', 'float32'):
            X[col] = X[col].fillna(-999)
        elif X[col].dtype in ('int64', 'int32'):
            X[col] = X[col].fillna(-1)

    params = {
        "iterations": 1000,
        "depth": 6,
        "learning_rate": 0.05,
        "l2_leaf_reg": 3,
        "loss_function": "RMSE",
        "eval_metric": "MAE",
        "random_seed": 42,
        "verbose": 0,
        "early_stopping_rounds": 50,
    }

    skf = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)
    all_preds = np.zeros(len(X))
    feature_importances = np.zeros(len(feature_cols))

    for fold, (train_idx, val_idx) in enumerate(skf.split(X, y_class_int)):
        X_train, X_val = X.iloc[train_idx], X.iloc[val_idx]
        y_train, y_val = y_score.iloc[train_idx], y_score.iloc[val_idx]

        model = CatBoostRegressor(**params)
        model.fit(X_train, y_train, eval_set=(X_val, y_val), verbose=0)

        preds = model.predict(X_val)
        all_preds[val_idx] = preds
        feature_importances += model.get_feature_importance() / 5

        fold_mae = mean_absolute_error(y_val, preds)
        print(f"    Fold {fold+1}: MAE = {fold_mae:.3f}")

    # Regression metrics
    mae = mean_absolute_error(y_score, all_preds)
    rmse = np.sqrt(mean_squared_error(y_score, all_preds))
    r2 = r2_score(y_score, all_preds)

    print(f"\n  ── REGRESSION RESULTS ──")
    print(f"  MAE:  {mae:.3f}")
    print(f"  RMSE: {rmse:.3f}")
    print(f"  R²:   {r2:.4f}")

    # Convert to classes
    pred_classes = pd.Series(all_preds).apply(score_to_class)
    pred_class_int = pred_classes.map(class_to_int).values

    macro_f1 = f1_score(y_class_int, pred_class_int, average="macro")
    weighted_f1 = f1_score(y_class_int, pred_class_int, average="weighted")

    print(f"\n  ── CLASSIFICATION (from regression) ──")
    print(f"  Macro F1:    {macro_f1:.4f}")
    print(f"  Weighted F1: {weighted_f1:.4f}")

    report = classification_report(
        y_class_int, pred_class_int,
        target_names=CLASS_ORDER, digits=3,
    )
    print(f"\n  Classification Report:")
    print(report)

    cm = confusion_matrix(y_class_int, pred_class_int)
    print(f"  Confusion Matrix (rows=true, cols=pred):")
    print(f"  {'':12s} {'Low':>8s} {'Medium':>8s} {'High':>8s} {'Critical':>8s}")
    for i, cls in enumerate(CLASS_ORDER):
        print(f"  {cls:12s} {cm[i,0]:8d} {cm[i,1]:8d} {cm[i,2]:8d} {cm[i,3]:8d}")

    # Feature importances
    imp_df = pd.DataFrame({
        "feature": feature_cols,
        "importance": feature_importances,
    }).sort_values("importance", ascending=False)

    print(f"\n  Top 20 Feature Importances:")
    for i, (_, row) in enumerate(imp_df.head(20).iterrows()):
        bar = "█" * int(row["importance"] / imp_df["importance"].max() * 30)
        print(f"    {i+1:2d}. {row['feature']:30s} {row['importance']:6.2f}  {bar}")

    return {
        "mae": mae, "rmse": rmse, "r2": r2,
        "macro_f1": macro_f1, "weighted_f1": weighted_f1,
        "importances": imp_df,
    }


# ─────────────────────────────────────────────────────────────────────────────
# RUN
# ─────────────────────────────────────────────────────────────────────────────

print(f"\n{'='*70}")
print(f" CONTROL: Exp3 replay (WITH requires_road_closure)")
print(f"{'='*70}")
exp3_replay = run_regression("Control: WITH closure", FEATURE_COLS_WITH_CLOSURE)

print(f"\n\n{'='*70}")
print(f" EXPERIMENT 4: WITHOUT requires_road_closure")
print(f"{'='*70}")
exp4 = run_regression("Exp4: WITHOUT closure", FEATURE_COLS)

# ─────────────────────────────────────────────────────────────────────────────
# COMPARISON
# ─────────────────────────────────────────────────────────────────────────────

print(f"\n\n{'='*70}")
print(f" COMPARISON: WITH vs WITHOUT requires_road_closure")
print(f"{'='*70}")
print(f"""
  ┌──────────────────────────┬──────────┬──────────┬──────────┬──────────┬──────────┐
  │ Model                    │   MAE    │   RMSE   │    R²    │ Macro F1 │Weight F1 │
  ├──────────────────────────┼──────────┼──────────┼──────────┼──────────┼──────────┤
  │ WITH closure (Exp3)      │  {exp3_replay['mae']:6.3f}  │  {exp3_replay['rmse']:6.3f}  │  {exp3_replay['r2']:.4f}  │  {exp3_replay['macro_f1']:.4f}  │  {exp3_replay['weighted_f1']:.4f}  │
  │ WITHOUT closure (Exp4)   │  {exp4['mae']:6.3f}  │  {exp4['rmse']:6.3f}  │  {exp4['r2']:.4f}  │  {exp4['macro_f1']:.4f}  │  {exp4['weighted_f1']:.4f}  │
  └──────────────────────────┴──────────┴──────────┴──────────┴──────────┴──────────┘

  Performance drop when removing requires_road_closure:
    MAE:        {exp4['mae'] - exp3_replay['mae']:+.3f}
    RMSE:       {exp4['rmse'] - exp3_replay['rmse']:+.3f}
    R²:         {exp4['r2'] - exp3_replay['r2']:+.4f}
    Macro F1:   {exp4['macro_f1'] - exp3_replay['macro_f1']:+.4f}
    Weighted F1:{exp4['weighted_f1'] - exp3_replay['weighted_f1']:+.4f}
""")

if exp4['r2'] > 0.70:
    print("  ✅ STRONG RESULT: R² > 0.70 even without the dominant feature.")
    print("     The model learns severity from CONTEXT, not from the scoring formula.")
    print("     This is a defensible AI value-add statement for judges.")
elif exp4['r2'] > 0.50:
    print("  ⚠ MODERATE: R² > 0.50 — model captures meaningful signal but weaker.")
else:
    print("  ❌ WEAK: R² < 0.50 — model struggles without closure information.")

print(f"\n{'='*70}")
print(f" EXPERIMENT 4 COMPLETE")
print(f"{'='*70}")
