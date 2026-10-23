"""Weighted UCS, independent exact costs and shared-loop integration (#22)."""

from __future__ import annotations

import json

import pytest
from search_helpers import FIXTURES, STAGES, GraphBoard, remaining_costs, replay

from bloxorz.core.contracts import Caps
from bloxorz.core.engine import Board
from bloxorz.core.stage import load_stage
from bloxorz.solvers import base, ucs


@pytest.mark.parametrize("name", ["FIX-01", "FIX-02", "FIX-03"])
def test_hand_computed_fixture_cost_and_replayed_path(name) -> None:
    stage = load_stage(next(FIXTURES.glob(f"{name}_*.json")))
    result = ucs.solve(stage)
    end, cost = replay(Board(stage), result.path)
    assert result.status == "solved" and Board(stage).is_goal(end)
    assert stage.expected is not None
    assert cost == result.cost == stage.expected.optimal_cost


@pytest.mark.parametrize("path", sorted(STAGES.glob("*.json")), ids=lambda path: path.stem)
def test_ucs_matches_independent_exact_weighted_costs(path) -> None:
    stage = load_stage(path)
    board = Board(stage)
    _, exact = remaining_costs(board)
    result = ucs.solve(stage)
    end, cost = replay(board, result.path)
    assert result.status == "solved" and board.is_goal(end)
    assert result.cost == cost == exact[board.start()]


def test_a_longer_path_can_cost_less_than_the_fifo_solution() -> None:
    stage = load_stage(next(STAGES.glob("L2-02_*.json")))
    shortest = base.search(stage)
    cheapest = ucs.solve(stage)
    assert len(shortest.path) == 46 and shortest.cost == 64
    assert len(cheapest.path) == 49 and cheapest.cost == 58


def test_cheaper_path_replaces_first_discovery(monkeypatch) -> None:
    monkeypatch.setattr(base, "Board", GraphBoard)
    result = ucs.solve(object())
    assert result.status == "solved" and result.cost == 3
    assert result.path == ((0, "D"), (0, "L"), (0, "R"))
    assert result.counts.expanded == 3 and result.counts.generated == 6
    assert result.counts.frontier_peak == 2


def test_stale_entries_do_not_expand_or_cause_a_phantom_cap(monkeypatch) -> None:
    class NoGoal(GraphBoard):
        def is_goal(self, state):
            return False

    monkeypatch.setattr(base, "Board", NoGoal)
    result = ucs.solve(object(), Caps(node_cap=4))
    assert result.status == "unsolvable"
    assert result.counts.expanded == 4 and result.counts.generated == 6
    assert result.counts.frontier_peak == 2


def test_caps_keep_the_shared_order_and_counts(monkeypatch) -> None:
    stage = load_stage(next(FIXTURES.glob("FIX-01_*.json")))
    assert ucs.solve(stage, Caps(node_cap=6)).status == "solved"
    capped = ucs.solve(stage, Caps(node_cap=5))
    assert capped.status == "cap" and capped.counts.expanded == 5
    assert capped.path == () and capped.cost == 0
    assert ucs.solve(stage, Caps(time_s=0)).counts.expanded == 0
    clock = iter([0] + [0] * 6 + [1])
    monkeypatch.setattr(base, "perf_counter", lambda: next(clock))
    assert ucs.solve(stage, Caps(time_s=1)).status == "cap"


def test_initial_goal_is_solved_with_zero_node_cap(monkeypatch) -> None:
    monkeypatch.setattr(Board, "is_goal", lambda self, state: True)
    result = ucs.solve(load_stage(next(FIXTURES.glob("FIX-01_*.json"))), Caps(node_cap=0))
    assert result.status == "solved" and result.path == () and result.cost == 0
    assert result.counts.expanded == 0
    assert result.counts.generated == result.counts.frontier_peak == 1


def test_unreachable_goal_returns_the_frozen_unsolved_result(tmp_path) -> None:
    path = tmp_path / "unsolvable.json"
    path.write_text(
        json.dumps(
            {
                "id": "NONE",
                "name": "isolated",
                "group": "L1",
                "source": "original",
                "grid": ["SGo"],
                "switches": [],
                "bridges": [],
            }
        ),
        encoding="utf-8",
    )
    result = ucs.solve(load_stage(path))
    assert result.status == "unsolvable" and result.path == () and result.cost == 0
    assert result.counts.expanded == 2 and result.counts.generated == 3
