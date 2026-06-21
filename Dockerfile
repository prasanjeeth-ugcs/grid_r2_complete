# ASTRAM AI - Production Docker Container
# Python 3.8+ base image
FROM python:3.8-slim

# Set working directory
WORKDIR /app

# Install system dependencies for CatBoost and data processing
RUN apt-get update && apt-get install -y \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better Docker layer caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY astram/ ./astram/
COPY "Astram event data_anonymized - Astram event data_anonymizedb40ac87.csv" ./

# Create data directory if it doesn't exist
RUN mkdir -p astram/data astram/models

# Expose port 5000 for FastAPI
EXPOSE 5000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import requests; requests.get('http://localhost:5000/api/metadata')" || exit 1

# Run the FastAPI server
CMD ["python", "-m", "uvicorn", "astram.backend.app:app", "--host", "0.0.0.0", "--port", "5000"]
