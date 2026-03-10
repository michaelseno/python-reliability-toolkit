from __future__ import annotations

import hashlib
import json
from pathlib import Path
from types import SimpleNamespace

from reliabilitykit.core.models import ArtifactRef
from reliabilitykit.plugins.pytest_plugin import ReliabilityPytestPlugin


def test_plugin_records_read_runtime_files_and_keep_latest(tmp_path: Path) -> None:
    run_dir = tmp_path / "run"
    plugin = ReliabilityPytestPlugin(run_dir=run_dir)

    runtime_dir = run_dir / ".runtime_records"
    runtime_dir.mkdir(parents=True, exist_ok=True)

    first = {
        "nodeid": "tests/e2e/test_sample.py::test_case",
        "name": "test_case",
        "status": "failed",
        "started_at": "2026-03-08T15:00:00Z",
        "ended_at": "2026-03-08T15:00:01Z",
        "duration_ms": 1000,
        "browser": "chromium",
        "error_message": "AssertionError: boom",
        "failure_type": "assertion_failure",
        "classification_confidence": 0.9,
        "artifacts": [],
        "chaos_events": [],
    }
    second = {
        **first,
        "status": "passed",
        "ended_at": "2026-03-08T15:00:02Z",
        "duration_ms": 2000,
        "error_message": None,
        "failure_type": "unknown",
        "classification_confidence": 0.0,
    }

    file_a = runtime_dir / "gw0-1.jsonl"
    file_a.write_text(json.dumps(first) + "\n", encoding="utf-8")
    file_b = runtime_dir / "gw1-2.jsonl"
    file_b.write_text(json.dumps(second) + "\n", encoding="utf-8")

    records = plugin.records

    assert len(records) == 1
    assert records[0].nodeid == first["nodeid"]
    assert records[0].status == "passed"
    assert records[0].duration_ms == 2000


def test_plugin_writes_final_record_with_artifacts_on_teardown(tmp_path: Path) -> None:
    run_dir = tmp_path / "run"
    plugin = ReliabilityPytestPlugin(run_dir=run_dir)
    nodeid = "tests/e2e/test_sample.py::test_case"

    plugin.pytest_runtest_setup(SimpleNamespace(nodeid=nodeid))
    plugin.pytest_runtest_logreport(
        SimpleNamespace(
            when="call",
            nodeid=nodeid,
            passed=False,
            failed=True,
            skipped=False,
            longrepr='Timeout 30000ms exceeded while waiting for event "response"',
            duration=1.23,
        )
    )

    plugin._states[nodeid].artifacts.append(ArtifactRef(kind="screenshot", path="artifacts/test.png"))

    plugin.pytest_runtest_logreport(
        SimpleNamespace(
            when="teardown",
            nodeid=nodeid,
            passed=True,
            failed=False,
            skipped=False,
            longrepr="",
            duration=0.0,
        )
    )

    records = plugin.records
    assert len(records) == 1
    assert records[0].failure_type == "network_error"
    assert records[0].error_message is not None
    assert "Headline:" in records[0].error_message
    assert records[0].artifacts
    assert any(artifact.kind == "screenshot" for artifact in records[0].artifacts)
    raw_failure_artifacts = [artifact for artifact in records[0].artifacts if artifact.kind == "failure_raw"]
    assert raw_failure_artifacts
    raw_failure_path = run_dir / raw_failure_artifacts[0].path
    assert raw_failure_path.exists()


def test_plugin_merges_runtime_context_entries(tmp_path: Path) -> None:
    run_dir = tmp_path / "run"
    plugin = ReliabilityPytestPlugin(run_dir=run_dir)
    nodeid = "tests/e2e/test_sample.py::test_case"

    runtime_dir = run_dir / ".runtime_records"
    runtime_dir.mkdir(parents=True, exist_ok=True)
    record = {
        "nodeid": nodeid,
        "name": "test_case",
        "status": "passed",
        "started_at": "2026-03-08T15:00:00Z",
        "ended_at": "2026-03-08T15:00:01Z",
        "duration_ms": 1000,
        "browser": "chromium",
        "error_message": None,
        "failure_type": "unknown",
        "classification_confidence": 0.0,
        "artifacts": [],
        "chaos_events": [],
    }
    (runtime_dir / "gw0-1.jsonl").write_text(json.dumps(record) + "\n", encoding="utf-8")

    key = hashlib.sha1(nodeid.encode("utf-8")).hexdigest()
    context_file = run_dir / ".runtime_context" / f"{key}.jsonl"
    context_file.parent.mkdir(parents=True, exist_ok=True)
    context_file.write_text(
        json.dumps({"type": "artifact", "kind": "screenshot", "path": "artifacts/test.png"}) + "\n",
        encoding="utf-8",
    )

    records = plugin.records

    assert len(records) == 1
    assert records[0].artifacts
    assert records[0].artifacts[0].path == "artifacts/test.png"
