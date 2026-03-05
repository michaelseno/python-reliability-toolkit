from __future__ import annotations

from datetime import datetime
from pathlib import Path

from reliabilitykit.core.models import RunRecord
from reliabilitykit.storage.base import StorageBackend


class S3StorageBackend(StorageBackend):
    def __init__(self, bucket: str) -> None:
        self.bucket = bucket

    def prepare_run_dir(self, run_id: str, started_at: datetime) -> Path:
        raise NotImplementedError("S3 backend will be implemented in a later phase")

    def write_run(self, run: RunRecord, run_dir: Path) -> None:
        raise NotImplementedError("S3 backend will be implemented in a later phase")

    def list_runs(self) -> list[Path]:
        raise NotImplementedError("S3 backend will be implemented in a later phase")
