from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

import pytest

from country_values_distance.cli import build_parser, main


REPO_ROOT = Path(__file__).resolve().parents[2]


def test_python_module_help_succeeds() -> None:
    env = os.environ.copy()
    env["PYTHONPATH"] = str(REPO_ROOT / "src")

    completed = subprocess.run(
        [sys.executable, "-m", "country_values_distance", "--help"],
        cwd=REPO_ROOT,
        env=env,
        capture_output=True,
        text=True,
        check=False,
    )

    assert completed.returncode == 0, completed.stderr
    assert "prepare-companies" in completed.stdout
    assert "run-all" in completed.stdout


@pytest.mark.parametrize(
    ("command", "expected"),
    [
        ("prepare-companies", "prepare_companies"),
        ("qualify-domains", "qualify_and_sample_companies"),
        ("check-availability", "check_availability"),
        ("check-robots", "check_robots_stage"),
        ("fetch-homepages", "fetch_homepages_stage"),
        ("extract-links", "extract_links_stage"),
        ("run-all", "run_all"),
    ],
)
def test_cli_dispatches_all_stage_commands(monkeypatch, command, expected) -> None:
    called: dict[str, str] = {}

    def fake_prepare_companies(*args, **kwargs):
        called["prepare_companies"] = "called"

    def fake_qualify_and_sample_companies(*args, **kwargs):
        called["qualify_and_sample_companies"] = "called"

    def fake_check_availability(*args, **kwargs):
        called["check_availability"] = "called"

    def fake_check_robots_stage(*args, **kwargs):
        called["check_robots_stage"] = "called"

    def fake_fetch_homepages_stage(*args, **kwargs):
        called["fetch_homepages_stage"] = "called"

    def fake_extract_links_stage(*args, **kwargs):
        called["extract_links_stage"] = "called"

    def fake_run_all(*args, **kwargs):
        called["run_all"] = "called"

    monkeypatch.setattr("country_values_distance.cli.prepare_companies", fake_prepare_companies)
    monkeypatch.setattr("country_values_distance.cli.qualify_and_sample_companies", fake_qualify_and_sample_companies)
    monkeypatch.setattr("country_values_distance.cli.check_availability", fake_check_availability)
    monkeypatch.setattr("country_values_distance.cli.check_robots_stage", fake_check_robots_stage)
    monkeypatch.setattr("country_values_distance.cli.fetch_homepages_stage", fake_fetch_homepages_stage)
    monkeypatch.setattr("country_values_distance.cli.extract_links_stage", fake_extract_links_stage)
    monkeypatch.setattr("country_values_distance.cli.run_all", fake_run_all)

    parser = build_parser()
    args = parser.parse_args([command])

    monkeypatch.setattr("sys.argv", ["country-values-distance", command])
    main()

    assert expected in called