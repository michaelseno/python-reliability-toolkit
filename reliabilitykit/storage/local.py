from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path

from reliabilitykit.core.models import RunRecord
from reliabilitykit.storage.base import StorageBackend


class LocalStorageBackend(StorageBackend):
    def __init__(self, root: Path) -> None:
        self.root = root
        self.runs_root = self.root / "runs"
        self.index_root = self.root / "index"

    def prepare_run_dir(self, run_id: str, started_at: datetime) -> Path:
        day_path = started_at.strftime("%Y/%m/%d")
        run_dir = self.runs_root / day_path / run_id
        (run_dir / "tests").mkdir(parents=True, exist_ok=True)
        (run_dir / "artifacts").mkdir(parents=True, exist_ok=True)
        self.index_root.mkdir(parents=True, exist_ok=True)
        return run_dir

    def write_run(self, run: RunRecord, run_dir: Path) -> None:
        run_json = run.model_dump(mode="json")
        total_tests = len(run.tests)
        passed = run.totals["passed"]
        failed = run.totals["failed"]
        run_json["totals"] = run.totals
        run_json["total_tests"] = total_tests
        run_json["pass_rate"] = round((passed / total_tests) * 100, 2) if total_tests else 0.0
        (run_dir / "run.json").write_text(json.dumps(run_json, indent=2), encoding="utf-8")

        for idx, test in enumerate(run.tests):
            (run_dir / "tests" / f"{idx:04d}.json").write_text(
                json.dumps(test.model_dump(mode="json"), indent=2),
                encoding="utf-8",
            )

        index_line = {
            "run_id": run.run_id,
            "project": run.project,
            "started_at": run.started_at.isoformat(),
            "status": run.status,
            "duration_ms": run.duration_ms,
            "passed": passed,
            "failed": failed,
            "total_tests": total_tests,
            "pass_rate": round((passed / total_tests) * 100, 2) if total_tests else 0.0,
            "chaos_profile": run.chaos_profile,
            "run_json_path": str((run_dir / "run.json").relative_to(self.root)),
            "report_path": str((run_dir / "report.html").relative_to(self.root)),
        }
        with (self.index_root / "runs_index.jsonl").open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(index_line) + "\n")

    def list_runs(self) -> list[Path]:
        return sorted(self.runs_root.glob("*/*/*/*/run.json"))

    def find_run(self, run_id: str) -> Path | None:
        for path in self.list_runs():
            if path.parent.name == run_id:
                return path
        return None
