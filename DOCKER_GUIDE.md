# ASTRAM AI - Docker Deployment Guide

Run ASTRAM AI in an isolated, reproducible Docker container.

---

## Prerequisites

Install Docker:
- **Windows**: [Docker Desktop for Windows](https://docs.docker.com/desktop/install/windows-install/)
- **Mac**: [Docker Desktop for Mac](https://docs.docker.com/desktop/install/mac-install/)
- **Linux**: [Docker Engine](https://docs.docker.com/engine/install/)

Verify installation:
```bash
docker --version
docker-compose --version
```

---

## Quick Start (3 Commands)

### Option 1: Using Docker Compose (Recommended)

```bash
# 1. Build the container
docker-compose build

# 2. Start the application
docker-compose up

# 3. Access the application
# Open browser: http://localhost:5000
```

That's it! The application is now running in a container.

### Option 2: Using Docker Directly

```bash
# 1. Build the image
docker build -t astram-ai:latest .

# 2. Run the container
docker run -d -p 5000:5000 \
  -v $(pwd)/astram/models:/app/astram/models \
  -v $(pwd)/astram/data:/app/astram/data \
  --name astram-ai-app \
  astram-ai:latest

# 3. Access the application
# Open browser: http://localhost:5000
```

---

## Container Management

### Start/Stop Container

```bash
# Start
docker-compose up -d

# Stop
docker-compose down

# Restart
docker-compose restart
```

### View Logs

```bash
# Real-time logs
docker-compose logs -f

# Last 100 lines
docker-compose logs --tail=100
```

### Check Container Status

```bash
# Using docker-compose
docker-compose ps

# Using docker
docker ps
```

### Access Container Shell

```bash
# Using docker-compose
docker-compose exec astram-ai bash

# Using docker
docker exec -it astram-ai-app bash
```

---

## Testing the Deployment

### 1. Health Check

```bash
curl http://localhost:5000/api/metadata
```

Expected response:
```json
{
  "model_version": "Method 6 - Hybrid Interaction-Heavy",
  "r2_score": 0.9522,
  "features_count": 36,
  "incidents_count": 8173
}
```

### 2. Test Prediction

```bash
curl -X POST http://localhost:5000/api/predict \
  -H "Content-Type: application/json" \
  -d '{
    "cause": "water_logging",
    "corridor": "Mysore Road",
    "hour": 8,
    "vehicle_type": "car",
    "road_closure": true
  }'
```

Expected: Impact score around 87.5 (Critical)

### 3. Open Web Interface

Navigate to: http://localhost:5000

You should see the ASTRAM AI Command Center dashboard.

---

## Troubleshooting

### Issue: Port 5000 already in use

**Solution**: Change port mapping in docker-compose.yml

```yaml
ports:
  - "8000:5000"  # Use port 8000 instead
```

Then access: http://localhost:8000

### Issue: Container exits immediately

**Check logs**:
```bash
docker-compose logs
```

**Common causes**:
1. Missing requirements.txt dependencies
2. Data file not found
3. Model file missing

**Fix**: Ensure all files are present:
```bash
ls requirements.txt
ls "Astram event data_anonymized - Astram event data_anonymizedb40ac87.csv"
ls astram/models/catboost_final_best.cbm
```

### Issue: Build fails on Windows

**Solution**: Use Git Bash or WSL2 for building

```bash
# In Git Bash or WSL2
docker-compose build --no-cache
```

### Issue: Permission denied (Linux)

**Solution**: Run with sudo or add user to docker group

```bash
sudo docker-compose up

# OR add user to docker group (one-time setup)
sudo usermod -aG docker $USER
# Log out and back in
```

---

## Performance Optimization

### Reduce Image Size

The current image is ~500MB. To reduce:

1. Use python:3.8-alpine base (smaller)
2. Multi-stage build to exclude build tools

Example optimized Dockerfile:

```dockerfile
FROM python:3.8-slim as builder
WORKDIR /app
COPY requirements.txt .
RUN pip install --user --no-cache-dir -r requirements.txt

FROM python:3.8-slim
WORKDIR /app
COPY --from=builder /root/.local /root/.local
COPY astram/ ./astram/
ENV PATH=/root/.local/bin:$PATH
CMD ["uvicorn", "astram.backend.app:app", "--host", "0.0.0.0", "--port", "5000"]
```

### Enable Caching

Add volume for faster restarts:

```yaml
volumes:
  - ./astram/models:/app/astram/models
  - ./astram/data:/app/astram/data
  - astram-cache:/root/.cache  # Add this
```

---

## Deployment to Cloud

### Deploy to AWS ECS

```bash
# 1. Tag image
docker tag astram-ai:latest <your-aws-account>.dkr.ecr.us-east-1.amazonaws.com/astram-ai:latest

# 2. Push to ECR
docker push <your-aws-account>.dkr.ecr.us-east-1.amazonaws.com/astram-ai:latest

# 3. Create ECS task definition and service
# (Use AWS Console or Terraform)
```

### Deploy to Google Cloud Run

```bash
# 1. Build and push
gcloud builds submit --tag gcr.io/<project-id>/astram-ai

# 2. Deploy
gcloud run deploy astram-ai \
  --image gcr.io/<project-id>/astram-ai \
  --platform managed \
  --port 5000
```

### Deploy to Heroku

```bash
# 1. Login to Heroku container registry
heroku container:login

# 2. Build and push
heroku container:push web -a astram-ai-app

# 3. Release
heroku container:release web -a astram-ai-app
```

---

## Environment Variables

Add custom configuration via environment variables:

```yaml
# docker-compose.yml
environment:
  - PYTHONUNBUFFERED=1
  - TZ=Asia/Kolkata
  - MODEL_PATH=/app/astram/models/catboost_final_best.cbm
  - DATA_PATH=/app/astram/data/enhanced_features_data.csv
  - LOG_LEVEL=INFO
```

---

## Security Best Practices

1. **Don't run as root** (add non-root user in Dockerfile):

```dockerfile
RUN adduser --disabled-password --gecos '' appuser
USER appuser
```

2. **Use secrets for sensitive data**:

```bash
echo "my-secret-key" | docker secret create api_key -
```

3. **Scan for vulnerabilities**:

```bash
docker scan astram-ai:latest
```

4. **Limit container resources**:

```yaml
# docker-compose.yml
deploy:
  resources:
    limits:
      cpus: '1.0'
      memory: 1G
```

---

## Production Checklist

Before deploying to production:

- [ ] Build succeeds without errors
- [ ] Health check passes
- [ ] All API endpoints tested
- [ ] Logs are being collected
- [ ] Resource limits configured
- [ ] Environment variables set
- [ ] Volumes mounted for persistence
- [ ] Firewall rules configured
- [ ] HTTPS/SSL certificate added (use nginx reverse proxy)
- [ ] Monitoring enabled (Prometheus, Datadog, etc.)

---

## Why Docker?

**Benefits for ASTRAM AI**:

1. **Reproducibility**: Same environment everywhere (no "works on my machine")
2. **Isolation**: Dependencies don't conflict with host system
3. **Portability**: Deploy to any cloud provider
4. **Easy Scaling**: Run multiple containers behind load balancer
5. **Version Control**: Tag images (v1.0, v1.1, etc.)
6. **Quick Rollback**: If new version fails, restart old container
7. **Development Parity**: Dev, staging, prod all identical

**For Your Friend's Replication Issue**:
- No need to install Python, pip, dependencies manually
- No path issues, encoding errors, or platform differences
- Just docker-compose up and it works

---

## Support

If you encounter issues:

1. Check logs: `docker-compose logs`
2. Verify prerequisites: `docker --version`
3. Rebuild without cache: `docker-compose build --no-cache`
4. Check TROUBLESHOOTING.md for common errors

---

**Last Updated**: June 21, 2024
