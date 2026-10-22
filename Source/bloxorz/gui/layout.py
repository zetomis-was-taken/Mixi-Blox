"""Pure grid-to-world geometry, kept free of Ursina so it stays testable headless.

World axes: +X is east (column), +Z is north (row 0), +Y is up. The camera sits on the -Z side, so
the grid reads with row 0 at the top of the screen.
"""

from __future__ import annotations

from dataclasses import dataclass

from bloxorz.core.contracts import State
from bloxorz.core.engine import orientation

TILE_SIZE = 1.0

# One tile of movement in world space, as (dx, dz).
DIRECTION_VECTORS: dict[str, tuple[float, float]] = {
    "U": (0.0, 1.0),
    "D": (0.0, -1.0),
    "L": (-1.0, 0.0),
    "R": (1.0, 0.0),
}


@dataclass(frozen=True)
class Pose:
    """A piece's axis-aligned box: centre and full size, in world units."""

    center: tuple[float, float, float]
    scale: tuple[float, float, float]


def cell_to_world(cell: tuple[int, int], rows: int, cols: int) -> tuple[float, float]:
    """Map a grid cell to the (x, z) centre of its tile, with the board centred on the origin."""
    row, col = cell
    x = (col - (cols - 1) / 2.0) * TILE_SIZE
    z = ((rows - 1 - row) - (rows - 1) / 2.0) * TILE_SIZE
    return x, z


def poses_for_state(state: State, rows: int, cols: int) -> tuple[Pose, ...]:
    """The boxes to draw for ``state`` — one for an unsplit block, one per cube when split.

    Orientation is derived here exactly as the engine derives it; nothing is stored on the state.
    """
    split = len(state.cubes) == 2
    poses: list[Pose] = []
    for cube in state.cubes:
        piece = orientation(cube, split)
        if piece == "standing":
            x, z = cell_to_world(cube[0], rows, cols)
            poses.append(Pose((x, 1.0, z), (1.0, 2.0, 1.0)))
        elif piece == "lying_h":
            x0, z = cell_to_world(cube[0], rows, cols)
            x1, _ = cell_to_world(cube[1], rows, cols)
            poses.append(Pose(((x0 + x1) / 2.0, 0.5, z), (2.0, 1.0, 1.0)))
        elif piece == "lying_v":
            x, z0 = cell_to_world(cube[0], rows, cols)
            _, z1 = cell_to_world(cube[1], rows, cols)
            poses.append(Pose((x, 0.5, (z0 + z1) / 2.0), (1.0, 1.0, 2.0)))
        else:  # a lone unit cube after a split
            x, z = cell_to_world(cube[0], rows, cols)
            poses.append(Pose((x, 0.5, z), (1.0, 1.0, 1.0)))
    return tuple(poses)
