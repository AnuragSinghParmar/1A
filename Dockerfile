# Adobe Hackathon Round 1A - PDF Document Structure Analyzer
# Optimized for linux/amd64, CPU-only execution

FROM --platform=linux/amd64 python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy project files
COPY src/ ./src/
COPY config/ ./config/

# Create necessary directories
RUN mkdir -p /app/input /app/output /app/logs

# Set Python path
ENV PYTHONPATH=/app/src:/app

# Set entrypoint
ENTRYPOINT ["python", "/app/src/main.py"]