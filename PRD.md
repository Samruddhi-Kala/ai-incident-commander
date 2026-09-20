# Product Requirements Document (PRD) — AI Incident Commander

**Document Version**: 1.1.0 (Correction Pass)  
**Status**: Approved Specification  
**Project Positioning**: Production-Inspired Portfolio Project  
**Author**: Lead Software Architect & Senior AI Engineer  

---

## 1. Product Overview

**AI Incident Commander** is a production-inspired AI incident investigation and response platform. It is designed to assist engineering teams, Site Reliability Engineers (SREs), and Incident Commanders (ICs) during software incident investigations.

By combining **Retrieval-Augmented Generation (RAG)** for organizational knowledge (runbooks, postmortems, service documentation, escalation policies) and **tool calling** for system state queries (metrics, logs, git commits, deployments, infrastructure health), AI Incident Commander executes systematic, evidence-driven investigation workflows. 

The platform operates under a strict **Human-in-the-Loop (HITL)** design: AI agents investigate, correlate telemetry, evaluate competing hypotheses, and propose remediation actions, but human engineers retain exclusive authorization over executing potentially impactful changes.

---

## 2. Problem Statement

Modern software architectures consist of distributed services, continuous deployment pipelines, and multi-layered infrastructure. When a production incident occurs:

1. **High Cognitive Load**: Engineers spend critical time navigating disjointed dashboards, querying log aggregators, checking recent git commits, and searching internal documentation under high pressure.
2. **Context Fragmentation**: Responders often lack instant visibility into recent deployment changes, service dependencies, or past postmortems describing identical failure modes.
3. **Imprecise Diagnostics**: Under stress, troubleshooting can resort to trial-and-error mitigation, increasing service downtime risks.
4. **Safety & Audit Concerns**: Autonomous scripts risk executing unintended modifications against production environments without clear verification or audit logs.

---

## 3. Product Vision & Portfolio Goals

### Product Vision
To build an intelligent investigation workspace that correlates multi-source telemetry, formulates evidence-backed hypotheses, identifies probable root causes, and recommends human-approved remediation.

### Evaluation & Portfolio Goal
Demonstrate whether an AI-assisted investigation platform can reduce the manual effort and cognitive load required to correlate incident signals compared to a manual investigation workflow, while maintaining zero unapproved remediation executions.

---

## 4. Goals & Non-Goals

### Goals
* **Automated Telemetry Correlation**: Correlate alert metadata with simulated metrics, logs, git history, and recent deployments upon incident ingestion.
* **Evidence-Based Hypothesis Engine**: Evaluate competing diagnostic hypotheses against empirical telemetry data before identifying a probable root cause.
* **Human-in-the-Loop Control**: Block any high-risk remediation action (`rollback_deployment`, `restart_service`, `scale_replicas`) until an authenticated human responder explicitly approves it.
* **Append-Only Audit Log**: Maintain an append-only application audit log recording all tool calls, arguments, outputs, evidence items, hypothesis shifts, and human approval decisions.
* **Progressive RAG Knowledge Retrieval**: Surface relevant runbook procedures and past incident postmortems using PostgreSQL + `pgvector`.

### Non-Goals
* **Not a Fully Autonomous Auto-Remediator**: The system will **never** automatically execute high-risk or destructive remediation operations without explicit human confirmation.
* **Not a Full Observability Platform Replacement**: The system does not replace Datadog, Prometheus, or Grafana; it interfaces with systems via tool adapters.
* **Not a Unstructured Chatbot**: The system follows structured, state-machine-driven investigation graphs rather than free-form conversation.
* **Not Demanding Production Microservice Infrastructure Initially**: The system is designed as a modular monolith running locally via Docker Compose, utilizing simulated tool adapters.

---

## 5. Target Users & Personas

### Persona A: Alex — On-Call Site Reliability Engineer (Primary User)
* **Role**: Primary responder to production alerts.
* **Pain Points**: Woken up at 3:00 AM; must synthesize metrics, logs, and commit logs across multiple tools under high stress.
* **Needs**: Instant correlation of recent deployments with error spikes, clear step-by-step investigation plans, and single-click execution of approved remediation actions.

### Persona B: Priya — Incident Commander (Secondary User)
* **Role**: Oversees severe incident response and stakeholder communications.
* **Pain Points**: Difficulty tracking which hypotheses have been tested or ruled out during an active incident.
* **Needs**: Clear incident timeline, evidence matrix, hypothesis verification status, and automated postmortem summary drafts.

### Persona C: Marcus — Platform Architect (Governance User)
* **Role**: Owns infrastructure guardrails and security compliance.
* **Pain Points**: Risk of unvetted AI scripts executing elevated commands against production databases or clusters.
* **Needs**: Role-based authorization, strict human approval gates for dangerous tools, and append-only audit trails.

---

## 6. User Stories

| ID | As a... | I want to... | So that I can... |
| :--- | :--- | :--- | :--- |
| **US-01** | On-Call Engineer | receive an automatically generated investigation plan when an incident is ingested | follow a structured sequence of diagnostic steps. |
| **US-02** | On-Call Engineer | view real-time metrics, error logs, and recent deployment diffs in a unified timeline | determine if a recent deployment caused an error spike. |
| **US-03** | On-Call Engineer | see retrieved runbook sections attached to relevant investigation steps | leverage proven resolution procedures quickly. |
| **US-04** | Incident Commander | review competing hypotheses with supporting and opposing evidence scores | evaluate the empirical confidence of proposed root causes. |
| **US-05** | On-Call Engineer | receive actionable remediation proposals with clear risk levels | understand proposed fixes and their operational risk. |
| **US-06** | Platform Architect | explicitly approve or reject high-risk remediation actions via an authorization interface | prevent unauthorized or accidental modifications. |
| **US-07** | Incident Commander | export a complete incident report and postmortem upon resolution | conduct post-incident reviews with minimal manual writing. |

---

## 7. Core Features & Functional Requirements

### 7.1 Incident Ingestion & Management (FR-01 to FR-03)
* **FR-01**: Ingest incident alerts via REST API, manual UI creation, or JSON payloads (containing service name, title, description, environment).
* **FR-02**: Support standardized metadata fields:
  * **Severities**: `SEV-1`, `SEV-2`, `SEV-3`, `SEV-4`.
  * **Incident Statuses**: `Triggered`, `Investigating`, `Mitigated`, `Resolved`.
* **FR-03**: Maintain service metadata and basic upstream/downstream dependency maps.

### 7.2 RAG Knowledge Retrieval (FR-04 to FR-05)
* **FR-04**: Store and index internal technical documentation (runbooks, architecture docs, past postmortems, policies) using PostgreSQL + `pgvector`.
* **FR-05 (V1)**: Execute cosine similarity search on document embeddings to attach relevant runbook procedures to ongoing investigations. *(Hybrid dense + sparse keyword search designed for V2)*.

### 7.3 Tool Integration & Telemetry Execution (FR-06 to FR-07)
* **FR-06**: Execute read-only diagnostic tools via simulated system adapters across 5 domains:
  1. *Observability*: `get_metrics()`, `search_logs()`, `get_error_rate()`, `get_latency()`.
  2. *Deployment*: `get_recent_deployments()`, `get_deployment_details()`, `compare_deployments()`.
  3. *Git*: `get_recent_commits()`, `get_commit_details()`, `search_code_changes()`.
  4. *Incident History*: `search_previous_incidents()`.
  5. *Infrastructure*: `get_service_health()`, `get_service_dependencies()`, `get_database_status()`.
* **FR-07**: Capture structured JSON responses for all tool invocations and record execution duration, status (`Success`, `Error`, `Timeout`), and raw output.

### 7.4 Agent Investigation & Hypothesis Engine (FR-08 to FR-09)
* **FR-08**: Structure agent behavior using a LangGraph state machine with discrete nodes for Planning, RAG Retrieval, Tool Selection, Execution, Evidence Collection, Hypothesis Engine, and Remediation.
* **FR-09**: Support iterative diagnostic loops: allow the agent to collect evidence, discover missing data, update step plans, and re-query tools before declaring a **probable root cause**.

### 7.5 Remediation & Human-in-the-Loop Engine (FR-10 to FR-12)
* **FR-10**: Categorize remediation tools by risk level:
  * **Risk Levels**: `LOW`, `MEDIUM`, `HIGH`, `CRITICAL`.
* **FR-11**: Enforce human approval for `HIGH` and `CRITICAL` actions. Approval verification checks:
  1. Authenticated user identity.
  2. Appropriate user role (`Responder` or `IncidentCommander`).
  3. Action is in `PENDING` state.
  4. Target action parameters have not been tampered with.
  5. Action has not been previously executed.
* **FR-12**: Maintain an append-only application audit log capturing user identity, tool arguments, human approval decisions (`APPROVED`, `REJECTED`), and execution results.

---

## 8. Non-Functional Requirements (NFRs)

### NFR-01: Performance & Measurement
* Response latency for LLM calls, RAG retrievals, tool executions, and full investigation workflows will be systematically measured and benchmarked during evaluation rather than enforced via hard runtime SLAs.
* Development setup should run comfortably on standard local workstations via Docker Compose.

### NFR-02: Reliability & State Persistence
* LangGraph state checkpointing guarantees investigation progress is persisted in Redis (or PostgreSQL), allowing workflow resumption if a service restarts.

### NFR-03: Security & Access Control
* Role-Based Access Control (RBAC): `Viewer`, `Responder`, `IncidentCommander`, `Admin`.
* Remediation approvals restricted strictly to `Responder` and above.
* Environment variable configuration for all API keys and secrets; zero hardcoded credentials.

### NFR-04: Auditability & Traceability
* Append-only database logs record all prompt inputs, tool arguments, evidence outputs, and user sign-offs with ISO-8601 UTC timestamps.

---

## 9. MVP Scope vs Advanced Features

### 9.1 MVP Scope (V1)
* FastAPI REST API backend with PostgreSQL + `pgvector` database.
* LangGraph agent orchestrator (Intake, Planner, RAG, Tool Selector, Executor, Evidence, Hypothesis Engine, Remediation, Approval Guard).
* Simulated engineering tool adapters (Observability, Deployment, Git, Infrastructure, Incident History).
* V1 RAG pipeline (Markdown chunking, OpenAI embeddings, `pgvector` similarity search).
* Human-in-the-loop approval interface and execution workflow.
* React + TypeScript + Tailwind CSS incident response dashboard.
* Append-only audit logging and postmortem export.

### 9.2 Advanced / Post-MVP Features (V2 / V3)
* V2 Hybrid Retrieval (PostgreSQL full-text search `tsvector` + dense vector search).
* V3 Cross-encoder reranking and adaptive retrieval thresholds.
* Real third-party tool adapters (Datadog API, GitHub API, Kubernetes API).
* Live WebSocket streaming of agent steps and tool outputs to the frontend UI.
* Offline evaluation testbench (RAG metrics & hypothesis accuracy benchmarks).

---

## 10. Human-in-the-Loop & Safety Requirements

1. **Explicit Separation**:
   ```text
   AI Recommendation ──► Authorization Check ──► Human Approval ──► Action Execution
   ```
2. **Approval Interface**: High-risk actions present an approval view displaying:
   * Action Name & Parameters (e.g., `rollback_deployment(service="payment-service", version="v2.4.0")`).
   * Supporting Evidence & Probable Root Cause Summary.
   * Action Risk Level (`HIGH` or `CRITICAL`).
   * Explicit **Approve** and **Reject** controls.
3. **Permission Boundary**: Read-only diagnostic tools execute automatically during investigation. Destructive or state-modifying tools strictly require human authorization.

---

## 11. Evaluation & Success Metrics

System success will be measured through offline benchmarking and experimental runs:

| Metric Category | Evaluation Metric | Purpose |
| :--- | :--- | :--- |
| **Investigation Performance** | Investigation Completion Rate | % of test incidents successfully investigated to resolution |
| **Diagnostic Quality** | Probable Root Cause Accuracy | % of test incidents where the top hypothesis matches ground truth |
| **Evidence Grounding** | Evidence Coverage Score | Ratio of hypothesis assertions supported by empirical telemetry evidence |
| **RAG Retrieval Quality** | Recall@K & MRR | Accuracy of retrieved runbook chunks on benchmark query sets |
| **RAG Faithfulness** | Context Faithfulness Score | Rate of generated claims directly supported by retrieved context |
| **Safety & Governance** | Unapproved Execution Rate | Target = **0%**; zero high-risk actions executed without human sign-off |
| **System Latency** | Step Execution Latency | Total duration measured across diagnostic workflow nodes |
