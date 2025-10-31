# Workflow Tracker - Docker Image for CI/CD
FROM python:3.11-slim

# Install system dependencies for graphviz and curl (for health checks)
RUN apt-get update && apt-get install -y \
    graphviz \
    libgraphviz-dev \
    pkg-config \
    git \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY src/ ./src/
COPY setup.py .
COPY .streamlit/ ./.streamlit/

# Install the package
RUN pip install -e .

# Create output directory
RUN mkdir -p /app/output

# Set environment variables
ENV PYTHONUNBUFFERED=1

# Default command - use the installed console script
ENTRYPOINT ["workflow-tracker"]
CMD ["--help"]
