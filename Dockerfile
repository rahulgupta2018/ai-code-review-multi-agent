# Multi-stage Dockerfile for AI Code Review Multi-Agent System with Google ADK Integration

# Base stage with Python 3.11 and system dependencies
FROM python:3.11-slim AS base

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
    gcc \
    g++ \
    make \
    libffi-dev \
    libssl-dev \
    libbz2-dev \
    libreadline-dev \
    libsqlite3-dev \
    libncurses5-dev \
    libncursesw5-dev \
    xz-utils \
    tk-dev \
    libxml2-dev \
    libxmlsec1-dev \
    liblzma-dev \
    wget \
    ca-certificates \
    gnupg \
    lsb-release \
    && rm -rf /var/lib/apt/lists/*

# Install Poetry
RUN pip install poetry==$POETRY_VERSION
ENV PATH="$POETRY_HOME/bin:$PATH"

# Create application user
RUN groupadd --gid 1000 appuser && \
    useradd --uid 1000 --gid appuser --shell /bin/bash --create-home appuser

# Set working directory
WORKDIR /app

# Copy dependency files and README
COPY pyproject.toml poetry.lock* README.md ./

# Copy source code (needed for Poetry package installation)
COPY src/ ./src/

# Development stage with additional tools
FROM base AS development

# Install development tools
RUN apt-get update && apt-get install -y \
    vim \
    nano \
    htop \
    tree \
    jq \
    && rm -rf /var/lib/apt/lists/*

# Install Google Cloud CLI
RUN curl -sSL https://packages.cloud.google.com/apt/doc/apt-key.gpg | gpg --dearmor -o /usr/share/keyrings/cloud.google.gpg && \
    echo "deb [signed-by=/usr/share/keyrings/cloud.google.gpg] https://packages.cloud.google.com/apt cloud-sdk main" | tee -a /etc/apt/sources.list.d/google-cloud-sdk.list && \
    apt-get update && apt-get install -y google-cloud-cli && \
    rm -rf /var/lib/apt/lists/*

# Install Python dependencies with development packages
RUN poetry config virtualenvs.create false && \
    poetry install --with=dev && \
    rm -rf $POETRY_CACHE_DIR

# Copy configuration and infrastructure
COPY config/ ./config/
COPY infra/ ./infra/
COPY tests/ ./tests/

# Set permissions for scripts
RUN chmod +x ./infra/scripts/*.sh ./infra/scripts/*.py 2>/dev/null || true

# Create required directories
RUN mkdir -p /app/logs /app/outputs /app/data /app/credentials /app/adk-workspace && \
    chown -R appuser:appuser /app

# Production stage
FROM base AS production

# Install Google Cloud CLI (minimal)
RUN curl -sSL https://packages.cloud.google.com/apt/doc/apt-key.gpg | gpg --dearmor -o /usr/share/keyrings/cloud.google.gpg && \
    echo "deb [signed-by=/usr/share/keyrings/cloud.google.gpg] https://packages.cloud.google.com/apt cloud-sdk main" | tee -a /etc/apt/sources.list.d/google-cloud-sdk.list && \
    apt-get update && apt-get install -y google-cloud-cli && \
    rm -rf /var/lib/apt/lists/*

# Install Python dependencies (production only)
RUN poetry config virtualenvs.create false && \
    poetry install --only=main && \
    rm -rf $POETRY_CACHE_DIR

# Copy application files
COPY config/ ./config/
COPY infra/scripts/ ./scripts/

# Create required directories
RUN mkdir -p /app/logs /app/outputs /app/data /app/credentials && \
    chown -R appuser:appuser /app

# Switch to application user
USER appuser

# Expose port for API
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import sys; sys.exit(0)" || exit 1

# Default command
CMD ["python", "-m", "src.api.main"]

# ADK stage for Application Developer Kit integration  
FROM development AS adk

# Set ADK environment variables
ENV ADK_WORKSPACE=/app/adk-workspace \
    ADK_DEV_PORTAL_PORT=8200 \
    ADK_LOG_LEVEL=INFO

# Copy startup script
COPY infra/scripts/start-adk-dev.sh /usr/local/bin/start-adk-dev.sh
RUN chmod +x /usr/local/bin/start-adk-dev.sh

# Expose ADK dev portal port
EXPOSE 8000 8200

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Default command for ADK development
CMD ["/usr/local/bin/start-adk-dev.sh"]

# Testing stage
FROM development AS testing

# Install additional testing tools
RUN poetry install --with=test

# Default command for testing
CMD ["python", "-m", "pytest", "tests/", "-v", "--cov=src", "--cov-report=html", "--cov-report=term"]