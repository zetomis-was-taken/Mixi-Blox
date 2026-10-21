"""Fragile contact prices on legal transitions, including stationary cubes."""

from __future__ import annotations

import json

from bloxorz.core.contracts import State
from bloxorz.core.engine import Board
from bloxorz.core.stage import load_stage


def test_only_new_fragile_contacts_are_charged(tmp_path) -> None:
    path = tmp_path / "cost.json"
    path.write_text(
        json.dumps(
            {
                "id": "COST",
                "name": "Cost probe",
                "group": "L2",
                "source": "original",
                "grid": ["Soooooo", "ooffooo", "oofooGo", "ooooooo"],
                "switches": [],
                "bridges": [],
            }
        ),
        encoding="utf-8",
    )
    board = Board(load_stage(path))
    lying = State((((1, 0), (1, 1)),), ())
    moves = {a: s for s, a in board.successors(lying)}
    # Rolling across the axis lands on two fragile cells; base 1 + two contacts.
    across = State((((0, 2), (0, 3)),), ())
    landed = {a: s for s, a in board.successors(across)}[(0, "D")]
    assert board.step_cost(across, (0, "D"), landed) == 3
    # Continued occupancy of a fragile tile is not an additional contact.
    moved = {a: s for s, a in board.successors(landed)}[(0, "D")]
    assert board.step_cost(landed, (0, "D"), moved) == 2
    assert board.step_cost(lying, (0, "U"), moves[(0, "U")]) == 1
    # Canonical ordering changes slots when needed; action names the source cube.
    split = State((((1, 2),), ((3, 4),)), ())
    ordinary = {a: s for s, a in board.successors(split)}[(1, "R")]
    assert board.step_cost(split, (1, "R"), ordinary) == 1
    entering = {a: s for s, a in board.successors(split)}[(0, "R")]
    assert board.step_cost(split, (0, "R"), entering) == 2


def test_teleport_destinations_count_as_fragile_contacts(tmp_path) -> None:
    path = tmp_path / "teleport.json"
    path.write_text(
        json.dumps(
            {
                "id": "COST-SPLIT",
                "name": "Teleport cost",
                "group": "L4",
                "source": "original",
                "grid": ["Soooooo", "ooofooo", "ooooofo", "YoooooG"],
                "switches": [
                    {
                        "type": "split",
                        "pos": [3, 0],
                        "action": None,
                        "bridges": None,
                        "teleport_cubes": [[1, 3], [2, 5]],
                    }
                ],
                "bridges": [],
            }
        ),
        encoding="utf-8",
    )
    board = Board(load_stage(path))
    lying = State((((1, 0), (2, 0)),), ())
    landing = {a: s for s, a in board.successors(lying)}[(0, "D")]
    assert len(landing.cubes) == 2
    assert board.step_cost(lying, (0, "D"), landing) == 3
