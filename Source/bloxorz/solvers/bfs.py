"""FIFO adapter for the shared loop (#18); BFS integration baseline."""

from bloxorz.core.contracts import Caps, SearchResult, Stage
from bloxorz.solvers.base import solve_search


def solve(stage: Stage, caps: Caps = Caps()) -> SearchResult:
    """Minimize moves; report the actual weighted cost of the returned path."""
    return solve_search(stage, caps, ordering="fifo")
