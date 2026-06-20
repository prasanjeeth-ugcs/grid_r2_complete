"""
Enhanced Data Preprocessing Pipeline - ASTRAM AI V2.0
=====================================================

Improvements over V1:
1. Kannada to English translation using googletrans
2. Enhanced temporal features for forecasting
3. Data quality validation and reporting
4. Extended feature engineering for planned events

Author: SHIVAPREETHAM ROHITH
Date: June 2026
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import warnings
warnings.filterwarnings('ignore')

# Try importing googletrans, provide fallback if not installed
try:
    from googletrans import Translator
    TRANSLATOR_AVAILABLE = True
except ImportError:
    print("WARNING: googletrans not installed. Install with: pip install googletrans==3.1.0a0")
    TRANSLATOR_AVAILABLE = False


class EnhancedPreprocessor:
    """Enhanced preprocessing pipeline with Kannada translation and forecasting features."""

    def __init__(self, input_path, output_path="astram/data/model_ready_v2.parquet"):
        self.input_path = input_path
        self.output_path = output_path
        self.translator = Translator() if TRANSLATOR_AVAILABLE else None
        self.translation_cache = {}
        self.quality_report = {}

    def load_data(self):
        """Load raw CSV data."""
        print(f"Loading data from {self.input_path}...")

        # Read CSV with proper encoding
        df = pd.read_csv(self.input_path, encoding='utf-8', low_memory=False)

        print(f"Loaded {len(df)} records with {len(df.columns)} columns")
        self.quality_report['total_records'] = len(df)
        self.quality_report['total_columns'] = len(df.columns)

        return df

    def translate_text(self, text, src='kn', dest='en', max_retries=3):
        """
        Translate text from Kannada to English with caching and retry logic.

        Args:
            text: Text to translate
            src: Source language (default: 'kn' for Kannada)
            dest: Destination language (default: 'en' for English)
            max_retries: Maximum number of retry attempts

        Returns:
            Translated text or original if translation fails
        """
        if not TRANSLATOR_AVAILABLE or pd.isna(text) or text == "":
            return text

        # Check cache
        if text in self.translation_cache:
            return self.translation_cache[text]

        # Check if text is already in English (simple heuristic)
        if text.isascii():
            return text

        # Translate
        for attempt in range(max_retries):
            try:
                translation = self.translator.translate(text, src=src, dest=dest)
                translated_text = translation.text

                # Cache result
                self.translation_cache[text] = translated_text
                return translated_text

            except Exception as e:
                if attempt == max_retries - 1:
                    print(f"Translation failed after {max_retries} attempts for text: {text[:50]}...")
                    return text  # Return original if translation fails
                continue

        return text

    def translate_descriptions(self, df):
        """Translate all description fields from Kannada to English."""
        print("\nTranslating descriptions from Kannada to English...")

        if not TRANSLATOR_AVAILABLE:
            print("Skipping translation - googletrans not available")
            df['description_en'] = df['description']
            df['description_original'] = df['description']
            return df

        # Preserve original
        df['description_original'] = df['description']

        # Translate in batches to show progress
        total = len(df)
        batch_size = 100
        translations = []

        for i in range(0, total, batch_size):
            batch = df['description'].iloc[i:i+batch_size]
            batch_translations = []

            for text in batch:
                translated = self.translate_text(text)
                batch_translations.append(translated)

            translations.extend(batch_translations)

            if (i + batch_size) % 500 == 0:
                print(f"  Translated {min(i + batch_size, total)}/{total} descriptions...")

        df['description_en'] = translations

        # Count successful translations (non-ASCII original → ASCII result)
        kannada_count = sum(1 for orig in df['description_original']
                           if not pd.isna(orig) and not orig.isascii())
        translated_count = sum(1 for orig, trans in zip(df['description_original'], df['description_en'])
                              if not pd.isna(orig) and not orig.isascii() and trans.isascii())

        print(f"  Translated {translated_count}/{kannada_count} Kannada descriptions to English")
        self.quality_report['kannada_descriptions'] = kannada_count
        self.quality_report['translated_descriptions'] = translated_count

        return df

    def validate_data_quality(self, df):
        """Generate data quality validation report."""
        print("\nValidating data quality...")

        quality = {}

        # Missing values
        missing = df.isnull().sum()
        quality['missing_values'] = missing[missing > 0].to_dict()

        # Coordinate validation (Bengaluru bounds)
        valid_lat = df['latitude'].between(12.5, 13.5)
        valid_lon = df['longitude'].between(77.0, 78.0)
        quality['invalid_coordinates'] = len(df[~(valid_lat & valid_lon)])

        # Temporal consistency
        df['start_datetime'] = pd.to_datetime(df['start_datetime'], errors='coerce')
        df['end_datetime'] = pd.to_datetime(df['end_datetime'], errors='coerce')
        df['created_date'] = pd.to_datetime(df['created_date'], errors='coerce')

        quality['invalid_dates'] = df['start_datetime'].isnull().sum()

        # Event type distribution
        quality['event_type_distribution'] = df['event_type'].value_counts().to_dict()
        quality['event_cause_distribution'] = df['event_cause'].value_counts().to_dict()

        # Corridor coverage
        quality['corridor_coverage'] = df['corridor'].value_counts().to_dict()
        quality['corridor_null_count'] = df['corridor'].isnull().sum()

        self.quality_report['data_quality'] = quality

        print(f"  Invalid coordinates: {quality['invalid_coordinates']}")
        print(f"  Invalid dates: {quality['invalid_dates']}")
        print(f"  Missing corridor: {quality['corridor_null_count']}")

        return df

    def add_forecasting_features(self, df):
        """Add temporal and trend features for forecasting."""
        print("\nEngineering forecasting features...")

        # 1. Datetime index
        df['event_date'] = pd.to_datetime(df['start_datetime']).dt.date

        # 2. Days since last incident (per corridor)
        df = df.sort_values(['corridor', 'start_datetime'])
        df['days_since_last_incident'] = df.groupby('corridor')['start_datetime'].diff().dt.total_seconds() / 86400
        df['days_since_last_incident'] = df['days_since_last_incident'].fillna(0)

        # 3. Rolling window features (7-day lookback)
        df['incident_count_last_7d'] = df.groupby('corridor').rolling(
            window=7, on='start_datetime', min_periods=1
        )['id'].transform('count').values

        # 4. Indian holiday calendar (simplified)
        indian_holidays_2023_2024 = [
            '2023-11-12',  # Diwali 2023
            '2023-10-24',  # Dussehra 2023
            '2024-01-26',  # Republic Day
            '2024-03-08',  # Holi 2024
            '2024-08-15',  # Independence Day
            '2024-10-12',  # Dussehra 2024
            '2024-11-01',  # Diwali 2024
        ]
        holiday_dates = pd.to_datetime(indian_holidays_2023_2024).date
        df['is_holiday'] = df['event_date'].isin(holiday_dates).astype(int)

        # 5. Moon phase (simplified - for night incident correlation)
        # Using lunar cycle approximation (29.53 days)
        reference_new_moon = datetime(2023, 11, 13)  # Known new moon
        df['days_since_new_moon'] = (df['start_datetime'] - reference_new_moon).dt.days % 29.53
        df['moon_phase'] = (df['days_since_new_moon'] / 29.53 * 8).astype(int)  # 0-7 (8 phases)

        # 6. Weather placeholders (will be filled by weather API later)
        df['weather_condition'] = None
        df['temperature_celsius'] = None
        df['rainfall_mm'] = None

        print(f"  Added 8 forecasting features")

        return df

    def add_resolution_time_features(self, df):
        """Calculate resolution times for prediction targets."""
        print("\nCalculating resolution time features...")

        # Post-event resolution time (actual outcome)
        df['resolved_datetime'] = pd.to_datetime(df['resolved_datetime'], errors='coerce')
        df['resolution_time_hours'] = (
            df['resolved_datetime'] - df['start_datetime']
        ).dt.total_seconds() / 3600

        # Clean outliers (negative or > 72 hours)
        df.loc[df['resolution_time_hours'] < 0, 'resolution_time_hours'] = np.nan
        df.loc[df['resolution_time_hours'] > 72, 'resolution_time_hours'] = 72  # Cap at 3 days

        # Fill missing resolution times with median by cause
        median_by_cause = df.groupby('event_cause')['resolution_time_hours'].median()
        df['resolution_time_hours'] = df.apply(
            lambda row: median_by_cause.get(row['event_cause'], 2.0)
            if pd.isna(row['resolution_time_hours']) else row['resolution_time_hours'],
            axis=1
        )

        print(f"  Median resolution time: {df['resolution_time_hours'].median():.2f} hours")

        return df

    def clean_and_standardize(self, df):
        """Clean and standardize data formats."""
        print("\nCleaning and standardizing data...")

        # Replace literal "NULL" strings
        df = df.replace("NULL", np.nan)
        df = df.replace("null", np.nan)
        df = df.replace("None", np.nan)

        # Boolean fields
        boolean_map = {
            'TRUE': True, 'FALSE': False,
            'yes': True, 'no': False,
            'True': True, 'False': False,
            True: True, False: False
        }

        if 'requires_road_closure' in df.columns:
            df['requires_road_closure'] = df['requires_road_closure'].map(boolean_map).fillna(False)

        if 'authenticated' in df.columns:
            df['authenticated'] = df['authenticated'].map(boolean_map).fillna(True)

        # Standardize corridor names (fill Non-corridor)
        df['corridor'] = df['corridor'].fillna('Non-corridor')

        # Standardize event cause (fill with 'others')
        df['event_cause'] = df['event_cause'].fillna('others')

        # Vehicle type standardization
        veh_type_map = {
            'bmtc_bus': 'BMTC Bus',
            'ksrtc_bus': 'KSRTC Bus',
            'heavy_vehicle': 'Heavy Vehicle',
            'lcv': 'LCV',
            'private_car': 'Private Car',
            'private_bus': 'Private Bus',
            'truck': 'Truck',
            'taxi': 'Taxi',
            'auto': 'Auto'
        }
        df['veh_type'] = df['veh_type'].map(veh_type_map).fillna('Others')

        print(f"  Standardized {len(df)} records")

        return df

    def generate_quality_report_html(self):
        """Generate HTML quality report."""
        print("\nGenerating data quality report...")

        html = f"""
<!DOCTYPE html>
<html>
<head>
    <title>ASTRAM Data Preprocessing Quality Report</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 40px; background: #f5f5f5; }}
        h1 {{ color: #1a1a1a; }}
        h2 {{ color: #333; margin-top: 30px; }}
        .metric {{ background: white; padding: 15px; margin: 10px 0; border-radius: 5px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }}
        .metric-label {{ font-weight: bold; color: #666; }}
        .metric-value {{ font-size: 1.2em; color: #1a73e8; }}
        table {{ border-collapse: collapse; width: 100%; background: white; margin: 10px 0; }}
        th, td {{ padding: 12px; text-align: left; border-bottom: 1px solid #ddd; }}
        th {{ background-color: #1a73e8; color: white; }}
        .good {{ color: #0f9d58; font-weight: bold; }}
        .warning {{ color: #f4b400; font-weight: bold; }}
        .error {{ color: #db4437; font-weight: bold; }}
    </style>
</head>
<body>
    <h1>ASTRAM AI V2.0 - Data Preprocessing Quality Report</h1>
    <p>Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>

    <h2>Dataset Overview</h2>
    <div class="metric">
        <span class="metric-label">Total Records:</span>
        <span class="metric-value">{self.quality_report.get('total_records', 0):,}</span>
    </div>
    <div class="metric">
        <span class="metric-label">Total Columns:</span>
        <span class="metric-value">{self.quality_report.get('total_columns', 0)}</span>
    </div>

    <h2>Translation Summary</h2>
    <div class="metric">
        <span class="metric-label">Kannada Descriptions Found:</span>
        <span class="metric-value">{self.quality_report.get('kannada_descriptions', 0)}</span>
    </div>
    <div class="metric">
        <span class="metric-label">Successfully Translated:</span>
        <span class="metric-value">{self.quality_report.get('translated_descriptions', 0)}</span>
    </div>

    <h2>Data Quality Metrics</h2>
"""

        quality = self.quality_report.get('data_quality', {})

        # Invalid coordinates
        invalid_coords = quality.get('invalid_coordinates', 0)
        coord_class = 'good' if invalid_coords == 0 else 'warning'
        html += f"""
    <div class="metric">
        <span class="metric-label">Invalid Coordinates:</span>
        <span class="metric-value {coord_class}">{invalid_coords}</span>
    </div>
"""

        # Invalid dates
        invalid_dates = quality.get('invalid_dates', 0)
        date_class = 'good' if invalid_dates == 0 else 'warning'
        html += f"""
    <div class="metric">
        <span class="metric-label">Invalid Dates:</span>
        <span class="metric-value {date_class}">{invalid_dates}</span>
    </div>
"""

        html += """
    <h2>Event Type Distribution</h2>
    <table>
        <tr><th>Event Type</th><th>Count</th></tr>
"""

        for event_type, count in quality.get('event_type_distribution', {}).items():
            html += f"        <tr><td>{event_type}</td><td>{count:,}</td></tr>\n"

        html += """
    </table>

    <p style="margin-top: 40px; color: #666; font-size: 0.9em;">
        Report generated by ASTRAM AI Enhanced Preprocessing Pipeline<br>
        Author: SHIVAPREETHAM ROHITH
    </p>
</body>
</html>
"""

        report_path = "project/data/preprocessing_report.html"
        with open(report_path, 'w', encoding='utf-8') as f:
            f.write(html)

        print(f"  Quality report saved to {report_path}")

    def run_full_pipeline(self):
        """Execute full preprocessing pipeline."""
        print("="*70)
        print("ASTRAM AI V2.0 - Enhanced Data Preprocessing Pipeline")
        print("="*70)

        # Step 1: Load data
        df = self.load_data()

        # Step 2: Clean and standardize
        df = self.clean_and_standardize(df)

        # Step 3: Translate Kannada descriptions
        df = self.translate_descriptions(df)

        # Step 4: Validate quality
        df = self.validate_data_quality(df)

        # Step 5: Add forecasting features
        df = self.add_forecasting_features(df)

        # Step 6: Add resolution time features
        df = self.add_resolution_time_features(df)

        # Step 7: Generate quality report
        self.generate_quality_report_html()

        # Step 8: Save enhanced dataset
        print(f"\nSaving enhanced dataset to {self.output_path}...")
        df.to_parquet(self.output_path, index=False, engine='pyarrow')
        print(f"  Saved {len(df)} records with {len(df.columns)} columns")

        print("\n" + "="*70)
        print("Preprocessing complete!")
        print("="*70)

        return df


def main():
    """Main execution function."""

    # Input and output paths
    input_csv = "Astram event data_anonymized - Astram event data_anonymizedb40ac87.csv"
    output_parquet = "astram/data/model_ready_v2.parquet"

    # Run preprocessing
    preprocessor = EnhancedPreprocessor(input_csv, output_parquet)
    df = preprocessor.run_full_pipeline()

    # Display summary
    print("\nDataset Summary:")
    print(f"  Total records: {len(df):,}")
    print(f"  Date range: {df['start_datetime'].min()} to {df['start_datetime'].max()}")
    print(f"  Corridors: {df['corridor'].nunique()}")
    print(f"  Event causes: {df['event_cause'].nunique()}")
    print(f"  Columns: {len(df.columns)}")

    return df


if __name__ == "__main__":
    df = main()
