"""The ``ALGORITHMS`` registry the GUI's Solve panel builds its cards from (#18)."""

from __future__ import annotations

from pathlib import Path

import pytest
from search_helpers import FIXTURES, replay

from bloxorz.core.contracts import Caps
from bloxorz.core.engine import Board
from bloxorz.core.stage import load_stage
from bloxorz.gui.replay import Replay
from bloxorz.solvers import ALGORITHMS

ROOT = Path(__file__).resolve().parents[1]
STAGES = ROOT / "Source/bloxorz/core/stages"
FIXTURE = FIXTURES / "FIX-01_straight_line.json"
# A plain board and the split board the movie driver has to keep in one piece.
SEAM_STAGES = ("L1-01_long_corridor.json", "L4-01_split_into_the_far_room.json")
PAUSE = 0.1


def test_registry_lists_the_four_algorithms_in_card_order() -> None:
    """The keys are the card labels and their order is the card order."""
    assert tuple(ALGORITHMS) == ("BFS", "DFS", "UCS", "A*")


@pytest.mark.parametrize("name", tuple(ALGORITHMS))
def test_each_registered_solver_returns_a_playable_path(name) -> None:
    stage = load_stage(FIXTURE)
    board = Board(stage)

    result = ALGORITHMS[name](stage, Caps())

    assert result.status == "solved"
    assert (len(result.path), result.cost) == (6, 6.0)
    end, cost = replay(board, result.path)
    assert board.is_goal(end) and cost == result.cost


@pytest.mark.parametrize("stage_file", SEAM_STAGES)
@pytest.mark.parametrize("name", tuple(ALGORITHMS))
def test_each_registered_solver_feeds_the_movie_driver(name, stage_file) -> None:
    """The registry hands the GUI a ``solve`` whose path ``Replay`` can plan and finish."""
    stage = load_stage(STAGES / stage_file)
    board = Board(stage)

    result = ALGORITHMS[name](stage, Caps())
    movie = Replay(board, result, PAUSE)

    assert movie.playable is True
    assert tuple(action for _, _, action in movie.steps) == result.path
    assert board.is_goal(movie.steps[-1][1])
