"""Behavioural tests for the two cost-aware solvers."""

from __future__ import annotations

import heapq
import itertools
import json
from pathlib import Path

import pytest

from bloxorz.core.contracts import Caps, State
from bloxorz.core.engine import Board
from bloxorz.core.stage import load_stage
from bloxorz.solvers import astar, ucs
from bloxorz.solvers.base import solve_search

ROOT = Path(__file__).resolve().parents[1]
FIXTURES = ROOT / "tests" / "fixtures"


def _replay(stage_path: Path, path: tuple[tuple[int, str], ...]) -> float:
    board = Board(load_stage(stage_path))
    state = board.start()
    cost = 0.0
    for action in path:
        legal = {candidate: next_state for next_state, candidate in board.successors(state)}
        assert action in legal
        next_state = legal[action]
        cost += board.step_cost(state, action, next_state)
        state = next_state
    assert board.is_goal(state)
    return cost


@pytest.mark.parametrize("solver", [ucs.solve, astar.solve])
@pytest.mark.parametrize("name", ["FIX-01", "FIX-02", "FIX-03"])
def test_cost_solvers_replay_the_hand_computed_fixtures(solver: object, name: str) -> None:
    stage_path = next(FIXTURES.glob(f"{name}_*.json"))
    stage = load_stage(stage_path)
    result = solver(stage)  # type: ignore[operator]
    assert result.status == "solved"
    assert stage.expected is not None
    assert result.cost == stage.expected.optimal_cost
    assert _replay(stage_path, result.path) == result.cost


@pytest.mark.parametrize("solver", [ucs.solve, astar.solve])
def test_cost_solvers_report_cap_before_an_expansion(solver: object) -> None:
    stage = load_stage(next(FIXTURES.glob("FIX-01_*.json")))
    result = solver(stage, Caps(node_cap=0))  # type: ignore[operator]
    assert result.status == "cap"
    assert result.path == ()
    assert result.cost == 0.0
    assert result.counts.expanded == 0
    assert result.counts.generated == result.counts.frontier_peak == 1


@pytest.mark.parametrize("solver", [ucs.solve, astar.solve])
def test_cost_solvers_exhaust_an_unsolvable_stage(tmp_path: Path, solver: object) -> None:
    path = tmp_path / "unsolvable.json"
    path.write_text(
        json.dumps(
            {
                "id": "UNSOLVABLE",
                "name": "isolated goal",
                "group": "L1",
                "source": "original",
                "grid": [".....", ".S.G.", "....."],
                "switches": [],
                "bridges": [],
            }
        ),
        encoding="utf-8",
    )
    result = solver(load_stage(path))  # type: ignore[operator]
    assert result.status == "unsolvable"
    assert result.path == ()
    assert result.cost == 0.0


class _GraphBoard:
    """A tiny directed graph that forces a decrease-key-by-reinsertion."""

    def __init__(self, _stage: object) -> None:
        self._states = {name: State((((0, index),),), ()) for index, name in enumerate("SABG")}

    def start(self) -> State:
        return self._states["S"]

    def is_goal(self, state: State) -> bool:
        return state == self._states["G"]

    def successors(self, state: State) -> list[tuple[State, tuple[int, str]]]:
        edges = {
            self._states["S"]: [
                (self._states["A"], (0, "R")),
                (self._states["B"], (0, "D")),
            ],
            self._states["B"]: [
                (self._states["A"], (0, "L")),
                (self._states["G"], (0, "D")),
            ],
            self._states["A"]: [(self._states["G"], (0, "R"))],
        }
        return edges.get(state, [])

    def step_cost(self, state: State, action: tuple[int, str], next_state: State) -> float:
        costs = {
            ("S", "A"): 5.0,
            ("S", "B"): 1.0,
            ("B", "A"): 1.0,
            ("B", "G"): 20.0,
            ("A", "G"): 1.0,
        }
        names = {value: name for name, value in self._states.items()}
        return costs[(names[state], names[next_state])]


def test_ucs_reopens_a_state_when_a_cheaper_non_uniform_path_is_found(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr("bloxorz.solvers.base.Board", _GraphBoard)
    result = solve_search(object(), Caps())  # type: ignore[arg-type]
    assert result.status == "solved"
    assert result.cost == 3.0
    assert result.path == ((0, "D"), (0, "L"), (0, "R"))


def _reachable_states(board: Board) -> set[State]:
    todo = [board.start()]
    seen = {todo[0]}
    while todo:
        state = todo.pop()
        for next_state, _ in board.successors(state):
            if next_state not in seen:
                seen.add(next_state)
                todo.append(next_state)
    return seen


def _exact_remaining_cost(board: Board, start: State) -> float | None:
    serial = itertools.count()
    frontier = [(0.0, next(serial), start)]
    best = {start: 0.0}
    while frontier:
        cost, _, state = heapq.heappop(frontier)
        if cost != best[state]:
            continue
        if board.is_goal(state):
            return cost
        for next_state, action in board.successors(state):
            next_cost = cost + board.step_cost(state, action, next_state)
            if next_cost < best.get(next_state, float("inf")):
                best[next_state] = next_cost
                heapq.heappush(frontier, (next_cost, next(serial), next_state))
    return None


@pytest.mark.parametrize("name", ["FIX-01", "FIX-02", "FIX-03"])
def test_astar_heuristic_is_admissible_on_every_reachable_fixture_state(
    name: str,
) -> None:
    stage = load_stage(next(FIXTURES.glob(f"{name}_*.json")))
    board = Board(stage)
    for state in _reachable_states(board):
        remaining = _exact_remaining_cost(board, state)
        if remaining is not None:
            assert astar.heuristic(stage, state) <= remaining
