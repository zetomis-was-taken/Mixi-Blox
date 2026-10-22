"""Headless checks for the GUI's pure geometry.

Ursina is never imported here: these tests must run in CI, which installs pytest but not Ursina.
"""

from __future__ import annotations

from pathlib import Path

from bloxorz.core.engine import Board
from bloxorz.core.stage import load_stage
from bloxorz.gui.layout import DIRECTION_VECTORS, cell_to_world, poses_for_state

ROOT = Path(__file__).resolve().parents[1]
STAGES = ROOT / "Source" / "bloxorz" / "core" / "stages"


def _stage(stem: str):
    return load_stage(STAGES / f"{stem}.json")


def test_cell_to_world_is_centred_and_flips_rows() -> None:
    rows, cols = 4, 5
    assert cell_to_world((0, 0), rows, cols) == (-2.0, 1.5)
    assert cell_to_world((3, 4), rows, cols) == (2.0, -1.5)


def test_direction_vectors_match_grid_movement() -> None:
    assert DIRECTION_VECTORS["U"] == (0.0, 1.0)  # row - 1
    assert DIRECTION_VECTORS["D"] == (0.0, -1.0)
    assert DIRECTION_VECTORS["L"] == (-1.0, 0.0)
    assert DIRECTION_VECTORS["R"] == (1.0, 0.0)


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
