"""The level select: the screen the game boots into.

One card per stage, one row per stage group, and a cleared stage keeps the mechanism-cyan card for
the rest of the session. Clicking a card starts that level. The order and the grouping come from
``catalog.py``, so this module only draws what the catalog says.
"""

from __future__ import annotations

from collections.abc import Callable

from ursina import Entity, Text, camera, destroy, window

from bloxorz.core.contracts import Stage

from . import catalog, theme, widgets

CARD_SCALE = (0.22, 0.07)
COLUMN_PITCH = 0.25
ROW_PITCH = 0.12
FIRST_ROW_Y = 0.20
GROUP_LABEL_X = -0.60
CARD_X = -0.40

TITLE = "MIXI-BLOX"
SUBTITLE = "pick a level"
LEGEND = "cyan = cleared"


class LevelSelectScene(Entity):
    """A grid of level cards grouped by stage group, plus the session's cleared marks."""

    def __init__(
        self,
        stages: tuple[Stage, ...],
        cleared: set[str],
        on_pick: Callable[[Stage], None],
    ) -> None:
        # UI entities belong to the UI camera, so their coordinates are screen fractions.
        super().__init__(name="level-select", parent=camera.ui)
        self.on_pick = on_pick
        window.title = "Mixi-Blox  |  levels"
        self._build(stages, cleared)

    def _build(self, stages: tuple[Stage, ...], cleared: set[str]) -> None:
        Text(
            parent=self,
            text=TITLE,
            origin=(0, 0),
            y=0.42,
            scale=2.0,
            color=theme.TEXT,
        )
        Text(
            parent=self,
            text=f"{SUBTITLE}   |   {LEGEND}",
            origin=(0, 0),
            y=0.32,
            scale=0.7,
            color=theme.TEXT,
        )

        for row, (group, levels) in enumerate(catalog.groups(stages)):
            y = FIRST_ROW_Y - row * ROW_PITCH
            Text(
                parent=self,
                text=group,
                position=(GROUP_LABEL_X, y, -0.01),
                origin=(0, 0),
                color=theme.TEXT,
            )
            for column, stage in enumerate(levels):
                self._card(stage, (CARD_X + column * COLUMN_PITCH, y), stage.id in cleared)

    def _card(self, stage: Stage, position: tuple[float, float], is_cleared: bool) -> None:
        widgets.card(
            parent=self,
            text=stage.id,
            position=position,
            scale=CARD_SCALE,
            color=theme.TILE_BRIDGE if is_cleared else theme.TILE_FLOOR,
            text_color=theme.TILE_FLOOR if is_cleared else theme.BACKGROUND,
            on_click=lambda: self.on_pick(stage),
        )

    def teardown(self) -> None:
        """Remove the screen: every card and label is a child of this entity."""
        destroy(self)

