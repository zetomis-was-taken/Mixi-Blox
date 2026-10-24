"""Breadth-first search through the owner-provided shared loop (#19)."""

from __future__ import annotations

from bloxorz.core.contracts import Caps, SearchResult, Stage
from bloxorz.solvers.base import Frontier, search


def solve(stage: Stage, caps: Caps = Caps()) -> SearchResult:
    """Return a shortest-move solution; its weighted cost is available separately."""
    # Explicit FIFO for symmetry with ucs.py and astar.py; base.search already defaults to it.
    return search(stage, caps, frontier=Frontier())
