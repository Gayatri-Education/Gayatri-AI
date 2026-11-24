# Production Dockerfile for Gayatri AI Assistant
# Configured for cloud container platforms and local Docker execution
FROM python:3.11-slim

# Prevent Python from writing .pyc files and enable unbuffered output for real-time logging
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    HOST=0.0.0.0 \
    PORT=8080 \
    WEB_MODE=true

WORKDIR /app

# Install minimal OS dependencies required for lxml, sentence-transformers, and networking
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    libxml2-dev \
    libxslt1-dev \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application source tree
COPY . .

# Ensure runtime directories exist
RUN mkdir -p /app/workspace /app/exports

# Expose default application port
EXPOSE 8080

# Dynamic port binding: reads $PORT provided by cloud container runtimes, defaults to 8080
CMD ["sh", "-c", "python main.py"]
