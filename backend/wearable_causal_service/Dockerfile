# ==============================================================================
# OPEN HEALTH — WEARABLE INGESTION & CAUSAL INFERENCE MICROSERVICE
# Port: 5050
# ==============================================================================
FROM python:3.11-slim AS base

# Prevent Python from writing .pyc files and enable unbuffered output
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PORT=5050

WORKDIR /app

# Install system dependencies (curl for healthcheck, sqlite3 libraries)
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Install Python requirements
COPY requirements.txt /app/
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy microservice application source code
COPY . /app/

# Expose strictly Port 5050
EXPOSE 5050

# Container healthcheck targeting the /health endpoint
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD curl -f http://localhost:5050/health || exit 1

# Launch production ASGI server
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "5050"]

