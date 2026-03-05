from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path

from reliabilitykit.core.models import RunEnvironment, RunRecord
from reliabilitykit.storage.local import LocalStorageBackend


def test_local_storage_writes_run_index(tmp_path: Path) -> None:
    storage = LocalStorageBackend(tmp_path / ".reliabilitykit")
    now = datetime.now(UTC)
    run_id = "20260303T000000Z-test"
    run_dir = storage.prepare_run_dir(run_id, now)

    run = RunRecord(
        run_id=run_id,
        project="reliability-toolkit",
        started_at=now,
        ended_at=now,
        duration_ms=0,
        status="passed",
        environment=RunEnvironment(os="darwin", python_version="3.11"),
        tests=[],
    )
    storage.write_run(run, run_dir)

    assert (run_dir / "run.json").exists()
    assert (tmp_path / ".reliabilitykit" / "index" / "runs_index.jsonl").exists()
