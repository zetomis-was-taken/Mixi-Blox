"""Cost ordering and duplicate handling for the shared #18 loop (#22)."""

from __future__ import annotations

from heapq import heappop, heappush
from itertools import count
from math import isfinite

from bloxorz.core.costs import MINIMUM_ACTION_COST
from bloxorz.solvers.base import Frontier, Node


class CostFrontier(Frontier):
    """Keep the cheapest discovered path and expose only live pending nodes.

    Strict improvements replace pending nodes or reopen expanded states. Old
    heap entries are skipped by identity; they do not contribute to ``len``
    or ``bool``. The best discovered cost survives a pop, so equal-cost cycles
    are refused. Subclasses may override ``priority`` to add an estimate.
    """

    def __init__(self) -> None:
        self._heap: list[tuple[float, float, int, Node]] = []
        self._best_cost: dict[tuple[object, ...], float] = {}
        self._pending: dict[tuple[object, ...], Node] = {}
        self._serial = count()

    def priority(self, node: Node) -> float:
        """UCS orders nodes by accumulated path cost."""
        return node.cost

    def push(self, node: Node) -> None:
        if not isfinite(node.cost) or node.cost < 0:
            raise ValueError("path cost must be finite and non-negative")
        if node.parent is not None:
            step = node.cost - node.parent.cost
            if not isfinite(step) or step < MINIMUM_ACTION_COST:
                raise ValueError(f"step_cost must be finite and >= {MINIMUM_ACTION_COST}")
        key = node.state.key()
        if node.cost >= self._best_cost.get(key, float("inf")):
            return
        priority = self.priority(node)
        if not isfinite(priority):
            raise ValueError("frontier priority must be finite")
        self._best_cost[key] = node.cost
        self._pending[key] = node
        heappush(self._heap, (priority, node.cost, next(self._serial), node))

    def pop(self) -> Node:
        while self._heap:
            node = heappop(self._heap)[3]
            key = node.state.key()
            if self._pending.get(key) is node:
                del self._pending[key]
                return node
        raise IndexError("pop from an empty cost frontier")

    def __len__(self) -> int:
        return len(self._pending)

    def __bool__(self) -> bool:
        return bool(self._pending)
