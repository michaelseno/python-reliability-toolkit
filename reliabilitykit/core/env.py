from __future__ import annotations

import os
import platform
import socket
import subprocess
import sys

import pytest

from reliabilitykit.core.models import RunEnvironment


def _try_git(cmd: list[str]) -> str | None:
    try:
        return subprocess.check_output(cmd, stderr=subprocess.DEVNULL, text=True).strip() or None
    except Exception:
        return None


def collect_environment() -> RunEnvironment:
    try:
        from playwright import __version__ as playwright_version
    except Exception:
        playwright_version = None

    ci_provider = None
    ci_run_id = None
    ci_job_id = None
    ci_job_url = None
    if os.getenv("GITHUB_ACTIONS") == "true":
        ci_provider = "github_actions"
        ci_run_id = os.getenv("GITHUB_RUN_ID")
        ci_job_id = os.getenv("GITHUB_JOB")
        repo = os.getenv("GITHUB_REPOSITORY")
        run_id = os.getenv("GITHUB_RUN_ID")
        if repo and run_id:
            ci_job_url = f"https://github.com/{repo}/actions/runs/{run_id}"
    elif os.getenv("CI"):
        ci_provider = "generic_ci"
        ci_run_id = os.getenv("CI_PIPELINE_ID") or os.getenv("BUILD_ID")
        ci_job_id = os.getenv("CI_JOB_ID") or os.getenv("BUILD_NUMBER")

    return RunEnvironment(
        os=f"{platform.system()} {platform.release()}",
        python_version=sys.version.split()[0],
        playwright_version=playwright_version,
        pytest_version=pytest.__version__,
        git_sha=_try_git(["git", "rev-parse", "HEAD"]),
        branch=_try_git(["git", "rev-parse", "--abbrev-ref", "HEAD"]),
        host=os.getenv("HOSTNAME") or socket.gethostname(),
        is_ci=bool(ci_provider),
        ci_provider=ci_provider,
        ci_run_id=ci_run_id,
        ci_job_id=ci_job_id,
        ci_job_url=ci_job_url,
    )
