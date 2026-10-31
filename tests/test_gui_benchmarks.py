"""Headless checks for the harness record behind the solver card's time and memory."""

from __future__ import annotations

import json
from pathlib import Path

from bloxorz.gui.benchmarks import Metrics, load, lookup


def _record(
    stage_name: str, algorithm: str, time_ms: float, peak_mem_kb: float
) -> dict[str, object]:
    return {
        "stage_name": stage_name,
        "algorithm": algorithm,
        "time_ms": time_ms,
        "peak_mem_kb": peak_mem_kb,
    }


def _write(tmp_path: Path, records: list[dict[str, object]]) -> Path:
    path = tmp_path / "benchmark_results.json"
    path.write_text(json.dumps(records), encoding="utf-8")
    return path


def test_records_are_keyed_by_stage_and_algorithm(tmp_path: Path) -> None:
    path = _write(
        tmp_path,
        [
            _record("Long corridor", "BFS", 41.03, 62.13),
            _record("Long corridor", "A*", 19.98, 42.89),
        ],
    )

    assert load(path) == {
        ("Long corridor", "BFS"): Metrics(time_ms=41.03, peak_mem_kb=62.13),
        ("Long corridor", "A*"): Metrics(time_ms=19.98, peak_mem_kb=42.89),
    }


def test_a_missing_broken_or_shapeless_file_answers_nothing(tmp_path: Path) -> None:
    broken = tmp_path / "broken.json"
    broken.write_text("{not json", encoding="utf-8")

    assert load(tmp_path / "absent.json") == {}
    assert load(broken) == {}
    assert load(_write(tmp_path, [{"stage_name": "Long corridor"}])) == {}


def test_the_shipped_record_reaches_the_benchmarked_stages() -> None:
    """Guards the path from the package to Report/ and the fields the card reads."""
    records = load()

    assert len(records) == 40
    assert records[("Long corridor", "BFS")] == Metrics(time_ms=41.03, peak_mem_kb=62.13)


def test_lookup_answers_only_for_a_benchmarked_pair() -> None:
    assert lookup("Long corridor", "BFS") == Metrics(time_ms=41.03, peak_mem_kb=62.13)
    assert lookup("Side rooms", "Dijkstra") is None
