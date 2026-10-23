"""Uniform-cost search through the owner-provided shared loop (#22)."""

from __future__ import annotations

from bloxorz.core.contracts import Caps, SearchResult, Stage
from bloxorz.solvers.base import search
from bloxorz.solvers.cost_frontier import CostFrontier


def solve(stage: Stage, caps: Caps = Caps()) -> SearchResult:
    """Return a minimum-total-cost solution, with path length available separately."""
    return search(stage, caps, frontier=CostFrontier())
