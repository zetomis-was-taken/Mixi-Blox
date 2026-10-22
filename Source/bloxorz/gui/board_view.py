"""Board view: one flat, neutral tile per non-void cell.

No lighting, shadows or texture work: the prototype only needs readable silhouettes. Tile colours
come from ``theme.py``, the placeholder palette the future ``theme.md`` will replace.
"""

from __future__ import annotations

from ursina import Entity

from bloxorz.core.contracts import Kind, Stage

from . import theme
from .layout import TILE_SIZE, cell_to_world

TILE_COLORS: dict[Kind, object] = {
    "floor": theme.TILE_FLOOR,
    "start": theme.TILE_START,
    "goal": theme.TILE_GOAL,
    "fragile": theme.TILE_FRAGILE,
    "bridge": theme.TILE_BRIDGE,
    "soft": theme.TILE_SWITCH,
    "heavy": theme.TILE_SWITCH,
    "split": theme.TILE_SWITCH,
}


class BoardView:
    """Builds the static board once; dynamic tiles (bridges) can be updated from a state."""

    def __init__(self, stage: Stage) -> None:
        self.stage = stage
        self.root = Entity(name="board")
        self.tiles: dict[tuple[int, int], Entity] = {}

        index = stage.index
        for row in range(index.rows):
            for col in range(index.cols):
                kind = index.kind[row * index.cols + col]
                if kind == "void":
                    continue
                cell = (row, col)
                x, z = cell_to_world(cell, index.rows, index.cols)
                tile = Entity(
                    parent=self.root,
                    name=f"tile-{row}-{col}",
                    model="cube",
                    color=TILE_COLORS[kind],
                    scale=(
                        TILE_SIZE - theme.TILE_GAP,
                        theme.TILE_HEIGHT,
                        TILE_SIZE - theme.TILE_GAP,
                    ),
                    position=(x, -theme.TILE_HEIGHT / 2.0, z),
                )
                self.tiles[cell] = tile

    def refresh(self, bridges: tuple[bool, ...]) -> None:
        """Tint bridge tiles from a state. A closed bridge is darker and visibly sunk."""
        for position, bridge in enumerate(self.stage.bridges):
            tile = self.tiles.get(bridge.pos)
            if tile is None:
                continue
            is_open = bridges[position]
            tile.color = theme.TILE_BRIDGE if is_open else theme.TILE_FLOOR
            tile.y = (-theme.TILE_HEIGHT / 2.0) if is_open else (-theme.TILE_HEIGHT * 1.1)
