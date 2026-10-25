"""BFS move optimality, FIFO order, cycle handling and the shared-loop contract (#19)."""

from __future__ import annotations

from collections import deque

import pytest
from search_helpers import FIXTURE_IDS, FIXTURES, STAGES, replay

from bloxorz.core.contracts import Caps, State
from bloxorz.core.engine import Board
from bloxorz.core.stage import load_stage
from bloxorz.solvers import base, bfs, ucs


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
    

class StackTrapBoard(_GraphBoard):
    """
    S offers the goal first and a five-move detour second. A FIFO frontier pops the
    goal immediately; a LIFO frontier would follow the detour and return six moves.
    """
    nodes = ("S", "G", "X1", "X2", "X3", "X4")
    edges = {"S": ("G", "X1"), "X1": ("X2",), "X2": ("X3",), "X3": ("X4",), "X4": ("G",)}


class CycleBoard(_GraphBoard):
    nodes = ("S", "A", "B", "G")
    edges = {"S": ("A",), "A": ("B",), "B": ("A", "G")}


def _shortest_moves(board: Board) -> int:
    """Shortest move count to any goal, computed without the shared loop."""
    distance = {board.start(): 0}
    pending = deque([board.start()])
    while pending:
        state = pending.popleft()
        for child, _ in board.successors(state):
            if child not in distance:
                distance[child] = distance[state] + 1
                pending.append(child)
    return min(depth for state, depth in distance.items() if board.is_goal(state))


@pytest.mark.parametrize("name", FIXTURE_IDS)
def test_hand_computed_fixture_move_count_and_replayed_path(name) -> None:
    stage = load_stage(next(FIXTURES.glob(f"{name}_*.json")))
    board = Board(stage)
    result = bfs.solve(stage)
    end, cost = replay(board, result.path)
    assert result.status == "solved" and board.is_goal(end)
    assert stage.expected is not None
    # These fixtures have no fragile tile, so move count and weighted cost coincide.
    assert len(result.path) == stage.expected.optimal_cost == result.cost == cost
    # generated counts every successor offered, refused or not: a plain
    # corridor offers exactly two per expansion and one is already seen.
    assert result.counts.generated == 2 * result.counts.expanded


@pytest.mark.parametrize("path", sorted(STAGES.glob("*.json")), ids=lambda path: path.stem)
def test_the_move_count_is_the_shortest_on_every_official_stage(path) -> None:
    stage = load_stage(path)
    board = Board(stage)
    result = bfs.solve(stage)
    end, cost = replay(board, result.path)
    assert result.status == "solved" and board.is_goal(end)
    assert len(result.path) == _shortest_moves(board)
    assert result.cost == cost


def test_fifo_takes_the_shallow_goal_a_depth_first_frontier_would_miss(monkeypatch) -> None:
    monkeypatch.setattr(base, "Board", StackTrapBoard)
    result = bfs.solve(object())
    assert result.status == "solved"
    assert len(result.path) == 1
    assert result.counts.expanded == 1


def test_a_cycle_terminates_and_each_state_is_expanded_once(monkeypatch) -> None:
    monkeypatch.setattr(base, "Board", CycleBoard)
    result = bfs.solve(object())
    assert result.status == "solved"
    assert len(result.path) == 3
    # Three states were expanded once each; A is offered again through B and refused
    assert result.counts.expanded == 3
    assert result.counts.generated == 5


def test_a_shorter_path_can_cost_more_than_the_ucs_path() -> None:
    stage = load_stage(next(STAGES.glob("L2-02_*.json")))
    fifo, optimal = bfs.solve(stage), ucs.solve(stage)
    assert (len(fifo.path), fifo.cost) == (46, 64)
    assert (len(optimal.path), optimal.cost) == (49, 58)
    assert fifo.cost > optimal.cost and len(fifo.path) < len(optimal.path)


@pytest.mark.parametrize("caps", [Caps(node_cap=0), Caps(time_s=0)])
def test_bfs_passes_limits_to_the_shared_loop(caps) -> None:
    result = bfs.solve(load_stage(next(FIXTURES.glob("FIX-01_*.json"))), caps)
    assert result.status == "cap" and result.path == () and result.cost == 0
    assert result.counts.expanded == 0
    assert result.counts.generated == result.counts.frontier_peak == 1
