"""Minimal 3D miniature of a level's board for the level select screen.

One flat slab per walkable cell, in exactly the colour the board itself uses in game
(``board_view.TILE_COLORS``), so the miniature reads as the level: the goal is a hole, an open
bridge is the mechanism cyan and a closed one is floor-dark, fragile cells are peach, and a switch
is its own cyan or teal cell. Every piece uses ``unlit_shader``, so the palette alone decides how
the preview looks and there is no lighting of its own to get wrong.

Tiles are drawn marginally narrower than a grid cell, so the groove between them shows the card
through and single cells stay countable at miniature scale.

The board sits on a cream card: the level select's backdrop is the tile colour, and a dark board
on a dark screen would have no silhouette.
"""

from __future__ import annotations

from panda3d.core import Vec3
from ursina import Entity, destroy, time
from ursina.shaders import unlit_shader

from bloxorz.core.contracts import Cell, Kind, Stage

from . import theme
from .board_view import TILE_COLORS, TILES_LEFT_OUT
from .layout import cell_to_world

# The tilt that makes a flat grid read as an isometric model.
PREVIEW_ROTATION = (48.0, -32.0, 0.0)

# The cream card the miniature stands on: where it sits, and how big it is (UI units — the window
# is 1.78 units wide and 1 unit tall, so the right half is the board's).
CARD_POSITION = (0.45, 0.0)
CARD_SIZE = (0.82, 0.70)

# The box the board is scaled into, inside the card's margins.
BOARD_BOX = (0.72, 0.56)

# The UI layer is not depth-tested, so z alone decides what covers what, and a tilted board
# spreads over a range of depths: the card is parked well behind all of it, and the board is built
# nearest to the camera so it lifts off the card.
CARD_Z = 0.0
CONTENT_Z = -0.5

# A tile spans this much of its grid cell, leaving a groove rather than butting against its
# neighbours. The slab is thin for the same reason: a full-thickness tile would show its own side
# across the groove and the board would read as one solid shape.
TILE_WIDTH = 0.84
TILE_THICKNESS = theme.TILE_CAP_HEIGHT

FADE_DURATION_SECONDS = 0.25


def _ease_out_cubic(t: float) -> float:
    return 1.0 - (1.0 - t) ** 3


def _kind(stage: Stage, cell: Cell) -> Kind:
    """The stage glyph kind of one cell."""
    return stage.index.kind[cell[0] * stage.index.cols + cell[1]]


def _tile_colors(stage: Stage) -> dict[Cell, object]:
    """The colour of every drawn cell, with each bridge tinted by its initial state."""
    colors: dict[Cell, object] = {
        cell: TILE_COLORS[_kind(stage, cell)]
        for cell in (
            (row, col)
            for row in range(stage.index.rows)
            for col in range(stage.index.cols)
        )
        if _kind(stage, cell) not in TILES_LEFT_OUT
    }
    for bridge in stage.bridges:
        if bridge.pos in colors:
            colors[bridge.pos] = TILE_COLORS["bridge" if bridge.initially_open else "floor"]
    return colors


def _slab(parent: Entity, name: str, position: tuple[float, float], tint: object) -> Entity:
    """One flat tile, its top face at y = 0 so the whole board shares one surface."""
    return Entity(
        parent=parent,
        name=name,
        model="cube",
        scale=(TILE_WIDTH, TILE_THICKNESS, TILE_WIDTH),
        position=(position[0], -TILE_THICKNESS / 2.0, position[1]),
        color=tint,
        shader=unlit_shader,
    )


def build_mini_board(stage: Stage, parent: Entity) -> dict[Cell, Entity]:
    """Draw the stage's board under ``parent`` and return its tiles, keyed by cell."""
    rows, cols = stage.index.rows, stage.index.cols
    tiles: dict[Cell, Entity] = {}

    for cell, tint in _tile_colors(stage).items():
        position = cell_to_world(cell, rows, cols)
        row, col = cell
        tiles[cell] = _slab(parent, f"mini-tile-{row}-{col}", position, tint)

    return tiles


def _projected_box(tiles: dict[Cell, Entity], wrapper: Entity) -> tuple[Vec3, Vec3]:
    """The screen box the miniature covers, relative to the board's own centre.

    The UI layer is drawn flat, so a piece's ``x`` and ``y`` are its screen position: tilting
    every tile's eight corners through the board's rotation gives the box the board will cover,
    whatever its size and however its cells are laid out.
    """
    tilt = wrapper.getTransform().getMat().getUpper3()
    half = Vec3(TILE_WIDTH / 2.0, TILE_THICKNESS / 2.0, TILE_WIDTH / 2.0)
    corners = [
        tilt.xform(Vec3(*tile.position) + Vec3(x * half.x, y * half.y, z * half.z))
        for tile in tiles.values()
        for x in (-1.0, 1.0)
        for y in (-1.0, 1.0)
        for z in (-1.0, 1.0)
    ]
    low = Vec3(
        min(corner.x for corner in corners),
        min(corner.y for corner in corners),
        0.0,
    )
    high = Vec3(
        max(corner.x for corner in corners),
        max(corner.y for corner in corners),
        0.0,
    )
    return low, high


class LevelPreviewPanel(Entity):
    """The cream card, the cached miniature boards, and the crossfade between them."""

    def __init__(self, parent: Entity) -> None:
        super().__init__(parent=parent, name="level_preview_panel")

        self.card = Entity(
            parent=self,
            model="quad",
            scale=CARD_SIZE,
            position=(CARD_POSITION[0], CARD_POSITION[1], CARD_Z),
            color=theme.BACKGROUND,
        )
        self._cache: dict[str, tuple[Entity, float]] = {}
        self.current_stage_id: str | None = None
        self._fading = False
        self._fade_elapsed = 0.0

    def set_stage(self, stage: Stage) -> None:
        """Show ``stage``'s miniature, reusing the cached one when it has been built before."""
        if stage.id == self.current_stage_id:
            return

        if self.current_stage_id is not None and self.current_stage_id in self._cache:
            self._cache[self.current_stage_id][0].enabled = False

        self.current_stage_id = stage.id

        if stage.id in self._cache:
            self._cache[stage.id][0].enabled = True
        else:
            self._build_preview(stage)

        self._fading = True
        self._fade_elapsed = 0.0

    def _build_preview(self, stage: Stage) -> None:
        """Tilt one miniature, centre it on the card, and scale it into ``BOARD_BOX``."""
        wrapper = Entity(
            parent=self,
            name=f"preview_wrap_{stage.id}",
            rotation=PREVIEW_ROTATION,
            position=(CARD_POSITION[0], CARD_POSITION[1], CONTENT_Z),
        )
        low, high = _projected_box(build_mini_board(stage, wrapper), wrapper)
        base_scale = min(BOARD_BOX[0] / (high.x - low.x), BOARD_BOX[1] / (high.y - low.y))
        wrapper.scale = (base_scale, base_scale, base_scale)
        # A stage's cells are not spread evenly over its grid, so the board's own box is what gets
        # centred on the card, not its grid origin.
        wrapper.x = CARD_POSITION[0] - (low.x + high.x) / 2.0 * base_scale
        wrapper.y = CARD_POSITION[1] - (low.y + high.y) / 2.0 * base_scale
        self._cache[stage.id] = (wrapper, base_scale)

    def update(self) -> None:
        """Ease the current miniature in, so a level change reads as one board replacing another."""
        if not self._fading or self.current_stage_id not in self._cache:
            return

        self._fade_elapsed += time.dt
        t = min(1.0, self._fade_elapsed / FADE_DURATION_SECONDS)
        wrapper, base_scale = self._cache[self.current_stage_id]
        scale = base_scale * (0.94 + 0.06 * _ease_out_cubic(t))
        wrapper.scale = (scale, scale, scale)
        if t >= 1.0:
            self._fading = False

    def teardown(self) -> None:
        """Drop every cached board."""
        self._cache.clear()
        destroy(self)
