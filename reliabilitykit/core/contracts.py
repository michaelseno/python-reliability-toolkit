from __future__ import annotations

from pydantic import BaseModel, Field


class TargetInput(BaseModel):
    base_url: str
    endpoint: str
    method: str = "GET"
    headers: dict[str, str] = Field(default_factory=dict)
    payload: dict | list | str | int | float | bool | None = None
    expected_status: int = 200
    timeout_ms: int = 1000


class ScenarioExecutionResult(BaseModel):
    scenario_id: str
    scenario_name: str
    status: str
    duration_ms: int
    error_rate: float = 0.0
    failure_type: str = "unknown"
    chaos_profile: str | None = None
    details: str | None = None
    recommendation: str | None = None
