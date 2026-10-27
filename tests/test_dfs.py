"""DFS termination, replay and LIFO ordering on the shared-loop contract (#20)."""

from __future__ import annotations

import pytest
from search_helpers import FIXTURE_IDS, FIXTURES, STAGES, replay

from bloxorz.core.contracts import Caps, State
from bloxorz.core.engine import Board
from bloxorz.core.stage import load_stage
from bloxorz.solvers import base, dfs, ucs
from bloxorz.solvers.base import Frontier


class _GraphBoard:
    """A board whose only job is to make the search order visible."""

    nodes: tuple[str, ...] = ()
    edges: dict[str, tuple[str, ...]] = {}

    def __init__(self, _stage) -> None:
        self.states = {name: State((((0, index),),), ()) for index, name in enumerate(self.nodes)}
        self.names = {state: name for name, state in self.states.items()}

    def start(self):
        return self.states["S"]

    def is_goal(self, state) -> bool:
        return self.names[state] == "G"

    def successors(self, state):
        return [(self.states[name], (0, "R")) for name in self.edges.get(self.names[state], ())]

    def step_cost(self, state, action, child) -> float:
        return 1.0


class DiveBoard(_GraphBoard):
    """Two routes to the goal: S -> A -> G (two moves) and S -> X1..X4 -> G (five).

    S offers the short route first, so a LIFO frontier dives into the long one while a
    FIFO frontier returns the two-move answer.
    """

    nodes = ("S", "A", "G", "X1", "X2", "X3", "X4")
    edges = {
        "S": ("A", "X1"),
        "A": ("G",),
        "X1": ("X2",),
        "X2": ("X3",),
        "X3": ("X4",),
        "X4": ("G",),
    }


class LoopBoard(_GraphBoard):
    """A cycle with no goal: without the seen set this search never returns."""

    nodes = ("S", "A", "B")
    edges = {"S": ("A",), "A": ("B",), "B": ("A",)}


@pytest.mark.parametrize("name", FIXTURE_IDS)
def test_hand_solved_fixtures_are_reached_and_replayed(name) -> None:
    stage = load_stage(next(FIXTURES.glob(f"{name}_*.json")))
    board = Board(stage)
    result = dfs.solve(stage)
    end, cost = replay(board, result.path)
    assert result.status == "solved" and board.is_goal(end)
    assert result.cost == cost
    # DFS makes no optimality promise, but it can never beat the optimum either.
    assert stage.expected is not None
    assert len(result.path) >= stage.expected.optimal_cost


@pytest.mark.parametrize("path", sorted(STAGES.glob("*.json")), ids=lambda path: path.stem)
def test_every_official_stage_terminates_with_a_replayable_path(path) -> None:
    stage = load_stage(path)
    board = Board(stage)
    result = dfs.solve(stage)
    end, cost = replay(board, result.path)
    assert result.status == "solved" and board.is_goal(end)
    assert result.cost == cost


def test_a_cycle_without_a_goal_ends_unsolvable(monkeypatch) -> None:
    monkeypatch.setattr(base, "Board", LoopBoard)
    result = dfs.solve(object())
    assert result.status == "unsolvable"
    # S, A and B are expanded once each; B offers A again and the seen set refuses it.
    assert result.counts.expanded == 3
    assert result.counts.generated == 4


def test_lifo_dives_into_the_long_route(monkeypatch) -> None:
    monkeypatch.setattr(base, "Board", DiveBoard)
    depth_first = dfs.solve(object())
    breadth_first = base.search(object(), frontier=Frontier())
    assert (len(depth_first.path), depth_first.counts.expanded) == (5, 5)
    assert len(breadth_first.path) == 2


def test_dfs_is_not_shortest_path_optimal() -> None:
    stage = load_stage(next(STAGES.glob("L1-02_*.json")))
    depth_first, uniform_cost = dfs.solve(stage), ucs.solve(stage)
    assert (len(depth_first.path), depth_first.cost) == (50, 50.0)
    assert (len(uniform_cost.path), uniform_cost.cost) == (22, 22.0)


@pytest.mark.parametrize("caps", [Caps(node_cap=0), Caps(time_s=0)])
def test_dfs_passes_limits_to_the_shared_loop(caps) -> None:
    result = dfs.solve(load_stage(next(FIXTURES.glob("FIX-01_*.json"))), caps)
    assert result.status == "cap" and result.path == () and result.cost == 0
    assert result.counts.expanded == 0
    assert result.counts.generated == result.counts.frontier_peak == 1
