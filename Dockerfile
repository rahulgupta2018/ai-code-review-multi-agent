# Multi-stage Dockerfile for AI Code Review Multi-Agent System with AGDK Integration
# This Dockerfile creates a production-ready container with Google Cloud AGDK support

# Base stage with Python 3.11 and system dependencies
FROM python:3.11-slim as base

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
    libffi-dev \
    liblzma-dev \
    wget \
    ca-certificates \
    gnupg \
    lsb-release \
    && rm -rf /var/lib/apt/lists/*

# Install Poetry
RUN pip install poetry==$POETRY_VERSION
ENV PATH="$POETRY_HOME/bin:$PATH"

# Development stage with additional tools
FROM base as development

# Install development tools
RUN apt-get update && apt-get install -y \
    vim \
    nano \
    htop \
    tree \
    jq \
    && rm -rf /var/lib/apt/lists/*

# Install Google Cloud CLI
RUN echo "deb [signed-by=/usr/share/keyrings/cloud.google.gpg] https://packages.cloud.google.com/apt cloud-sdk main" | tee -a /etc/apt/sources.list.d/google-cloud-sdk.list && \
    curl https://packages.cloud.google.com/apt/doc/apt-key.gpg | apt-key --keyring /usr/share/keyrings/cloud.google.gpg add - && \
    apt-get update && apt-get install -y google-cloud-cli && \
    rm -rf /var/lib/apt/lists/*

# Install Google Cloud Python client libraries (for AGDK)
RUN pip install google-cloud-aiplatform google-cloud-discoveryengine google-cloud-dialogflow google-auth

# Create application user
RUN groupadd --gid 1000 appuser && \
    useradd --uid 1000 --gid appuser --shell /bin/bash --create-home appuser

# Set working directory
WORKDIR /app

# Copy dependency files
COPY pyproject.toml poetry.lock* ./

# Install Python dependencies
RUN poetry config virtualenvs.create false && \
    poetry install --no-dev && \
    rm -rf $POETRY_CACHE_DIR

# Production stage
FROM base as production

# Install Google Cloud CLI (minimal)
RUN echo "deb [signed-by=/usr/share/keyrings/cloud.google.gpg] https://packages.cloud.google.com/apt cloud-sdk main" | tee -a /etc/apt/sources.list.d/google-cloud-sdk.list && \
    curl https://packages.cloud.google.com/apt/doc/apt-key.gpg | apt-key --keyring /usr/share/keyrings/cloud.google.gpg add - && \
    apt-get update && apt-get install -y google-cloud-cli && \
    rm -rf /var/lib/apt/lists/*

# Create application user
RUN groupadd --gid 1000 appuser && \
    useradd --uid 1000 --gid appuser --shell /bin/bash --create-home appuser

# Set working directory
WORKDIR /app

# Copy dependency files
COPY pyproject.toml poetry.lock* ./

# Install Python dependencies (production only)
RUN poetry config virtualenvs.create false && \
    poetry install --only=main && \
    rm -rf $POETRY_CACHE_DIR

# Copy application code
COPY src/ ./src/
COPY config/ ./config/
COPY scripts/ ./scripts/

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

# AGDK-specific stage for agent development
FROM development as agdk

# Install additional AGDK development tools
RUN pip install google-agdk jupyter lab

# Install tree-sitter for multi-language parsing
RUN pip install tree-sitter tree-sitter-python tree-sitter-javascript tree-sitter-typescript tree-sitter-java tree-sitter-go tree-sitter-rust

# Create AGDK workspace
RUN mkdir -p /app/agdk-workspace /app/dev-portal

# Copy AGDK configuration
COPY config/agdk/ ./config/agdk/

# Set AGDK environment variables
ENV AGDK_WORKSPACE=/app/agdk-workspace \
    AGDK_DEV_PORTAL_PORT=8200 \
    AGDK_LOG_LEVEL=INFO

# Expose AGDK dev portal port
EXPOSE 8200

# Start script for AGDK development
COPY scripts/start-agdk-dev.sh /usr/local/bin/start-agdk-dev.sh
RUN chmod +x /usr/local/bin/start-agdk-dev.sh

# Default command for AGDK development
CMD ["/usr/local/bin/start-agdk-dev.sh"]

# Testing stage
FROM development as testing

# Install testing dependencies
RUN poetry install --with=dev,test

# Install additional testing tools
RUN pip install pytest-cov pytest-xdist pytest-mock coverage[toml]

# Copy test files
COPY tests/ ./tests/

# Default command for testing
CMD ["python", "-m", "pytest", "tests/", "-v", "--cov=src", "--cov-report=html", "--cov-report=term"]

# Final stage selection based on build argument
FROM ${BUILD_STAGE:-production} as final