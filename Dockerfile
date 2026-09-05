# ── Stage 1: Builder ──────────────────────────────────────────────────────────
FROM python:3.11-slim AS builder

WORKDIR /build

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --upgrade pip && \
    pip install --prefix=/install --no-cache-dir -r requirements.txt

# ── Stage 2: Runtime ──────────────────────────────────────────────────────────
FROM python:3.11-slim AS runtime

LABEL maintainer="Shinzo AI"
LABEL description="Emotionally intelligent AI companion — FastAPI application"

WORKDIR /app

# Copy installed packages from builder
COPY --from=builder /install /usr/local

# Copy application code
COPY app/ ./app/
COPY dataset/ ./dataset/
COPY pyproject.toml .

# Create persistent data directory for SQLite + FAISS indexes
RUN mkdir -p /data/shinzo_faiss_indexes && chmod 777 /data

# Non-root user for security
RUN useradd --no-create-home --shell /bin/false shinzo && \
    chown -R shinzo:shinzo /app && \
    chown -R shinzo:shinzo /data
USER shinzo

# Environment defaults (override with Render environment variables)
ENV SHINZO_ENV=production \
    LLM_PROVIDER=mock \
    DATABASE_URL=sqlite:////data/shinzo.db \
    PROACTIVE_ENABLED=true \
    QUIET_HOURS_START=22:00 \
    QUIET_HOURS_END=08:00 \
    API_AUTH_ENABLED=false \
    LOG_LEVEL=INFO \
    PORT=8000

EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=30s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health')"

CMD ["sh", "-c", "uvicorn app.api.main:app --host 0.0.0.0 --port ${PORT:-8000} --workers 1"]
