# AI Code Review Multi-Agent System

A comprehensive multi-agent code review platform built with Google GADK (Agent Development Kit) integration, featuring memory-aware analysis, real-time coordination, and dashboard-ready output generation.

## 🏗️ Architecture Overview

This system implements a memory-first, multi-agent architecture with six specialized analysis agents:

- **Code Analyzer Agent**: Code structure, complexity, and architecture analysis
- **Engineering Practices Agent**: SOLID principles, quality metrics, best practices
- **Security Standards Agent**: OWASP vulnerabilities, security patterns, threat modeling
- **Carbon Efficiency Agent**: Performance optimization, resource usage, energy consumption
- **Cloud Native Agent**: 12-factor compliance, container optimization, cloud patterns
- **Microservices Agent**: Service boundaries, API design, distributed system patterns

## 🚀 Key Features

### Multi-Agent Intelligence
- **Memory-Aware Analysis**: Agents learn from historical patterns and cross-project knowledge
- **Real-time Coordination**: Redis-based session management with WebSocket broadcasting
- **Intelligent Orchestration**: LLM-driven strategy selection (SMART/FOCUSED/PARALLEL)

### Google GADK Integration
- **Developer Portal**: End-to-end session visualization and debugging
- **Tool Orchestration**: GADK-compatible tool adapters with deterministic interfaces
- **Event-Driven Architecture**: Typed events and session lifecycle management

### Comprehensive Input Processing
- **Multi-Source Ingestion**: Local files, Git repositories, GitHub/GitLab API, ZIP archives
- **Tree-sitter AST Parsing**: Support for 10+ programming languages
- **Language Detection**: Automatic file type detection and processing

### Advanced Memory System
- **Dual Storage**: SQLite persistent memory + Redis real-time coordination
- **Pattern Recognition**: Learn and recognize code patterns across projects
- **Confidence Calibration**: Historical accuracy tracking and feedback integration

### Dashboard-Ready Outputs
- **Multi-Format Reports**: JSON, HTML, PDF, XML generation
- **Agent-Specific Storage**: Structured findings, reports, and metrics
- **Consolidated Reporting**: Executive summaries and comprehensive dashboards
- **Real-time Updates**: WebSocket-based progress broadcasting

## 📁 Project Structure

```
src/
├── integrations/gadk/          # Google GADK integration
├── core/                       # Core infrastructure
│   ├── config/                # Configuration management
│   ├── input/                 # Multi-source input processing
│   ├── output/                # Output generation and formatting
│   └── orchestrator/          # Smart agent orchestration
├── agents/                     # Analysis agents
│   ├── base/                  # Base agent classes
│   ├── code_analyzer/         # Code analysis agent
│   ├── engineering_practices/ # SOLID principles agent
│   ├── security_standards/    # Security analysis agent
│   ├── carbon_efficiency/     # Performance optimization agent
│   ├── cloud_native/          # Cloud-native patterns agent
│   └── microservices/         # Microservices patterns agent
├── memory/                     # Memory and learning system
│   ├── storage/               # SQLite + Redis storage
│   ├── retrieval/             # Multi-strategy retrieval
│   └── learning/              # Pattern recognition and learning
└── api/                        # FastAPI application
    ├── routes/                # API endpoints
    └── middleware/            # CORS, validation, error handling

outputs/                        # Agent-specific outputs
├── code_analyzer/             # Code analysis results
├── engineering_practices/     # Best practices analysis
├── security_standards/        # Security findings
├── carbon_efficiency/         # Performance optimization
├── cloud_native/              # Cloud-native assessment
├── microservices/             # Microservices analysis
└── consolidated/              # Cross-agent summaries

config/                         # Configuration files
├── agents/                    # Agent-specific configurations
├── llm/                       # LLM provider settings
├── orchestrator/              # Orchestration strategies
├── rules/                     # Quality control rules
└── environments/              # Environment-specific configs
```

## 🛠️ Setup and Installation

### Prerequisites
- Python 3.11+
- Redis (for real-time coordination)
- Poetry (for dependency management)
- Google Cloud credentials (for GADK integration)

### Development Setup

1. **Clone and Install Dependencies**
   ```bash
   git clone <repository-url>
   cd ai-code-review-multi-agent
   poetry install
   ```

2. **Configure Environment**
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

3. **Initialize Database**
   ```bash
   poetry run python -c "from src.memory.storage.memory_store import memory_store; print('Memory store initialized')"
   ```

4. **Start Redis** (for real-time coordination)
   ```bash
   redis-server
   ```

5. **Run Development Server**
   ```bash
   poetry run uvicorn src.api.main:app --reload --host 0.0.0.0 --port 8000
   ```

### Google Cloud Project Setup

The system includes automated scripts to set up Google Cloud projects with all required services:

#### Quick Setup (Recommended)
```bash
# Create project with chilternwarriors.cc@gmail.com (default)
./scripts/quick-gcp-setup.sh setup

# Or create with your own email
./scripts/quick-gcp-setup.sh setup-custom

# Test what would be created (dry run)
./scripts/quick-gcp-setup.sh test
```

#### Manual Configuration
```bash
# Update configuration file
./scripts/quick-gcp-setup.sh config

# Create project with custom settings
./scripts/create-google-cloud-project.sh create -e your-email@gmail.com -r europe-west1

# Verify setup
./scripts/quick-gcp-setup.sh verify
```

The setup script automatically:
- Creates a new Google Cloud project
- Enables all required APIs (Vertex AI, Discovery Engine, Dialogflow, etc.)
- Creates service accounts with proper permissions
- Sets up storage buckets
- Generates service account keys
- Updates your `.env` file

#### Configuration Management
The setup is fully configurable via `config/google-cloud-setup.yaml`:
```yaml
account:
  email: "chilternwarriors.cc@gmail.com"  # Change to your email
project:
  name_prefix: "ai-code-review-multi-agent"  # Customize project name
location:
  region: "us-central1"  # Change default region
```

### Google GADK Setup

After Google Cloud project setup:

1. **Install Google ADK**
   ```bash
   docker exec ai-code-review-gadk pip install google-adk
   ```

2. **Start Developer Portal** (automatically configured)
   ```bash
   # Portal starts automatically with the container
   # Access at: http://localhost:8200
   ```

## 🔧 Configuration

### Environment Variables
```bash
# Core Configuration
ENVIRONMENT=development
USE_GADK=false

# GADK Configuration
GADK_ENABLED=false
GADK_PROJECT_ID=your-project-id
GADK_DEV_PORTAL_HOST=localhost
GADK_DEV_PORTAL_PORT=8200

# LLM Providers
DEFAULT_LLM_PROVIDER=ollama
OLLAMA_BASE_URL=http://localhost:11434
OPENAI_API_KEY=your-openai-key
GEMINI_API_KEY=your-gemini-key

# Memory System
REDIS_URL=redis://localhost:6379
DATABASE_URL=sqlite:///data/memory.db
MEMORY_CONFIDENCE_THRESHOLD=0.7

# Logging
LOG_LEVEL=INFO
```

### Agent Configuration
Each agent can be configured individually in `config/agents/`:
- `code_analyzer.yaml` - Complexity thresholds, pattern detection
- `engineering_practices.yaml` - SOLID principles, quality metrics
- `security_standards.yaml` - OWASP rules, security patterns
- `carbon_efficiency.yaml` - Performance thresholds, optimization targets
- `cloud_native.yaml` - 12-factor compliance, container optimization
- `microservices.yaml` - Service boundary rules, API design patterns

## 🚀 Usage

### CLI Interface
```bash
# Analyze local directory
poetry run gadk-review analyze ./src --agents code_analyzer,security_standards

# Analyze Git repository
poetry run gadk-review analyze https://github.com/user/repo --strategy smart

# Generate dashboard export
poetry run gadk-review export --format dashboard --output ./reports
```

### API Usage
```python
import httpx

# Submit analysis
response = httpx.post("http://localhost:8000/api/v1/analysis", json={
    "source": {
        "type": "local",
        "path": "./src"
    },
    "agents": ["code_analyzer", "security_standards"],
    "strategy": "smart"
})

# Get results
analysis_id = response.json()["analysis_id"]
results = httpx.get(f"http://localhost:8000/api/v1/analysis/{analysis_id}/results")
```

### WebSocket Progress Updates
```javascript
const ws = new WebSocket('ws://localhost:8000/api/v1/analysis/progress');
ws.onmessage = function(event) {
    const progress = JSON.parse(event.data);
    console.log(`Analysis ${progress.session_id}: ${progress.progress}%`);
};
```

## 📊 Output Formats

### Dashboard Data
```json
{
  "summary": {
    "total_agents": 6,
    "total_findings": 23,
    "health_score": 85,
    "analysis_coverage": 92.5
  },
  "agent_metrics": [
    {
      "agent_name": "code_analyzer",
      "total_findings": 8,
      "critical_findings": 1,
      "quality_score": 8.2
    }
  ],
  "trends": {
    "quality_scores": [75.0, 78.0, 82.0, 85.0],
    "finding_counts": [45, 38, 32, 28]
  }
}
```

### Finding Structure
```json
{
  "id": "code_analyzer_1_20241001_123456",
  "title": "High Cyclomatic Complexity",
  "description": "Function exceeds complexity threshold",
  "severity": "warning",
  "category": "complexity",
  "file_path": "src/module.py",
  "line_number": 45,
  "recommendation": "Consider breaking down this function",
  "confidence": 0.9,
  "supporting_patterns": [
    {
      "type": "similar_pattern",
      "confidence": 0.85,
      "historical_accuracy": 0.92
    }
  ]
}
```

## 🧪 Testing

```bash
# Run all tests
poetry run pytest

# Run specific test categories
poetry run pytest -m unit          # Unit tests only
poetry run pytest -m integration   # Integration tests only
poetry run pytest -m memory        # Memory system tests
poetry run pytest -m gadk          # GADK integration tests

# Generate coverage report
poetry run pytest --cov=src --cov-report=html
```

## 📈 Monitoring and Observability

### GADK Developer Portal
- Session visualization and debugging
- Tool invocation traces
- Memory access patterns
- Real-time performance metrics

### Application Metrics
- Analysis execution times
- Memory system performance
- Agent accuracy scores
- Output generation metrics

### Logging
- Structured JSON logging
- Agent-specific log streams
- Memory operation tracking
- Error aggregation and alerting

## 🤝 Contributing

1. **Fork the repository**
2. **Create a feature branch** (`git checkout -b feature/amazing-feature`)
3. **Run tests and linting** (`poetry run pytest && poetry run black src`)
4. **Commit changes** (`git commit -m 'Add amazing feature'`)
5. **Push to branch** (`git push origin feature/amazing-feature`)
6. **Open a Pull Request**

### Development Guidelines
- Follow the existing code style (Black, isort, flake8)
- Write tests for new functionality
- Update documentation for API changes
- Use type hints throughout the codebase

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🔗 Related Documentation

- [Google GADK Documentation](https://cloud.google.com/agent-builder)
- [Implementation Plan](docs/google_gadk_implementation_plan.md)
- [Agent Architecture](docs/AGENT_ARCHITECTURE_EXPLANATION.md)
- [Memory System Design](docs/MEMORY_INTEGRATION_SUMMARY.md)

## 📞 Support

For issues and questions:
- Open an issue on GitHub
- Check the documentation in the `docs/` directory
- Review the configuration examples in `config/`