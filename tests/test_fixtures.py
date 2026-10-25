"""The #21 contract: the fixture set is fixed, and each recorded cost is the exact minimum."""

from __future__ import annotations

import pytest
from search_helpers import FIXTURE_IDS, FIXTURES, remaining_costs

from bloxorz.core.engine import Board
from bloxorz.core.stage import load_stage


def test_the_fixture_set_stays_within_the_recorded_range() -> None:
    """#21 asks for three to five; the solver tests parametrize over this tuple."""
    assert 3 <= len(FIXTURE_IDS) <= 5


@pytest.mark.parametrize("name", FIXTURE_IDS)
def test_the_recorded_cost_is_the_exact_minimum(name) -> None:
    stage = load_stage(next(FIXTURES.glob(f"{name}_*.json")))
    board = Board(stage)
    _, exact = remaining_costs(board)
    assert stage.expected is not None
    # The solver tests show the cost is reachable; this pins the number itself. A typo in
    # `expected` would otherwise pass a solver that is consistently wrong with it.
    assert exact[board.start()] == stage.expected.optimal_cost
