# ============================================
# Sentinel AI — Production Dockerfile
# Multi-stage build for minimal image size
# ============================================

# Stage 1: Builder — install Python dependencies
FROM python:3.11-slim AS builder

WORKDIR /build

# Install build dependencies for C extensions
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libffi-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy and install Python deps (layer cached unless requirements.txt changes)
COPY requirements.txt .
RUN pip install --no-cache-dir --prefix=/install -r requirements.txt


# Stage 2: Runtime — slim image with only what's needed
FROM python:3.11-slim AS runtime

# Install runtime system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    nmap \
    whois \
    dnsutils \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Create non-root user for security
RUN groupadd -r sentinel && useradd -r -g sentinel -m -s /bin/bash sentinel

WORKDIR /app

# Copy installed Python packages from builder stage
COPY --from=builder /install /usr/local

# Copy application source
COPY --chown=sentinel:sentinel . .

# Create necessary directories
RUN mkdir -p /app/logs /app/data /app/reports && \
    chown -R sentinel:sentinel /app/logs /app/data /app/reports

# Switch to non-root user
USER sentinel

# Expose API port
EXPOSE 8000

# Health check — fails if /health endpoint doesn't respond
HEALTHCHECK --interval=30s --timeout=10s --start-period=15s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Run the FastAPI application
CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "2"]
