# AI Code Review Multi-Agent System - Phase 1 Complete

A comprehensive multi-agent code review platform built with **Google ADK (Agent Development Kit)**, featuring native Ollama integration, LiteLLM routing, and containerized deployment.

## 🏗️ Architecture Overview

This system implements a **native Google ADK architecture** with six specialized analysis agents using ADK's `LlmAgent`, `FunctionTool`, and `BaseToolset` patterns:

- **Code Analyzer Agent**: Code structure, complexity, and architecture analysis using Tree-sitter AST parsing
- **Security Standards Agent**: OWASP vulnerabilities, security patterns, and threat modeling
- **Carbon Efficiency Agent**: Performance optimization, resource usage, and energy consumption analysis
- **Cloud Native Agent**: 12-factor compliance, container optimization, and cloud-native patterns
- **Microservices Agent**: Service boundaries, API design, and distributed system patterns  
- **Engineering Practices Agent**: SOLID principles, testing practices, and software quality metrics

## 🚀 Key Features

### Google ADK Native Implementation
- **✅ ADK LlmAgent**: All agents use Google ADK's native `LlmAgent` patterns
- **✅ FunctionTool Framework**: Real analysis tools using ADK's `FunctionTool` and `BaseToolset`
- **✅ ADK SessionService**: Native session management and state handling
- **✅ ADK Workflows**: `SequentialAgent`, `ParallelAgent`, and `LoopAgent` orchestration
- **✅ Custom ADK Dev Portal**: Full-featured web portal at http://localhost:8200

### Dual LLM Environment Support
- **🔧 Development**: Local Ollama integration (`llama3.1:8b`) via `host.docker.internal:11434`
- **🚀 Production**: Google Gemini (`gemini-2.0-flash-exp`) via Vertex AI
- **⚡ Auto-switching**: Environment-based provider selection with fallback support

### Real Code Analysis (No Mocks)
- **Tree-sitter Integration**: Multi-language AST parsing (Python, JS, TS, Java, Go, Rust, C++, C#)
- **Complexity Analysis**: Real cyclomatic complexity calculation and maintainability scoring
- **Security Scanning**: Pattern-based vulnerability detection using AST traversal
- **Architecture Analysis**: Dependency graphs, coupling detection, and design pattern recognition

### Production-Ready Development Environment
- **🐳 Docker Environment**: Complete containerized stack with all dependencies
- **📊 Custom ADK Portal**: Real-time monitoring, tool discovery, and workspace management
- **🔧 Debug Tools**: Redis Commander, File Browser, and comprehensive logging
- **📈 Health Monitoring**: Container health checks and service monitoring

## 📁 Project Structure

```
src/
├── tools/                      # ADK FunctionTool implementations
│   ├── base/                  # BaseToolset framework and schemas
│   ├── security/              # Security analysis tools (vulnerability scanner, auth analyzer)
│   ├── quality/               # Code quality tools (complexity analyzer, duplication detector)
│   ├── architecture/          # Architecture tools (dependency analyzer, coupling detector)
│   ├── carbon_efficiency/     # Energy analysis tools (resource optimizer, carbon footprint)
│   ├── cloud_native/          # Cloud-native tools (container analyzer, k8s validator)
│   ├── microservices/         # Microservices tools (service boundary, communication analyzer)
│   └── engineering_practices/ # Engineering tools (testing analyzer, CI/CD validator)
├── agents/                     # ADK native agents
│   ├── configs/               # ADK agent YAML configurations
│   └── adk_agents.py          # LlmAgent implementations and ADKWorkflowManager
├── core/                       # Core infrastructure
│   ├── config/                # Configuration management
│   ├── input/                 # Multi-source input processing
│   └── output/                # Output generation and formatting
├── memory/                     # Future: ADK MemoryService integration
└── api/                        # FastAPI application (future implementation)

outputs/                        # Agent-specific outputs
├── code_analyzer/             # Code analysis results
├── security_standards/        # Security findings
├── carbon_efficiency/         # Performance optimization results
├── cloud_native/              # Cloud-native assessment
├── microservices/             # Microservices analysis
├── engineering_practices/     # Best practices analysis
└── consolidated/              # Cross-agent summaries

config/
├── adk/                       # Google ADK configuration
│   ├── app.yaml              # Main application config
│   ├── llm_config.yaml       # Dual LLM provider setup
│   ├── session_config.yaml   # SessionService config
│   └── workflow_config.yaml  # Workflow agent configuration
├── agents/                    # Agent-specific configurations
├── rules/                     # Quality control and bias prevention
└── environments/              # Environment-specific configs

scripts/
├── start-adk-dev.sh          # ADK development environment launcher
├── adk-dev-portal.py         # Custom ADK development portal
└── setup scripts...          # Google Cloud setup automation
```

## 🛠️ Setup and Installation

### Prerequisites
- Python 3.11+
- Docker & Docker Compose (recommended)
- Google Cloud account (for Gemini API)
- Redis (managed in Docker environment)

### Quick Start

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd ai-code-review-multi-agent
   ```

2. **Run with Docker (Recommended)**
   ```bash
   # Start ADK development environment
   docker-compose --profile development up -d

   # Access ADK Dev Portal at http://localhost:8200
   # Redis Commander at http://localhost:8081  
   # File Browser at http://localhost:8080
   ```

3. **Available Docker Profiles**
   - `development`: Core ADK environment with dev portal and debugging tools
   - `production`: Production-ready setup with monitoring
   - `full`: Complete stack with all services
   - `minimal`: Lightweight setup for basic testing
   - `monitoring`: Adds Prometheus and Grafana
   - `tools`: Development tools only

4. **Or run locally**
   ```bash
   # Install dependencies (includes Tree-sitter parsers)
   pip install -e .

   # Setup environment
   chmod +x scripts/dev-setup.sh
   ./scripts/dev-setup.sh

   # Start ADK development environment
   chmod +x scripts/start-adk-dev.sh
   ./scripts/start-adk-dev.sh
   ```

### Configuration Setup

1. **Configure Environment**
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

2. **Google Cloud Setup (for Gemini API)**
   ```bash
   # Follow the setup guide
   ./scripts/setup-google-cloud.sh
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


Adk-web-ui docker commands

docker stop adk-web-ui
docker rm adk-web-ui
docker build -t agentic-code-review-system-adk-code-review 

docker run -d --name adk-web-ui -p 8400:8200 -v $(pwd):/app --workdir /app agentic-code-review-system-adk-code-review adk web --host 0.0.0.0 --port 8200 .

sleep 30 && docker ps | grep adk-web-ui