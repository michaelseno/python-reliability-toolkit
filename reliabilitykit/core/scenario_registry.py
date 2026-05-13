from __future__ import annotations

from pydantic import BaseModel, Field


class ScenarioDefinition(BaseModel):
    scenario_id: str
    scenario_name: str
    category: str
    description: str
    severity_if_failed: str
    pytest_marker: str
    tags: list[str] = Field(default_factory=list)
    remediation: str = "Review endpoint reliability behavior and address unstable responses."
    execution_type: str = "single"


SCENARIO_REGISTRY: dict[str, ScenarioDefinition] = {
    "baseline_health": ScenarioDefinition(
        scenario_id="baseline_health",
        scenario_name="Baseline Health",
        category="baseline",
        description="Basic endpoint availability and healthy HTTP response behavior.",
        severity_if_failed="high",
        pytest_marker="scenario_baseline_health",
        tags=["api", "core", "baseline"],
        remediation="Investigate non-2xx/3xx responses, upstream dependency failures, and endpoint health checks.",
        execution_type="single",
    ),
    "repeated_stability": ScenarioDefinition(
        scenario_id="repeated_stability",
        scenario_name="Repeated Stability",
        category="repeated_stability",
        description="Sequential repeated requests maintain stable behavior.",
        severity_if_failed="high",
        pytest_marker="scenario_repeated_stability",
        tags=["api", "stability"],
        remediation="Review short sequence request handling, transient failures, and timeout/error consistency.",
        execution_type="sequential_repeated",
    ),
    "burst_stability": ScenarioDefinition(
        scenario_id="burst_stability",
        scenario_name="Burst Stability",
        category="bounded_stability",
        description="A small bounded concurrent request group remains stable within approved audit limits.",
        severity_if_failed="high",
        pytest_marker="scenario_burst_stability",
        tags=["api", "burst"],
        remediation="Review short-interval request handling and timeout/error behavior for this endpoint.",
        execution_type="bounded_burst",
    ),
    "invalid_payload_handling": ScenarioDefinition(
        scenario_id="invalid_payload_handling",
        scenario_name="Invalid Payload Handling",
        category="validation",
        description="Invalid payloads are rejected without unstable behavior.",
        severity_if_failed="medium",
        pytest_marker="scenario_invalid_payload_handling",
        tags=["api", "validation"],
        remediation="Confirm invalid payloads return controlled 4xx validation responses without server instability.",
        execution_type="negative_validation",
    ),
    "missing_fields_validation": ScenarioDefinition(
        scenario_id="missing_fields_validation",
        scenario_name="Missing Fields Validation",
        category="validation",
        description="Missing required fields return controlled validation errors.",
        severity_if_failed="medium",
        pytest_marker="scenario_missing_fields_validation",
        tags=["api", "validation"],
        remediation="Confirm missing required fields return controlled validation errors and documented error shapes.",
        execution_type="negative_validation",
    ),
    "auth_failure_handling": ScenarioDefinition(
        scenario_id="auth_failure_handling",
        scenario_name="Auth Failure Handling",
        category="auth",
        description="Invalid credentials return expected auth failures.",
        severity_if_failed="high",
        pytest_marker="scenario_auth_failure_handling",
        tags=["api", "auth"],
        remediation="Verify invalid or missing credentials consistently return 401/403 without exposing diagnostic details.",
        execution_type="auth_negative",
    ),
    "timeout_sensitivity": ScenarioDefinition(
        scenario_id="timeout_sensitivity",
        scenario_name="Timeout Sensitivity",
        category="timeout",
        description="Endpoints are evaluated for timeout sensitivity under strict timing.",
        severity_if_failed="high",
        pytest_marker="scenario_timeout_sensitivity",
        tags=["api", "timeout"],
        remediation="Review timeout thresholds, dependency latency, and graceful timeout/error handling.",
        execution_type="timeout",
    ),
    "response_consistency": ScenarioDefinition(
        scenario_id="response_consistency",
        scenario_name="Response Consistency",
        category="consistency",
        description="Repeated calls maintain consistent status behavior.",
        severity_if_failed="medium",
        pytest_marker="scenario_response_consistency",
        tags=["api", "consistency"],
        remediation="Investigate inconsistent status behavior across equivalent short-interval requests.",
        execution_type="consistency",
    ),
}


def get_scenario(scenario_id: str) -> ScenarioDefinition:
    return SCENARIO_REGISTRY[scenario_id]
