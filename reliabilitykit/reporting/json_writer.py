from __future__ import annotations

import json
from pathlib import Path

from reliabilitykit.core.models import RunRecord


def write_json(run: RunRecord, output_path: Path) -> None:
    output_path.write_text(json.dumps(run.model_dump(mode="json"), indent=2), encoding="utf-8")
