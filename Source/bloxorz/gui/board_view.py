"""Board view: one flat, neutral tile per non-void cell.

No lighting, shadows or texture work: the prototype only needs readable silhouettes. Tile colours
come from ``theme.py``, the placeholder palette the future ``theme.md`` will replace.

Tiles are placed through :meth:`BoardView._place_tiles`, which stacks the bridge height (static)
and the load-animation offset (dynamic) on top of each tile's resting height, so the two cannot
overwrite each other.
"""

from __future__ import annotations

from ursina import Entity

from bloxorz.core.contracts import Kind, Stage

from . import theme
from .intro import LoadIntro
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

# Resting centre heights: an open bridge sits flush with the floor, a closed one sinks out of reach.
TILE_Y = -theme.TILE_HEIGHT / 2.0
BRIDGE_CLOSED_Y = -theme.TILE_HEIGHT * 1.1


class BoardView:
    """Builds the static board once; dynamic tiles (bridges) can be updated from a state."""

    def __init__(self, stage: Stage) -> None:
        self.stage = stage
        self.root = Entity(name="board")
        self.tiles: dict[tuple[int, int], Entity] = {}
        self._rest_y: dict[tuple[int, int], float] = {}
        self._intro_offsets: list[float] = []

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
                    position=(x, TILE_Y, z),
                )
                self.tiles[cell] = tile
                self._rest_y[cell] = TILE_Y
        self._intro_offsets = [0.0] * len(self.tiles)

    def update_intro(self, intro: LoadIntro) -> None:
        """Float each tile up into place; the tiles start below the board and rise one by one."""
        self._intro_offsets = [
            -(1.0 - intro.tile_progress(index)) * intro.timing.tile_rise
            for index in range(len(self.tiles))
        ]
        self._place_tiles()

    def refresh(self, bridges: tuple[bool, ...]) -> None:
        """Tint bridge tiles from a state. A closed bridge is darker and visibly sunk."""
        for position, bridge in enumerate(self.stage.bridges):
            tile = self.tiles.get(bridge.pos)
            if tile is None:
                continue
            is_open = bridges[position]
            tile.color = theme.TILE_BRIDGE if is_open else theme.TILE_FLOOR
            self._rest_y[bridge.pos] = TILE_Y if is_open else BRIDGE_CLOSED_Y
        self._place_tiles()

    def _place_tiles(self) -> None:
        for index, (cell, tile) in enumerate(self.tiles.items()):
            tile.y = self._rest_y[cell] + self._intro_offsets[index]
