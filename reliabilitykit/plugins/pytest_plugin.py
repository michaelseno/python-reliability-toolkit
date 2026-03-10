from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, UTC, timedelta
import hashlib
import json
import os
from pathlib import Path
import re
from typing import Any

import pytest

from reliabilitykit.core.classifier import classify_failure
from reliabilitykit.core.failure_digest import build_failure_digest
from reliabilitykit.core.models import ArtifactRef, ChaosEvent, TestRecord


@dataclass
class TestState:
    started_at: datetime | None = None
    ended_at: datetime | None = None
    status: str | None = None
    error_message: str | None = None
    raw_error_message: str | None = None
    artifacts: list[ArtifactRef] = field(default_factory=list)
    chaos_events: list[ChaosEvent] = field(default_factory=list)


class ReliabilityPytestPlugin:
    def __init__(self, run_dir: Path, browser: str = "chromium") -> None:
        self.run_dir = run_dir
        self.browser = browser
        self.session_start: datetime | None = None
        self.session_end: datetime | None = None
        self._states: dict[str, TestState] = {}
        self._runtime_dir = self.run_dir / ".runtime_records"
        self._context_dir = self.run_dir / ".runtime_context"
        self._artifacts_dir = self.run_dir / "artifacts"
        self._runtime_dir.mkdir(parents=True, exist_ok=True)
        self._context_dir.mkdir(parents=True, exist_ok=True)
        self._artifacts_dir.mkdir(parents=True, exist_ok=True)
        self._worker_id = os.getenv("PYTEST_XDIST_WORKER", "master")
        self._runtime_file = self._runtime_dir / f"{self._worker_id}-{os.getpid()}.jsonl"

    def _build_record(self, nodeid: str, state: TestState) -> TestRecord | None:
        if not state.started_at or not state.ended_at or not state.status:
            return None
        classify_source = state.raw_error_message or state.error_message
        failure_type, confidence = classify_failure(classify_source)
        return TestRecord(
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

    def _safe_nodeid(self, nodeid: str) -> str:
        sanitized = re.sub(r"[^A-Za-z0-9._-]+", "_", nodeid).strip("_")
        if not sanitized:
            sanitized = hashlib.sha1(nodeid.encode("utf-8")).hexdigest()[:12]
        return sanitized[-160:]

    def _write_failure_raw_artifact(self, nodeid: str, raw_error: str) -> ArtifactRef:
        safe = self._safe_nodeid(nodeid)
        path = self._artifacts_dir / f"{safe}.failure_raw.txt"
        path.write_text(raw_error, encoding="utf-8")
        relative = path.relative_to(self.run_dir)
        return ArtifactRef(kind="failure_raw", path=str(relative), size_bytes=path.stat().st_size)

    def _append_runtime_record(self, record: TestRecord) -> None:
        payload = record.model_dump(mode="json")
        with self._runtime_file.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(payload) + "\n")

    def _normalize_artifact_path(self, raw_path: str) -> str:
        candidate = Path(raw_path)
        if candidate.is_absolute():
            try:
                return str(candidate.relative_to(self.run_dir))
            except ValueError:
                return raw_path

        prefixed = self.run_dir / candidate
        try:
            return str(prefixed.relative_to(self.run_dir))
        except ValueError:
            return raw_path

    def _context_file(self, nodeid: str) -> Path:
        key = hashlib.sha1(nodeid.encode("utf-8")).hexdigest()
        return self._context_dir / f"{key}.jsonl"

    def _merge_runtime_context(self, record: TestRecord) -> TestRecord:
        context_file = self._context_file(record.nodeid)
        if not context_file.exists():
            return record

        artifacts = list(record.artifacts)
        chaos_events = list(record.chaos_events)
        artifact_keys = {(a.kind, a.path) for a in artifacts}
        chaos_keys = {(e.timestamp, e.profile, e.mode, e.url, e.method, e.action) for e in chaos_events}

        with context_file.open("r", encoding="utf-8") as handle:
            for line in handle:
                payload = line.strip()
                if not payload:
                    continue
                entry = json.loads(payload)
                kind = entry.get("type")
                if kind == "artifact":
                    artifact = ArtifactRef(
                        kind=entry.get("kind", "unknown"),
                        path=entry.get("path", ""),
                        size_bytes=int(entry.get("size_bytes", 0) or 0),
                        sha256=entry.get("sha256"),
                    )
                    key = (artifact.kind, artifact.path)
                    if key not in artifact_keys and artifact.path:
                        artifacts.append(artifact)
                        artifact_keys.add(key)
                elif kind == "chaos_event":
                    event = ChaosEvent(
                        timestamp=entry.get("timestamp", datetime.now(UTC).isoformat()),
                        profile=entry.get("profile", "unknown"),
                        mode=entry.get("mode", "unknown"),
                        url=entry.get("url", ""),
                        method=entry.get("method", ""),
                        action=entry.get("action", ""),
                    )
                    key = (event.timestamp, event.profile, event.mode, event.url, event.method, event.action)
                    if key not in chaos_keys:
                        chaos_events.append(event)
                        chaos_keys.add(key)

        return record.model_copy(update={"artifacts": artifacts, "chaos_events": chaos_events})

    @property
    def records(self) -> list[TestRecord]:
        records_by_nodeid: dict[str, TestRecord] = {}
        runtime_files = sorted(self._runtime_dir.glob("*.jsonl"))

        for runtime_file in runtime_files:
            with runtime_file.open("r", encoding="utf-8") as handle:
                for line in handle:
                    payload = line.strip()
                    if not payload:
                        continue
                    record = TestRecord.model_validate_json(payload)
                    existing = records_by_nodeid.get(record.nodeid)
                    if existing is None or record.ended_at >= existing.ended_at:
                        records_by_nodeid[record.nodeid] = record

        if records_by_nodeid:
            merged = [self._merge_runtime_context(record) for record in records_by_nodeid.values()]
            return sorted(merged, key=lambda record: (record.started_at, record.nodeid))

        output: list[TestRecord] = []
        for nodeid, state in self._states.items():
            record = self._build_record(nodeid, state)
            if record is not None:
                output.append(self._merge_runtime_context(record))
        return sorted(output, key=lambda record: (record.started_at, record.nodeid))

    def pytest_sessionstart(self, session: pytest.Session) -> None:
        self.session_start = datetime.now(UTC)

    def pytest_sessionfinish(self, session: pytest.Session, exitstatus: int) -> None:
        self.session_end = datetime.now(UTC)

    def pytest_runtest_setup(self, item: pytest.Item) -> None:
        state = self._states.setdefault(item.nodeid, TestState())
        state.started_at = datetime.now(UTC)

    def pytest_runtest_logreport(self, report: pytest.TestReport) -> None:
        if report.when not in {"call", "teardown"}:
            return
        state = self._states.setdefault(report.nodeid, TestState())
        if report.when == "call":
            state.ended_at = datetime.now(UTC)
            if state.started_at is None:
                duration_seconds = float(getattr(report, "duration", 0.0) or 0.0)
                state.started_at = state.ended_at - timedelta(seconds=max(duration_seconds, 0.0))
            if report.passed:
                state.status = "passed"
                state.error_message = None
                state.raw_error_message = None
            elif report.failed:
                state.status = "failed"
                raw_error = str(report.longrepr)
                state.raw_error_message = raw_error
                digest, _ = build_failure_digest(report.nodeid, report.when, raw_error)
                state.error_message = digest
                raw_artifact = self._write_failure_raw_artifact(report.nodeid, raw_error)
                if not any(a.kind == "failure_raw" and a.path == raw_artifact.path for a in state.artifacts):
                    state.artifacts.append(raw_artifact)
            elif report.skipped:
                state.status = "skipped"
                state.error_message = None
                state.raw_error_message = None
        elif state.ended_at is None:
            state.ended_at = datetime.now(UTC)

        if state.status is None:
            return

        record = self._build_record(report.nodeid, state)
        if record is not None:
            self._append_runtime_record(record)

    @pytest.fixture
    def rk_test_context(self, request: pytest.FixtureRequest) -> dict[str, Any]:
        nodeid = request.node.nodeid
        state = self._states.setdefault(nodeid, TestState())

        def add_artifact(kind: str, path: str, size_bytes: int = 0, sha256: str | None = None) -> None:
            normalized_path = self._normalize_artifact_path(path)
            state.artifacts.append(ArtifactRef(kind=kind, path=normalized_path, size_bytes=size_bytes, sha256=sha256))

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
