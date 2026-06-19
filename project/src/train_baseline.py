"""
=============================================================================
 BASELINE EXPERIMENTS — Impact Class Prediction
=============================================================================
 Exp 1: CatBoost Classifier — Structured features only (baseline)
 Exp 2: CatBoost Classifier — Structured + NLP embeddings
 Exp 3: CatBoost Regressor  — Predict impact_score → convert to classes
=============================================================================
"""

import pandas as pd
import numpy as np
import sys, io, os, warnings, json
from datetime import datetime

warnings.filterwarnings("ignore")
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

from sklearn.model_selection import StratifiedKFold
from sklearn.metrics import (
    classification_report, confusion_matrix,
    f1_score, mean_absolute_error, mean_squared_error, r2_score
)
from catboost import CatBoostClassifier, CatBoostRegressor, Pool

# ─────────────────────────────────────────────────────────────────────────────
# LOAD DATA
# ─────────────────────────────────────────────────────────────────────────────

DATA_PATH = r"d:\round2 - anti\project\model_ready.parquet"
RESULTS_DIR = r"d:\round2 - anti\project\models"

print("=" * 70)
print(" BASELINE EXPERIMENTS — CatBoost Impact Prediction")
print("=" * 70)

df = pd.read_parquet(DATA_PATH)
print(f"\n  Loaded: {df.shape[0]} rows × {df.shape[1]} columns")
print(f"  Target distribution:")
print(f"    {df['impact_class'].value_counts().to_string()}")

# ─────────────────────────────────────────────────────────────────────────────
# DEFINE FEATURE SETS
# ─────────────────────────────────────────────────────────────────────────────

# Columns that are NOT features (identifiers, raw strings, targets)
EXCLUDE_COLS = [
    "id",
    "event_cause",       # raw string — use event_cause_encoded instead
    "event_type",        # raw string — use event_type_encoded instead
    "corridor",          # raw string — use corridor_tier instead
    "veh_type",          # raw string — use veh_type_encoded instead
    "police_station",    # raw string — use station_event_count instead
    "impact_score",      # target (regression)
    "impact_class",      # target (classification)
]

EMBEDDING_COLS = [c for c in df.columns if c.startswith("desc_emb_")]

# Structured features = everything except exclusions and embeddings
STRUCTURED_COLS = [
    c for c in df.columns
    if c not in EXCLUDE_COLS and c not in EMBEDDING_COLS
]

# Full features = structured + embeddings
FULL_COLS = STRUCTURED_COLS + EMBEDDING_COLS

print(f"\n  Feature sets:")
print(f"    Structured only:  {len(STRUCTURED_COLS)} features")
print(f"    + NLP embeddings: {len(FULL_COLS)} features ({len(EMBEDDING_COLS)} embedding dims)")

print(f"\n  Structured features:")
for c in STRUCTURED_COLS:
    print(f"    {c}")

# ─────────────────────────────────────────────────────────────────────────────
# TARGETS
# ─────────────────────────────────────────────────────────────────────────────

y_class = df["impact_class"]
y_score = df["impact_score"]

CLASS_ORDER = ["Low", "Medium", "High", "Critical"]
class_to_int = {c: i for i, c in enumerate(CLASS_ORDER)}
y_class_int = y_class.map(class_to_int)

# ─────────────────────────────────────────────────────────────────────────────
# CATBOOST PARAMS
# ─────────────────────────────────────────────────────────────────────────────

CATBOOST_CLF_PARAMS = {
    "iterations": 1000,
    "depth": 6,
    "learning_rate": 0.05,
    "l2_leaf_reg": 3,
    "loss_function": "MultiClass",
    "eval_metric": "TotalF1:average=Macro",
    "auto_class_weights": "Balanced",
    "random_seed": 42,
    "verbose": 0,
    "early_stopping_rounds": 50,
}

CATBOOST_REG_PARAMS = {
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

N_FOLDS = 5


def score_to_class(score):
    if score >= 65:
        return "Critical"
    elif score >= 40:
        return "High"
    elif score >= 20:
        return "Medium"
    else:
        return "Low"


# ─────────────────────────────────────────────────────────────────────────────
# EXPERIMENT RUNNER
# ─────────────────────────────────────────────────────────────────────────────

def run_classification_experiment(name, feature_cols, X_df, y, params):
    """Run stratified K-fold CatBoost classification experiment."""
    print(f"\n{'─'*70}")
    print(f"  {name}")
    print(f"{'─'*70}")
    print(f"  Features: {len(feature_cols)} | Samples: {len(X_df)}")

    X = X_df[feature_cols].copy()

    # Fill NaN for CatBoost (it handles them natively, but let's be safe)
    for col in X.columns:
        if X[col].dtype == 'float64' or X[col].dtype == 'float32':
            X[col] = X[col].fillna(-999)
        elif X[col].dtype in ['int64', 'int32']:
            X[col] = X[col].fillna(-1)

    skf = StratifiedKFold(n_splits=N_FOLDS, shuffle=True, random_state=42)

    all_preds = np.zeros(len(X), dtype=int)
    all_probs = np.zeros((len(X), len(CLASS_ORDER)))
    fold_scores = []
    feature_importances = np.zeros(len(feature_cols))

    for fold, (train_idx, val_idx) in enumerate(skf.split(X, y)):
        X_train, X_val = X.iloc[train_idx], X.iloc[val_idx]
        y_train, y_val = y.iloc[train_idx], y.iloc[val_idx]

        model = CatBoostClassifier(**params)
        model.fit(
            X_train, y_train,
            eval_set=(X_val, y_val),
            verbose=0,
        )

        preds = model.predict(X_val).flatten().astype(int)
        probs = model.predict_proba(X_val)
        all_preds[val_idx] = preds
        all_probs[val_idx] = probs

        fold_f1 = f1_score(y_val, preds, average="macro")
        fold_scores.append(fold_f1)
        feature_importances += model.get_feature_importance() / N_FOLDS

        print(f"    Fold {fold+1}: macro_f1 = {fold_f1:.4f}")

    # Overall metrics
    macro_f1 = f1_score(y, all_preds, average="macro")
    weighted_f1 = f1_score(y, all_preds, average="weighted")

    print(f"\n  ── RESULTS ──")
    print(f"  Macro F1:    {macro_f1:.4f}")
    print(f"  Weighted F1: {weighted_f1:.4f}")
    print(f"  Fold std:    ±{np.std(fold_scores):.4f}")

    # Classification report
    print(f"\n  Classification Report:")
    report = classification_report(
        y, all_preds,
        target_names=CLASS_ORDER,
        digits=3,
    )
    print(report)

    # Confusion matrix
    cm = confusion_matrix(y, all_preds)
    print(f"  Confusion Matrix (rows=true, cols=pred):")
    print(f"  {'':12s} {'Low':>8s} {'Medium':>8s} {'High':>8s} {'Critical':>8s}")
    for i, cls in enumerate(CLASS_ORDER):
        print(f"  {cls:12s} {cm[i,0]:8d} {cm[i,1]:8d} {cm[i,2]:8d} {cm[i,3]:8d}")

    # Feature importances
    importance_df = pd.DataFrame({
        "feature": feature_cols,
        "importance": feature_importances,
    }).sort_values("importance", ascending=False)

    print(f"\n  Top 20 Feature Importances:")
    for i, (_, row) in enumerate(importance_df.head(20).iterrows()):
        bar = "█" * int(row["importance"] / importance_df["importance"].max() * 30)
        print(f"    {i+1:2d}. {row['feature']:30s} {row['importance']:6.2f}  {bar}")

    return {
        "name": name,
        "macro_f1": macro_f1,
        "weighted_f1": weighted_f1,
        "fold_scores": fold_scores,
        "importances": importance_df,
        "predictions": all_preds,
        "model": model,  # last fold model
    }


def run_regression_experiment(name, feature_cols, X_df, y_cont, y_cls, params):
    """Run K-fold CatBoost regression, then convert predictions to classes."""
    print(f"\n{'─'*70}")
    print(f"  {name}")
    print(f"{'─'*70}")
    print(f"  Features: {len(feature_cols)} | Samples: {len(X_df)} | Target: impact_score")

    X = X_df[feature_cols].copy()
    for col in X.columns:
        if X[col].dtype == 'float64' or X[col].dtype == 'float32':
            X[col] = X[col].fillna(-999)
        elif X[col].dtype in ['int64', 'int32']:
            X[col] = X[col].fillna(-1)

    skf = StratifiedKFold(n_splits=N_FOLDS, shuffle=True, random_state=42)

    all_preds_score = np.zeros(len(X))
    fold_maes = []
    feature_importances = np.zeros(len(feature_cols))

    for fold, (train_idx, val_idx) in enumerate(skf.split(X, y_cls)):
        X_train, X_val = X.iloc[train_idx], X.iloc[val_idx]
        y_train, y_val = y_cont.iloc[train_idx], y_cont.iloc[val_idx]

        model = CatBoostRegressor(**params)
        model.fit(
            X_train, y_train,
            eval_set=(X_val, y_val),
            verbose=0,
        )

        preds = model.predict(X_val)
        all_preds_score[val_idx] = preds
        fold_mae = mean_absolute_error(y_val, preds)
        fold_maes.append(fold_mae)
        feature_importances += model.get_feature_importance() / N_FOLDS

        print(f"    Fold {fold+1}: MAE = {fold_mae:.3f}")

    # Regression metrics
    mae = mean_absolute_error(y_cont, all_preds_score)
    rmse = np.sqrt(mean_squared_error(y_cont, all_preds_score))
    r2 = r2_score(y_cont, all_preds_score)

    print(f"\n  ── REGRESSION RESULTS ──")
    print(f"  MAE:  {mae:.3f}")
    print(f"  RMSE: {rmse:.3f}")
    print(f"  R²:   {r2:.4f}")

    # Convert predictions to classes
    all_preds_class = pd.Series(all_preds_score).apply(score_to_class)
    all_preds_class_int = all_preds_class.map(class_to_int).values

    macro_f1 = f1_score(y_cls, all_preds_class_int, average="macro")
    weighted_f1 = f1_score(y_cls, all_preds_class_int, average="weighted")

    print(f"\n  ── CLASSIFICATION (from regression) ──")
    print(f"  Macro F1:    {macro_f1:.4f}")
    print(f"  Weighted F1: {weighted_f1:.4f}")

    report = classification_report(
        y_cls, all_preds_class_int,
        target_names=CLASS_ORDER,
        digits=3,
    )
    print(f"\n  Classification Report:")
    print(report)

    cm = confusion_matrix(y_cls, all_preds_class_int)
    print(f"  Confusion Matrix (rows=true, cols=pred):")
    print(f"  {'':12s} {'Low':>8s} {'Medium':>8s} {'High':>8s} {'Critical':>8s}")
    for i, cls in enumerate(CLASS_ORDER):
        print(f"  {cls:12s} {cm[i,0]:8d} {cm[i,1]:8d} {cm[i,2]:8d} {cm[i,3]:8d}")

    # Feature importances
    importance_df = pd.DataFrame({
        "feature": feature_cols,
        "importance": feature_importances,
    }).sort_values("importance", ascending=False)

    print(f"\n  Top 20 Feature Importances:")
    for i, (_, row) in enumerate(importance_df.head(20).iterrows()):
        bar = "█" * int(row["importance"] / importance_df["importance"].max() * 30)
        print(f"    {i+1:2d}. {row['feature']:30s} {row['importance']:6.2f}  {bar}")

    return {
        "name": name,
        "macro_f1": macro_f1,
        "weighted_f1": weighted_f1,
        "mae": mae,
        "rmse": rmse,
        "r2": r2,
        "importances": importance_df,
    }


# =============================================================================
# RUN EXPERIMENTS
# =============================================================================

print(f"\n{'='*70}")
print(f" EXPERIMENT 1: CatBoost Classifier — Structured Only (Baseline)")
print(f"{'='*70}")

exp1 = run_classification_experiment(
    "Exp1: Structured Only",
    STRUCTURED_COLS, df, y_class_int, CATBOOST_CLF_PARAMS,
)

print(f"\n{'='*70}")
print(f" EXPERIMENT 2: CatBoost Classifier — Structured + NLP Embeddings")
print(f"{'='*70}")

exp2 = run_classification_experiment(
    "Exp2: Structured + NLP",
    FULL_COLS, df, y_class_int, CATBOOST_CLF_PARAMS,
)

print(f"\n{'='*70}")
print(f" EXPERIMENT 3: CatBoost Regressor — Score Prediction → Class")
print(f"{'='*70}")

exp3 = run_regression_experiment(
    "Exp3: Regression → Class",
    FULL_COLS, df, y_score, y_class_int, CATBOOST_REG_PARAMS,
)


# =============================================================================
# COMPARISON SUMMARY
# =============================================================================

print(f"\n\n{'='*70}")
print(f" EXPERIMENT COMPARISON SUMMARY")
print(f"{'='*70}")
print(f"""
  ┌───────────────────────────────────┬───────────┬────────────┐
  │ Experiment                        │ Macro F1  │ Weighted F1│
  ├───────────────────────────────────┼───────────┼────────────┤
  │ Exp1: Structured Only (baseline)  │  {exp1['macro_f1']:.4f}   │   {exp1['weighted_f1']:.4f}   │
  │ Exp2: Structured + NLP           │  {exp2['macro_f1']:.4f}   │   {exp2['weighted_f1']:.4f}   │
  │ Exp3: Regression → Class          │  {exp3['macro_f1']:.4f}   │   {exp3['weighted_f1']:.4f}   │
  └───────────────────────────────────┴───────────┴────────────┘
""")

nlp_gain = exp2['macro_f1'] - exp1['macro_f1']
reg_vs_clf = exp3['macro_f1'] - exp2['macro_f1']

print(f"  NLP Embedding Gain (Exp2 - Exp1):  {nlp_gain:+.4f} macro F1")
print(f"  Regression vs Classification:      {reg_vs_clf:+.4f} macro F1")

if nlp_gain > 0.01:
    print(f"\n  → NLP embeddings ADD SIGNAL (+{nlp_gain:.4f}). Keep them.")
elif nlp_gain > -0.005:
    print(f"\n  → NLP embeddings are NEUTRAL ({nlp_gain:+.4f}). May drop for speed.")
else:
    print(f"\n  → NLP embeddings HURT performance ({nlp_gain:+.4f}). Remove them.")

# NLP feature importance analysis
print(f"\n  ── NLP vs Structured Feature Importance (Exp2) ──")
imp2 = exp2["importances"]
nlp_imp = imp2[imp2["feature"].str.startswith("desc_emb_")]["importance"].sum()
struct_imp = imp2[~imp2["feature"].str.startswith("desc_emb_")]["importance"].sum()
total_imp = nlp_imp + struct_imp
print(f"    Structured importance: {struct_imp:.1f} ({struct_imp/total_imp*100:.1f}%)")
print(f"    NLP embedding importance: {nlp_imp:.1f} ({nlp_imp/total_imp*100:.1f}%)")

# Save last model
model_path = os.path.join(RESULTS_DIR, "catboost_best.cbm")
best_exp = exp2 if exp2['macro_f1'] >= exp1['macro_f1'] else exp1
best_exp["model"].save_model(model_path)
print(f"\n  Best model saved: {model_path}")

print(f"\n{'='*70}")
print(f" EXPERIMENTS COMPLETE")
print(f"{'='*70}")
