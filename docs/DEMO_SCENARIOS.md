# ASTRAM AI - Demo Scenarios

**Competition Demo Guide**
**Estimated Demo Time**: 5-7 minutes

---

## Demo Flow Overview

**Opening (30 seconds)**
- "ASTRAM AI is a traffic operational intelligence platform built for Bengaluru"
- "Trained on 8,173 real incidents from 21 major corridors"
- "Achieved R² = 0.9522 with our final model"

**3 Key Scenarios** (2 minutes each)
1. Critical Incident Response
2. Corridor Intelligence Analysis
3. System Comparison & Insights

**Closing (30 seconds)**
- Key metrics summary
- Real-world deployment readiness

---

## Scenario 1: Critical Incident Response
**Page**: Incident Response Copilot
**Duration**: 2 minutes
**Objective**: Show real-time incident assessment and resource planning

### Setup
```
Event Cause: water_logging
Corridor: Mysore Road (Tier 1 - High Priority)
Time: 08:30 (Morning Rush Hour)
Vehicle Type: Car
Road Closure: YES
```

### Script

**[Navigate to Page 2: Incident Response Copilot]**

> "Let me show you a critical scenario that happened during Bengaluru's monsoon season."

**[Fill in the form]**
- Cause: Water Logging
- Corridor: Mysore Road
- Hour: 8 (morning rush)
- Vehicle: Car
- Road Closure: Yes

**[Click Predict Impact]**

> "Within milliseconds, ASTRAM provides a complete operational assessment."

**Key Points to Highlight**:

1. **Impact Score: 87.5/100 (Critical)**
   - "The model predicted this as a Critical incident with 87.5 impact score"
   - "This makes sense - water logging + road closure + Tier 1 corridor + rush hour"

2. **Risk Classification: Critical**
   - "System automatically classifies into 4 risk tiers"
   - "Critical incidents get priority resource allocation"

3. **Confidence: High (89%)**
   - "Based on 247 similar historical incidents"
   - "The model has high confidence because we've seen this pattern before"

4. **Resource Plan**:
   - Phase 1 (0-15 min): 8 personnel, 2 vehicles, 15 barricades
   - Phase 2 (15-30 min): 6 personnel, 3 vehicles
   - **Resolution Time**: 90-120 minutes
   - "Complete operational timeline generated automatically"

5. **Similar Historical Incidents**:
   - "3 similar water logging incidents on Mysore Road"
   - "2 were Critical, 1 was High risk"
   - "Historical context helps validate predictions"

6. **Formula vs AI Toggle**:
   - **[Toggle to Formula mode]**
   - Formula: 82.3
   - **[Toggle back to AI]**
   - AI: 87.5
   - "AI model captures nuances that simple formulas miss"

**Transition**: "Now let me show you our corridor intelligence layer..."

---

## Scenario 2: Corridor Intelligence Analysis
**Page**: Corridor Intelligence
**Duration**: 2 minutes
**Objective**: Show data-driven corridor insights

### Setup
Select: **Bellary Road 1** (Tier 1 corridor)

### Script

**[Navigate to Page 3: Corridor Intelligence]**

> "Page 3 gives traffic authorities deep insights into each corridor's behavior patterns."

**[Select Bellary Road 1 from dropdown]**

**Key Points to Highlight**:

1. **Corridor DNA Profile**:
   - "Based on 412 historical incidents on Bellary Road 1"
   - Dominant Cause: Congestion (38%)
   - Critical Rate: 12% (higher than average)
   - Avg Resolution: 48 minutes
   - "Each corridor has a unique 'DNA' based on its history"

2. **Stress Index: 67.8/100**:
   - "Bellary Road 1 is a high-stress corridor"
   - "Stress = incident frequency × severity × closure rate"
   - Color-coded: Red (High Stress)

3. **Operational Risk Windows** (Heatmap):
   - Peak risks: Mon-Fri, 8-9 AM (Morning Rush)
   - Peak risks: Mon-Fri, 6-7 PM (Evening Rush)
   - Low risk: Weekends, Early Morning
   - "Helps with proactive shift planning"

4. **Shift Briefing**:
   - **[Select Morning Shift 7 AM - 3 PM]**
   - High-risk hours: 8-9 AM
   - Recommended actions: "Deploy extra personnel during 8-9 AM"
   - "Real briefing data for on-ground teams"

**[Switch to another corridor for comparison]**

**[Select ORR West 2 - Tier 3]**

5. **Corridor Comparison**:
   - Bellary Road 1 (Tier 1): Stress 67.8, Critical Rate 12%
   - ORR West 2 (Tier 3): Stress 34.2, Critical Rate 3%
   - "Clear difference between high-priority and low-priority corridors"

**Transition**: "Finally, let me show you the command center view..."

---

## Scenario 3: Command Center & System Intelligence
**Page**: Command Center
**Duration**: 1.5 minutes
**Objective**: Show system overview and data scale

### Script

**[Navigate to Page 1: Command Center]**

> "This is the central dashboard for traffic authorities."

**Key Points to Highlight**:

1. **Data Scale**:
   - 8,173 historical incidents
   - 21 corridors monitored
   - 54 police stations
   - 14 cause categories
   - "Real Bengaluru traffic data, not synthetic"

2. **Model Performance**:
   - **R² = 0.9522** (show prominently)
   - MAE: 3.24 points
   - Train-Test Gap: 0.39% (very low overfitting)
   - "Achieved through 6 experimental trials"
   - "Method 6: Hybrid Interaction-Heavy model won"

3. **Key Features**:
   - **Kannada Text Detection**:
     - "85% of incident reports contain Kannada text"
     - "We use Unicode detection to identify local vs official reports"
   - **36 Advanced Features**:
     - "Including 3-way interaction features"
     - "Corridor × Closure × Time interactions"
   - **Cause Clustering**:
     - "Events grouped by severity: High/Medium/Low"

4. **Real-Time Capabilities** (if simulator available):
   - **[Show Active Incidents]**
   - Live incident feed
   - System pulse metrics
   - "Production-ready for deployment"

5. **API Architecture**:
   - 32 REST API endpoints
   - FastAPI backend (<50ms response)
   - Precomputed lookup tables for speed
   - "Scalable for citywide deployment"

---

## Closing Summary (30 seconds)

> "To summarize, ASTRAM AI delivers three critical capabilities:"

1. **Accurate Impact Prediction**
   - R² = 0.9522 on real Bengaluru data
   - 36 advanced features including Kannada detection

2. **Operational Intelligence**
   - Corridor DNA profiles
   - Risk windows for shift planning
   - Historical pattern matching

3. **Production Ready**
   - 3-page responsive web interface
   - 32 API endpoints
   - <50ms response time
   - Ready for deployment

> "This isn't just a model - it's a complete operational platform built for Bengaluru's unique traffic challenges."

---

## Quick Reference: Numbers to Remember

| Metric | Value |
|--------|-------|
| Historical Incidents | 8,173 |
| Model R² | 0.9522 |
| Corridors | 21 |
| Model Features | 36 |
| API Endpoints | 32 |
| Kannada Detection | 85% of reports |
| Improvement vs Baseline | +2.84% |
| Train-Test Gap | 0.39% |
| Response Time | <50ms |

---

## Backup Scenarios (if extra time)

### Scenario 4: What-If Analysis
Show how predictions change with different inputs:
- Same incident WITHOUT road closure → Impact drops from 87.5 to 52.3
- Same incident at 2 AM (off-peak) → Impact drops to 41.8
- Different corridor (Tier 3) → Impact drops to 38.5

**Message**: "The model understands context and nuance"

### Scenario 5: Model Evolution
Show the ablation study:
- Trial 1: R² = 0.9002 (Failed)
- Trial 2: R² = 0.9445 (Success)
- Method 6: R² = 0.9522 (Winner)

**Message**: "Rigorous experimentation led to best results"

---

## Demo Tips

### Before Demo
- ✅ Test all 3 pages load correctly
- ✅ Verify API is running (port 5000)
- ✅ Have backup screenshots ready
- ✅ Practice transitions between pages

### During Demo
- ✅ Speak clearly and confidently
- ✅ Explain WHY each number matters
- ✅ Point out unique features (Kannada detection)
- ✅ Show real data, not toy examples
- ✅ Keep momentum - don't dwell too long on one screen

### If Technical Issues
- ✅ Have screenshots as backup
- ✅ Explain the concept even if UI doesn't load
- ✅ Emphasize the data and methodology

### Questions Judges Might Ask

**Q: Why R² and not accuracy?**
A: "This is a regression problem predicting continuous impact scores (0-100), not classification. R² measures how well we predict the severity, which is more valuable than simple classification."

**Q: How do you handle real-time data?**
A: "Currently trained on historical data. For real-time, we'd integrate with traffic APIs and weather feeds. The architecture supports it - we have a real-time simulator built in."

**Q: What makes this better than existing systems?**
A: "Three things: 1) Trained on real Bengaluru data (8,173 incidents), 2) Kannada text detection for local context, 3) Corridor-specific intelligence - each corridor has unique patterns."

**Q: Can this scale to other cities?**
A: "Absolutely. The architecture is city-agnostic. We'd need to retrain on that city's historical data and adapt corridor definitions, but the methodology transfers."

**Q: How did you improve R² from 0.9259 to 0.9522?**
A: "We ran 6 experimental trials testing different target variable formulations. Method 6 used heavy interaction features - 3-way interactions between closure, corridor tier, and temporal factors. Full ablation study documented."

---

## Post-Demo Follow-up

If judges want to see code or documentation:
- Show [ABLATION_STUDY.md](project/ABLATION_STUDY.md:1) - all 6 trials
- Show [ALL_TRIALS_SUMMARY.txt](project/src/ALL_TRIALS_SUMMARY.txt:1) - detailed results
- Show [PROJECT_STATUS.md](PROJECT_STATUS.md:1) - current state
- Show API docs in README

---

**Good luck with your demo!**
