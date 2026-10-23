"""Board view: one flat tile per walkable cell, plus the detail piece each special kind carries.

The goal is deliberately not drawn: its cell stays empty and the cream background shows through,
the way the original game's hole does. The start is an ordinary tile with no mark. Fragile cells
and switches get a raised detail piece so they read differently from plain floor at a glance.
Colours come from ``theme.py``; the mapping is documented in ``docs/gui/theme.md``.

Tiles butt against each other with no gap. Each one is a thin coloured cap over a deeper base in
the same dark tile colour, so the platform shows a solid 0.30-unit edge. A faint translucent teal
line along every shared edge marks the grid; lines follow their tile's height, so they rise with
the load animation and sink with a closing bridge.

Mechanisms react to the block: a switch plate sinks while the block bears on it, a fragile crack
opens under the weight, and a bridge eases between its two heights with its tint following the
height. Which cells carry load is decided in ``reaction.py``; this module only draws the answer.

Tiles, lines and details are placed through :meth:`BoardView._place_tiles` and
:meth:`BoardView._place_details`, which stack the bridge height (eased) and the load-animation
offset (dynamic) on top of each piece's resting height, so the two cannot overwrite each other.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import NamedTuple

from ursina import Color, Entity, color

from bloxorz.core.contracts import Cell, Kind, Stage, State

from . import reaction, theme
from .intro import LoadIntro
from .layout import TILE_SIZE, cell_to_world
from .reaction import approach

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

# Full travel of a bridge between its two heights; the eased step per frame is sized from it.
BRIDGE_TRAVEL = TILE_CAP_Y - BRIDGE_CLOSED_Y

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


@dataclass(frozen=True)
class _DetailView:
    """One built piece, with the cell it sits on and its unladen footprint."""

    entity: Entity
    cell: Cell
    kind: Kind
    rest_y: float
    size: tuple[float, float]


def _bridge_height(is_open: bool) -> float:
    """Resting height of a bridge: level with the floor when open, sunk when closed."""
    return TILE_CAP_Y if is_open else BRIDGE_CLOSED_Y


def _blend(low: Color, high: Color, t: float) -> Color:
    """A colour ``t`` of the way from ``low`` to ``high``; both are ``color.rgb32`` values."""
    return color.rgba(
        low[0] + (high[0] - low[0]) * t,
        low[1] + (high[1] - low[1]) * t,
        low[2] + (high[2] - low[2]) * t,
        low[3] + (high[3] - low[3]) * t,
    )


def _bridge_color(height: float) -> Color:
    """Tint a bridge by how far it has risen: closed is floor-dark, open the mechanism cyan."""
    travelled = (height - BRIDGE_CLOSED_Y) / BRIDGE_TRAVEL if BRIDGE_TRAVEL else 1.0
    return _blend(theme.TILE_FLOOR, theme.TILE_BRIDGE, min(max(travelled, 0.0), 1.0))


class BoardView:
    """Builds the static board once, then eases the mechanisms the controller drives."""

    def __init__(self, stage: Stage) -> None:
        self.stage = stage
        self.root = Entity(name="board")
        self.tiles: dict[Cell, Entity] = {}
        self.details: list[_DetailView] = []
        self.lines: list[Entity] = []
        self._tile_bases: dict[Cell, Entity] = {}
        self._rest_y: dict[Cell, float] = {}
        self._line_at: dict[Cell, list[Entity]] = {}
        self._intro_offsets: list[float] = []
        self._detail_intro_offsets: list[float] = []
        # Mechanism state: the load already shown, and where each mechanism is heading.
        self._state: State | None = None
        self._load: dict[Cell, float] = {}
        self._load_targets: dict[Cell, float] = {}
        self._bridge_targets: dict[Cell, float] = {}

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

                lines = self._build_lines(cell, drawn, x, z)
                if lines:
                    self.lines.extend(lines)
                    self._line_at[cell] = lines

        # Bridges start where the stage file says they are, so the first state retargets nothing.
        for bridge in stage.bridges:
            if bridge.pos in self.tiles:
                self._rest_y[bridge.pos] = _bridge_height(bridge.initially_open)

        self._intro_offsets = [0.0] * len(self.tiles)
        self._detail_intro_offsets = [0.0] * len(self.details)
        self._place_tiles()

    def _build_details(self, cell: Cell, kind: Kind, x: float, z: float) -> list[_DetailView]:
        """The raised pieces for one cell, resting on its top face."""
        rest_y = TILE_SURFACE_Y + theme.TRIM_LIFT + theme.TRIM_HEIGHT / 2.0
        return [
            _DetailView(
                entity=Entity(
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
                        rest_y,
                        z + detail.offset[1] * _SURFACE,
                    ),
                ),
                cell=cell,
                kind=kind,
                rest_y=rest_y,
                size=(detail.size[0] * _SURFACE, detail.size[1] * _SURFACE),
            )
            for number, detail in enumerate(DETAILS.get(kind, ()))
        ]

    def _build_lines(
        self,
        cell: Cell,
        drawn: set[Cell],
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

    def refresh(self, state: State) -> None:
        """Retarget the mechanisms for ``state``: where each bridge heads, and the plate loads."""
        if state == self._state:
            return
        self._state = state
        for position, bridge in enumerate(self.stage.bridges):
            if bridge.pos in self.tiles:
                self._bridge_targets[bridge.pos] = _bridge_height(state.bridges[position])
        self._load_targets = reaction.load_per_cell(self.stage, state)

    def update(self, dt: float) -> None:
        """Ease every mechanism toward its target, then redraw the pieces that carry them."""
        press_step = dt / theme.PRESS_SECONDS
        bridge_step = dt * BRIDGE_TRAVEL / theme.BRIDGE_SECONDS
        for cell, target in self._load_targets.items():
            self._load[cell] = approach(self._load.get(cell, 0.0), target, press_step)
        for cell, target in self._bridge_targets.items():
            self._rest_y[cell] = approach(self._rest_y[cell], target, bridge_step)
        self._place_tiles()
        self._place_details()

    def _place_tiles(self) -> None:
        for index, (cell, tile) in enumerate(self.tiles.items()):
            tile.y = self._rest_y[cell] + self._intro_offsets[index]
            self._tile_bases[cell].y = tile.y + TILE_BASE_DROP
            if cell in self._bridge_targets:
                tile.color = _bridge_color(self._rest_y[cell])
            for line in self._line_at.get(cell, ()):
                line.y = self._line_y(tile.y)

    def _place_details(self) -> None:
        for view, offset in zip(self.details, self._detail_intro_offsets):
            self._place_detail(view, self._load.get(view.cell, 0.0), offset)

    @staticmethod
    def _place_detail(view: _DetailView, load: float, offset: float) -> None:
        """Put one piece at its resting height, deformed by however hard it is being pressed."""
        if view.kind == "fragile":
            # The fracture opens along its depth as the panel takes weight.
            view.entity.y = view.rest_y + offset
            view.entity.scale_z = view.size[1] * (1.0 + theme.CRACK_OPEN * load)
            return
        # A plate sinks by however far into the press it has travelled.
        view.entity.y = view.rest_y - theme.PRESS_DEPTH * load + offset
