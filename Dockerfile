# ASTRAM AI - Production Docker Container
# Python 3.9 base image (required for pandas 2.1.4 + CatBoost 1.2.2)
FROM python:3.9-slim

# Install system dependencies
# curl  — used by the healthcheck
# build-essential — required by some CatBoost native extensions
RUN apt-get update && apt-get install -y --no-install-recommends \
        build-essential \
        curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy pinned requirements first so this layer is cached unless deps change
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application source
COPY astram/ ./astram/
COPY ["Astram event data_anonymized - Astram event data_anonymizedb40ac87.csv", "./"]

# Create runtime directories and run the preprocessing pipeline.
# The outputs (parquet, lookup tables, model) are baked into the image.
# They can also be overridden at runtime via volume mounts.
RUN mkdir -p astram/data astram/models astram/backend/lookup_tables && \
    python astram/scripts/preprocess_data.py && \
    python astram/backend/precompute_lookups.py

# Expose the application port
EXPOSE 8000

# Health check — hits the lightweight /api/health endpoint
# start-period gives the app time to load the ML model on first request
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD curl -f http://localhost:8000/api/health || exit 1

# Production: 2 workers, port 8000, IST timezone baked via TZ env
CMD ["python", "-m", "uvicorn", "astram.backend.app:app", \
     "--host", "0.0.0.0", "--port", "8000", \
     "--workers", "2", "--log-level", "info"]
