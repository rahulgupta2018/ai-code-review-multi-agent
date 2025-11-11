# Simplified Dockerfile for ADK Code Review System

# Use Python 3.10 for better compatibility
FROM python:3.10-slim AS base

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    POETRY_VERSION=1.6.1 \
    POETRY_HOME="/opt/poetry" \
    POETRY_CACHE_DIR=/tmp/poetry_cache \
    POETRY_NO_INTERACTION=1 \
    POETRY_VENV_IN_PROJECT=1

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    git \
    && rm -rf /var/lib/apt/lists/*

# Install Poetry
RUN pip install poetry==$POETRY_VERSION
ENV PATH="$POETRY_HOME/bin:$PATH"

# Set working directory
WORKDIR /app

# Copy dependency files
COPY pyproject.toml ./

# Install Python dependencies
RUN poetry config virtualenvs.create false && \
    poetry install --no-dev && \
    rm -rf $POETRY_CACHE_DIR

# Copy source code
COPY . .

# Create required directories
RUN mkdir -p /app/logs /app/outputs /app/data /app/credentials /app/adk-workspace

# Expose ports
EXPOSE 8000 8200

# Health check - use docs endpoint since /health might not exist
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:8000/docs || exit 1

# Default command - run ADK web server directly pointing to main project structure
CMD ["adk", "web", "--host", "0.0.0.0", "--port", "8000", "/app"]