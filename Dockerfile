# Production-optimized Dockerfile for Google Cloud deployment
# Supports both Cloud Run and App Engine

# ============================================================================
# Stage 1: Frontend Build
# ============================================================================
FROM node:20-alpine AS frontend-builder

WORKDIR /app/frontend

# Copy package files for better caching
COPY frontend/package*.json frontend/yarn.lock ./

# Install dependencies with updated lockfile handling
RUN yarn install --network-timeout 300000 --update-checksums || \
    yarn install --network-timeout 300000

# Copy source and build
COPY frontend/ .
RUN yarn build

# ============================================================================
# Stage 2: Python Backend
# ============================================================================
FROM python:3.11-slim AS backend

WORKDIR /app

# Install system dependencies (minimal for security)
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# Copy and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy application source
COPY backend/ ./backend/
COPY main.py server.py ./

# Copy environment file if it exists (create backend directory first if needed)
RUN mkdir -p ./backend/
COPY backend/.env ./backend/.env

# Copy built frontend from previous stage
COPY --from=frontend-builder /app/frontend/build/ ./frontend/build/

# Create non-root user for security
RUN useradd --create-home --shell /bin/bash app && \
    chown -R app:app /app
USER app

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import requests; requests.get('http://localhost:' + __import__('os').environ.get('PORT', '8080') + '/health', timeout=5)"

# Expose port
EXPOSE 8080

# Use universal startup script
CMD ["python", "server.py"]