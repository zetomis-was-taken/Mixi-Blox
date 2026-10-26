"""Development aid: one breadth-first search so solver playback can be watched today.

This is **not** the submission's BFS. ``bloxorz.solvers`` (#18–#23) owns the real algorithms; this
module exists only so ``python Source/main.py --gui --replay-demo`` can hand the level scene a
mapping and the solve → movie → card loop can be exercised before that package lands. Delete this
file and the flag when #18 merges.

It lives in ``gui/`` rather than ``solvers/`` on purpose: the solvers package is owned by #18 and
policed by ``tests/test_contract.py``. That same test is why ``Caps.time_s`` is ignored here — the
GUI layer may not import a clock — while ``node_cap`` is honoured.
"""

from __future__ import annotations

from collections import deque

from bloxorz.core.contracts import Action, Caps, Counts, SearchResult, Stage, State
from bloxorz.core.engine import Board

from .replay import Algorithms

DEMO_NAME = "BFS (demo)"


def solve(stage: Stage, caps: Caps = Caps()) -> SearchResult:
    """The shortest path by breadth-first search, with the counts the contract asks for."""
    board = Board(stage)
    start = board.start()
    # ``Counts`` is frozen, so the running totals are locals until a result value is built.
    expanded = 0
    generated = 1
    frontier_peak = 1
    frontier: deque[tuple[State, tuple[Action, ...], float]] = deque([(start, (), 0.0)])
    seen = {start.key()}

    while frontier:
        state, path, cost = frontier.popleft()
        if board.is_goal(state):
            return SearchResult(
                "solved", path, cost, Counts(expanded, generated, frontier_peak)
            )
        if caps.node_cap is not None and expanded >= caps.node_cap:
            return SearchResult("cap", (), 0.0, Counts(expanded, generated, frontier_peak))
        expanded += 1
        for next_state, action in board.successors(state):
            if next_state.key() in seen:
                continue
            seen.add(next_state.key())
            generated += 1
            cost_after = cost + board.step_cost(state, action, next_state)
            frontier.append((next_state, path + (action,), cost_after))
            frontier_peak = max(frontier_peak, len(frontier))

    return SearchResult("unsolvable", (), 0.0, Counts(expanded, generated, frontier_peak))


ALGORITHMS: Algorithms = {DEMO_NAME: solve}
