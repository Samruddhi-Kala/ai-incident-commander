# AI Incident Commander

A production-inspired AI incident investigation and response platform that combines Retrieval-Augmented Generation (RAG), tool calling, and structured agentic workflows for evidence-driven root-cause analysis and human-approved remediation.

---

## 📌 Project Overview & Positioning

**AI Incident Commander** is a portfolio-grade AI engineering platform designed to demonstrate how LLMs, knowledge retrieval, and tool execution can assist on-call engineers during production incidents. 

Rather than functioning as a generic conversational chatbot or an unvetted auto-remediator, AI Incident Commander executes a **structured, evidence-based investigation workflow**:

* **RAG Knowledge Base**: Connects the AI to organizational knowledge (runbooks, service architecture, past incident postmortems, escalation policies).
* **Engineering Tool Calling**: Queries live telemetry through simulated system adapters (metrics, logs, git commits, deployment history, infrastructure health).
* **Agentic Workflows**: Executes multi-step hypothesis generation, objective evidence collection, and verification via LangGraph.
* **Human-in-the-Loop (HITL)**: Requires explicit human authorization before executing any potentially impactful remediation action (e.g., rolling back deployments or restarting services).
* **Audit Trail**: Preserves a detailed append-only application audit log of all tool executions, evidence items, hypothesis shifts, and approval decisions.

---

## 🌐 API Layer & Endpoints (Phase 3)

The system exposes a clean, versioned REST API (`/api/v1`) designed following a strict `Route -> Service -> Repository -> Database` architecture.

### Service Management API
* `POST /api/v1/services` — Register a new service in the catalog.
* `GET  /api/v1/services` — List services with pagination (`?page=1&page_size=20`).
* `GET  /api/v1/services/{id}` — Retrieve detailed service record.
* `PATCH /api/v1/services/{id}` — Update mutable service fields (`owner_team`, `tier`, `dependencies`).

### Incident Management & Ingestion API
* `POST /api/v1/incidents` — Manually report a production incident (automatically initializes investigation session `INV-XXXX`).
* `POST /api/v1/incidents/ingest` — Ingest alerts from external monitoring triggers (Datadog, CloudWatch).
* `GET  /api/v1/incidents` — List incidents with pagination and filtering (`?status=Triggered&severity=SEV-1&service_id=...`).
* `GET  /api/v1/incidents/{id}` — Retrieve incident details with service context and active investigation state.
* `PATCH /api/v1/incidents/{id}` — Update incident status/severity (`Triggered` -> `Investigating` -> `Mitigated` -> `Resolved`).

### Example API Requests

#### 1. Create a Service
```bash
curl -X POST "http://localhost:8000/api/v1/services" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "payment-service",
    "description": "Core payment processing microservice",
    "owner_team": "Payment Core",
    "tier": "Tier-0",
    "dependencies": ["auth-service", "database-cluster"]
  }'
```

#### 2. Ingest an Alert Trigger
```bash
curl -X POST "http://localhost:8000/api/v1/incidents/ingest" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Payment API Gateway Timeout Spike",
    "description": "Error rate exceeded 15% threshold following release",
    "severity": "SEV-1",
    "service_name": "payment-service",
    "source": "datadog"
  }'
```

---

## 🗄️ Database Architecture & Migrations

The database layer is built on **PostgreSQL 16** with the **`pgvector`** extension using SQLAlchemy 2.0 ORM and Alembic migrations.

### Core Database Entities (12 Tables)
* **Identity & Governance**: `users`, `audit_logs`
* **Service Catalog & Incidents**: `services`, `incidents`
* **Investigation Domain**: `investigations`, `investigation_steps`, `evidence`, `hypotheses`, `tool_calls`, `remediation_actions`
* **RAG Knowledge Vector Store**: `documents`, `document_chunks` (with 1536-dim HNSW `pgvector` index)

### Database Migration Commands
```bash
# Run database migrations to latest schema (head)
cd backend
python -m alembic upgrade head

# Check current migration revision
python -m alembic current

# Seed development sample data (Services, Users, Incidents)
python app/db/seed.py
```

---

## 🚀 Quickstart & Developer Setup

### 1. Prerequisites
* Python 3.11+
* Docker & Docker Compose

### 2. Environment Setup
Copy the template environment file:
```bash
cp .env.example .env
```

### 3. Start Infrastructure (PostgreSQL + pgvector & Redis)
Start the PostgreSQL container (with `pgvector` pre-installed) and Redis container:
```bash
docker compose up -d postgres redis
```

### 4. Install Backend Dependencies
Create a virtual environment and install requirements:
```bash
python -m venv .venv
# On Windows:
.venv\Scripts\activate
# On Linux/macOS:
source .venv/bin/activate

pip install -r backend/requirements.txt
```

### 5. Run Database Migrations & Seed Sample Data
Enable `pgvector` extension and prepare the database schema:
```bash
cd backend
python -m alembic upgrade head
python app/db/seed.py
cd ..
```

### 6. Start Development Backend
Start the FastAPI server via Uvicorn:
```bash
cd backend
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```
Access points:
* **Interactive Swagger UI**: [http://localhost:8000/docs](http://localhost:8000/docs)
* **Application Health Endpoint**: [http://localhost:8000/health](http://localhost:8000/health)
* **PostgreSQL / pgvector Health**: [http://localhost:8000/health/db](http://localhost:8000/health/db)
* **Redis Health**: [http://localhost:8000/health/redis](http://localhost:8000/health/redis)

### 7. Run Test Suite
Execute backend tests using pytest:
```bash
python -m pytest tests/backend -v
```

---

## 📚 RAG Knowledge Engine & Ingestion (Phase 4)

The platform includes a modular, production-inspired Retrieval-Augmented Generation (RAG) knowledge engine that connects organizational documentation (runbooks, architecture topology, historic postmortems, escalation policies) to future AI incident investigation workflows.

### RAG Pipeline Flow
```text
knowledge_base/
      ↓
MarkdownLoader (Recursive discovery, title extraction, category inference)
      ↓
TextCleaner (Whitespace normalization, CRLF to UNIX LF, code block preservation)
      ↓
HeadingChunker (Heading-aware section splitting, overlap, metadata breadcrumbs)
      ↓
EmbeddingService (Abstract provider: OpenAI text-embedding-3-small or offline Fake embeddings)
      ↓
PostgreSQL + pgvector (documents & document_chunks tables with 1536-dim HNSW index)
      ↓
KnowledgeRetriever (Vector cosine similarity, full-text GIN search, or blended hybrid search)
      ↓
ContextBuilder (Structured Markdown with explicit SOURCE/TYPE/TITLE citations)
```

### Knowledge Base Organization
Documents are maintained in the root `knowledge_base/` directory:
* `runbooks/` — Service-specific troubleshooting guides (e.g., `payment-service.md`)
* `architecture/` — System architecture and dependency specs (e.g., `system-overview.md`)
* `incidents/` — Historic incident postmortems (e.g., `INC-2025-08-01-payment-timeout.md`)
* `policies/` — Escalation SLAs and severity criteria (e.g., `severity-policy.md`)

### Running Knowledge Base Ingestion
To index or update the knowledge base into PostgreSQL + pgvector:
```bash
# Ingest all documents from knowledge_base/
python -m app.rag.ingest

# Force re-ingestion and chunk re-embedding even if content hash is unchanged
python -m app.rag.ingest --force

# Ingest from a custom directory
python -m app.rag.ingest --dir path/to/custom_docs
```

### Embedding Providers: Offline vs. Production
* **Deterministic Offline Embeddings (Default)**: `EMBEDDING_PROVIDER="fake"` generates deterministic, unit-normalized 1536-dimensional vectors using SHA-256 seeded Gaussian random generation. Tests and local development run without external API access or API keys.
* **OpenAI Embeddings**: Set `EMBEDDING_PROVIDER="openai"` and provide `OPENAI_API_KEY="..."` in `.env` to generate embeddings via `text-embedding-3-small` (1536 dims).

### RAG REST APIs (Development Endpoints)
* `POST /api/v1/rag/search` — Query knowledge base via vector, text, or hybrid retrieval:
  ```json
  {
    "query": "payment gateway timeout threshold",
    "top_k": 3,
    "mode": "vector"
  }
  ```
* `POST /api/v1/rag/ingest` — Trigger knowledge base ingestion programmatically:
  ```json
  {
    "force": false
  }
  ```

---

## 🔧 Simulated Engineering Tools & Telemetry Adapters (Phase 5)

The platform includes a modular engineering tool adapter layer providing simulated diagnostic tools across five operational domains. The tools simulate real-world observability, deployment, source control, incident history, and infrastructure systems with deterministic scenarios (including the `payment-service` degradation and memory-exhaustion scenario).

### Tool Adapters & Capabilities (14 Tools across 5 Domains)

| Domain | Adapter | Tools | Description |
| :--- | :--- | :--- | :--- |
| **Observability** | `ObservabilityAdapter` | `get_metrics`, `search_logs`, `get_error_rate`, `get_latency` | Metric time-series, log searching with level/text filters, error rates, latency percentiles (p50/p90/p95/p99) |
| **Deployment** | `DeploymentAdapter` | `get_recent_deployments`, `get_deployment_details`, `compare_deployments` | Deployment history, release metadata, commit SHAs, and configuration diff comparison |
| **Source Control** | `GitAdapter` | `get_recent_commits`, `get_commit_details`, `search_code_changes` | Git commits, unified file diffs, author info, and message/file search |
| **Incident History** | `IncidentHistoryAdapter` | `search_previous_incidents` | Historical incident search with keyword matching, severity filtering, and recurring pattern detection |
| **Infrastructure** | `InfrastructureAdapter` | `get_service_health`, `get_service_dependencies`, `get_database_status` | Kubernetes pod statuses, container resource metrics, active alerts, dependency graphs, and database connection pools |

### Central Tool Registry & LLM Function Calling

* **`ToolRegistry`**: Central singleton registry for tool discovery, dispatch, domain querying, and execution latency tracking.
* **LLM Schema Generation**: Automatically inspects adapter method signatures and docstrings to produce structured tool schemas ready for LLM function calling (OpenAI, Anthropic, LangChain/LangGraph).
* **Deterministic Test Scenario**: Includes a coordinated incident scenario (`payment-service` degraded due to connection pool exhaustion and OOM errors following release `v2.5.1` / commit `a1b2c3d4e5f6`).

### Tools REST APIs

* `GET  /api/v1/tools/` — Catalog of all registered diagnostic tools and domains.
* `GET  /api/v1/tools/schemas` — LLM function calling schema definitions for all tools.
* `POST /api/v1/tools/execute` — Execute a single diagnostic tool with arguments:
  ```json
  {
    "tool_name": "get_error_rate",
    "arguments": {
      "service_name": "payment-service",
      "minutes": 30
    }
  }
  ```
---

## 🤖 LangGraph Agent Orchestrator (Phase 6)

The platform features an automated AI investigation orchestrator built on **LangGraph**. It coordinates diagnostic reasoning across knowledge retrieval and live telemetry tools to produce evidence-backed root cause analyses without human intervention.

### 🛡️ Critical Safety Boundary

> **IMPORTANT**: Phase 6 provides **diagnostic AI orchestration only**. 
> The agent is strictly read-only: it retrieves runbooks, invokes read-only telemetry and diagnostic tools, collects empirical evidence, formulates and verifies competing failure hypotheses, and recommends remediation proposals.
> **Remediation actions (rollbacks, restarts, database changes, infrastructure mutations) and human approval workflows are intentionally deferred to Phase 7.**
> There are no action-execution or automated-remediation nodes in this phase.

### Investigation Architecture

```text
                    INCIDENT TRIGGER
                           │
                           ▼
                  ┌─────────────────┐
                  │ 1. Intake Node  │
                  └────────┬────────┘
                           │
                           ▼
                  ┌─────────────────┐
                  │ 2. Planner Node │
                  └────────┬────────┘
                           │
         ┌─────────────────┴─────────────────┐
         ▼                                   ▼
┌──────────────────┐               ┌───────────────────┐
│   3. RAG Node    │               │  4. Tools Node    │
│(Runbooks/History)│               │(Telemetry/Metrics)│
└────────┬─────────┘               └─────────┬─────────┘
         │                                   │
         └─────────────────┬─────────────────┘
                           ▼
                  ┌─────────────────┐
                  │ 5. Evidence Node│
                  └────────┬────────┘
                           │
                           ▼
                  ┌─────────────────┐
                  │ 6. Hypotheses   │
                  └────────┬────────┘
                           │
                           ▼
                  ┌─────────────────┐
                  │ 7. Verification │
                  └────────┬────────┘
                           │
             Need More Evidence? (Loop Guard)
             ├── YES (iter < max) ──► 4. Tools Node
             └── NO  ───────────────► 8. Root Cause Node
                           │
                           ▼
                  ┌─────────────────┐
                  │ 8. Root Cause   │
                  │    Synthesis    │
                  └────────┬────────┘
                           │
                           ▼
                 INVESTIGATION RESULT
```

### Graph Nodes

1. **Intake Node** (`app.agent.nodes.intake`): Loads incident, resolves service metadata and dependencies, initializes or attaches the active investigation session (`INV-XXXX`), and records Step 1 in `investigation_steps`.
2. **Planner Node** (`app.agent.nodes.planner`): Analyzes incident context using the LLM to generate a structured `InvestigationPlan` containing diagnostic questions, required tools, and RAG search queries.
3. **RAG Node** (`app.agent.nodes.rag`): Invokes the existing `RAGService` to retrieve relevant runbooks, architecture topology, and past incident postmortems with full source attribution.
4. **Tools Node** (`app.agent.nodes.tools`): Validates planned tools against `ToolRegistry`, rejects unknown tools safely, and executes registered tools via `ToolService`, persisting records to `tool_calls` and `audit_logs`.
5. **Evidence Node** (`app.agent.nodes.evidence`): Converts raw tool execution results into structured `Evidence` entities with relevance scores, persisted in the database.
6. **Hypotheses Node** (`app.agent.nodes.hypotheses`): Uses the LLM to generate multiple competing failure theories (`HypothesisItem`), persisted in `hypotheses`.
7. **Verification Node** (`app.agent.nodes.verification`): Tests hypotheses against empirical evidence, updates confidence scores and statuses (`Verified_Strong`, `Verified_Weak`, `Ruled_Out`), and evaluates if further diagnostic iterations are required.
8. **Root Cause Node** (`app.agent.nodes.root_cause`): Synthesizes the probable root cause, overall confidence score, alternative explanations, and non-executable remediation proposals, updating the `investigations` table to `Completed`.

### Agent State Schema (`InvestigationState`)

```python
class InvestigationState(TypedDict):
    incident_id: str
    investigation_id: str
    investigation_number: str
    title: str
    description: str
    severity: str
    status: str
    service_name: Optional[str]
    service_tier: Optional[str]
    service_dependencies: List[str]
    investigation_plan: Optional[Dict[str, Any]]
    retrieved_context: Optional[str]
    retrieved_sources: List[Dict[str, Any]]
    selected_tools: List[Dict[str, Any]]
    tool_results: List[Dict[str, Any]]
    tool_calls_count: int
    iteration_count: int
    max_iterations: int
    need_more_evidence: bool
    evidence: List[Dict[str, Any]]
    hypotheses: List[Dict[str, Any]]
    verification_results: List[Dict[str, Any]]
    probable_root_cause: Optional[str]
    confidence: Optional[float]
    recommended_remediation: List[str]
    analysis_reasoning: Optional[str]
    current_step: str
    status_outcome: str
    errors: List[str]
```

### Configuration Options

| Variable | Default | Description |
| :--- | :--- | :--- |
| `LLM_PROVIDER` | `fake` | LLM backend: `fake` (deterministic offline reasoning for tests/dev), `openai`, `anthropic` |
| `LLM_MODEL` | `gpt-4o-mini` | Model identifier when using external providers |
| `LLM_API_KEY` | `""` | API key for external LLM provider |
| `AGENT_MAX_ITERATIONS` | `5` | Maximum evidence gathering feedback loops before forced conclusion |
| `AGENT_MAX_TOOL_CALLS` | `10` | Hard cap on total tool calls across an entire investigation |

### Investigation REST API

* `POST /api/v1/investigations/{incident_id}/run` — Trigger automated LangGraph investigation:
  ```json
  {
    "max_iterations": 3
  }
  ```
  Returns full structured investigation findings, diagnostic steps, evidence, hypotheses, and root cause.
* `GET /api/v1/investigations/{incident_id}` — Retrieve active or completed investigation details.

### Example Investigation Response

```json
{
  "investigation_id": "b765a624-9de6-4202-9f24-5676439307a8",
  "incident_id": "61306724-0605-4253-97f8-e04b526e00ce",
  "investigation_number": "INV-9873",
  "status": "Completed",
  "probable_root_cause": "Deployment regression in payment-service (v2.5.1 / commit a1b2c3d4e5f6) introduced misconfigured connection pool sizing and memory exhaustion, resulting in saturated database connection pools, container OOM kills, and cascading HTTP 504 timeouts.",
  "confidence_score": 0.88,
  "recommended_remediation": [
    "Roll back payment-service deployment from v2.5.1 to previous stable release v2.5.0.",
    "Revert commit a1b2c3d4e5f6 connection pool sizing adjustments.",
    "Restart degraded pod replicas after rollback to restore healthy capacity."
  ],
  "steps": [
    {"step_order": 1, "title": "Step 1 — Incident Intake & Context Normalization", "status": "Completed"},
    {"step_order": 2, "title": "Step 2 — Diagnostic Planning", "status": "Completed"},
    {"step_order": 3, "title": "Step 3 — Organizational Knowledge Retrieval", "status": "Completed"},
    {"step_order": 4, "title": "Step 4 — Diagnostic Telemetry Collection", "status": "Completed"},
    {"step_order": 5, "title": "Step 5 — Evidence Extraction & Correlation", "status": "Completed"},
    {"step_order": 6, "title": "Step 6 — Competing Hypotheses Formulation", "status": "Completed"},
    {"step_order": 7, "title": "Step 7 — Hypothesis Verification & Evidence Correlation", "status": "Completed"},
    {"step_order": 8, "title": "Step 8 — Root Cause Synthesis & Remediation Guidance", "status": "Completed"}
  ],
  "evidence": [
    {"source_tool": "get_error_rate", "summary": "Error rate currently observed at 15.3% (baseline: 1.0%).", "relevance_score": 0.9},
    {"source_tool": "get_recent_deployments", "summary": "Recent deployment 'v2.5.1' deployed to production at 20m ago.", "relevance_score": 0.9}
  ],
  "hypotheses": [
    {"status": "Verified_Strong", "confidence_score": 0.88, "hypothesis_text": "Recent software deployment introduced connection exhaustion and latency spike in payment-service: ..."}
  ]
}
```

---

## 🛠️ Technology Stack

| Domain | Technology Stack | Purpose |
| :--- | :--- | :--- |
| **Backend Framework** | Python 3.11+ / FastAPI | Async REST API gateway |
| **Knowledge Engine (RAG)** | Custom Chunking + pgvector | Document parsing, HNSW vector search, full-text retrieval |
| **Engineering Tools** | 5 Simulated Domain Adapters + Registry | Diagnostic tool calling interface with LLM schema generation |
| **Agent Orchestration** | LangGraph | Stateful, graph-based agent workflow management |
| **Database & Vector Store** | PostgreSQL 16 + `pgvector` | Primary database for relational data, JSONB logs, and vector embeddings |
| **Cache & Queue** | Redis | Session state, tool response caching, and agent checkpointing |
| **Migration Engine** | Alembic | Database schema migrations |
| **Frontend UI** | React 18 + TypeScript *(Future Phase)* | Single-page application dashboard |
| **Environment** | Docker & Docker Compose | Local containerized setup |

---

## 📌 Implementation Status

```text
Phase 1 completed:
Project foundation and development infrastructure.

Phase 2 completed:
Database layer: 12 SQLAlchemy 2.0 ORM models, Alembic migrations (001, 002, 003),
lightweight Repository layer, development seeding mechanism, and database tests.

Phase 3 completed:
Service Management API, Incident Management API, Ingestion Endpoint, Initial Investigation
Session Initialization, Pydantic v2 Schemas, Service Layer pattern (Route -> Service -> Repo -> DB),
and API tests.

Phase 4 completed:
RAG Knowledge Engine & Document Ingestion: Recursive Markdown document loader, text sanitization,
heading-aware chunking with metadata breadcrumbs, embedding service abstraction (OpenAI & offline
deterministic fake embeddings), PostgreSQL + pgvector vector similarity search, full-text search,
hybrid retrieval, citation context builder, CLI ingestion tool, and RAG search/ingest APIs.

Phase 5 completed:
Simulated Engineering Tools & Telemetry Adapters: 5 domain adapters (Observability, Deployment,
Git, Incident History, Infrastructure) providing 14 diagnostic tools, BaseToolAdapter with latency
tracking and error handling, central ToolRegistry with discovery, dispatch, and LLM function-calling
schema generation, REST endpoints (/api/v1/tools/), tool execution persistence into tool_calls and
audit_logs, and 63 unit and integration tests.

Phase 6 completed:
LangGraph Agent Orchestrator: Stateful, inspectable LangGraph investigation StateGraph with 8 modular
nodes (Intake, Planner, RAG, Tools, Evidence, Hypotheses, Verification, Root Cause), structured Pydantic
reasoning outputs, deterministic offline LLM reasoning engine for testing/local dev, loop guards for
max-iteration and tool-call limits, full transactional database persistence across all 6 investigation tables,
API endpoints (POST /api/v1/investigations/{incident_id}/run, GET /api/v1/investigations/{incident_id}),
and 19 unit, integration, and API tests with 100% pass rate.

Not implemented yet:
Remediation execution & approval engine (Phase 7)
Authentication & Authorization
React frontend (Phase 8)
```

