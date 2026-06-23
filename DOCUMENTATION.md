# ASTRAM AI - Documentation Index

Complete guide to all documentation files in this project.

---

## 📖 Documentation Files

### 1. **QUICK_START.md** ⭐ START HERE
**Purpose:** Get running in under 2 minutes
**For:** Everyone (judges, developers, users)
**Contains:**
- Docker one-liner
- Manual install steps
- Quick demo scenario

**When to use:** First time setup, quick demo

---

### 2. **README.md**
**Purpose:** Complete system documentation
**For:** Technical reviewers, developers
**Contains:**
- Full architecture details
- All 12 backend engines explained
- 32 API endpoints documented
- Model training details (R² = 0.9522)
- Project structure
- Design decisions

**When to use:** Understanding the full system

---

### 3. **DOCKER_GUIDE.md**
**Purpose:** Docker deployment guide
**For:** DevOps, deployment teams
**Contains:**
- Pull pre-built image
- Build locally
- Push to Docker Hub
- Troubleshooting
- System requirements

**When to use:** Deploying to production or sharing with team

---

### 4. **VIDEO_DEMO_SCRIPT.md**
**Purpose:** 2-minute video demo walkthrough
**For:** Presentation, judges, stakeholders
**Contains:**
- Timed script (5s opening, 70s main feature, 25s analytics)
- Key visualizations to show
- Camera and audio tips
- Demo scenario with exact inputs

**When to use:** Creating demo video or live presentation

---

## 🎯 Quick Navigation

**I want to...**

| Goal | Read This |
|------|-----------|
| Run the app NOW | [QUICK_START.md](QUICK_START.md) |
| Understand the system | [README.md](README.md) |
| Deploy with Docker | [DOCKER_GUIDE.md](DOCKER_GUIDE.md) |
| Make a demo video | [VIDEO_DEMO_SCRIPT.md](VIDEO_DEMO_SCRIPT.md) |
| Use the API | http://localhost:8000/docs (after starting) |

---

## 📊 System Overview

### What is ASTRAM AI?
Traffic incident severity prediction system for Bengaluru using ML.

### Key Stats
- **Accuracy:** R² = 0.9522 (95.22%)
- **Data:** 8,173 real incidents
- **Corridors:** 21 major roads
- **Model:** CatBoost Gradient Boosting
- **APIs:** 27 REST endpoints
- **Pages:** 3-page web interface

### Core Features
1. **Page 1:** Command Center (city-wide overview, heatmaps, maps)
2. **Page 2:** Response Copilot (AI predictions, resource planning) ⭐
3. **Page 3:** Corridor Intelligence (strategic analytics)

---

## 🚀 Getting Started (3 Steps)

### Step 1: Run the Application
```bash
docker pull shivapreetham/astram-ai:latest
docker run -d -p 8000:8000 shivapreetham/astram-ai:latest
```

### Step 2: Open Browser
Navigate to: http://localhost:8000

### Step 3: Try the Demo
- Go to Page 2 (Response Copilot)
- Select: water_logging + Mysore Road + Hour 8 + Closure Yes
- Click "Analyze Incident"
- See: Impact 28.2, 1,775 similar incidents

---

## 📁 Project Structure

```
grid_r2_complete/
├── QUICK_START.md           ← Start here
├── README.md                 ← Full documentation
├── DOCKER_GUIDE.md          ← Deployment guide
├── VIDEO_DEMO_SCRIPT.md      ← Demo walkthrough
├── DOCUMENTATION.md          ← This file
├── Dockerfile                ← Docker build config
├── docker-compose.yml        ← Docker compose config
├── requirements.txt          ← Python dependencies
├── preprocess_data.py        ← Data preprocessing
├── astram/
│   ├── backend/
│   │   ├── app.py            ← Main FastAPI app (27 endpoints)
│   │   ├── model_engine.py   ← CatBoost ML model
│   │   ├── precompute_lookups.py ← Generate lookup tables
│   │   └── lookup_tables/    ← 6 precomputed JSON files
│   ├── frontend/
│   │   └── index.html        ← 3-page web interface
│   └── models/
│       └── catboost_best.cbm ← Trained model
└── Astram event data_anonymized - *.csv ← 8,173 incidents
```

---

## 🔧 Tech Stack

| Layer | Technology |
|-------|-----------|
| ML Model | CatBoost 1.2.2 |
| Backend | FastAPI 0.108, Python 3.9 |
| Frontend | Vanilla JS, Leaflet.js, Chart.js |
| Data | Pandas 2.1.4, PyArrow 14.0.2 |
| Deployment | Docker, Docker Compose |
| APIs | REST (27 endpoints) |

---

## 📞 Support

**For issues:**
1. Check [DOCKER_GUIDE.md](DOCKER_GUIDE.md#troubleshooting)
2. View logs: `docker logs <container-id>`
3. Test API: `curl http://localhost:8000/api/metadata`

**For questions:**
- Review [README.md](README.md) for technical details
- Check API docs: http://localhost:8000/docs

---

## ✅ Deployment Checklist

**Before Demo:**
- [ ] Container running: `docker ps`
- [ ] Port 8000 accessible: `curl http://localhost:8000/`
- [ ] API responding: `curl http://localhost:8000/api/metadata`
- [ ] Browser opens: http://localhost:8000
- [ ] All 3 pages load (Command Center, Copilot, Intelligence)

**For Video:**
- [ ] Read [VIDEO_DEMO_SCRIPT.md](VIDEO_DEMO_SCRIPT.md)
- [ ] Practice demo scenario (water_logging on Mysore Road)
- [ ] Test screen recording software
- [ ] Prepare voiceover script

**For Deployment:**
- [ ] Read [DOCKER_GUIDE.md](DOCKER_GUIDE.md)
- [ ] Login to Docker Hub: `docker login`
- [ ] Tag image: `docker tag grid_r2_complete-astram-ai:latest username/astram-ai:latest`
- [ ] Push: `docker push username/astram-ai:latest`

---

**ASTRAM AI** - Bengaluru Traffic Operational Intelligence
*Flipkart Grid 2.0, Round 2 Submission*
