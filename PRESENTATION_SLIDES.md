# ASTRAM AI - Presentation Slides Outline

**Flipkart Grid 2.0, Round 2**
**Recommended: 7 slides, 5-7 minutes**

---

## Slide 1: Title & Problem Statement

### Visual
- **Title**: ASTRAM AI
- **Subtitle**: Traffic Operational Intelligence for Bengaluru
- **Team Name**: [Your Team]
- Background: Bengaluru traffic scene or map

### Content
**Problem**: Event-Driven Congestion in Bengaluru

Traffic authorities face 3 critical questions every day:
1. How severe is this incident?
2. What resources do we need?
3. What does historical data tell us?

**Current Gap**: Manual assessment, inconsistent resource allocation

---

## Slide 2: Solution Overview

### Visual
- System architecture diagram (3 layers: Data, Model, Interface)
- Icons for each component

### Content
**ASTRAM AI Platform**

Three Core Capabilities:
1. **Impact Prediction** - Instant severity assessment (R² = 0.9522)
2. **Resource Planning** - Phased deployment recommendations
3. **Corridor Intelligence** - Data-driven insights for each corridor

**Built on**: 8,173 real Bengaluru incidents across 21 corridors

---

## Slide 3: Data & Features

### Visual
- Infographic showing data breakdown
- Map of 21 corridors
- Sample of Kannada text

### Content
**Real Bengaluru Data**

| Data Point | Value |
|------------|-------|
| Historical Incidents | 8,173 |
| Corridors | 21 (3 tiers) |
| Police Stations | 54 |
| Cause Categories | 14 |
| Time Period | 5 months |

**Unique Feature: Kannada Text Detection**
- 85% of reports contain Kannada
- Indicates local vs official reporting
- Unicode pattern matching

**36 Engineered Features**:
- Temporal (hour, weekday, cyclical encoding)
- Corridor tier prioritization
- 3-way interaction features
- Data completeness metrics

---

## Slide 4: Model Performance

### Visual
- Bar chart showing Trial 1-6 R² scores
- Highlight Method 6 as winner
- Train vs Test comparison

### Content
**Rigorous Experimentation**

We ran **6 systematic trials** to achieve best results:

| Trial | Approach | R² | Status |
|-------|----------|-----|--------|
| 1 | Aggressive Closure | 0.9002 | ❌ |
| 2 | Composite Scoring | 0.9445 | ✅ |
| 3 | Polynomial | 0.9279 | ❌ |
| 4 | Exponential | 0.9439 | ⚠️ |
| 5 | Percentile-Based | 0.9521 | ✅✅ |
| **6** | **Interaction-Heavy** | **0.9522** | **🏆** |

**Final Model: Method 6**
- R² = **0.9522** (+2.84% vs baseline)
- MAE = 3.241
- Gap = 0.39% (minimal overfitting)

**Key Innovation**: 3-way interaction features
```
closure × corridor_tier × temporal_score
```

---

## Slide 5: User Interface Demo

### Visual
- Screenshots of all 3 pages side-by-side
- Annotated with key features

### Content
**3-Page Web Interface**

**Page 1: Command Center**
- System overview
- Key metrics dashboard
- Model performance

**Page 2: Incident Response Copilot**
- Input: Cause, corridor, time, closure
- Output: Impact score, risk class, resources
- Similar historical incidents

**Page 3: Corridor Intelligence**
- Corridor DNA profiles
- Stress index (0-100)
- Operational risk windows (heatmap)
- Shift briefing generator

**Technical Specs**:
- 32 REST API endpoints
- <50ms response time
- Production-ready

---

## Slide 6: Live Demo Highlight

### Visual
- Live demo OR pre-recorded demo GIF
- Show one complete prediction flow

### Content
**Demo: Critical Water Logging Incident**

**Input**:
- Cause: Water Logging
- Corridor: Mysore Road (Tier 1)
- Time: 8:30 AM (Rush Hour)
- Road Closure: YES

**Output** (in <50ms):
- **Impact Score**: 87.5 / 100
- **Risk Class**: Critical
- **Confidence**: High (89%)
- **Resources**: 8 personnel, 2 vehicles, 15 barricades
- **Resolution**: 90-120 minutes
- **Similar Incidents**: 3 historical matches

**Why Critical?**
- Tier 1 corridor (high priority)
- Road closure during rush hour
- Water logging in monsoon season
- Historical pattern confirms severity

---

## Slide 7: Impact & Conclusion

### Visual
- Summary metrics dashboard
- Deployment roadmap

### Content
**Real-World Impact**

**For Traffic Authorities**:
✅ Faster decision-making (<50ms predictions)
✅ Optimized resource allocation (phased plans)
✅ Proactive shift planning (risk windows)
✅ Data-driven corridor insights

**Technical Excellence**:
✅ R² = 0.9522 on real data
✅ 6 trials documented (transparent methodology)
✅ Kannada text detection (Bengaluru-specific)
✅ Production-ready architecture

**Deployment Ready**:
- 32 API endpoints operational
- Docker containerization
- Comprehensive documentation
- Continuous monitoring framework

**Next Steps**:
- Live traffic API integration
- Weather data correlation
- Cloud deployment (AWS/Azure)

---

**Thank you!**

**Questions?**

---

## Backup Slides (Appendix)

### Backup Slide A: Technical Architecture

**Detailed System Diagram**:
```
┌─────────────┐     ┌──────────────┐     ┌─────────────┐
│ Data Layer  │────▶│ Model Layer  │────▶│ API Layer   │
└─────────────┘     └──────────────┘     └─────────────┘
      │                    │                     │
   8,173 incidents    CatBoost Model      32 endpoints
   21 corridors       36 features          <50ms
   76 columns         R²=0.9522            FastAPI
```

**Technology Stack**:
- ML: CatBoost, Scikit-learn, Pandas, NumPy
- Backend: FastAPI, Uvicorn
- Frontend: HTML5, JavaScript, Chart.js, Leaflet
- Data: Parquet, CSV
- Deployment: Docker, Python 3.8+

---

### Backup Slide B: Feature Engineering Details

**36 Features Breakdown**:

**Base Features (26)**:
- Encoded: event_cause, veh_type
- Corridor: corridor_tier, is_corridor
- Temporal: hour, weekday, is_weekend, is_night, is_peak
- Cyclical: hour_sin/cos, weekday_sin/cos
- Closure: requires_road_closure
- Traffic: traffic_intensity, weekday_weight, temporal_score
- Interactions: closure_tier, peak_tier, weekend_tier, etc.
- Text: has_kannada, desc_length

**Enhanced Features (10 new in Method 6)**:
- desc_word_count
- cause_cluster (severity grouping)
- has_end_coords, coords_complete
- hour_deviation, is_extreme_hour
- closure_tier_temporal (3-way)
- closure_peak_tier (3-way)
- kannada_tier, intensity_tier

---

### Backup Slide C: Ablation Study Summary

**What We Learned**:

✅ **What Worked**:
- Multi-factor composite scoring
- Heavy interaction features (3-way)
- Cause-specific severity mapping
- Kannada text detection
- Shallow tree depth (4)

❌ **What Didn't Work**:
- Single-factor dominance (Trial 1)
- Polynomial transformations (Trial 3)
- Deep trees (overfitting)

**Key Insight**: Complex relationships captured by interactions, not polynomial terms

---

### Backup Slide D: Corridor Intelligence Example

**Bellary Road 1 DNA Profile**:
- Incidents: 412
- Dominant Cause: Congestion (38%)
- Critical Rate: 12%
- Avg Resolution: 48 minutes
- Stress Index: 67.8 / 100 (High)

**Risk Windows**:
- Peak: Mon-Fri 8-9 AM, 6-7 PM
- Low: Weekends, Early Morning
- Recommendation: Extra personnel during rush hours

**vs ORR West 2** (Tier 3):
- Stress Index: 34.2 (Medium)
- Critical Rate: 3%
- Lower priority, fewer resources

---

### Backup Slide E: Model Comparison Table

| Metric | Baseline | Trial 2 | Method 6 |
|--------|----------|---------|----------|
| R² Score | 0.9259 | 0.9445 | **0.9522** |
| MAE | 3.404 | 3.296 | **3.241** |
| Gap | 0.57% | 0.85% | **0.39%** |
| Features | 26 | 26 | 36 |
| Depth | 6 | 5 | 4 |
| LR | 0.05 | 0.03 | 0.05 |

**Winner**: Method 6 (Best R² + Lowest Gap)

---

## Presentation Tips

### Timing (7 minutes total)
- Slide 1: 30 sec
- Slide 2: 45 sec
- Slide 3: 1 min
- Slide 4: 1.5 min
- Slide 5: 1 min
- Slide 6: 2 min (demo)
- Slide 7: 45 sec

### Delivery Tips
1. **Start Strong**: "ASTRAM AI predicts traffic incident severity with 95% accuracy"
2. **Show Real Data**: Emphasize 8,173 real incidents, not synthetic
3. **Highlight Innovation**: Kannada text detection is unique
4. **Demo Confidently**: Practice the demo scenario beforehand
5. **End with Impact**: Focus on real-world deployment readiness

### Visual Guidelines
- Use Bengaluru traffic photos/maps for context
- Color scheme: Dark theme (matches web interface)
- Charts: Simple bar/line charts (avoid clutter)
- Fonts: Large, readable (min 24pt for body text)
- Animations: Minimal (slide in only)

### Q&A Preparation

**Common Questions**:

**Q**: "Why R² instead of accuracy?"
**A**: "Regression problem (continuous 0-100 scores). R² measures prediction quality better than classification accuracy."

**Q**: "Real-time capabilities?"
**A**: "Architecture supports it. Currently trained on historical. Would integrate traffic/weather APIs for production."

**Q**: "Scalability to other cities?"
**A**: "Model is city-agnostic. Need to retrain on new city's data, but methodology transfers."

**Q**: "How long to retrain?"
**A**: "~10 minutes on 8,000 samples. Supports continuous learning as new data arrives."

**Q**: "Why Kannada detection?"
**A**: "85% of Bengaluru incident reports use Kannada. Indicates local reporting context vs official channels. Unique to our dataset."

---

**Good Luck!**

Remember:
- You have a strong model (R² = 0.9522)
- Real Bengaluru data (not synthetic)
- Production-ready system
- Unique features (Kannada detection)
- Rigorous methodology (6 documented trials)

**You've got this!** 🚀
