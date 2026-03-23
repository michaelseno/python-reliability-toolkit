from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field


FailureType = Literal[
    "assertion_failure",
    "timeout_navigation",
    "timeout_selector",
    "network_error",
    "http_5xx",
    "browser_crash",
    "environment_error",
    "unknown",
]


class ArtifactRef(BaseModel):
    kind: str
    path: str
    size_bytes: int = 0
    sha256: str | None = None


class ChaosEvent(BaseModel):
    timestamp: datetime
    profile: str
    mode: str
    url: str
    method: str
    action: str


class TestRecord(BaseModel):
    nodeid: str
    name: str
    status: Literal["passed", "failed", "skipped"]
    started_at: datetime
    ended_at: datetime
    duration_ms: int
    browser: str = "chromium"
    retry_index: int = 0
    error_message: str | None = None
    failure_type: FailureType = "unknown"
    classification_confidence: float = 0.0
    artifacts: list[ArtifactRef] = Field(default_factory=list)
    chaos_events: list[ChaosEvent] = Field(default_factory=list)


class RunEnvironment(BaseModel):
    os: str
    python_version: str
    playwright_version: str | None = None
    pytest_version: str | None = None
    git_sha: str | None = None
    branch: str | None = None
    host: str | None = None
    is_ci: bool = False
    ci_provider: str | None = None
    ci_run_id: str | None = None
    ci_job_id: str | None = None
    ci_job_url: str | None = None


class RunRecord(BaseModel):
    schema_version: str = "1.0"
    run_id: str
    project: str
    started_at: datetime
    ended_at: datetime
    duration_ms: int
    status: Literal["passed", "failed"]
    environment: RunEnvironment
    chaos_profile: str | None = None
    chaos_seed: int | None = None
    surface: str = "legacy_ui"
    scan_pack: str | None = None
    tests: list[TestRecord] = Field(default_factory=list)

    @property
    def totals(self) -> dict[str, int]:
        passed = sum(1 for t in self.tests if t.status == "passed")
        failed = sum(1 for t in self.tests if t.status == "failed")
        skipped = sum(1 for t in self.tests if t.status == "skipped")
        return {"passed": passed, "failed": failed, "skipped": skipped}
