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


SCENARIO_REGISTRY: dict[str, ScenarioDefinition] = {
    "baseline_health": ScenarioDefinition(
        scenario_id="baseline_health",
        scenario_name="Baseline Health",
        category="baseline",
        description="Basic endpoint availability and healthy HTTP response behavior.",
        severity_if_failed="high",
        pytest_marker="scenario_baseline_health",
        tags=["api", "core", "baseline"],
    ),
    "repeated_stability": ScenarioDefinition(
        scenario_id="repeated_stability",
        scenario_name="Repeated Stability",
        category="repeated_stability",
        description="Sequential repeated requests maintain stable behavior.",
        severity_if_failed="high",
        pytest_marker="scenario_repeated_stability",
        tags=["api", "stability"],
    ),
    "burst_stability": ScenarioDefinition(
        scenario_id="burst_stability",
        scenario_name="Burst Stability",
        category="burst_stability",
        description="Concurrent burst traffic remains resilient.",
        severity_if_failed="high",
        pytest_marker="scenario_burst_stability",
        tags=["api", "burst"],
    ),
    "invalid_payload_handling": ScenarioDefinition(
        scenario_id="invalid_payload_handling",
        scenario_name="Invalid Payload Handling",
        category="validation",
        description="Invalid payloads are rejected without unstable behavior.",
        severity_if_failed="medium",
        pytest_marker="scenario_invalid_payload_handling",
        tags=["api", "validation"],
    ),
    "missing_fields_validation": ScenarioDefinition(
        scenario_id="missing_fields_validation",
        scenario_name="Missing Fields Validation",
        category="validation",
        description="Missing required fields return controlled validation errors.",
        severity_if_failed="medium",
        pytest_marker="scenario_missing_fields_validation",
        tags=["api", "validation"],
    ),
    "auth_failure_handling": ScenarioDefinition(
        scenario_id="auth_failure_handling",
        scenario_name="Auth Failure Handling",
        category="auth",
        description="Invalid credentials return expected auth failures.",
        severity_if_failed="high",
        pytest_marker="scenario_auth_failure_handling",
        tags=["api", "auth"],
    ),
    "timeout_sensitivity": ScenarioDefinition(
        scenario_id="timeout_sensitivity",
        scenario_name="Timeout Sensitivity",
        category="timeout",
        description="Endpoints are evaluated for timeout sensitivity under strict timing.",
        severity_if_failed="high",
        pytest_marker="scenario_timeout_sensitivity",
        tags=["api", "timeout"],
    ),
    "response_consistency": ScenarioDefinition(
        scenario_id="response_consistency",
        scenario_name="Response Consistency",
        category="consistency",
        description="Repeated calls maintain consistent status behavior.",
        severity_if_failed="medium",
        pytest_marker="scenario_response_consistency",
        tags=["api", "consistency"],
    ),
}


def get_scenario(scenario_id: str) -> ScenarioDefinition:
    return SCENARIO_REGISTRY[scenario_id]
