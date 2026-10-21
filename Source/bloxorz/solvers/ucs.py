"""Uniform-Cost Search for Mixi-Blox stages."""

from __future__ import annotations

from bloxorz.core.contracts import Caps, SearchResult, Stage
from bloxorz.solvers.base import solve_search


def solve(stage: Stage, caps: Caps = Caps()) -> SearchResult:
    """Return a minimum-total-cost solution using Dijkstra's algorithm."""
    return solve_search(stage, caps)
