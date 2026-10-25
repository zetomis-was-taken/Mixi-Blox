"""The title screen: the first thing the game shows.

A centred wordmark, a one-line tagline, and a short column of cards — play, which opens the level
select, and quit. ``Enter`` and ``Esc`` mirror those two cards, so the screen never depends on the
mouse. Cards come from ``widgets.py`` and every colour from ``theme.py``, like the other menu
screens; nothing here reads a stage or drives the board.
"""

from __future__ import annotations

from collections.abc import Callable

from ursina import Entity, Text, application, camera, destroy, window

from . import theme, widgets

TITLE = "MIXI-BLOX"
SUBTITLE = "roll the block onto the goal"

TITLE_Y = 0.24
TITLE_SCALE = 2.0
SUBTITLE_Y = 0.15
SUBTITLE_SCALE = 0.7

# One column of cards: a pitch wider than a card's height leaves a visible gap between the two.
CARD_SCALE = (0.30, 0.085)
CARD_PITCH = 0.13
FIRST_CARD_Y = -0.02

HINT_Y = -0.30
HINT_SCALE = 0.6
KEY_HINTS = "Enter play      Esc quit"


class TitleScene(Entity):
    """The boot screen: the wordmark, and the way into the game or out of it."""

    def __init__(self, on_play: Callable[[], None]) -> None:
        # UI entities belong to the UI camera, so their coordinates are screen fractions.
        super().__init__(name="title", parent=camera.ui)
        self.on_play = on_play
        window.title = "Mixi-Blox  |  title"
        self._build()

    def input(self, key: str) -> None:
        """The keyboard route through the menu, mirroring its two cards."""
        if key == "enter":
            self.on_play()
        elif key == "escape":
            application.quit()

    def _build(self) -> None:
        self._line(TITLE, TITLE_Y, TITLE_SCALE)
        self._line(SUBTITLE, SUBTITLE_Y, SUBTITLE_SCALE)

        actions: tuple[tuple[str, Callable[[], None], bool], ...] = (
            ("Play", self.on_play, True),
            ("Quit", application.quit, False),
        )
        for position, (label, callback, primary) in enumerate(actions):
            widgets.card(
                parent=self,
                text=label,
                position=(0.0, FIRST_CARD_Y - position * CARD_PITCH),
                scale=CARD_SCALE,
                color=theme.TILE_BRIDGE if primary else theme.TILE_FLOOR,
                text_color=theme.TILE_FLOOR if primary else theme.BACKGROUND,
                on_click=callback,
            )

        self._line(KEY_HINTS, HINT_Y, HINT_SCALE)

    def _line(self, text: str, y: float, scale: float) -> None:
        """A centred line of text, in the one colour every menu screen writes in."""
        Text(parent=self, text=text, origin=(0, 0), y=y, scale=scale, color=theme.TEXT)

    def teardown(self) -> None:
        """Remove the screen: every card and label is a child of this entity."""
        destroy(self)
