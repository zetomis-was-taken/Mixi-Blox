"""The harness's committed measurements, so a solver card can show time and peak memory.

Contract rule 5 keeps clocks and allocators out of ``gui/``: the search measures nothing, and the
game does not either. Those two figures therefore come from ``Report/data/benchmark_results.json``,
the record the benchmark harness writes for the same stage and algorithm. A stage outside the
benchmark set, or a tree shipped without ``Report/``, has no record, and the card simply leaves the
figures out.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

# Source/bloxorz/gui/benchmarks.py -> the repository root, where Report/ lives.
DEFAULT_PATH = Path(__file__).resolve().parents[3] / "Report" / "data" / "benchmark_results.json"


@dataclass(frozen=True)
class Metrics:
    """One measured run: how long it took, and the memory it peaked at."""

    time_ms: float
    peak_mem_kb: float


def load(path: Path = DEFAULT_PATH) -> dict[tuple[str, str], Metrics]:
    """Read the harness record, keyed by ``(stage name, algorithm)``.

    A missing, unreadable or malformed file answers an empty mapping instead of raising: the
    figures are a nicety on the card, never a reason for the game to fail to start.
    """
    try:
        records = json.loads(Path(path).read_text(encoding="utf-8"))
        return {
            (record["stage_name"], record["algorithm"]): Metrics(
                time_ms=float(record["time_ms"]),
                peak_mem_kb=float(record["peak_mem_kb"]),
            )
            for record in records
        }
    except (OSError, ValueError, KeyError, TypeError):
        return {}


@lru_cache(maxsize=1)
def _records() -> dict[tuple[str, str], Metrics]:
    """The shipped record, read once."""
    return load()


def lookup(stage_name: str, algorithm: str) -> Metrics | None:
    """The measured figures for one stage and algorithm, or ``None`` when it was not benchmarked."""
    return _records().get((stage_name, algorithm))
