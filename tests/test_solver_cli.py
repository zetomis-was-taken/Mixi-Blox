"""The public solver CLI and its result/cap/error boundary."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]


@pytest.mark.parametrize("algorithm", ["bfs", "dfs", "ucs", "astar"])
def test_module_cli_runs_every_registered_solver(algorithm) -> None:
    completed = subprocess.run(
        [
            sys.executable,
            "-m",
            "Source.main",
            "--stage",
            "tests/fixtures/FIX-01_straight_line.json",
            "--solver",
            algorithm,
        ],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=True,
    )
    result = json.loads(completed.stdout)
    assert result["status"] == "solved" and result["cost"] == 6
    assert len(result["path"]) == 6 and result["counts"]["expanded"] == 6


def test_module_cli_distinguishes_caps_from_configuration_errors() -> None:
    command = [
        sys.executable,
        "-m",
        "Source.main",
        "--stage",
        "tests/fixtures/FIX-01_straight_line.json",
        "--solver",
        "ucs",
        "--node-cap",
    ]
    capped = subprocess.run(command + ["0"], cwd=ROOT, capture_output=True, text=True)
    assert capped.returncode == 1 and json.loads(capped.stdout)["status"] == "cap"
    invalid = subprocess.run(command + ["-1"], cwd=ROOT, capture_output=True, text=True)
    assert invalid.returncode == 2 and "non-negative" in invalid.stderr


def test_module_cli_no_gui_prints_help() -> None:
    res = subprocess.run(
        [sys.executable, "-m", "Source.main", "--no-gui"],
        cwd=ROOT,
        capture_output=True,
        text=True,
    )
    assert res.returncode == 0
    assert "Mixi-Blox" in res.stdout or "usage:" in res.stdout


def test_module_cli_no_gui_inspects_stage() -> None:
    res = subprocess.run(
        [
            sys.executable,
            "-m",
            "Source.main",
            "--no-gui",
            "--stage",
            "tests/fixtures/FIX-01_straight_line.json",
        ],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=True,
    )
    assert "FIX-01" in res.stdout
    assert "legal moves" in res.stdout


def test_module_cli_rejects_solver_with_gui() -> None:
    res = subprocess.run(
        [
            sys.executable,
            "-m",
            "Source.main",
            "--gui",
            "--solver",
            "ucs",
        ],
        cwd=ROOT,
        capture_output=True,
        text=True,
    )
    assert res.returncode == 2
    assert "--solver cannot be used with --gui" in res.stderr

