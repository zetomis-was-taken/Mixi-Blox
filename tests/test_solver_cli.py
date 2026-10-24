"""The public UCS/A* CLI and its result/cap/error boundary."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]


@pytest.mark.parametrize("algorithm", ["ucs", "astar", "bfs"])
def test_module_cli_runs_the_cost_solvers(algorithm) -> None:
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
