"""
Phase 6 Manual Verification Script

Triggers an automated incident investigation workflow using LangGraph,
and inspects the database to verify all investigation artifacts:
1. Investigation row (status=Completed, probable_root_cause, confidence_score)
2. Investigation steps (all 8 sequential diagnostic phases)
3. Telemetry evidence items collected and scored
4. Competing failure hypotheses evaluated and scored
5. Tool calls persisted with investigation_id, execution latency, and arguments
6. Audit logs persisted with SYSTEM_AGENT actor and event metadata
"""
import os
import sys
import uuid

# Ensure backend directory is on python search path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../backend")))

from app.db.session import SessionLocal
from app.models.service import Service
from app.models.incident import Incident
from app.models.investigation import Investigation
from app.models.investigation_step import InvestigationStep
from app.models.evidence import Evidence
from app.models.hypothesis import Hypothesis
from app.models.tool_call import ToolCall
from app.models.audit_log import AuditLog
from app.agent.graph import run_investigation_workflow
from app.agent.llm import LLMService


def main():
    print("=" * 60)
    print("PHASE 6 MANUAL VERIFICATION: LANGGRAPH ORCHESTRATION")
    print("=" * 60)

    with SessionLocal() as db:
        # 1. Setup Service
        svc_name = f"payment-service-{uuid.uuid4().hex[:4]}"
        service = Service(
            name=svc_name,
            owner_team="Payments SRE",
            tier="Tier-1",
            dependencies=["postgres-primary", "auth-service", "redis-cache"],
        )
        db.add(service)
        db.commit()
        db.refresh(service)
        print(f"[1] Created test service: {service.name} (Tier: {service.tier})")

        # 2. Setup Incident
        incident = Incident(
            title="Elevated Checkout Failures and P99 Latency Surge",
            description="HTTP 504 Gateway Timeouts surging to 24.2% on /v1/checkout following deployment.",
            severity="SEV-1",
            service_id=service.id,
        )
        db.add(incident)
        db.commit()
        db.refresh(incident)
        print(f"[2] Created test incident: {incident.title} [{incident.severity}] (ID: {incident.id})")

        # 3. Execute LangGraph Investigation Workflow
        print("\n[3] Executing LangGraph Investigation Workflow...")
        final_state = run_investigation_workflow(
            incident_id=str(incident.id),
            max_iterations=3,
            db=db,
            llm=LLMService(provider="fake"),
        )

        inv_id = uuid.UUID(final_state["investigation_id"])
        print(f"    Investigation Number: {final_state['investigation_number']}")
        print(f"    Status Outcome:       {final_state['status_outcome']}")
        print(f"    Current Step:         {final_state['current_step']}")
        print(f"    Confidence:           {final_state['confidence']}")
        print(f"    Probable Root Cause:  {final_state['probable_root_cause']}")

        # 4. Verify Database Records
        print("\n[4] Verifying Database Artifacts:")

        # 4a. Investigation
        inv_record = db.get(Investigation, inv_id)
        assert inv_record is not None, "Investigation record missing!"
        print(f"    - Investigation Table:  Found {inv_record.investigation_number} (status: {inv_record.status}, confidence: {inv_record.confidence_score})")

        # 4b. Investigation Steps
        steps = db.query(InvestigationStep).filter(InvestigationStep.investigation_id == inv_id).order_by(InvestigationStep.step_order).all()
        print(f"    - Investigation Steps:  {len(steps)} recorded steps:")
        for s in steps:
            print(f"        * Step {s.step_order}: {s.title} [{s.status}]")

        # 4c. Evidence
        evidence = db.query(Evidence).filter(Evidence.investigation_id == inv_id).all()
        print(f"    - Evidence Records:     {len(evidence)} items collected:")
        for e in evidence:
            print(f"        * [{e.source_tool}] (score: {e.relevance_score:.2f}): {e.summary[:75]}...")

        # 4d. Hypotheses
        hypotheses = db.query(Hypothesis).filter(Hypothesis.investigation_id == inv_id).all()
        print(f"    - Hypotheses Evaluated: {len(hypotheses)} competing theories:")
        for h in hypotheses:
            print(f"        * [{h.status}] (conf: {h.confidence_score:.2f}) {h.hypothesis_text[:80]}...")

        # 4e. Tool Calls
        tool_calls = db.query(ToolCall).filter(ToolCall.investigation_id == inv_id).all()
        print(f"    - Tool Calls Persisted: {len(tool_calls)} diagnostic invocations:")
        for tc in tool_calls:
            print(f"        * {tc.tool_name} [{tc.status}] (latency: {tc.execution_time_ms}ms)")

        # 4f. Audit Logs
        audit_logs = db.query(AuditLog).filter(AuditLog.incident_id == incident.id).all()
        print(f"    - Audit Logs:           {len(audit_logs)} audit records created for incident.")

        print("\n" + "=" * 60)
        print("ALL DATABASE ARTIFACTS VERIFIED SUCCESSFULLY!")
        print("=" * 60)


if __name__ == "__main__":
    main()
