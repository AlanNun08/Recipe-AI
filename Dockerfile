# Dockerfile for AI Recipe + Grocery Delivery App
FROM python:3.9-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements file
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy backend code
COPY backend/ ./backend/

# Copy main.py (entry point)
COPY main.py .

# Copy frontend build (if exists)
COPY frontend/build/ ./frontend/build/

# Expose port (Google Cloud Run uses PORT environment variable)
EXPOSE 8080

# Set environment variables
ENV PYTHONPATH=/app
ENV PORT=8080

# Run the application
CMD ["python", "main.py"]