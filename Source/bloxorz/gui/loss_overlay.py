"""The loss overlay: retry or level select over the board.

A modal card shown when a move drops the block or breaks a fragile tile.
Offers Retry (R / Enter) and Levels (Esc / L).
"""

from __future__ import annotations

from collections.abc import Callable

from ursina import Entity, Text, camera

from bloxorz.core.contracts import Stage

from . import theme, widgets

PANEL_SCALE = (0.70, 0.34)

TITLE = "Stage failed"
TITLE_Y = 0.11
STAGE_Y = 0.05
RESULT_Y = 0.00

CARD_SCALE = (0.24, 0.075)
CARD_PITCH = 0.28
CARD_Y = -0.06
HINT_Y = -0.14

KEY_HINTS = "R / Enter retry      Esc / L levels"


class LossOverlay(Entity):
    """A modal loss card: retry, or leave for the level select."""

    def __init__(
        self,
        stage: Stage,
        on_retry: Callable[[], None],
        on_levels: Callable[[], None],
    ) -> None:
        super().__init__(name="loss-overlay", parent=camera.ui)
        self.on_retry = on_retry
        self.on_levels = on_levels
        self._build(stage)

    def input(self, key: str) -> None:
        """The keyboard route through the overlay, mirroring its cards."""
        if key in ("r", "enter"):
            self.on_retry()
        elif key in ("escape", "l"):
            self.on_levels()

    def _build(self, stage: Stage) -> None:
        Entity(
            parent=self,
            model="quad",
            color=theme.OVERLAY_PANEL,
            scale=PANEL_SCALE,
            z=widgets.PANEL_Z,
        )
        Text(parent=self, text=TITLE, origin=(0, 0), y=TITLE_Y, scale=1.4, color=theme.TEXT)
        Text(
            parent=self,
            text=f"{stage.id}  {stage.name}",
            origin=(0, 0),
            y=STAGE_Y,
            scale=0.8,
            color=theme.TEXT,
        )
        Text(
            parent=self,
            text="The block fell off the platform",
            origin=(0, 0),
            y=RESULT_Y,
            scale=0.9,
            color=theme.TEXT,
        )
        actions: tuple[tuple[str, Callable[[], None], bool], ...] = (
            ("Retry", self.on_retry, True),
            ("Level select", self.on_levels, False),
        )

        start = -CARD_PITCH * (len(actions) - 1) / 2.0
        for position, (label, callback, primary) in enumerate(actions):
            widgets.card(
                parent=self,
                text=label,
                position=(start + position * CARD_PITCH, CARD_Y),
                scale=CARD_SCALE,
                color=theme.TILE_BRIDGE if primary else theme.TILE_FLOOR,
                text_color=theme.TILE_FLOOR if primary else theme.BACKGROUND,
                on_click=callback,
            )
        Text(
            parent=self,
            text=KEY_HINTS,
            origin=(0, 0),
            y=HINT_Y,
            scale=0.75,
            color=theme.TEXT,
        )
