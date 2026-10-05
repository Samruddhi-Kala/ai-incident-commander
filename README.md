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

## 🛠️ Technology Stack

| Domain | Technology Stack | Purpose |
| :--- | :--- | :--- |
| **Backend Framework** | Python 3.11+ / FastAPI | Async REST API gateway |
| **Knowledge Engine (RAG)** | Custom Chunking + pgvector | Document parsing, HNSW vector search, full-text retrieval |
| **Agent Orchestration** | LangGraph *(Future Phase)* | Stateful, graph-based agent workflow management |
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
Database layer: 12 SQLAlchemy 2.0 ORM models, Alembic migrations (001 & 002),
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

Not implemented yet:
LangGraph agent orchestrator
Simulated engineering tools & tool calling
Remediation execution
Authentication & Authorization
React frontend
```
