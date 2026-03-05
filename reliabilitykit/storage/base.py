from __future__ import annotations

from datetime import datetime
from pathlib import Path

from reliabilitykit.core.models import RunRecord


class StorageBackend:
    def prepare_run_dir(self, run_id: str, started_at: datetime) -> Path:
        raise NotImplementedError

    def write_run(self, run: RunRecord, run_dir: Path) -> None:
        raise NotImplementedError

    def list_runs(self) -> list[Path]:
        raise NotImplementedError
