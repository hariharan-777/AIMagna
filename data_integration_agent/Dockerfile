# =============================================================================
# LLL Data Integration Agent - Dockerfile
# =============================================================================
# Compact multi-stage build using Python 3.12 (stable with ADK)
# =============================================================================

FROM python:3.12-slim-bookworm AS builder

WORKDIR /build

# Install build dependencies
RUN pip install --no-cache-dir --upgrade pip wheel

# Copy and install requirements
COPY requirements.txt .
RUN pip wheel --no-cache-dir --wheel-dir=/wheels -r requirements.txt

# =============================================================================
# Production image
# =============================================================================

FROM python:3.12-slim-bookworm

WORKDIR /app

# Install wheels from builder
COPY --from=builder /wheels /wheels
RUN pip install --no-cache-dir /wheels/* && rm -rf /wheels

# Copy application code
COPY . .

# Create logs directory
RUN mkdir -p /app/logs

# Environment variables (overridden by Secret Manager in Cloud Run)
ENV PORT=8080 \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

EXPOSE 8080

# Run the server - use $PORT environment variable
CMD ["sh", "-c", "python -m uvicorn server:app --host 0.0.0.0 --port $PORT"]
