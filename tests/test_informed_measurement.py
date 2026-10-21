"""Measurement medians, failure cleanup and the module-based public CLI."""

from __future__ import annotations

import json
import subprocess
import sys
import tracemalloc
from pathlib import Path

import pytest

from bloxorz.bench import informed_search as bench
from bloxorz.core.contracts import Caps, Counts, SearchResult

ROOT = Path(__file__).resolve().parents[1]


def test_measurement_takes_independent_medians_and_preserves_cap_outcomes(monkeypatch) -> None:
    clock = iter([0, 1, 10, 13, 20, 22])
    peaks = iter([(0, 1000), (0, 5000), (0, 3000)])
    monkeypatch.setattr(bench, "perf_counter", lambda: next(clock))
    monkeypatch.setattr(tracemalloc, "get_traced_memory", lambda: next(peaks))
    calls = []

    def capped(stage, caps):
        calls.append((stage, caps))
        return SearchResult("cap", (), 0.0, Counts(2, 3, 1))

    row = bench.measure(capped, object(), Caps())
    assert len(calls) == 3
    assert row["time_s"] == 2 and row["peak_mem_bytes"] == 3000
    assert row["expanded"] == 2 and row["generated"] == 3
    assert row["status"] == "cap" and row["moves"] is row["cost"] is None
    assert not tracemalloc.is_tracing()


def test_measurement_stops_tracing_when_solver_raises() -> None:
    def broken(stage, caps):
        raise RuntimeError("broken solver")

    with pytest.raises(RuntimeError, match="broken solver"):
        bench.measure(broken, object(), Caps())
    assert not tracemalloc.is_tracing()


def test_measurement_rejects_nondeterministic_counts() -> None:
    counts = iter([1, 2, 3])

    def unstable(stage, caps):
        return SearchResult("cap", (), 0.0, Counts(next(counts), 4, 2))

    with pytest.raises(AssertionError, match="differed"):
        bench.measure(unstable, object(), Caps())
    assert not tracemalloc.is_tracing()


def test_report_renders_missing_results_as_dashes_instead_of_zeroes() -> None:
    metadata = {
        "created_at_utc": "test",
        "python": "3.12",
        "platform": "test",
        "base_commit": "test",
        "source_sha256": "test",
    }
    error = {
        "stage": "T-01",
        "algorithm": "UCS",
        "status": "error",
        "error_message": "RuntimeError",
    }
    rendered = bench.markdown([error], metadata)
    assert "| T-01 | UCS | LỖI | - | - | - | - | - | - | - |" in rendered


@pytest.mark.parametrize("algorithm", ["bfs", "dfs", "ucs", "astar"])
def test_module_cli_runs_real_solvers_and_returns_serializable_results(algorithm) -> None:
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
