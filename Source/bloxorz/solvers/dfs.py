"""LIFO adapter for the shared loop (#18); DFS integration baseline."""

from bloxorz.core.contracts import Caps, SearchResult, Stage
from bloxorz.solvers.base import solve_search


def solve(stage: Stage, caps: Caps = Caps()) -> SearchResult:
    """Search depth first with discover-on-push cycle detection; not optimal."""
    return solve_search(stage, caps, ordering="lifo")
