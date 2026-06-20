"""
Enhanced Data Preprocessing Pipeline - ASTRAM AI V2.0 (Fast Version)
====================================================================

Core preprocessing without slow translation (translation moved to notebook).

Author: SHIVAPREETHAM ROHITH
Date: June 2026
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import warnings
warnings.filterwarnings('ignore')


def main():
    """Main preprocessing pipeline."""
    print("="*70)
    print("ASTRAM AI V2.0 - Enhanced Data Preprocessing Pipeline")
    print("="*70)

    # Load data
    print("\n[1/7] Loading data...")
    input_csv = "Astram event data_anonymized - Astram event data_anonymizedb40ac87.csv"
    df = pd.read_csv(input_csv, encoding='utf-8', low_memory=False)
    print(f"  Loaded {len(df):,} records with {len(df.columns)} columns")

    # Clean and standardize
    print("\n[2/7] Cleaning and standardizing...")
    df = df.replace(["NULL", "null", "None"], np.nan)

    # Boolean fields
    boolean_map = {'TRUE': True, 'FALSE': False, 'yes': True, 'no': False,
                   'True': True, 'False': False, True: True, False: False}
    if 'requires_road_closure' in df.columns:
        df['requires_road_closure'] = df['requires_road_closure'].map(boolean_map).fillna(False)
    if 'authenticated' in df.columns:
        df['authenticated'] = df['authenticated'].map(boolean_map).fillna(True)

    # Standardize fields
    df['corridor'] = df['corridor'].fillna('Non-corridor')
    df['event_cause'] = df['event_cause'].fillna('others')

    # Vehicle type mapping
    veh_map = {'bmtc_bus': 'BMTC Bus', 'ksrtc_bus': 'KSRTC Bus',
               'heavy_vehicle': 'Heavy Vehicle', 'lcv': 'LCV',
               'private_car': 'Private Car', 'private_bus': 'Private Bus',
               'truck': 'Truck', 'taxi': 'Taxi', 'auto': 'Auto'}
    df['veh_type'] = df['veh_type'].map(veh_map).fillna('Others')

    # Parse dates
    print("\n[3/7] Parsing temporal fields...")
    df['start_datetime'] = pd.to_datetime(df['start_datetime'], errors='coerce')
    df['end_datetime'] = pd.to_datetime(df['end_datetime'], errors='coerce')
    df['created_date'] = pd.to_datetime(df['created_date'], errors='coerce')
    df['resolved_datetime'] = pd.to_datetime(df['resolved_datetime'], errors='coerce')

    # Add forecasting features
    print("\n[4/7] Engineering forecasting features...")

    # Event date
    df['event_date'] = df['start_datetime'].dt.date

    # Time features
    df['hour'] = df['start_datetime'].dt.hour
    df['weekday'] = df['start_datetime'].dt.weekday
    df['month'] = df['start_datetime'].dt.month
    df['is_weekend'] = df['weekday'].isin([5, 6]).astype(int)
    df['is_night'] = df['hour'].isin(list(range(22, 24)) + list(range(0, 6))).astype(int)

    # Days since last incident (per corridor)
    df = df.sort_values(['corridor', 'start_datetime'])
    df['days_since_last_incident'] = df.groupby('corridor')['start_datetime'].diff().dt.total_seconds() / 86400
    df['days_since_last_incident'] = df['days_since_last_incident'].fillna(0)

    # Indian holidays
    holidays = pd.to_datetime(['2023-11-12', '2023-10-24', '2024-01-26',
                                '2024-03-08', '2024-08-15', '2024-10-12',
                                '2024-11-01']).date
    df['is_holiday'] = df['event_date'].isin(holidays).astype(int)

    # Moon phase (make timezone-aware)
    ref_new_moon = pd.Timestamp('2023-11-13', tz='UTC')
    df['days_since_new_moon'] = ((df['start_datetime'] - ref_new_moon).dt.total_seconds() / 86400) % 29.53
    df['moon_phase'] = (df['days_since_new_moon'] / 29.53 * 8).fillna(0).astype(int)

    # Weather placeholders
    df['weather_condition'] = None
    df['temperature_celsius'] = None
    df['rainfall_mm'] = None

    # Resolution time
    print("\n[5/7] Calculating resolution times...")
    df['resolution_time_hours'] = (df['resolved_datetime'] - df['start_datetime']).dt.total_seconds() / 3600
    df.loc[df['resolution_time_hours'] < 0, 'resolution_time_hours'] = np.nan
    df.loc[df['resolution_time_hours'] > 72, 'resolution_time_hours'] = 72

    # Fill missing with median by cause
    median_by_cause = df.groupby('event_cause')['resolution_time_hours'].median()
    df['resolution_time_hours'] = df.apply(
        lambda row: median_by_cause.get(row['event_cause'], 2.0)
        if pd.isna(row['resolution_time_hours']) else row['resolution_time_hours'],
        axis=1
    )

    # Translation placeholder (preserve original)
    print("\n[6/7] Preparing translation fields...")
    df['description_original'] = df['description']
    df['description_en'] = df['description']  # Translation will be done in notebook
    print("  (Translation will be performed in EDA notebook)")

    # Save
    print("\n[7/7] Saving enhanced dataset...")
    output_path = "astram/data/model_ready_v2.parquet"
    df.to_parquet(output_path, index=False, engine='pyarrow')
    print(f"  Saved to {output_path}")
    print(f"  Records: {len(df):,}, Columns: {len(df.columns)}")

    # Summary
    print("\n" + "="*70)
    print("Preprocessing Complete!")
    print("="*70)
    print(f"\nDataset Summary:")
    print(f"  Total records: {len(df):,}")
    print(f"  Date range: {df['start_datetime'].min()} to {df['start_datetime'].max()}")
    print(f"  Corridors: {df['corridor'].nunique()}")
    print(f"  Event causes: {df['event_cause'].nunique()}")
    print(f"  Median resolution time: {df['resolution_time_hours'].median():.2f} hours")
    print(f"  Kannada descriptions: {sum(1 for d in df['description'] if not pd.isna(d) and not str(d).isascii()):,}")

    return df


if __name__ == "__main__":
    df = main()
