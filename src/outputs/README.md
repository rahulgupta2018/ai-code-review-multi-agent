# Agent Output Directories

This directory contains structured outputs from all analysis agents.

## Directory Structure

### Agent-Specific Outputs
- `code_analyzer/` - Code structure, complexity, and architecture analysis
- `engineering_practices/` - SOLID principles, quality metrics, best practices
- `security_standards/` - OWASP vulnerabilities, security patterns, threat modeling
- `carbon_efficiency/` - Performance optimization, resource usage, energy consumption
- `cloud_native/` - 12-factor compliance, container optimization, cloud patterns
- `microservices/` - Service boundaries, API design, distributed system patterns

### Output Types
Each agent directory contains:
- `findings/` - Structured JSON findings for dashboard consumption
- `reports/` - Generated reports (HTML, PDF, Markdown)
- `metrics/` - Analysis metrics and trend data

### Consolidated Outputs
- `consolidated/` - Cross-agent executive summaries and comprehensive reports
  - `executive_summary.json` - High-level dashboard data
  - `technical_report.json` - Detailed technical findings
  - `metrics_dashboard.json` - Comprehensive metrics for dashboards
  - `trends_analysis.json` - Historical trends and patterns

## Usage

These outputs are generated automatically by the analysis agents and are designed for:
- Dashboard integration and visualization
- CI/CD pipeline consumption
- Executive reporting
- Historical trend analysis
- Cross-project learning and knowledge accumulation