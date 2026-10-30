"""Headless checks for the GUI's pure geometry.

Ursina is never imported here: these tests must run in CI, which installs pytest but not Ursina.
"""

from __future__ import annotations

from pathlib import Path

from bloxorz.core.contracts import State
from bloxorz.core.engine import Board
from bloxorz.core.stage import load_stage
from bloxorz.gui.layout import (
    DIRECTION_VECTORS,
    board_center,
    cell_to_world,
    goal_rim_pieces,
    landed_cube_index,
    poses_for_state,
)

ROOT = Path(__file__).resolve().parents[1]
STAGES = ROOT / "Source" / "bloxorz" / "core" / "stages"


def _stage(stem: str):
    return load_stage(STAGES / f"{stem}.json")


def test_cell_to_world_is_centred_and_flips_rows() -> None:
    rows, cols = 4, 5
    assert cell_to_world((0, 0), rows, cols) == (-2.0, 1.5)
    assert cell_to_world((3, 4), rows, cols) == (2.0, -1.5)


def test_board_center_follows_the_walkable_footprint() -> None:
    # L1-01 leaves two empty columns on the left of its 15-wide grid, so the tiles sit half a
    # tile left of the grid centre. L1-02 is offset in depth instead.
    assert board_center(_stage("L1-01_long_corridor")) == (-0.5, 0.0)
    assert board_center(_stage("L1-02_two_flights")) == (0.0, 0.5)


def test_direction_vectors_match_grid_movement() -> None:
    assert DIRECTION_VECTORS["U"] == (0.0, 1.0)  # row - 1
    assert DIRECTION_VECTORS["D"] == (0.0, -1.0)
    assert DIRECTION_VECTORS["L"] == (-1.0, 0.0)
    assert DIRECTION_VECTORS["R"] == (1.0, 0.0)


def test_the_goal_rim_frames_the_cell_without_filling_it() -> None:
    """The hole must stay a hole: four bars inside the cell, none over its middle."""
    pieces = goal_rim_pieces()

    assert len(pieces) == 4
    for (offset_x, offset_z), (size_x, size_z) in pieces:
        assert abs(offset_x) + size_x / 2.0 <= 0.5 + 1e-9, "a bar overhangs the cell"
        assert abs(offset_z) + size_z / 2.0 <= 0.5 + 1e-9, "a bar overhangs the cell"
    assert all(
        abs(offset_x) >= size_x / 2.0 or abs(offset_z) >= size_z / 2.0
        for (offset_x, offset_z), (size_x, size_z) in pieces
    ), "a bar covers the middle of the hole"

    # A frame, not an L: the offsets cancel on both axes.
    assert abs(sum(offset_x for (offset_x, _), _ in pieces)) < 1e-9
    assert abs(sum(offset_z for (_, offset_z), _ in pieces)) < 1e-9


def test_standing_and_lying_poses_have_the_block_extents() -> None:
    stage = _stage("L1-01_long_corridor")
    board = Board(stage)
    rows, cols = stage.index.rows, stage.index.cols

    standing = poses_for_state(board.start(), rows, cols)
    assert len(standing) == 1
    assert standing[0].scale == (1.0, 2.0, 1.0)

    right = next(
        next_state
        for next_state, action in board.successors(board.start())
        if action == (0, "R")
    )
    lying = poses_for_state(right, rows, cols)
    assert len(lying) == 1
    assert lying[0].scale == (2.0, 1.0, 1.0)
    assert lying[0].center[1] == 0.5


def test_split_state_renders_two_unit_cubes() -> None:
    stage = _stage("L4-01_split_into_the_far_room")
    board = Board(stage)
    state = board.start()
    for _ in range(2):  # the split switch is two rolls to the right of the start
        state = next(
            next_state
            for next_state, action in board.successors(state)
            if action == (0, "R")
        )
    assert len(state.cubes) == 2

    poses = poses_for_state(state, stage.index.rows, stage.index.cols)
    assert len(poses) == 2
    assert all(pose.scale == (1.0, 1.0, 1.0) for pose in poses)


def _split_state(*cells: tuple[int, int]) -> State:
    """A state holding one lone cube per cell; ``State`` sorts them by cell itself."""
    return State(cubes=tuple((cell,) for cell in cells), bridges=())


def test_a_split_roll_is_found_by_the_cells_it_lands_on() -> None:
    """One action can swap the cubes' indices, because the state orders them by cell."""
    start = _split_state((0, 0), (0, 3))
    down = _split_state((0, 3), (1, 0))

    assert landed_cube_index(start, down, (0, "D")) == 1


def test_a_split_roll_that_keeps_the_order_keeps_its_index() -> None:
    start = _split_state((0, 0), (0, 3))
    right = _split_state((0, 1), (0, 3))

    assert landed_cube_index(start, right, (0, "R")) == 0


def test_a_transition_no_roll_can_predict_has_no_landing() -> None:
    """A teleport or a merge is not a roll, so the view is told to snap instead."""
    start = _split_state((0, 0), (0, 3))
    merged = State(cubes=(((0, 0), (0, 1)),), bridges=())

    assert landed_cube_index(start, _split_state((0, 3), (2, 2)), (0, "R")) is None
    assert landed_cube_index(start, merged, (0, "R")) is None


def test_every_split_roll_on_a_split_stage_finds_its_landing() -> None:
    """The invariant the view relies on, over every position ``L4-01`` can reach."""
    board = Board(_stage("L4-01_split_into_the_far_room"))
    seen = {board.start().key()}
    queue = [board.start()]
    checked = swapped = 0

    while queue:
        state = queue.pop()
        for next_state, action in board.successors(state):
            if len(state.cubes) == 2 and len(next_state.cubes) == 2:
                landing = landed_cube_index(state, next_state, action)
                assert landing is not None, action
                checked += 1
                swapped += landing != action[0]
            if next_state.key() not in seen:
                seen.add(next_state.key())
                queue.append(next_state)

    assert checked > 0, "L4-01 must have split positions to roll from"
    assert swapped > 0, "and some of them must swap indices, or this proves nothing"
