"""Shared-loop behavior, weighted board paths and exhaustive heuristic checks."""

from __future__ import annotations

import heapq
from collections import defaultdict
from itertools import count
from pathlib import Path

import pytest

from bloxorz.core.contracts import Caps, State
from bloxorz.core.engine import Board
from bloxorz.core.stage import load_stage
from bloxorz.solvers import astar, base, bfs, dfs, ucs

ROOT = Path(__file__).resolve().parents[1]
STAGES = ROOT / "Source/bloxorz/core/stages"
SOLVERS = [bfs.solve, dfs.solve, ucs.solve, astar.solve]
FIXTURE = ROOT / "tests/fixtures/FIX-01_straight_line.json"


def replay(board: Board, path: tuple) -> tuple[State, float]:
    state, cost = board.start(), 0.0
    for action in path:
        next_state = {a: s for s, a in board.successors(state)}[action]
        cost += board.step_cost(state, action, next_state)
        state = next_state
    return state, cost


@pytest.mark.parametrize("solver", SOLVERS)
def test_every_frontier_uses_the_same_goal_cap_and_count_protocol(solver) -> None:
    stage = load_stage(FIXTURE)
    exact = solver(stage, Caps(node_cap=6))
    assert exact.status == "solved"
    assert len(exact.path) == exact.cost == exact.counts.expanded == 6
    assert exact.counts.generated == 7
    assert exact.counts.frontier_peak == 1
    capped = solver(stage, Caps(node_cap=5))
    assert capped.status == "cap" and capped.path == () and capped.cost == 0
    assert capped.counts.expanded == 5


@pytest.mark.parametrize("solver", SOLVERS)
def test_time_cap_zero_returns_counts_without_expanding(solver) -> None:
    result = solver(load_stage(FIXTURE), Caps(time_s=0))
    assert result.status == "cap"
    assert result.counts.expanded == 0
    assert result.counts.generated == result.counts.frontier_peak == 1


@pytest.mark.parametrize("solver", SOLVERS)
def test_initial_goal_is_solved_with_an_empty_path_and_zero_node_cap(monkeypatch, solver) -> None:
    monkeypatch.setattr(Board, "is_goal", lambda self, state: True)
    result = solver(load_stage(FIXTURE), Caps(node_cap=0))
    assert result.status == "solved" and result.path == () and result.cost == 0
    assert result.counts.expanded == 0
    assert result.counts.generated == result.counts.frontier_peak == 1


@pytest.mark.parametrize("solver", SOLVERS)
def test_time_cap_can_expire_after_work(monkeypatch, solver) -> None:
    # The last deadline check precedes popping the already queued goal, matching
    # the contract's explicit pseudocode (node-cap precedence is tested above).
    clock = iter([0] + [0] * 6 + [1])
    monkeypatch.setattr(base, "perf_counter", lambda: next(clock))
    result = solver(load_stage(FIXTURE), Caps(time_s=1))
    assert result.status == "cap" and result.path == ()
    assert result.counts.expanded == 6


@pytest.mark.parametrize(
    "caps", [Caps(node_cap=-1), Caps(node_cap=1.5), Caps(time_s=-1), Caps(time_s=float("nan"))]
)
def test_invalid_caps_fail_as_configuration_errors(caps) -> None:
    with pytest.raises(ValueError):
        ucs.solve(load_stage(FIXTURE), caps)


@pytest.mark.parametrize("path", sorted(STAGES.glob("*.json")), ids=lambda p: p.stem)
def test_weighted_solutions_and_heuristic_match_an_independent_reverse_oracle(path) -> None:
    stage = load_stage(path)
    board = Board(stage)
    estimate = astar.make_heuristic(stage)
    seen = {board.start()}
    todo = list(seen)
    reverse = defaultdict(list)
    goals = []
    while todo:
        state = todo.pop()
        if board.is_goal(state):
            goals.append(state)
        for child, action in board.successors(state):
            cost = board.step_cost(state, action, child)
            assert cost >= 1
            assert estimate(state) <= cost + estimate(child)
            reverse[child].append((state, cost))
            if child not in seen:
                seen.add(child)
                todo.append(child)
    serial = count()
    distance = {goal: 0.0 for goal in goals}
    frontier = [(0.0, next(serial), goal) for goal in goals]
    heapq.heapify(frontier)
    while frontier:
        cost, _, state = heapq.heappop(frontier)
        if distance[state] != cost:
            continue
        for previous, edge_cost in reverse[state]:
            candidate = cost + edge_cost
            if candidate < distance.get(previous, float("inf")):
                distance[previous] = candidate
                heapq.heappush(frontier, (candidate, next(serial), previous))
    for state, cost in distance.items():
        assert estimate(state) <= cost
    for solver in SOLVERS:
        result = solver(stage)
        assert result.status == "solved"
        end, cost = replay(board, result.path)
        assert board.is_goal(end) and cost == result.cost
        if solver in (ucs.solve, astar.solve):
            assert result.cost == distance[board.start()]


def test_ucs_prefers_a_longer_but_less_fragile_route_on_a_real_board() -> None:
    stage = load_stage(next(STAGES.glob("L2-02_*.json")))
    shortest, cheapest = bfs.solve(stage), ucs.solve(stage)
    assert len(shortest.path) < len(cheapest.path)
    assert cheapest.cost < shortest.cost
    assert astar.solve(stage).cost == cheapest.cost


def test_split_heuristic_does_not_use_an_unsafe_teleport_distance() -> None:
    stage = load_stage(next(STAGES.glob("L4-01_*.json")))
    assert astar.heuristic(stage, Board(stage).start()) == 0


def test_stale_heap_entries_are_not_counted_as_expansions(monkeypatch) -> None:
    from test_cost_search import _GraphBoard

    class NoGoalBoard(_GraphBoard):
        def is_goal(self, state):
            return False

    monkeypatch.setattr(base, "Board", NoGoalBoard)
    result = base.solve_search(object())
    assert result.status == "unsolvable"
    assert result.counts.expanded == 4
    assert result.counts.generated == 6
    assert result.counts.frontier_peak == 3


@pytest.mark.parametrize("solver", [bfs.solve, dfs.solve])
def test_queue_and_stack_exhaust_cycles_without_revisiting_keys(monkeypatch, solver) -> None:
    from test_cost_search import _GraphBoard

    class CyclicBoard(_GraphBoard):
        def is_goal(self, state):
            return False

        def successors(self, state):
            if state == self._states["G"]:
                return [(self._states["S"], (0, "U"))]
            return super().successors(state)

        def step_cost(self, state, action, child):
            return 1.0

    monkeypatch.setattr(base, "Board", CyclicBoard)
    result = solver(object())
    assert result.status == "unsolvable" and result.path == ()
    assert result.counts.expanded == result.counts.generated == 4


def test_astar_reopens_an_expanded_node_with_an_admissible_inconsistent_heuristic(
    monkeypatch,
) -> None:
    from test_cost_search import _GraphBoard

    class ReopenBoard(_GraphBoard):
        def step_cost(self, state, action, next_state):
            names = {value: name for name, value in self._states.items()}
            costs = {("S", "A"): 3, ("S", "B"): 1, ("B", "A"): 1, ("A", "G"): 10, ("B", "G"): 20}
            return float(costs[names[state], names[next_state]])

    monkeypatch.setattr(base, "Board", ReopenBoard)
    result = base.solve_search(
        object(), heuristic=lambda state: 10.0 if state.cubes == (((0, 2),),) else 0.0
    )
    assert result.status == "solved" and result.cost == 12
    assert result.path == ((0, "D"), (0, "L"), (0, "R"))
    assert result.counts.expanded == 4  # A is expanded at g=3, then reopened at g=2.


@pytest.mark.parametrize("step", [0.0, -1.0, float("nan"), float("inf")])
def test_invalid_edge_costs_fail_loudly(monkeypatch, step) -> None:
    monkeypatch.setattr(Board, "step_cost", lambda self, state, action, child: step)
    with pytest.raises(ValueError, match="step_cost"):
        ucs.solve(load_stage(FIXTURE))
