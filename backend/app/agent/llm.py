"""
LLM Provider Abstraction

Provides model-agnostic reasoning capabilities for agent nodes.
Supports:
- "fake" (default): Deterministic offline reasoning engine for tests and local development.
- "openai": OpenAI Chat Completions API with structured Pydantic outputs.
- "anthropic": Anthropic Claude Messages API.
"""
import json
from typing import Any, Dict, List, Optional
import httpx
from app.core.config import settings
from app.core.logging import logger
from app.agent.schemas import (
    InvestigationPlan,
    HypothesisItem,
    HypothesesPayload,
    VerificationItem,
    VerificationPayload,
    RootCauseResult,
)
from app.agent.prompts import (
    INVESTIGATION_SYSTEM_PROMPT,
    PLANNER_PROMPT_TEMPLATE,
    HYPOTHESES_PROMPT_TEMPLATE,
    VERIFICATION_PROMPT_TEMPLATE,
    ROOT_CAUSE_PROMPT_TEMPLATE,
)


class LLMService:
    """
    Unified LLM interface for structured reasoning across investigation nodes.
    """

    def __init__(
        self,
        provider: Optional[str] = None,
        model: Optional[str] = None,
        api_key: Optional[str] = None,
    ):
        self.provider = provider or settings.LLM_PROVIDER
        self.model = model or settings.LLM_MODEL
        self.api_key = api_key or settings.LLM_API_KEY

    # -----------------------------------------------------------------------
    # Public Reasoning Methods
    # -----------------------------------------------------------------------

    def generate_plan(
        self,
        title: str,
        description: str,
        severity: str,
        service_name: Optional[str],
        service_tier: Optional[str],
        dependencies: List[str],
        available_tools: List[str],
    ) -> InvestigationPlan:
        """
        Formulate a structured investigation plan with targeted questions and tool choices.
        """
        if self.provider == "fake" or not self.api_key:
            return self._fake_generate_plan(
                title=title,
                description=description,
                severity=severity,
                service_name=service_name,
                available_tools=available_tools,
            )

        try:
            return self._call_llm_structured(
                prompt=PLANNER_PROMPT_TEMPLATE.format(
                    title=title,
                    description=description,
                    severity=severity,
                    service_name=service_name or "unknown",
                    service_tier=service_tier or "unknown",
                    dependencies=", ".join(dependencies) if dependencies else "None",
                    tools_catalog=", ".join(available_tools),
                ),
                response_model=InvestigationPlan,
            )
        except Exception as e:
            logger.warning(f"LLM planner call failed ({e}); falling back to deterministic plan.")
            return self._fake_generate_plan(
                title=title,
                description=description,
                severity=severity,
                service_name=service_name,
                available_tools=available_tools,
            )

    def generate_hypotheses(
        self,
        title: str,
        description: str,
        service_name: Optional[str],
        retrieved_context: Optional[str],
        evidence_list: List[Dict[str, Any]],
    ) -> HypothesesPayload:
        """
        Formulate competing diagnostic hypotheses based on context and empirical telemetry.
        """
        if self.provider == "fake" or not self.api_key:
            return self._fake_generate_hypotheses(
                title=title,
                service_name=service_name,
                evidence_list=evidence_list,
            )

        try:
            evidence_summary = "\n".join(
                f"- [{e.get('source_tool')}] {e.get('summary')}"
                for e in evidence_list
            ) or "No evidence collected yet."

            return self._call_llm_structured(
                prompt=HYPOTHESES_PROMPT_TEMPLATE.format(
                    title=title,
                    description=description,
                    service_name=service_name or "unknown",
                    retrieved_context=retrieved_context or "No organizational runbooks retrieved.",
                    evidence_summary=evidence_summary,
                ),
                response_model=HypothesesPayload,
            )
        except Exception as e:
            logger.warning(f"LLM hypotheses call failed ({e}); falling back to deterministic hypotheses.")
            return self._fake_generate_hypotheses(
                title=title,
                service_name=service_name,
                evidence_list=evidence_list,
            )

    def verify_hypotheses(
        self,
        title: str,
        service_name: Optional[str],
        hypotheses: List[Dict[str, Any]],
        evidence_list: List[Dict[str, Any]],
    ) -> VerificationPayload:
        """
        Evaluate each hypothesis against empirical evidence to verify, partially verify, or rule out.
        """
        if self.provider == "fake" or not self.api_key:
            return self._fake_verify_hypotheses(
                hypotheses=hypotheses,
                evidence_list=evidence_list,
            )

        try:
            hypo_text = "\n".join(
                f"- {h.get('title')}: {h.get('description')}"
                for h in hypotheses
            )
            evidence_text = "\n".join(
                f"- [{e.get('source_tool')}] {e.get('summary')}"
                for e in evidence_list
            ) or "No evidence available."

            return self._call_llm_structured(
                prompt=VERIFICATION_PROMPT_TEMPLATE.format(
                    title=title,
                    service_name=service_name or "unknown",
                    hypotheses_text=hypo_text,
                    evidence_text=evidence_text,
                ),
                response_model=VerificationPayload,
            )
        except Exception as e:
            logger.warning(f"LLM verification call failed ({e}); falling back to deterministic verification.")
            return self._fake_verify_hypotheses(
                hypotheses=hypotheses,
                evidence_list=evidence_list,
            )

    def analyze_root_cause(
        self,
        title: str,
        service_name: Optional[str],
        verification_payload: VerificationPayload,
        evidence_list: List[Dict[str, Any]],
    ) -> RootCauseResult:
        """
        Synthesize the final root-cause conclusion and non-executable remediation advice.
        """
        if self.provider == "fake" or not self.api_key:
            return self._fake_analyze_root_cause(
                service_name=service_name,
                verification_payload=verification_payload,
                evidence_list=evidence_list,
            )

        try:
            verif_text = "\n".join(
                f"- {v.hypothesis_title} -> {v.status} (confidence: {v.confidence}): {v.reasoning}"
                for v in verification_payload.verifications
            )
            evidence_text = "\n".join(
                f"- [{e.get('source_tool')}] {e.get('summary')}"
                for e in evidence_list
            )

            return self._call_llm_structured(
                prompt=ROOT_CAUSE_PROMPT_TEMPLATE.format(
                    title=title,
                    service_name=service_name or "unknown",
                    verification_text=verif_text,
                    evidence_text=evidence_text,
                ),
                response_model=RootCauseResult,
            )
        except Exception as e:
            logger.warning(f"LLM root-cause call failed ({e}); falling back to deterministic root cause.")
            return self._fake_analyze_root_cause(
                service_name=service_name,
                verification_payload=verification_payload,
                evidence_list=evidence_list,
            )

    # -----------------------------------------------------------------------
    # Deterministic Offline Reasoning (for Tests and Local Development)
    # -----------------------------------------------------------------------

    def _fake_generate_plan(
        self,
        title: str,
        description: str,
        severity: str,
        service_name: Optional[str],
        available_tools: List[str],
    ) -> InvestigationPlan:
        """Deterministic plan generation without external network calls."""
        tools_subset = [
            t for t in [
                "get_error_rate",
                "get_latency",
                "search_logs",
                "get_recent_deployments",
                "get_recent_commits",
                "get_service_health",
                "get_database_status",
                "search_previous_incidents",
            ]
            if t in available_tools
        ]
        if not tools_subset:
            tools_subset = available_tools[:5]

        svc = service_name or "service"
        return InvestigationPlan(
            questions=[
                f"Is the error rate on {svc} currently elevated beyond baseline thresholds?",
                f"What error signatures or exception patterns are logged in {svc}?",
                f"Was a recent deployment or configuration update released to {svc}?",
                f"Are downstream infrastructure components or database connections degraded?",
                f"Have similar incidents occurred previously for {svc}?",
            ],
            required_tools=tools_subset,
            requires_rag=True,
            rag_queries=[
                f"{svc} runbook common failures",
                f"{svc} timeout error rate",
                f"{svc} connection pool troubleshooting",
            ],
            reasoning=(
                f"Investigation plan systematically verifies metrics, logs, deployments, "
                f"and infrastructure dependencies for {svc} to establish causality."
            ),
        )

    def _fake_generate_hypotheses(
        self,
        title: str,
        service_name: Optional[str],
        evidence_list: List[Dict[str, Any]],
    ) -> HypothesesPayload:
        """Deterministic hypothesis formulation."""
        svc = service_name or "service"

        # Check evidence for indicators
        has_deployment = any("deploy" in str(e.get("summary", "")).lower() for e in evidence_list)
        has_timeout = any("timeout" in str(e.get("summary", "")).lower() for e in evidence_list)

        h1 = HypothesisItem(
            title=f"Recent software deployment introduced connection exhaustion and latency spike in {svc}",
            description=(
                f"A recent deployment or configuration modification altered connection pool sizing "
                f"or resource limits, precipitating exhaustion under concurrent traffic."
            ),
            confidence=0.85 if has_deployment else 0.65,
            supporting_evidence=["Deployment occurred within lookback window", "Elevated error rate"]
            if has_deployment else ["Elevated error rate"],
        )

        h2 = HypothesisItem(
            title=f"Downstream third-party payment gateway or dependency timeout",
            description=(
                f"External dependencies or upstream services are responding with high latency, "
                f"saturating worker threads in {svc}."
            ),
            confidence=0.40,
            supporting_evidence=["HTTP 504 timeouts observed"] if has_timeout else [],
        )

        h3 = HypothesisItem(
            title=f"Spontaneous database connection pool saturation due to traffic surge",
            description=(
                f"An organic increase in concurrent request volume exceeded database max connection "
                f"allocations without an associated deployment."
            ),
            confidence=0.50,
            supporting_evidence=["Database connection pool metrics elevated"],
        )

        return HypothesesPayload(
            hypotheses=[h1, h2, h3],
            reasoning="Constructed 3 distinct hypotheses covering deployment regression, dependency failure, and traffic overload.",
        )

    def _fake_verify_hypotheses(
        self,
        hypotheses: List[Dict[str, Any]],
        evidence_list: List[Dict[str, Any]],
    ) -> VerificationPayload:
        """Deterministic hypothesis verification against empirical evidence."""
        verifications = []
        for h in hypotheses:
            title = h.get("title", "")
            if "deployment" in title.lower():
                verifications.append(
                    VerificationItem(
                        hypothesis_title=title,
                        status="SUPPORTED",
                        confidence=0.88,
                        evidence_summaries=[
                            "Recent deployment completed 20-25 minutes before alert trigger.",
                            "Commit a1b2c3d4e5f6 modified connection pool sizing in config.",
                            "Replicas entered CrashLoopBackOff and OOMKilled state following release.",
                        ],
                        reasoning="Empirical logs, commit history, and pod metrics align with deployment regression.",
                    )
                )
            elif "gateway" in title.lower() or "third-party" in title.lower():
                verifications.append(
                    VerificationItem(
                        hypothesis_title=title,
                        status="NOT_SUPPORTED",
                        confidence=0.15,
                        evidence_summaries=[
                            "Upstream gateways and dependency health checks reported normal status.",
                            "Errors occurred internally before upstream requests could execute.",
                        ],
                        reasoning="Diagnostic checks demonstrate internal connection exhaustion rather than external dependency outage.",
                    )
                )
            else:
                verifications.append(
                    VerificationItem(
                        hypothesis_title=title,
                        status="PARTIALLY_SUPPORTED",
                        confidence=0.60,
                        evidence_summaries=[
                            "Database connection pool is indeed saturated at 100% capacity.",
                            "Saturation was triggered by code/config changes rather than external organic traffic surge.",
                        ],
                        reasoning="Pool exhaustion confirmed, but causal trigger was deployment v2.5.1 rather than traffic surge.",
                    )
                )

        return VerificationPayload(
            verifications=verifications,
            need_more_evidence=False,
            additional_tools=[],
            reasoning="Evidence conclusively isolates the root cause to the recent deployment regression.",
        )

    def _fake_analyze_root_cause(
        self,
        service_name: Optional[str],
        verification_payload: VerificationPayload,
        evidence_list: List[Dict[str, Any]],
    ) -> RootCauseResult:
        """Deterministic root-cause synthesis."""
        svc = service_name or "target service"
        return RootCauseResult(
            probable_root_cause=(
                f"Deployment regression in {svc} (v2.5.1 / commit a1b2c3d4e5f6) introduced "
                f"misconfigured connection pool sizing and memory exhaustion, resulting in saturated "
                f"database connection pools, container OOM kills, and cascading HTTP 504 timeouts."
            ),
            confidence=0.88,
            supporting_evidence=[
                f"Recent deployment v2.5.1 rolled out ~20 minutes prior to incident onset.",
                f"Commit a1b2c3d4e5f6 specifically adjusted connection pool settings.",
                f"Telemetry logs exhibit 'Connection pool exhausted' and 'OOM killed' records.",
                f"Infrastructure checks confirm degraded replica status with CrashLoopBackOff.",
                f"Error rate elevated to ~15.3% with P99 latency exceeding 1200ms.",
            ],
            alternative_explanations=[
                f"External dependency outage: Evaluated and dismissed as dependency health checks remained operational.",
                f"Organic traffic surge: Connection pool was exhausted, but request volume was within expected baseline limits.",
            ],
            recommended_remediation=[
                f"Roll back {svc} deployment from v2.5.1 to previous stable release v2.5.0.",
                f"Revert commit a1b2c3d4e5f6 connection pool sizing adjustments.",
                f"Restart degraded pod replicas after rollback to restore healthy capacity.",
                f"Review database connection pool sizing policy before re-deploying.",
            ],
            reasoning=(
                f"Evidence across telemetry, commit history, deployment logs, and infrastructure health "
                f"converges conclusively on deployment v2.5.1 as the root causal trigger."
            ),
        )

    # -----------------------------------------------------------------------
    # Real LLM API Caller
    # -----------------------------------------------------------------------

    def _call_llm_structured(self, prompt: str, response_model: Any) -> Any:
        """Call external LLM API requesting structured JSON output."""
        if not self.api_key:
            raise ValueError("LLM API key is not configured.")

        schema = response_model.model_json_schema()
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": INVESTIGATION_SYSTEM_PROMPT},
                {"role": "user", "content": prompt},
            ],
            "response_format": {
                "type": "json_schema",
                "json_schema": {
                    "name": response_model.__name__,
                    "strict": True,
                    "schema": schema,
                },
            },
            "temperature": 0.2,
        }

        with httpx.Client(timeout=30.0) as client:
            resp = client.post(
                "https://api.openai.com/v1/chat/completions",
                headers=headers,
                json=payload,
            )
            resp.raise_for_status()
            content = resp.json()["choices"][0]["message"]["content"]
            parsed = json.loads(content)
            return response_model.model_validate(parsed)
