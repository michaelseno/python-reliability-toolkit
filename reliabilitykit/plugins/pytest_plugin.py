from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, UTC
from pathlib import Path
from typing import Any

import pytest

from reliabilitykit.core.classifier import classify_failure
from reliabilitykit.core.models import ArtifactRef, ChaosEvent, TestRecord


@dataclass
class TestState:
    started_at: datetime | None = None
    ended_at: datetime | None = None
    status: str | None = None
    error_message: str | None = None
    artifacts: list[ArtifactRef] = field(default_factory=list)
    chaos_events: list[ChaosEvent] = field(default_factory=list)


class ReliabilityPytestPlugin:
    def __init__(self, run_dir: Path, browser: str = "chromium") -> None:
        self.run_dir = run_dir
        self.browser = browser
        self.session_start: datetime | None = None
        self.session_end: datetime | None = None
        self._states: dict[str, TestState] = {}

    @property
    def records(self) -> list[TestRecord]:
        output: list[TestRecord] = []
        for nodeid, state in self._states.items():
            if not state.started_at or not state.ended_at or not state.status:
                continue
            failure_type, confidence = classify_failure(state.error_message)
            output.append(
                TestRecord(
                    nodeid=nodeid,
                    name=nodeid.split("::")[-1],
                    status=state.status,
                    started_at=state.started_at,
                    ended_at=state.ended_at,
                    duration_ms=int((state.ended_at - state.started_at).total_seconds() * 1000),
                    browser=self.browser,
                    error_message=state.error_message,
                    failure_type=failure_type,
                    classification_confidence=confidence,
                    artifacts=state.artifacts,
                    chaos_events=state.chaos_events,
                )
            )
        return output

    def pytest_sessionstart(self, session: pytest.Session) -> None:
        self.session_start = datetime.now(UTC)

    def pytest_sessionfinish(self, session: pytest.Session, exitstatus: int) -> None:
        self.session_end = datetime.now(UTC)

    def pytest_runtest_setup(self, item: pytest.Item) -> None:
        state = self._states.setdefault(item.nodeid, TestState())
        state.started_at = datetime.now(UTC)

    def pytest_runtest_logreport(self, report: pytest.TestReport) -> None:
        if report.when != "call":
            return
        state = self._states.setdefault(report.nodeid, TestState())
        state.ended_at = datetime.now(UTC)
        if report.passed:
            state.status = "passed"
        elif report.failed:
            state.status = "failed"
            state.error_message = str(report.longrepr)
        elif report.skipped:
            state.status = "skipped"

    @pytest.fixture
    def rk_test_context(self, request: pytest.FixtureRequest) -> dict[str, Any]:
        nodeid = request.node.nodeid
        state = self._states.setdefault(nodeid, TestState())

        def add_artifact(kind: str, path: str, size_bytes: int = 0, sha256: str | None = None) -> None:
            state.artifacts.append(ArtifactRef(kind=kind, path=path, size_bytes=size_bytes, sha256=sha256))

        def add_chaos_event(profile: str, mode: str, url: str, method: str, action: str) -> None:
            state.chaos_events.append(
                ChaosEvent(
                    timestamp=datetime.now(UTC),
                    profile=profile,
                    mode=mode,
                    url=url,
                    method=method,
                    action=action,
                )
            )

        return {
            "run_dir": str(self.run_dir),
            "add_artifact": add_artifact,
            "add_chaos_event": add_chaos_event,
        }
