"""Breadth-first search through the ownder-provided shared loop (#19)."""

from __future__ import annotations

from bloxorz.core.contracts import Caps, SearchResult, Stage
from bloxorz.solvers.base import Frontier, search


def solve(stage: Stage, caps: Caps = Caps()) -> SearchResult:
    """Return a shortest-move solution; its weighted cost is available separately."""
    return search(stage, caps, frontier=Frontier())
