from __future__ import annotations

from reliabilitykit.core.env import collect_environment


def test_collect_environment_has_runtime_fields() -> None:
    env = collect_environment()
    assert env.os
    assert env.python_version
    assert env.pytest_version
    assert env.host


def test_collect_environment_detects_github_actions(monkeypatch) -> None:
    monkeypatch.setenv("GITHUB_ACTIONS", "true")
    monkeypatch.setenv("GITHUB_RUN_ID", "1234")
    monkeypatch.setenv("GITHUB_REPOSITORY", "org/repo")
    monkeypatch.setenv("GITHUB_JOB", "test")

    env = collect_environment()
    assert env.is_ci is True
    assert env.ci_provider == "github_actions"
    assert env.ci_run_id == "1234"
    assert env.ci_job_id == "test"
    assert env.ci_job_url == "https://github.com/org/repo/actions/runs/1234"
