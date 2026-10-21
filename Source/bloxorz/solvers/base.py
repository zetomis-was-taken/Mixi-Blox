"""One search loop and counting protocol for FIFO, LIFO, UCS and A* (#18)."""

from __future__ import annotations

from collections import deque
from dataclasses import dataclass
from heapq import heappop, heappush
from itertools import count
from math import isfinite
from time import perf_counter
from typing import Callable, Literal

from bloxorz.core.contracts import Action, Caps, Counts, SearchResult, Stage, State, Status
from bloxorz.core.costs import MINIMUM_ACTION_COST
from bloxorz.core.engine import Board

Ordering = Literal["fifo", "lifo", "cost"]
Heuristic = Callable[[State], float]


@dataclass(frozen=True)
class _Node:
    state: State
    cost: float
    parent: _Node | None = None
    action: Action | None = None


def _path(node: _Node) -> tuple[Action, ...]:
    actions: list[Action] = []
    while node.parent is not None:
        assert node.action is not None
        actions.append(node.action)
        node = node.parent
    return tuple(reversed(actions))


class _Frontier:
    """Ordering is the only difference between the queue/stack/heap frontiers."""

    def __init__(self, ordering: Ordering) -> None:
        self.ordering = ordering
        self.queue: deque[_Node] = deque()
        self.heap: list[tuple[float, float, int, _Node]] = []
        self.serial = count()

    def push(self, node: _Node, estimate: float = 0.0) -> None:
        if self.ordering == "cost":
            heappush(self.heap, (node.cost + estimate, node.cost, next(self.serial), node))
        else:
            self.queue.append(node)

    def pop(self) -> _Node:
        if self.ordering == "cost":
            return heappop(self.heap)[3]
        return self.queue.popleft() if self.ordering == "fifo" else self.queue.pop()

    def __len__(self) -> int:
        return len(self.heap) if self.ordering == "cost" else len(self.queue)


def _validate_caps(caps: Caps) -> None:
    if caps.node_cap is not None and (
        isinstance(caps.node_cap, bool) or not isinstance(caps.node_cap, int) or caps.node_cap < 0
    ):
        raise ValueError("node_cap must be a non-negative integer or None")
    if caps.time_s is not None and (not isfinite(caps.time_s) or caps.time_s < 0):
        raise ValueError("time_s must be finite and non-negative or None")


def solve_search(
    stage: Stage,
    caps: Caps = Caps(),
    *,
    ordering: Ordering = "cost",
    heuristic: Heuristic | None = None,
) -> SearchResult:
    """Search a compiled stage, returning counts on every normal outcome.

    FIFO/LIFO discover each key once. Cost ordering reinserts improved ``g``
    values and ignores stale heap entries, including reopening expanded keys.
    A* supplies a state heuristic; UCS uses zero. Ties are deterministic and
    never compare states. The time cap precedes pop, as in the frozen API's
    pseudocode; the node cap follows the goal test and precedes expansion.
    """
    _validate_caps(caps)
    if ordering not in ("fifo", "lifo", "cost"):
        raise ValueError(f"unknown frontier ordering: {ordering!r}")
    if heuristic is not None and ordering != "cost":
        raise ValueError("a heuristic requires cost ordering")
    board = Board(stage)
    started = perf_counter()
    estimate = heuristic if heuristic is not None else lambda _state: 0.0
    root = _Node(board.start(), 0.0)
    frontier = _Frontier(ordering)
    frontier.push(root, estimate(root.state))
    best_cost = {root.state.key(): 0.0}
    expanded, generated, frontier_peak = 0, 1, 1

    def result(status: Status, node: _Node | None = None) -> SearchResult:
        return SearchResult(
            status,
            _path(node) if node is not None else (),
            node.cost if node is not None else 0.0,
            Counts(expanded, generated, frontier_peak),
        )

    while frontier:
        if caps.time_s is not None and perf_counter() - started >= caps.time_s:
            return result("cap")
        node = frontier.pop()
        if ordering == "cost" and node.cost != best_cost[node.state.key()]:
            continue
        if board.is_goal(node.state):
            return result("solved", node)
        if caps.node_cap is not None and expanded >= caps.node_cap:
            return result("cap")
        expanded += 1
        for next_state, action in board.successors(node.state):
            step = board.step_cost(node.state, action, next_state)
            if not isfinite(step) or step < MINIMUM_ACTION_COST:
                raise ValueError(f"step_cost must be finite and >= {MINIMUM_ACTION_COST}: {step!r}")
            next_cost = node.cost + step
            key = next_state.key()
            if key in best_cost and (ordering != "cost" or next_cost >= best_cost[key]):
                continue
            best_cost[key] = next_cost
            frontier.push(_Node(next_state, next_cost, node, action), estimate(next_state))
            generated += 1
            frontier_peak = max(frontier_peak, len(frontier))
    return result("unsolvable")
