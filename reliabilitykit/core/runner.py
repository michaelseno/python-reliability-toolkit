from __future__ import annotations

from datetime import UTC, datetime
import os
from pathlib import Path
from uuid import uuid4

import pytest

from reliabilitykit.core.config import ReliabilityConfig
from reliabilitykit.core.env import collect_environment
from reliabilitykit.core.models import RunRecord
from reliabilitykit.plugins.pytest_plugin import ReliabilityPytestPlugin
from reliabilitykit.storage.local import LocalStorageBackend


def create_run_id(now: datetime | None = None) -> str:
    now = now or datetime.now(UTC)
    return f"{now.strftime('%Y%m%dT%H%M%SZ')}-{uuid4().hex[:8]}"


def execute_pytest_run(
    config: ReliabilityConfig,
    pytest_args: list[str],
    chaos_profile: str | None = None,
    chaos_seed: int | None = None,
    browser: str = "chromium",
    workers: str | None = None,
    surface: str = "legacy_ui",
    scan_pack: str | None = None,
) -> RunRecord:
    started_at = datetime.now(UTC)
    run_id = create_run_id(started_at)
    storage = LocalStorageBackend(Path(config.storage.local.path))
    run_dir = storage.prepare_run_dir(run_id, started_at)

    plugin = ReliabilityPytestPlugin(run_dir=run_dir, browser=browser)
    args = [*config.pytest.args]
    if workers:
        args.extend(["-n", workers])
    args.extend(pytest_args)

    prior_profile = os.environ.get("RK_CHAOS_PROFILE")
    prior_seed = os.environ.get("RK_CHAOS_SEED")
    prior_run_dir = os.environ.get("RK_RUN_DIR")
    os.environ["RK_RUN_DIR"] = str(run_dir)
    if chaos_profile:
        os.environ["RK_CHAOS_PROFILE"] = chaos_profile
    if chaos_seed is not None:
        os.environ["RK_CHAOS_SEED"] = str(chaos_seed)

    try:
        exit_code = pytest.main(args, plugins=[plugin])
    finally:
        if prior_profile is None:
            os.environ.pop("RK_CHAOS_PROFILE", None)
        else:
            os.environ["RK_CHAOS_PROFILE"] = prior_profile

        if prior_seed is None:
            os.environ.pop("RK_CHAOS_SEED", None)
        else:
            os.environ["RK_CHAOS_SEED"] = prior_seed

        if prior_run_dir is None:
            os.environ.pop("RK_RUN_DIR", None)
        else:
            os.environ["RK_RUN_DIR"] = prior_run_dir

    ended_at = datetime.now(UTC)
    tests = plugin.records
    status = "passed" if exit_code == 0 else "failed"
    run = RunRecord(
        run_id=run_id,
        project=config.project.name,
        started_at=started_at,
        ended_at=ended_at,
        duration_ms=int((ended_at - started_at).total_seconds() * 1000),
        status=status,
        environment=collect_environment(),
        chaos_profile=chaos_profile,
        chaos_seed=chaos_seed,
        surface=surface,
        scan_pack=scan_pack,
        tests=tests,
    )
    storage.write_run(run, run_dir)
    return run
