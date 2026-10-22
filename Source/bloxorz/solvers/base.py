"""The shared search loop (#18).

One loop owns the bookkeeping every algorithm needs: the frontier, the duplicate policy, the
expansion count, the cap checks and the result record. An algorithm supplies only its frontier
ordering, so BFS, DFS, UCS and A* differ in one place.

The loop shape is the one ``docs/contracts.md`` § Solver API freezes: the time cap is checked
before the pop, the goal test runs before the node cap, the node cap runs before the increment,
and the counters move at exactly three points.
"""

from __future__ import annotations

from collections import deque
from dataclasses import dataclass
from math import isfinite
from time import perf_counter

from bloxorz.core.contracts import Action, Caps, Counts, SearchResult, Stage, State, Status
from bloxorz.core.engine import Board


@dataclass(frozen=True, eq=False)
class Node:
    """One search node: its state, its accumulated cost and how it was reached.

    The path is rebuilt from the parent chain on demand. A tuple copied into every node would
    make peak memory grow with the square of the path length, and the harness measures peak
    memory (#24). Nodes carry identity rather than value: only ``State`` has a value identity,
    and that is what the frontier keys on.
    """

    state: State
    cost: float = 0.0
    parent: Node | None = None
    action: Action | None = None

    def child(self, state: State, action: Action, cost: float) -> Node:
        """The node one action away."""
        return Node(state=state, cost=cost, parent=self, action=action)

    @property
    def path(self) -> tuple[Action, ...]:
        """The actions that reach this node, in order."""
        actions: list[Action] = []
        node = self
        while node.parent is not None:
            assert node.action is not None
            actions.append(node.action)
            node = node.parent
        return tuple(reversed(actions))


class Frontier:
    """The default FIFO frontier: first discovery wins.

    The frontier owns the duplicate policy, not the loop. ``push`` refuses a key it has already
    seen, which is what lets the loop be the frozen pseudocode verbatim.

    A subclass changes the ordering by overriding ``push`` and ``pop``, and nothing else. Two
    rules bind a subclass:

    - ``len(frontier)`` counts **live** nodes, not stored entries. A cost-ordered frontier keeps
      a stale entry alive after a cheaper path replaces it; counting stored entries would make
      ``frontier_peak`` measure leftovers, and would leave the loop spinning over a frontier
      with no usable node in it.
    - ``bool(frontier)`` is therefore "there is at least one live node".
    """

    def __init__(self) -> None:
        self._queue: deque[Node] = deque()
        self._seen: set[tuple[object, ...]] = set()

    def push(self, node: Node) -> None:
        """Offer a node. A key already seen is refused: the first discovery wins."""
        key = node.state.key()
        if key in self._seen:
            return
        self._seen.add(key)
        self._queue.append(node)

    def pop(self) -> Node:
        """The next node to expand."""
        return self._queue.popleft()

    def __len__(self) -> int:
        """How many live nodes the frontier holds."""
        return len(self._queue)

    def __bool__(self) -> bool:
        """Whether any live node is left."""
        return bool(self._queue)


def _validate_caps(caps: Caps) -> None:
    """A cap that cannot be honoured is a configuration error, not a result."""
    if caps.node_cap is not None and (
        isinstance(caps.node_cap, bool) or not isinstance(caps.node_cap, int) or caps.node_cap < 0
    ):
        raise ValueError("node_cap must be a non-negative integer or None")
    if caps.time_s is not None and (not isfinite(caps.time_s) or caps.time_s < 0):
        raise ValueError("time_s must be finite and non-negative or None")


def search(
    stage: Stage,
    caps: Caps = Caps(),
    *,
    frontier: Frontier | None = None,
) -> SearchResult:
    """Search one compiled stage and return the outcome as a value.

    The loop owns the counters, the caps and the result record; the frontier owns the ordering
    and the duplicate policy. The counters are kept as locals because ``Counts`` is frozen, and
    the record is built on return - the points they move at are the frozen ones.

    The order is the frozen one: the time cap is checked before the pop, the goal test runs
    before the node cap, and the node cap runs before the increment. So a solution found exactly
    at the cap is still ``solved``, and ``node_cap`` counts completed expansions.

    The solver measures nothing else: no clock except the deadline above, and no memory. Both
    belong to the harness (#24).
    """
    _validate_caps(caps)
    board = Board(stage)  # O(1): the stage arrives compiled
    t0 = perf_counter()

    frontier = Frontier() if frontier is None else frontier
    expanded, generated, frontier_peak = 0, 1, 1
    frontier.push(Node(state=board.start()))

    def result(status: Status, node: Node | None = None) -> SearchResult:
        return SearchResult(
            status,
            node.path if node is not None else (),
            node.cost if node is not None else 0.0,
            Counts(expanded, generated, frontier_peak),
        )

    while frontier:
        if caps.time_s is not None and (perf_counter() - t0) >= caps.time_s:
            return result("cap")
        node = frontier.pop()
        if board.is_goal(node.state):
            return result("solved", node)
        if caps.node_cap is not None and expanded >= caps.node_cap:
            return result("cap")
        expanded += 1
        for next_state, action in board.successors(node.state):
            generated += 1
            step = board.step_cost(node.state, action, next_state)
            frontier.push(node.child(next_state, action, node.cost + step))
            frontier_peak = max(frontier_peak, len(frontier))
    return result("unsolvable")
