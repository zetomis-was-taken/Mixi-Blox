"""Depth-first search through the owner-provided shared loop (#20)."""

from __future__ import annotations

from bloxorz.core.contracts import Caps, SearchResult, Stage
from bloxorz.solvers.base import Frontier, Node, search


class StackFrontier(Frontier):
    """LIFO ordering; the duplicate policy and counters stay in the base frontier."""

    def pop(self) -> Node:
        """Expand the most recently discovered node first."""
        return self._queue.pop()


def solve(stage: Stage, caps: Caps = Caps()) -> SearchResult:
    """Return the first goal reached depth-first; the path is not move-optimal."""
    return search(stage, caps, frontier=StackFrontier())
