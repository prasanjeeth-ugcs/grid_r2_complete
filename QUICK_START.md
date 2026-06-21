# ASTRAM AI - Quick Start Guide

Get ASTRAM AI running in **under 2 minutes**.

---

## Option 1: Docker (Recommended)

```bash
# Pull and run (easiest)
docker pull shivapreetham/astram-ai:latest
docker run -d -p 5000:5000 shivapreetham/astram-ai:latest

# Or build locally
docker-compose up -d
```

**Open:** http://localhost:5000

---

## Option 2: Manual Install

```bash
# Install
pip install -r requirements.txt

# Preprocess data
python preprocess_data.py
python astram/backend/precompute_lookups.py

# Run
python -m uvicorn astram.backend.app:app --port 5000
```

**Open:** http://localhost:5000

---

## Try a Demo

**Page 2: Response Copilot**
1. Select: `water_logging` + `Mysore Road` + Hour `8` + Closure `Yes`
2. Click "Analyze Incident"
3. See: Impact Score **28.2** (Medium), **1,775** similar incidents

---

## What You Get

- ✅ **27 API endpoints** (http://localhost:5000/docs)
- ✅ **3 web pages** (Command Center, Response Copilot, Corridor Intelligence)
- ✅ **CatBoost ML model** (R² = 0.9522)
- ✅ **8,173 incidents** analyzed
- ✅ **21 corridors** tracked

---

## Need Help?

- **Docs**: See [README.md](README.md) for full details
- **Docker**: See [DOCKER_GUIDE.md](DOCKER_GUIDE.md)
- **Video**: See [VIDEO_DEMO_SCRIPT.md](VIDEO_DEMO_SCRIPT.md)
- **Logs**: `docker logs -f <container-id>`

---

**That's it!** 🚀
