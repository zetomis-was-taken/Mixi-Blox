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


def test_at_least_one_fixture_has_a_cyclic_state_graph() -> None:
    """Otherwise `optimal_cost` is unfalsifiable.

    On a tree every state has one simple route to the goal, so any solver that reaches it
    returns the optimum whatever it does. A cycle is what lets two valid routes differ in
    length, and FIX-05 is the fixture that keeps one alive.
    """
    cyclic = []
    for name in FIXTURE_IDS:
        stage = load_stage(next(FIXTURES.glob(f"{name}_*.json")))
        board = Board(stage)
        seen, _ = remaining_costs(board)
        edges = {frozenset((state, nxt)) for state in seen for nxt, _ in board.successors(state)}
        if len(edges) >= len(seen):
            cyclic.append(name)
    assert cyclic, "every fixture is a tree, so optimal_cost cannot be wrong"
