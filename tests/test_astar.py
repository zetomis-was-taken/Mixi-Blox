"""A* lower bounds, consistency, optimal cost and reopening (#23)."""

from __future__ import annotations

import pytest
from search_helpers import FIXTURES, STAGES, GraphBoard, remaining_costs, replay

from bloxorz.core.contracts import Caps
from bloxorz.core.engine import Board
from bloxorz.core.stage import load_stage
from bloxorz.solvers import astar, base, ucs


@pytest.mark.parametrize("name", ["FIX-01", "FIX-02", "FIX-03"])
def test_tiny_fixture_heuristic_never_exceeds_exact_remaining_cost(name) -> None:
    stage = load_stage(next(FIXTURES.glob(f"{name}_*.json")))
    board = Board(stage)
    seen, exact = remaining_costs(board)
    estimate = astar.make_heuristic(stage)
    for state in seen:
        assert estimate(state) >= 0
        if state in exact:
            assert estimate(state) <= exact[state]
    result = astar.solve(stage)
    end, cost = replay(board, result.path)
    assert result.status == "solved" and board.is_goal(end)
    assert stage.expected is not None
    assert result.cost == cost == stage.expected.optimal_cost


@pytest.mark.parametrize("path", sorted(STAGES.glob("*.json")), ids=lambda path: path.stem)
def test_heuristic_bounds_every_remaining_cost_and_edge_and_matches_ucs(path) -> None:
    stage = load_stage(path)
    board = Board(stage)
    seen, exact = remaining_costs(board)
    estimate = astar.make_heuristic(stage)
    for state in seen:
        assert estimate(state) >= 0
        if state in exact:
            assert estimate(state) <= exact[state]
        if board.is_goal(state):
            assert estimate(state) == 0
        for child, action in board.successors(state):
            assert estimate(state) <= board.step_cost(state, action, child) + estimate(child)
    result = astar.solve(stage)
    end, cost = replay(board, result.path)
    assert result.status == "solved" and board.is_goal(end)
    assert result.cost == cost == exact[board.start()] == ucs.solve(stage).cost


@pytest.mark.parametrize("name", ["L4-01", "L4-02"])
def test_split_stage_uses_zero_even_before_teleport_activation(name) -> None:
    stage = load_stage(next(STAGES.glob(f"{name}_*.json")))
    seen, _ = remaining_costs(Board(stage))
    estimate = astar.make_heuristic(stage)
    assert all(estimate(state) == 0 for state in seen)
    assert astar.solve(stage) == ucs.solve(stage)


def test_admissible_inconsistent_estimate_reopens_an_expanded_state(monkeypatch) -> None:
    class ReopenBoard(GraphBoard):
        costs = {("S", "A"): 3, ("S", "B"): 1, ("B", "A"): 1, ("A", "G"): 10, ("B", "G"): 20}

    board = ReopenBoard(None)
    monkeypatch.setattr(base, "Board", ReopenBoard)

    def estimate(state):
        return 10.0 if state == board.states["B"] else 0.0

    # h(B)=10 <= 11 remaining, yet h(B)>c(B,A)+h(A)=1.
    result = base.search(object(), frontier=astar.AStarFrontier(estimate))
    assert result.status == "solved" and result.cost == 12
    assert result.path == ((0, "D"), (0, "L"), (0, "R"))
    assert result.counts.expanded == 4
    assert result.counts.generated == 7 and result.counts.frontier_peak == 2


def test_a_one_move_goal_is_a_counterexample_to_an_extra_orientation_penalty() -> None:
    stage = load_stage(next(FIXTURES.glob("FIX-01_*.json")))
    board = Board(stage)
    state = board.start()
    for _ in range(5):
        state = {action: child for child, action in board.successors(state)}[(0, "R")]
    goal = {action: child for child, action in board.successors(state)}[(0, "R")]
    assert board.is_goal(goal)
    actual = board.step_cost(state, (0, "R"), goal)
    assert astar.heuristic(stage, state) == 0.5 <= actual == 1
    assert astar.heuristic(stage, state) + 1 > actual


@pytest.mark.parametrize("caps", [Caps(node_cap=0), Caps(time_s=0)])
def test_astar_passes_limits_to_the_shared_loop(caps) -> None:
    result = astar.solve(load_stage(next(FIXTURES.glob("FIX-01_*.json"))), caps)
    assert result.status == "cap" and result.path == () and result.cost == 0
    assert result.counts.expanded == 0
    assert result.counts.generated == result.counts.frontier_peak == 1
