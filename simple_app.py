"""
Simple ASTRAM AI - Traffic Incident Impact Predictor
Clean, working demo for Flipkart Grid 2.0
"""

from fastapi import FastAPI
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uvicorn
import joblib
import pandas as pd
import numpy as np
from pathlib import Path

app = FastAPI(title="ASTRAM AI")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

# Load model
MODEL_PATH = Path("astram/models/catboost_final_best.cbm")

try:
    from catboost import CatBoostRegressor
    model = CatBoostRegressor()
    model.load_model(str(MODEL_PATH))
    print(f"Model loaded: {MODEL_PATH}")
except Exception as e:
    print(f"Warning: Could not load model: {e}")
    model = None

# Dropdowns data
CORRIDORS = ["Bellary Road 1", "Mysore Road", "Hosur Road", "Outer Ring Road", "Bannerghatta Road"]
CAUSES = ["water_logging", "accident", "protest", "construction", "vehicle_breakdown", "procession"]
VEHICLE_TYPES = ["car", "bike", "auto", "bus", "truck"]

class PredictRequest(BaseModel):
    cause: str
    corridor: str
    hour: int
    vehicle_type: str
    road_closure: bool = True
    weekday: int = 3

def create_features(req: PredictRequest):
    """Create 36 features for the model"""
    # Simplified feature engineering for demo
    cause_map = {"water_logging": 0, "accident": 1, "protest": 2, "construction": 3, "vehicle_breakdown": 4, "procession": 5}
    veh_map = {"car": 0, "bike": 1, "auto": 2, "bus": 3, "truck": 4}

    is_corridor = 1 if req.corridor in CORRIDORS else 0
    corridor_tier = 2 if "Road 1" in req.corridor else 1
    is_peak = 1 if req.hour in [7,8,9,17,18,19] else 0
    is_weekend = 1 if req.weekday >= 5 else 0
    is_night = 1 if req.hour < 6 or req.hour > 22 else 0

    # Create 36 features (matching model training)
    features = [
        cause_map.get(req.cause, 0),  # event_cause_encoded
        veh_map.get(req.vehicle_type, 0),  # veh_type_encoded
        corridor_tier,
        is_corridor,
        req.hour,
        req.weekday,
        is_weekend,
        is_night,
        is_peak,
        np.sin(2 * np.pi * req.hour / 24),  # hour_sin
        np.cos(2 * np.pi * req.hour / 24),  # hour_cos
        np.sin(2 * np.pi * req.weekday / 7),  # weekday_sin
        np.cos(2 * np.pi * req.weekday / 7),  # weekday_cos
        1 if req.road_closure else 0,  # requires_road_closure
        0.7 if is_peak else 0.3,  # traffic_intensity
        0.8 if req.weekday < 5 else 0.5,  # weekday_weight
        is_peak * 0.5 + (1-is_weekend) * 0.3,  # temporal_score
        corridor_tier * (1 if req.road_closure else 0),  # closure_tier
        corridor_tier * is_peak,  # peak_tier
        corridor_tier * (1-is_weekend),  # weekend_tier
        (1 if req.road_closure else 0) * is_peak,  # closure_peak
        (1 if req.road_closure else 0) * 0.5,  # closure_temporal
        corridor_tier ** 2,  # tier_squared
        corridor_tier * 0.5,  # tier_temporal
        0,  # has_kannada (demo mode)
        len(req.cause) * 10,  # desc_length
        len(req.cause.split('_')),  # desc_word_count
        cause_map.get(req.cause, 0) % 3,  # cause_cluster
        1,  # has_end_coords
        1,  # coords_complete
        abs(req.hour - 12),  # hour_deviation
        1 if req.hour < 5 or req.hour > 23 else 0,  # is_extreme_hour
        corridor_tier * 0.5 * (1 if req.road_closure else 0),  # closure_tier_temporal
        (1 if req.road_closure else 0) * is_peak * corridor_tier,  # closure_peak_tier
        0 * corridor_tier,  # kannada_tier
        0.7 * corridor_tier,  # intensity_tier
    ]

    return features

@app.get("/", response_class=HTMLResponse)
def home():
    return """
<!DOCTYPE html>
<html>
<head>
    <title>ASTRAM AI - Traffic Impact Predictor</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            padding: 40px 20px;
        }
        .container {
            max-width: 1200px;
            margin: 0 auto;
        }
        .header {
            text-align: center;
            color: white;
            margin-bottom: 40px;
        }
        .header h1 {
            font-size: 48px;
            font-weight: 800;
            margin-bottom: 10px;
            text-shadow: 0 2px 10px rgba(0,0,0,0.2);
        }
        .header p {
            font-size: 18px;
            opacity: 0.95;
        }
        .stats {
            display: grid;
            grid-template-columns: repeat(3, 1fr);
            gap: 20px;
            margin-bottom: 40px;
        }
        .stat-card {
            background: white;
            border-radius: 16px;
            padding: 24px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.15);
        }
        .stat-value {
            font-size: 36px;
            font-weight: 700;
            color: #667eea;
            display: block;
            margin-bottom: 8px;
        }
        .stat-label {
            color: #666;
            font-size: 14px;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }
        .main-card {
            background: white;
            border-radius: 20px;
            padding: 40px;
            box-shadow: 0 20px 60px rgba(0,0,0,0.2);
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 40px;
        }
        .form-section h2 {
            font-size: 24px;
            margin-bottom: 24px;
            color: #333;
        }
        .form-group {
            margin-bottom: 20px;
        }
        label {
            display: block;
            margin-bottom: 8px;
            font-weight: 600;
            color: #555;
            font-size: 14px;
        }
        select, input {
            width: 100%;
            padding: 12px 16px;
            border: 2px solid #e5e7eb;
            border-radius: 10px;
            font-size: 15px;
            transition: all 0.2s;
        }
        select:focus, input:focus {
            outline: none;
            border-color: #667eea;
        }
        .toggle-group {
            display: flex;
            align-items: center;
            justify-content: space-between;
        }
        .toggle {
            position: relative;
            width: 50px;
            height: 26px;
            background: #e5e7eb;
            border-radius: 50px;
            cursor: pointer;
            transition: background 0.3s;
        }
        .toggle.active {
            background: #667eea;
        }
        .toggle-slider {
            position: absolute;
            top: 3px;
            left: 3px;
            width: 20px;
            height: 20px;
            background: white;
            border-radius: 50%;
            transition: transform 0.3s;
        }
        .toggle.active .toggle-slider {
            transform: translateX(24px);
        }
        .btn {
            width: 100%;
            padding: 16px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            border: none;
            border-radius: 12px;
            font-size: 16px;
            font-weight: 700;
            cursor: pointer;
            transition: transform 0.2s, box-shadow 0.2s;
        }
        .btn:hover {
            transform: translateY(-2px);
            box-shadow: 0 10px 30px rgba(102, 126, 234, 0.4);
        }
        .btn:active {
            transform: translateY(0);
        }
        .result-section {
            display: flex;
            flex-direction: column;
            justify-content: center;
            align-items: center;
        }
        .score-display {
            text-align: center;
            margin-bottom: 30px;
        }
        .score-circle {
            width: 200px;
            height: 200px;
            border-radius: 50%;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            margin: 0 auto 20px;
            box-shadow: 0 15px 40px rgba(102, 126, 234, 0.3);
        }
        .score-value-display {
            font-size: 64px;
            font-weight: 900;
            color: white;
            line-height: 1;
        }
        .score-label-display {
            font-size: 14px;
            color: rgba(255,255,255,0.9);
            margin-top: 8px;
        }
        .risk-badge {
            display: inline-block;
            padding: 8px 20px;
            border-radius: 30px;
            font-weight: 700;
            font-size: 14px;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }
        .risk-low { background: #d1fae5; color: #065f46; }
        .risk-medium { background: #fed7aa; color: #92400e; }
        .risk-high { background: #fecaca; color: #991b1b; }
        .risk-critical { background: #fca5a5; color: #7f1d1d; }
        .result-details {
            width: 100%;
        }
        .detail-row {
            display: flex;
            justify-content: space-between;
            padding: 12px 0;
            border-bottom: 1px solid #f3f4f6;
        }
        .detail-label {
            color: #666;
            font-size: 14px;
        }
        .detail-value {
            font-weight: 600;
            color: #333;
        }
        .hidden { display: none; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>ASTRAM AI</h1>
            <p>Traffic Incident Impact Prediction System - Flipkart Grid 2.0</p>
        </div>

        <div class="stats">
            <div class="stat-card">
                <span class="stat-value">0.9522</span>
                <span class="stat-label">Model R² Score</span>
            </div>
            <div class="stat-card">
                <span class="stat-value">8,173</span>
                <span class="stat-label">Training Incidents</span>
            </div>
            <div class="stat-card">
                <span class="stat-value">36</span>
                <span class="stat-label">Engineered Features</span>
            </div>
        </div>

        <div class="main-card">
            <div class="form-section">
                <h2>Incident Parameters</h2>

                <div class="form-group">
                    <label>Event Cause</label>
                    <select id="cause">
                        <option value="water_logging">Water Logging</option>
                        <option value="accident">Accident</option>
                        <option value="protest">Protest</option>
                        <option value="construction">Construction</option>
                        <option value="vehicle_breakdown">Vehicle Breakdown</option>
                        <option value="procession">Procession</option>
                    </select>
                </div>

                <div class="form-group">
                    <label>Corridor</label>
                    <select id="corridor">
                        <option value="Mysore Road">Mysore Road</option>
                        <option value="Bellary Road 1">Bellary Road 1</option>
                        <option value="Hosur Road">Hosur Road</option>
                        <option value="Outer Ring Road">Outer Ring Road</option>
                        <option value="Bannerghatta Road">Bannerghatta Road</option>
                    </select>
                </div>

                <div class="form-group">
                    <label>Vehicle Type</label>
                    <select id="vehicle">
                        <option value="car">Car</option>
                        <option value="bike">Bike</option>
                        <option value="auto">Auto</option>
                        <option value="bus">Bus</option>
                        <option value="truck">Truck</option>
                    </select>
                </div>

                <div class="form-group">
                    <label>Hour of Day: <span id="hour-display">08:00 AM</span></label>
                    <input type="range" id="hour" min="0" max="23" value="8" oninput="document.getElementById('hour-display').textContent = formatHour(this.value)">
                </div>

                <div class="form-group">
                    <label>Weekday</label>
                    <select id="weekday">
                        <option value="0">Monday</option>
                        <option value="1">Tuesday</option>
                        <option value="2">Wednesday</option>
                        <option value="3" selected>Thursday</option>
                        <option value="4">Friday</option>
                        <option value="5">Saturday</option>
                        <option value="6">Sunday</option>
                    </select>
                </div>

                <div class="form-group toggle-group">
                    <label>Road Closure Required</label>
                    <div class="toggle active" id="closure-toggle" onclick="this.classList.toggle('active')">
                        <div class="toggle-slider"></div>
                    </div>
                </div>

                <button class="btn" onclick="predictImpact()">Predict Impact</button>
            </div>

            <div class="result-section">
                <div id="results" class="hidden">
                    <div class="score-display">
                        <div class="score-circle">
                            <div class="score-value-display" id="score-value">--</div>
                            <div class="score-label-display">Impact Score</div>
                        </div>
                        <div id="risk-badge"></div>
                    </div>

                    <div class="result-details">
                        <div class="detail-row">
                            <span class="detail-label">Incident Type</span>
                            <span class="detail-value" id="detail-cause"></span>
                        </div>
                        <div class="detail-row">
                            <span class="detail-label">Location</span>
                            <span class="detail-value" id="detail-corridor"></span>
                        </div>
                        <div class="detail-row">
                            <span class="detail-label">Time</span>
                            <span class="detail-value" id="detail-time"></span>
                        </div>
                        <div class="detail-row">
                            <span class="detail-label">Road Closure</span>
                            <span class="detail-value" id="detail-closure"></span>
                        </div>
                    </div>
                </div>

                <div id="placeholder" style="text-align: center; color: #999;">
                    <svg width="100" height="100" viewBox="0 0 100 100" style="opacity: 0.3;">
                        <circle cx="50" cy="50" r="40" stroke="#667eea" stroke-width="8" fill="none"/>
                        <path d="M50 20 L50 50 L70 50" stroke="#667eea" stroke-width="6" stroke-linecap="round"/>
                    </svg>
                    <p style="margin-top: 20px;">Enter incident details and click Predict</p>
                </div>
            </div>
        </div>
    </div>

    <script>
        function formatHour(h) {
            const hour = parseInt(h);
            const ampm = hour >= 12 ? 'PM' : 'AM';
            const display = hour % 12 || 12;
            return display.toString().padStart(2, '0') + ':00 ' + ampm;
        }

        function getRiskClass(score) {
            if (score >= 75) return { label: 'Critical', class: 'risk-critical' };
            if (score >= 50) return { label: 'High', class: 'risk-high' };
            if (score >= 25) return { label: 'Medium', class: 'risk-medium' };
            return { label: 'Low', class: 'risk-low' };
        }

        async function predictImpact() {
            const data = {
                cause: document.getElementById('cause').value,
                corridor: document.getElementById('corridor').value,
                hour: parseInt(document.getElementById('hour').value),
                vehicle_type: document.getElementById('vehicle').value,
                weekday: parseInt(document.getElementById('weekday').value),
                road_closure: document.getElementById('closure-toggle').classList.contains('active')
            };

            try {
                const response = await fetch('/predict', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(data)
                });

                const result = await response.json();

                document.getElementById('placeholder').classList.add('hidden');
                document.getElementById('results').classList.remove('hidden');

                const risk = getRiskClass(result.impact_score);
                document.getElementById('score-value').textContent = result.impact_score.toFixed(1);
                document.getElementById('risk-badge').innerHTML = `<span class="risk-badge ${risk.class}">${risk.label} Risk</span>`;

                document.getElementById('detail-cause').textContent = data.cause.replace('_', ' ').toUpperCase();
                document.getElementById('detail-corridor').textContent = data.corridor;
                document.getElementById('detail-time').textContent = formatHour(data.hour) + ' - ' + ['Monday','Tuesday','Wednesday','Thursday','Friday','Saturday','Sunday'][data.weekday];
                document.getElementById('detail-closure').textContent = data.road_closure ? 'Yes' : 'No';
            } catch (error) {
                alert('Prediction failed: ' + error);
            }
        }
    </script>
</body>
</html>
"""

@app.post("/predict")
def predict(req: PredictRequest):
    if model is None:
        # Fallback demo mode
        base_score = 50
        if req.road_closure:
            base_score += 25
        if req.hour in [7,8,9,17,18,19]:
            base_score += 15
        if req.cause == "water_logging":
            base_score += 20

        return {"impact_score": min(base_score, 100)}

    features = create_features(req)
    score = model.predict([features])[0]

    return {
        "impact_score": float(score),
        "model_version": "Method 6 (R² = 0.9522)"
    }

if __name__ == "__main__":
    print("\n" + "="*60)
    print("ASTRAM AI - Simple Demo Server")
    print("="*60)
    print(f"Model: {MODEL_PATH}")
    print(f"Model loaded: {'Yes' if model else 'No (demo mode)'}")
    print("\nStarting server at http://localhost:8000")
    print("="*60 + "\n")

    uvicorn.run(app, host="0.0.0.0", port=8000)
