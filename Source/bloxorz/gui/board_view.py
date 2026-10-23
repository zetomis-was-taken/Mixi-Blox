"""Board view: one flat tile per walkable cell, plus the detail piece each special kind carries.

The goal is deliberately not drawn: its cell stays empty and the cream background shows through,
the way the original game's hole does. The start is an ordinary tile with no mark. Fragile cells
and switches get a raised detail piece so they read differently from plain floor at a glance.
Colours come from ``theme.py``; the mapping is documented in ``docs/gui/theme.md``.

Tiles butt against each other with no gap. Each one is a thin coloured cap over a deeper base in
the same dark tile colour, so the platform shows a solid 0.30-unit edge. A faint translucent teal
line along every shared edge marks the grid; lines follow their tile's height, so they rise with
the load animation and sink with a closing bridge.

Tiles, lines and details are placed through :meth:`BoardView._place_tiles` and
:meth:`BoardView._place_details`, which stack the bridge height (static) and the load-animation
offset (dynamic) on top of each piece's resting height, so the two cannot overwrite each other.
"""

from __future__ import annotations

from typing import NamedTuple

from ursina import Entity

from bloxorz.core.contracts import Kind, Stage

from . import theme
from .intro import LoadIntro
from .layout import TILE_SIZE, cell_to_world

TILE_COLORS: dict[Kind, object] = {
    "floor": theme.TILE_FLOOR,
    "start": theme.TILE_FLOOR,
    "fragile": theme.TILE_FRAGILE,
    "bridge": theme.TILE_BRIDGE,
    "soft": theme.TILE_SOFT,
    "heavy": theme.TILE_HEAVY,
    "split": theme.TILE_SPLIT,
}

# The goal is a hole in the original game, so it gets no tile; the background shows through.
TILES_LEFT_OUT: frozenset[Kind] = frozenset({"void", "goal"})

# Resting heights. A tile is a thin coloured cap over a deeper side base; the extra thickness is
# what makes the platform read as a solid block rather than a flat plane.
TILE_SURFACE_Y = 0.0
TILE_CAP_Y = TILE_SURFACE_Y - theme.TILE_CAP_HEIGHT / 2.0
TILE_BASE_DROP = -theme.TILE_HEIGHT / 2.0
BRIDGE_CLOSED_Y = TILE_CAP_Y - theme.TILE_HEIGHT * 0.6

# Detail geometry is stated as fractions of the visible tile surface. Tiles have no gap, so the
# surface is a full tile.
_SURFACE = TILE_SIZE


class _Detail(NamedTuple):
    """One raised piece: centre offset, footprint, tint — all in tile-surface fractions."""

    offset: tuple[float, float]
    size: tuple[float, float]
    color: object


# Plain floor and bridges carry no detail; their colour and height already say what they are.
DETAILS: dict[Kind, tuple[_Detail, ...]] = {
    "fragile": (_Detail((0.0, 0.0), (0.92, 0.12), theme.TILE_MARK_DARK),),
    # A soft switch is a small button, a heavy switch a wide plate, and a split switch two halves
    # with a visible seam between them.
    "soft": (_Detail((0.0, 0.0), (0.45, 0.45), theme.TILE_MARK),),
    "heavy": (_Detail((0.0, 0.0), (0.80, 0.80), theme.TILE_MARK),),
    "split": (
        _Detail((-0.22, 0.0), (0.32, 0.80), theme.TILE_MARK),
        _Detail((0.22, 0.0), (0.32, 0.80), theme.TILE_MARK),
    ),
}


class BoardView:
    """Builds the static board once; dynamic tiles (bridges) can be updated from a state."""

    def __init__(self, stage: Stage) -> None:
        self.stage = stage
        self.root = Entity(name="board")
        self.tiles: dict[tuple[int, int], Entity] = {}
        self.details: list[Entity] = []
        self.lines: list[Entity] = []
        self._tile_bases: dict[tuple[int, int], Entity] = {}
        self._rest_y: dict[tuple[int, int], float] = {}
        self._detail_rest_y: list[float] = []
        self._line_at: dict[tuple[int, int], list[Entity]] = {}
        self._intro_offsets: list[float] = []
        self._detail_intro_offsets: list[float] = []

        index = stage.index
        drawn = {
            (row, col)
            for row in range(index.rows)
            for col in range(index.cols)
            if index.kind[row * index.cols + col] not in TILES_LEFT_OUT
        }
        for row in range(index.rows):
            for col in range(index.cols):
                kind = index.kind[row * index.cols + col]
                if kind in TILES_LEFT_OUT:
                    continue
                cell = (row, col)
                x, z = cell_to_world(cell, index.rows, index.cols)
                tile = Entity(
                    parent=self.root,
                    name=f"tile-{row}-{col}",
                    model="cube",
                    color=TILE_COLORS[kind],
                    scale=(
                        _SURFACE,
                        theme.TILE_CAP_HEIGHT,
                        _SURFACE,
                    ),
                    position=(x, TILE_CAP_Y, z),
                )
                base = Entity(
                    parent=self.root,
                    name=f"tile-base-{row}-{col}",
                    model="cube",
                    color=theme.TILE_SIDE,
                    scale=(
                        _SURFACE,
                        theme.TILE_HEIGHT - theme.TILE_CAP_HEIGHT,
                        _SURFACE,
                    ),
                    position=(x, TILE_CAP_Y + TILE_BASE_DROP, z),
                )
                self.tiles[cell] = tile
                self._tile_bases[cell] = base
                self._rest_y[cell] = TILE_CAP_Y

                built = self._build_details(cell, kind, x, z)
                self.details.extend(built)
                self._detail_rest_y.extend(detail.y for detail in built)

                lines = self._build_lines(cell, drawn, x, z)
                if lines:
                    self.lines.extend(lines)
                    self._line_at[cell] = lines
        self._intro_offsets = [0.0] * len(self.tiles)
        self._detail_intro_offsets = [0.0] * len(self.details)

    def _build_details(self, cell: tuple[int, int], kind: Kind, x: float, z: float) -> list[Entity]:
        """The raised pieces for one cell, resting on its top face."""
        built = []
        for number, detail in enumerate(DETAILS.get(kind, ())):
            built.append(
                Entity(
                    parent=self.root,
                    name=f"detail-{cell[0]}-{cell[1]}-{number}",
                    model="cube",
                    color=detail.color,
                    scale=(
                        detail.size[0] * _SURFACE,
                        theme.TRIM_HEIGHT,
                        detail.size[1] * _SURFACE,
                    ),
                    position=(
                        x + detail.offset[0] * _SURFACE,
                        TILE_SURFACE_Y + theme.TRIM_LIFT + theme.TRIM_HEIGHT / 2.0,
                        z + detail.offset[1] * _SURFACE,
                    ),
                )
            )
        return built

    def _build_lines(
        self,
        cell: tuple[int, int],
        drawn: set[tuple[int, int]],
        x: float,
        z: float,
    ) -> list[Entity]:
        """Separator lines for the north and west edges shared with another drawn tile.

        Drawing only those two edges gives every interior boundary exactly one line instead of
        doubling it from both neighbours, and leaves the outer silhouette unlined.
        """
        row, col = cell
        half = TILE_SIZE / 2.0
        edges = []
        if (row - 1, col) in drawn:
            edges.append((x, z + half, TILE_SIZE, theme.GRID_LINE_WIDTH, "n"))
        if (row, col - 1) in drawn:
            edges.append((x - half, z, theme.GRID_LINE_WIDTH, TILE_SIZE, "w"))
        return [
            Entity(
                parent=self.root,
                name=f"grid-{row}-{col}-{side}",
                model="cube",
                color=theme.GRID_LINE,
                scale=(size_x, theme.GRID_LINE_HEIGHT, size_z),
                position=(line_x, self._line_y(TILE_CAP_Y), line_z),
            )
            for line_x, line_z, size_x, size_z, side in edges
        ]

    @staticmethod
    def _line_y(tile_y: float) -> float:
        """Height of a separator resting on a cap whose centre is at ``tile_y``."""
        return (
            tile_y
            + theme.TILE_CAP_HEIGHT / 2.0
            + theme.GRID_LINE_LIFT
            + theme.GRID_LINE_HEIGHT / 2.0
        )

    def update_intro(self, intro: LoadIntro) -> None:
        """Float the tiles up into place, then the details that sit on them."""
        self._intro_offsets = [
            -(1.0 - intro.tile_progress(index)) * intro.timing.tile_rise
            for index in range(len(self.tiles))
        ]
        self._detail_intro_offsets = [
            -(1.0 - intro.obstacle_progress(index)) * intro.timing.obstacle_rise
            for index in range(len(self.details))
        ]
        self._place_tiles()
        self._place_details()

    def refresh(self, bridges: tuple[bool, ...]) -> None:
        """Tint bridge tiles from a state. A closed bridge is darker and visibly sunk."""
        for position, bridge in enumerate(self.stage.bridges):
            tile = self.tiles.get(bridge.pos)
            if tile is None:
                continue
            is_open = bridges[position]
            tile.color = theme.TILE_BRIDGE if is_open else theme.TILE_FLOOR
            self._rest_y[bridge.pos] = TILE_CAP_Y if is_open else BRIDGE_CLOSED_Y
        self._place_tiles()

    def _place_tiles(self) -> None:
        for index, (cell, tile) in enumerate(self.tiles.items()):
            tile.y = self._rest_y[cell] + self._intro_offsets[index]
            self._tile_bases[cell].y = tile.y + TILE_BASE_DROP
            for line in self._line_at.get(cell, ()):
                line.y = self._line_y(tile.y)

    def _place_details(self) -> None:
        for detail, rest_y, offset in zip(
            self.details, self._detail_rest_y, self._detail_intro_offsets
        ):
            detail.y = rest_y + offset
