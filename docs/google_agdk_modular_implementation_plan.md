# Agentic Code Review on Google AGDK – Modular Implementation Plan

> Successor to `docs/google_agdk_implementation_plan.md`. Incorporates modular delivery slices, operational readiness, and governance improvements while retaining every architectural commitment from the original plan.

---

## 1. Executive Summary
- **Objective**: Deliver a memory-first, multi-agent code review platform running entirely on Google AGDK with backwards-compatible outputs and developer experience.
- **Strategy**: Ship in **incremental, independently testable slices**. Each slice culminates in a runnable artifact (CLI/API invocation, contract tests, or dev-portal trace) so we can validate, learn, and iterate rapidly.
- **Scope retained**: All original functional areas—runtime integration, tool extraction, advanced memory/learning, expanded agent catalog (6 agents), reporting, API, observability, and production rollout—remain in scope.
- **Key enhancements**:
  - MVP parity slice for the legacy Code Analyzer before advanced learning.
  - Split “foundation” and “memory” mega-phases into smaller, cross-functional increments.
  - Added environment provisioning, migration/rollback, ops, cost management, enablement, and RACI coverage.
  - Formalized quality gates, exit criteria, and tooling automation per increment.

---

## 2. Guiding Principles
1. **Feature-flagged adoption**: `analysis.use_agdk` governs rollout; legacy executor remains callable until GA sign-off.
2. **Vertical slices before horizontal scale**: The first production milestone is a Code Analyzer MVP on AGDK with baseline memory reads. Only then do we expand memory learning and additional agents.
3. **Contract-first interfaces**: Typed tool requests/responses, Pydantic configs, and OpenAPI schemas prevent regression when reusing heuristics.
4. **Observable by default**: Every runtime action surfaces telemetry in the AGDK Dev Portal plus Stackdriver/Grafana dashboards.
5. **Security & compliance built-in**: Google IAM, secret management, and audit trails are mandatory acceptance criteria for each environment.
6. **Operational excellence**: Runbooks, SLOs, and rollback plans are required before feature flags flip to “default on.”

---

## 3. Architectural Blueprint

### 3.1 Runtime & Orchestration
- `src/integrations/agdk/runtime_factory.py`: Factory for AGDK runtime sessions, feature flags, telemetry hooks.
- `src/core/orchestrator/smart_master_orchestrator.py`: Maintains logic to pick agents, now extended with AGDK session management and Redis-backed coordination.
- `src/core/orchestrator/state_manager.py`: Real-time state coordination using Redis Streams plus WebSocket broadcasting.
- Dev Portal: Containerized service exposing run traces, tool payloads, and memory interactions for every session.

### 3.2 Agent Catalog (6 total)
- `code_analyzer`, `engineering_practices`, `security_standards`, `carbon_efficiency`, `cloud_native`, `microservices`—all memory aware and running on AGDK.
- Each agent includes:
  - `agent.py`, `events.py`, `session_state.py`
  - Tool modules in `/tools/` directory implementing deterministic heuristics.
  - Output folders under `outputs/<agent>/` for findings, reports, metrics.

### 3.3 Tool Taxonomy & Contracts
- Tools lifted from legacy heuristics (complexity, architecture, patterns, LLM insights, QC) plus new ones (memory retrieval, pattern recognition, confidence scoring, report generation, dashboard exports).
- Contracts defined as Pydantic models in `src/agents/<domain>/google/schemas.py` for requests/responses, shared across runtime and tests.

### 3.4 Memory & Learning Architecture
- **Storages**: SQLite for persistent memory, Redis for coordination/ephemeral state.
- **Core modules**: `memory_store.py`, `memory_partitioning.py`, `memory_retriever.py`, `pattern_engine.py`, `confidence_scorer.py`, `feedback_loop.py`.
- **Capabilities**: Multi-dimensional partitioning (project/language/pattern/etc.), context-aware retrieval strategies, continuous learning with feedback, cross-agent knowledge sharing.

### 3.5 Configuration & Secrets
- Existing structure preserved (`config/app.yaml`, `config/agents/`, `config/llm/`, `config/rules/`, `config/orchestrator/`, `config/environments/`).
- Augment with AGDK toggles, Dev Portal endpoints, memory tuning, LLM fallback order, cost constraints, redis/sqlite connection details.
- `.env.example` extended with Google credentials, provider keys, memory thresholds, monitoring toggles.

### 3.6 Outputs & Reporting
- `OutputManager`, `ReportGenerator`, `DashboardExporter`, `IntegrationExporter`, `TemplateEngine` orchestrate JSON/HTML/PDF/XML outputs.
- Consolidated reports under `outputs/consolidated/` deliver executive summaries, technical deep dives, metrics dashboards, and trend analysis.

### 3.7 API Layer & Integrations
- FastAPI app with versioned routes (`/api/v1/system`, `/api/v1/analysis`, `/api/v1/findings`, `/api/v1/reports`, `/api/v1/exports`, `/api/v1/memory`, `/api/v1/stream`).
- Real-time WebSocket progress updates, CI/CD integration formats, authentication middleware, rate limiting, error handling, and validation.

---

## 4. Delivery Strategy

### 4.1 Release Trains & Vertical Slices
Each increment ends with:
- Feature flag toggles wired and default-off until quality gates met.
- Automated tests or smoke run executed via CI pipeline.
- Dev Portal trace or API call documented as evidence.

### 4.2 Workstreams
| Workstream | Scope | Primary Owners | Notes |
| --- | --- | --- | --- |
| **Runtime & Infrastructure** | AGDK runtime, Dev Portal, containerization, IAM, networking | Platform Eng | Leads environment setup and runtime upgrades. |
| **Agents & Tooling** | Tool extraction, agent lifecycle callbacks, memory integration | App Eng | Focus on contract parity and domain heuristics. |
| **Memory & Learning** | Storage, retrieval strategies, learning engines | ML/Knowledge Eng | Works closely with Agents for APIs and evaluation. |
| **Outputs & Experience** | Reporting, dashboards, API, frontend/CLI | Product Eng | Ensures stakeholder-facing artifacts. |
| **Quality & SRE** | Testing frameworks, monitoring, runbooks, chaos drills | QA + SRE | Gatekeepers for release readiness. |

### 4.3 MVP Parity Definition
- Purpose: Prove we can run Code Analyzer on AGDK with baseline memory reads, deterministic tooling, and identical outputs to legacy path.
- Scope: Runtime factory, tool adapters for Code Analyzer heuristics, `analysis.use_agdk` flag, Dev Portal trace, `outputs/code_analyzer` parity check.
- Out of Scope (until post-MVP): Advanced learning, multi-agent coordination, dashboard exports, WebSockets.

### 4.4 Quality Gates
- **Build & Lint**: Poetry-managed environment, black/isort/ruff, mypy.
- **Tests**: Unit (tool contracts), integration (runtime session), regression (legacy vs AGDK comparison), chaos scenarios.
- **Observability**: Logs, metrics, and traces available in Dev Portal and Stackdriver before flag flips.
- **Ops**: Runbooks, SLOs, on-call sign-off.

---

## 5. Incremental Roadmap (20 Weeks)

### Increment 0 – Access & Shared Tooling (Week 0-1)
**Goals**: AGDK preview access, shared tooling image, Dev Portal container.

| Deliverable | Tasks | Tests & Evidence | Exit Criteria |
| --- | --- | --- | --- |
| Tooling Image | Build `agdk-tooling` image with AGDK CLI, dev portal, Poetry, project scripts. Publish to registry. | CI build artifact, smoke-run `agdk --version`. | Image available, documentation updated. |
| Dev Portal Pod | Helm/Docker Compose definitions, ingress/port-forward instructions, secrets mounting. | Portal reachable locally (`/health`), screenshot of trace viewer. | Portal accessible from dev cluster. |
| IAM & Secrets | GCP service accounts, secret rotation scripts, access logging. | Terraform plan, secret validation script. | Credential readiness checklist signed. |

### Increment 0.1 – Configuration & Environment Baseline (Week 1-2)
- Extend `config/app.yaml`, `.env.example`, add missing agent configs (placeholders), orchestrator toggles.
- Implement `ConfigManager` with Pydantic validation and environment overrides.
- Add configuration contract tests.

### Increment 0.2 – Input Processing Slice (Week 2-3)
- Multi-source ingestion (`local`, `git`, `GitHub`, `GitLab`, `zip`, single file) with Tree-sitter integration for 10+ languages.
- Language detection, AST preprocessing, filtering.
- Smoke test: run ingestion CLI on sample repositories, verify AST generation stored to temp.

### Increment 0.3 – Output & Reporting Foundation (Week 3-4)
- `OutputManager`, JSON baseline, stub HTML/PDF pipeline (report templates stub), CI/CD integration formats placeholders.
- Dashboard export schema draft, validated via JSON schema tests.

### Increment 1 – AGDK Runtime MVP (Week 4-5)
- Implement `runtime_factory.py`, register placeholder tools, feature flag wiring.
- CLI command `scripts/run_code_analysis.py --use-agdk` to launch AGDK session with stub tool returning static response.
- Dev Portal trace verifying session lifecycle.

### Increment 2 – Code Analyzer MVP Parity (Week 5-7)
- Lift complexity, pattern, architecture, LLM insight, quality control tools into AGDK modules with typed schemas.
- `tool_adapters.py` wires dependencies (memory manager in read-only mode).
- Contract tests comparing AGDK tool outputs vs legacy functions.
- Run orchestrator in AGDK mode for Code Analyzer, capture diff vs legacy outputs (target <1% variance; mismatches reviewed).

### Increment 3 – Memory Baseline (Week 7-8)
- SQLite persistence, Redis coordination, `MemoryAccessTool` for CRUD, `MemoryRetrievalCoordinator` with contextual + recent strategies.
- Feature flag `memory.advanced_strategies=false` default.
- Tests: integration suite covering writes/reads, orchestrator session storing experiences.

### Increment 4 – Learning & Advanced Retrieval (Week 8-10)
- Implement partitioning, pattern recognition, confidence scoring, feedback loop.
- Enable additional retrieval strategies (similarity, temporal, cross-context).
- Add instrumentation metrics (hit rate, latency) to monitor effectiveness.
- Chaos tests injecting Redis/SQLite outages.

### Increment 5 – Orchestrator & Real-time Coordination (Week 10-12)
- Update `SmartMasterOrchestrator` to drive AGDK sessions with Redis state, WebSocket broadcasting, and fallback to legacy path.
- Dev Portal trace with multi-step tool execution and memory calls.
- API `/api/v1/stream` endpoint providing progress updates.

### Increment 6 – Expanded Agents (Week 12-15)
- Sequentially port remaining agents (engineering_practices, security_standards, carbon_efficiency, cloud_native, microservices) using reusable base patterns.
- Each agent delivered via mini-sprint with deliverables:
  - Agent config file, tool modules, tests, outputs structure.
  - Cross-agent consolidated report updates.
  - QA sign-off verifying domain-specific heuristics.

### Increment 7 – Outputs & Experience Completion (Week 14-16)
- Finalize HTML/PDF templates, integration exporters (GitHub, GitLab, Jira), dashboard-ready metrics.
- Implement consolidated executive & technical reports, trends analysis.
- Smoke tests using golden dataset and contract tests verifying schema stability.

### Increment 8 – Operational Hardening (Week 15-18)
- Monitoring + alerting (Stackdriver metrics, Grafana dashboards, AGDK telemetry exports).
- SLOs: e.g., P95 analysis completion < 15 min, error budget 2%.
- Runbooks for runtime, memory DB, Dev Portal, LLM providers; tabletop incident drills.
- Cost monitoring (Vertex AI, OpenAI, Redis, storage) with budget alerts.

### Increment 9 – Production Rollout & Enablement (Week 18-20)
- Environment promotion pipeline: dev → staging → canary → GA.
- Data migration scripts seeding memory partitions, backup/restore automation.
- Training program, paired sessions, documentation updates, support workflows.
- Feature flag default-on once canary SLOs met and stakeholder sign-off.

---

## 6. Testing & Validation Strategy
| Layer | Scope | Tooling |
| --- | --- | --- |
| **Unit** | Tool logic, config validation, schema tests, memory helpers | pytest, hypothesis, golden fixtures |
| **Contract** | Tool request/response parity vs legacy | Snapshot tests, JSON schema validation |
| **Integration (Agent)** | AGDK session with agent-specific tools, memory interactions | pytest + AGDK runtime harness |
| **End-to-end** | CLI/API invocation from ingestion to outputs, cross-agent consolidation | Scenario tests with real repos |
| **Performance** | Memory retrieval latency, multi-agent throughput, LLM fallback | Locust, custom profiling scripts |
| **Chaos & Resilience** | Redis failover, LLM timeouts, network partitions | Chaos Mesh, fault injection scripts |
| **Security & Compliance** | IAM validation, secret rotation, audit log checks | Terraform compliance, automated IAM tests |
| **Observability QA** | Dev Portal trace completeness, log/metric coverage | Manual review + automated telemetry assertions |

Quality gates integrate with CI/CD (GitHub Actions or Cloud Build) and run on each merge gated by feature flag toggles.

---

## 7. Environment Provisioning & Infrastructure
1. **Infrastructure as Code**: Terraform modules for GKE clusters, Redis, Cloud SQL (if using managed PostgreSQL for memory), service accounts, secrets, IAM policies, load balancers.
2. **Secrets & Config**: Google Secret Manager for credentials, sealed-secrets for K8s, `.env` templating for local dev.
3. **Networking**: Host networking or node access for Ollama, firewall rules for OpenAI/Gemini endpoints, VPC Service Controls for data egress control.
4. **Runtime Deployment**: Helm charts for AGDK runtime, Dev Portal, API layer, WebSocket service, memory storage sidecars.
5. **Promotion Strategy**: Environments (dev, staging, canary, prod) with automated promotions, data seeding scripts, and rollback (helm rollback + database snapshot restore).

---

## 8. Data Management, Migration & Rollback
- **Initial Seeding**: Scripts to migrate existing SQLite memory data into new partitioning schema; validated with checksum and sample retrieval tests.
- **Delta Sync**: During dual-run, capture writes from both legacy and AGDK paths, reconcile via change-data-capture job.
- **Backup**: Nightly snapshots of SQLite/Cloud SQL, Redis AOF persistence, cross-region backup copies.
- **Retention & Privacy**: Partition-level TTL, privacy tagging for customer data, audit trails for memory access.
- **Rollback Plan**: Feature flag revert + restore from last good snapshot, run smoke test to confirm legacy path unaffected.

---

## 9. Operational Readiness & SRE
- **Monitoring**: Metrics (session duration, tool latency, memory hit rate, LLM provider health), logs (structured JSON), traces (OpenTelemetry exporting to Stackdriver).
- **Alerting**: PagerDuty integrations with on-call rotations, escalation policies defined.
- **Runbooks**: For AGDK runtime restart, Dev Portal failure, Redis degradation, LLM provider outage, memory corruption, API errors.
- **SLOs**: Defined per environment; e.g., availability 99.5%, mean time to recovery < 30 min.
- **Incident Response**: Blameless postmortems, weekly ops review, cap on error budget consumption.

---

## 10. Resourcing, Roles & Governance
| Role | Responsibilities | Named Owners (example) |
| --- | --- | --- |
| Program Lead | Scope alignment, stakeholder comms, risk mitigation | Eng Director |
| Product Manager | Roadmap, priorities, customer validation | PM |
| Tech Lead (Runtime) | AGDK integration, infra decisions, runtime quality gates | Platform TL |
| Tech Lead (Agents) | Heuristic parity, memory integration, testing | App TL |
| Data/ML Lead | Learning systems, evaluation, feedback loop | ML TL |
| QA Lead | Test strategy, automation, release certification | QA Manager |
| SRE Lead | Monitoring, runbooks, incident response | SRE Manager |
| Enablement Lead | Training, documentation, support workflows | DevRel |

**Governance Cadence**
- Weekly steering with leads reviewing increment progress, risk burndown, budget.
- Bi-weekly demo of latest slice (Dev Portal trace or dashboard screenshot).
- Stage-gate reviews at MVP completion, multi-agent rollout, production launch.

---

## 11. Cost & Capacity Management
- Track spend for Vertex AI/Gemini, OpenAI, Redis, Cloud SQL, compute hours, storage.
- Budget dashboards with forecast vs actual, auto-alert at 80% consumption.
- Model usage throttles in `config/llm/providers.yaml` with concurrency limits and fallback order to keep within budget.
- Capacity planning for memory storage growth (projected per agent × per repo) with quarterly adjustments.

---

## 12. Training & Change Management
- **Enablement Plan**: Workshops on AGDK tooling, Dev Portal navigation, new CLI/API usage.
- **Documentation**: Update README, `/docs/agents/` guides, runbooks, integration examples.
- **Support Workflow**: Tiered support queue, Slack channel, knowledge base articles, FAQ.
- **Adoption Metrics**: Track % analyses on AGDK, mean time to onboard engineer, satisfaction surveys.

---

## 13. Risk Register (Updated)
| Risk | Impact | Likelihood | Mitigation | Owner |
| --- | --- | --- | --- | --- |
| AGDK API changes | Runtime outages | Medium | Pin version, adapter layer, monitor release notes | Platform TL |
| Memory performance regression | Slower analyses | Medium | Latency dashboards, caching, load testing | ML TL |
| Learning accuracy drift | Incorrect findings | Medium | Validation suite, human-in-loop review, rollback | App TL |
| Cross-project data leakage | Compliance breach | Low | Access controls, partition audits, data masking | SRE Lead |
| Dev Portal downtime | Loss of observability | Medium | Fallback logging, HA deployment, health checks | Platform TL |
| Configuration drift | Runtime errors | Medium | Pydantic validation, config tests, GitOps workflow | QA Lead |
| Cost overrun | Budget issues | Medium | Quota limits, usage alerts, cost dashboard | PM |
| Team bandwidth constraints | Slipped milestones | Medium | RACI clarity, stage gating, hire/contract | Program Lead |
| Training gaps | Low adoption | Medium | Enablement plan, pair programming sessions | Enablement Lead |
| External dependency outage (LLM providers) | Partial functionality | High | Provider fallback chain, circuit breakers, caching | App TL |

---

## 14. Exit Criteria Summary
- **MVP Parity**: Code Analyzer runs on AGDK, outputs parity within tolerance, feature flag available.
- **Advanced Memory**: Retrieval strategies validated, telemetry in place, chaos tests pass.
- **Multi-Agent**: All six agents operational with domain tests, consolidated reporting works, cross-agent memory sharing verified.
- **Operational**: Monitoring, runbooks, SLOs, cost dashboards, incident drills complete.
- **Production Launch**: Dual-run success, canary meets SLOs, documentation & training delivered, feature flag default-on.

---

## 15. Appendices

### A. Directory Map
- `src/integrations/agdk/`: runtime factory, tool adapters, credentials helpers.
- `src/agents/<domain>/google/`: agent implementations, tool modules, events, session state.
- `src/memory/`: storage, retrieval, learning components.
- `src/api/`: FastAPI routes, schemas, middleware.
- `config/`: app, agents, llm, orchestrator, rules, environments.
- `outputs/`: agent-specific findings/reports/metrics, consolidated dashboards.
- `scripts/`: dev, CI, data migration, testing utilities.

### B. Tool Mapping (All Agents)
- Tables preserved from original plan (ComplexityAnalysisTool, PatternDetectionTool, etc.) ensuring deterministic logic, memory integration, and learning enhancements.

### C. Testing Harness Inventory
- `tests/agents/*`: Unit + contract tests per tool.
- `tests/memory/*`: Retrieval and learning tests.
- `tests/api/*`: Endpoint + schema validation.
- `tests/e2e/*`: Scenario-based CLI/API runs with golden datasets.

### D. Documentation Deliverables
- Updated developer handbook, onboarding playbook, API reference, observability guide, troubleshooting matrix.

---

> With this modular roadmap, each team can land value in smaller, testable chunks, maintain quality, and keep the multi-agent AGDK migration on schedule while covering every original commitment.
