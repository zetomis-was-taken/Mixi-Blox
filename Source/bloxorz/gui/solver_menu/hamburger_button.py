"""The hamburger icon button for the solver menu (Ursina).

Sits in the top-right corner of the HUD, styled with the project palette.
Clicking toggles the solver dropdown menu open or closed.
"""

from __future__ import annotations

from collections.abc import Callable

from ursina import Button, Entity

from .. import theme, widgets

BUTTON_SCALE = (0.055, 0.055)
BUTTON_X = 0.74
BUTTON_Y = 0.44

BAR_SCALE = (0.55, 0.08)
BAR_Y_OFFSETS = (0.22, 0.0, -0.22)
BAR_Z = -0.01


class HamburgerButton(Entity):
    """A top-right icon button with 3 horizontal bars."""

    def __init__(self, parent: Entity, on_toggle: Callable[[], None]) -> None:
        super().__init__(name="hamburger-button", parent=parent)
        self.on_toggle = on_toggle
        self._busy = False
        self._build()

    def _build(self) -> None:
        self.button = Button(
            parent=self,
            model="quad",
            position=(BUTTON_X, BUTTON_Y, widgets.CARD_Z),
            scale=BUTTON_SCALE,
            color=theme.TILE_FLOOR,
            highlight_color=theme.TILE_BRIDGE,
            pressed_color=theme.TILE_HEAVY,
        )
        self.button.on_click = self._handle_click

        self.bars: list[Entity] = []
        for y_offset in BAR_Y_OFFSETS:
            bar = Entity(
                parent=self.button,
                model="quad",
                position=(0, y_offset, BAR_Z),
                scale=BAR_SCALE,
                color=theme.BACKGROUND,
            )
            self.bars.append(bar)

    def _handle_click(self) -> None:
        self.on_toggle()

    def set_busy(self, busy: bool) -> None:
        """Tint the button if a solver is running."""
        self._busy = busy
        self.button.color = theme.TILE_HEAVY if busy else theme.TILE_FLOOR

