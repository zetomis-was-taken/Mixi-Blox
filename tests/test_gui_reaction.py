"""Headless checks for the mechanism reactions.

Ursina is never imported here: ``reaction.py`` decides which cells carry load and how a value
eases toward its target, so the weight rule and the easing are covered by CI instead of by
watching the window.
"""

from __future__ import annotations

from pathlib import Path

from bloxorz.core.contracts import Cell, Cube, Stage, State
from bloxorz.core.stage import load_stage
from bloxorz.gui.reaction import approach, load_per_cell, reactive_cells

ROOT = Path(__file__).resolve().parents[1]
STAGES = ROOT / "Source" / "bloxorz" / "core" / "stages"

HEAVY = "L3-01_bridge_under_a_heavy_switch.json"
SOFT = "L3-02_a_one-way_bridge.json"
FRAGILE = "L2-01_fragile_shelves.json"
PLAIN = "L1-01_long_corridor.json"


def stage_for(name: str) -> Stage:
    return load_stage(STAGES / name)


def state_with(stage: Stage, *cubes: Cube) -> State:
    """A state with ``cubes`` on ``stage``, every bridge as the file declares it."""
    return State(
        cubes=cubes,
        bridges=tuple(bridge.initially_open for bridge in stage.bridges),
    )


def switch_cell(stage: Stage, kind: str) -> Cell:
    return next(cell for cell, switch in stage.index.switch_at.items() if switch.type == kind)


def fragile_cell(stage: Stage) -> Cell:
    index = stage.index
    return next(
        (row, col)
        for row in range(index.rows)
        for col in range(index.cols)
        if index.kind[row * index.cols + col] == "fragile"
    )


def test_a_plain_stage_has_nothing_to_load() -> None:
    stage = stage_for(PLAIN)
    assert reactive_cells(stage) == set()
    assert load_per_cell(stage, stage_start(stage)) == {}


def stage_start(stage: Stage) -> State:
    return state_with(stage, (stage.index.start,))


def test_every_reactive_cell_is_a_key_so_a_released_plate_is_told_to_rise() -> None:
    stage = stage_for(HEAVY)
    loads = load_per_cell(stage, stage_start(stage))

    assert set(loads) == reactive_cells(stage)
    assert set(loads) == {switch_cell(stage, "heavy")}
    assert not any(loads.values())


def test_a_heavy_plate_only_answers_to_the_full_block() -> None:
    stage = stage_for(HEAVY)
    cell = switch_cell(stage, "heavy")
    beside = (cell[0], cell[1] - 1)

    standing = load_per_cell(stage, state_with(stage, (cell,)))
    lying = load_per_cell(stage, state_with(stage, (beside, cell)))

    assert standing[cell] == 1.0
    # The engine fires a heavy switch only for the standing block; the plate keeps its height
    # for the same reason, so the picture never claims a switch has fired when it has not.
    assert lying[cell] == 0.0


def test_a_soft_plate_answers_to_any_piece() -> None:
    stage = stage_for(SOFT)
    cell = switch_cell(stage, "soft")
    beside = (cell[0], cell[1] + 1)

    assert load_per_cell(stage, state_with(stage, (cell,)))[cell] == 1.0
    assert load_per_cell(stage, state_with(stage, (cell, beside)))[cell] == 1.0


def test_a_fragile_panel_takes_weight() -> None:
    stage = stage_for(FRAGILE)
    cell = fragile_cell(stage)
    beside = (cell[0], cell[1] + 1)

    assert load_per_cell(stage, state_with(stage, (cell, beside)))[cell] == 1.0


def test_a_split_cube_loads_the_cells_it_covers() -> None:
    stage = stage_for(FRAGILE)
    cell = fragile_cell(stage)
    beside = (cell[0], cell[1] + 1)

    loads = load_per_cell(stage, state_with(stage, (cell,), (beside,)))

    assert loads[cell] == 1.0


def test_approach_moves_by_one_step() -> None:
    assert approach(0.0, 1.0, 0.25) == 0.25
    assert approach(1.0, 0.0, 0.25) == 0.75


def test_approach_never_passes_its_target() -> None:
    assert approach(0.9, 1.0, 0.5) == 1.0
    assert approach(0.1, 0.0, 0.5) == 0.0


def test_approach_lands_a_stranded_value() -> None:
    # A frame longer than the travel, or a zero duration, must not leave a plate mid-press.
    assert approach(0.3, 1.0, 0.0) == 1.0
    assert approach(0.0, 1.0, 4.0) == 1.0
