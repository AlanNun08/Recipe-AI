# Multi-stage build optimized for Google Cloud Run
FROM node:20-slim as frontend-builder

# Set working directory
WORKDIR /app/frontend

# Copy frontend package files
COPY frontend/package*.json ./
COPY frontend/yarn.lock ./

# Install dependencies
RUN yarn install --production=false --network-timeout 300000

# Copy frontend source
COPY frontend/ .

# Build frontend for production
RUN yarn build

# Python backend stage
FROM python:3.9-slim

# Set working directory
WORKDIR /app

# Install system dependencies (minimal for faster builds)
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    --no-install-recommends && \
    rm -rf /var/lib/apt/lists/*

# Copy and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy backend source (REVERTED TO WORKING STRUCTURE)
COPY backend/ ./backend/
COPY main.py .

# Copy built frontend from previous stage
COPY --from=frontend-builder /app/frontend/build/ ./frontend/build/

# Copy production startup script and make executable
COPY start_production.py .
COPY start.sh .
RUN chmod +x start_production.py start.sh

# Create non-root user for security
RUN useradd --create-home --shell /bin/bash app && \
    chown -R app:app /app
USER app

# Set environment variables for production
ENV NODE_ENV=production
ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1

# Expose port (Cloud Run will set PORT env var)
EXPOSE 8080

# Add health check (use correct port)
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD python -c "import requests; requests.get('http://localhost:' + __import__('os').environ.get('PORT', '8080') + '/health', timeout=10)"

# Start the application using startup script
CMD ["./start.sh"]