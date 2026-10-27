"""The pause screen: the two ways onward from a level, over the frozen board (Ursina).

`Esc` raises it from a loaded, unsolved level; `Enter` or `Esc` continues, and `L` opens the level
select — the same two actions its cards offer. The card is drawn like the win overlay, a nearly
opaque cream panel, so the level stays visible behind it. It only draws and calls back: the level
scene owns the paused state, stops the clock and drops movement input while the card is up.

The card is not offered during the load animation, a solver movie or a result card, where `Esc`
already means something else; those guards live in the scene that owns them.
"""

from __future__ import annotations

from collections.abc import Callable

from ursina import Entity, Text, camera

from bloxorz.core.contracts import Stage

from . import theme, widgets

PANEL_SCALE = (0.62, 0.34)

TITLE = "Paused"
TITLE_Y = 0.11
STAGE_Y = 0.05

CARD_SCALE = (0.24, 0.075)
CARD_PITCH = 0.28
CARD_Y = -0.04
HINT_Y = -0.12

KEY_HINTS = "Enter / Esc continue      L level select"


class PauseOverlay(Entity):
    """A modal pause card: continue, or leave for the level select."""

    def __init__(
        self,
        stage: Stage,
        on_continue: Callable[[], None],
        on_levels: Callable[[], None],
    ) -> None:
        # UI entities belong to the UI camera, so their coordinates are screen fractions.
        super().__init__(name="pause-overlay", parent=camera.ui)
        self.on_continue = on_continue
        self.on_levels = on_levels
        self._build(stage)

    def _build(self, stage: Stage) -> None:
        Entity(parent=self, model="quad", color=theme.OVERLAY_PANEL, scale=PANEL_SCALE)
        Text(parent=self, text=TITLE, origin=(0, 0), y=TITLE_Y, scale=1.4, color=theme.TEXT)
        Text(
            parent=self,
            text=f"{stage.id}  {stage.name}",
            origin=(0, 0),
            y=STAGE_Y,
            scale=0.8,
            color=theme.TEXT,
        )
        self._build_cards()
        Text(
            parent=self,
            text=KEY_HINTS,
            origin=(0, 0),
            y=HINT_Y,
            scale=0.6,
            color=theme.TEXT,
        )

    def _build_cards(self) -> None:
        """Two cards, the way onward first; their click and key routes are the same actions."""
        actions: tuple[tuple[str, Callable[[], None], bool], ...] = (
            ("Continue", self.on_continue, True),
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
