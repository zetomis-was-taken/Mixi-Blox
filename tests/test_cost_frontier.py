"""Live-node semantics, cheaper paths and deterministic heap ties (#22)."""

from __future__ import annotations

import pytest

from bloxorz.core.contracts import State
from bloxorz.solvers.base import Node
from bloxorz.solvers.cost_frontier import CostFrontier


def node(position: int, cost: float) -> Node:
    return Node(State((((0, position),),), ()), cost)


def test_replacement_counts_one_live_node_and_skips_the_old_entry() -> None:
    frontier = CostFrontier()
    expensive, cheap, other = node(1, 5), node(1, 2), node(2, 9)
    for item in (expensive, cheap, node(1, 2), node(1, 6), other):
        frontier.push(item)
    assert len(frontier) == 2
    assert frontier.pop() is cheap
    assert len(frontier) == 1
    assert frontier.pop() is other
    assert not frontier and len(frontier) == 0


def test_only_stale_entries_left_is_an_empty_frontier() -> None:
    frontier = CostFrontier()
    frontier.push(node(1, 5))
    cheap = node(1, 2)
    frontier.push(cheap)
    assert frontier.pop() is cheap
    assert not frontier and len(frontier) == 0
    with pytest.raises(IndexError):
        frontier.pop()


def test_popped_state_can_reopen_only_for_a_strictly_cheaper_path() -> None:
    frontier = CostFrontier()
    frontier.push(node(1, 5))
    frontier.pop()
    frontier.push(node(1, 5))
    assert not frontier
    cheap = node(1, 3)
    frontier.push(cheap)
    assert len(frontier) == 1 and frontier.pop() is cheap


def test_equal_priorities_preserve_insertion_order_without_comparing_states() -> None:
    frontier = CostFrontier()
    first, second = node(2, 1), node(1, 1)
    frontier.push(first)
    frontier.push(second)
    assert frontier.pop() is first
    assert frontier.pop() is second


@pytest.mark.parametrize("price", [0.0, -1.0, 0.5, float("nan"), float("inf")])
def test_invalid_edge_prices_fail_instead_of_producing_a_result(price) -> None:
    frontier = CostFrontier()
    parent = node(0, 0)
    with pytest.raises(ValueError):
        frontier.push(parent.child(node(1, 0).state, (0, "R"), price))
