"""The level's Solve control: one card per algorithm, plus the "solving" state (Ursina).

Hidden by default. The scene owns the timing: it shows the panel when the load animation ends,
hides it once the level is cleared, and calls ``set_busy`` on the frame **before** a blocking
``solve`` call — the card must be on screen while the search runs, or the window looks dead. The
busy mark is also what stops a second click from starting a second search.

Colours are the menu pair already in ``theme.py`` — dark cards with cream labels, the same as the
win overlay's secondary actions — so this screen adds nothing to the palette.
"""

from __future__ import annotations

from collections.abc import Callable

from ursina import Button, Entity, Text, camera

from . import theme, widgets

CARD_SCALE = (0.16, 0.06)
CARD_PITCH = 0.18
CARD_Y = -0.42
TITLE = "Solve"
TITLE_Y = -0.345
TITLE_SCALE = 0.7
BUSY_SUFFIX = "…"


class SolverPanel(Entity):
    """A row of algorithm cards that reports which run is in progress."""

    def __init__(self, algorithms: tuple[str, ...], on_pick: Callable[[str], None]) -> None:
        # UI entities belong to the UI camera, so their coordinates are screen fractions.
        super().__init__(name="solver-panel", parent=camera.ui)
        self.algorithms = algorithms
        self.on_pick = on_pick
        self.cards: dict[str, Button] = {}
        self._busy: str | None = None
        self._shown = False
        self._build()
        # The panel is built visible, so hide it directly rather than through the guarded ``hide``.
        self.enabled = False

    def _build(self) -> None:
        Text(
            parent=self,
            text=TITLE,
            origin=(0, 0),
            y=TITLE_Y,
            scale=TITLE_SCALE,
            color=theme.TEXT,
        )
        start = -CARD_PITCH * (len(self.algorithms) - 1) / 2.0
        for position, algorithm in enumerate(self.algorithms):
            self.cards[algorithm] = widgets.card(
                parent=self,
                text=algorithm,
                position=(start + position * CARD_PITCH, CARD_Y),
                scale=CARD_SCALE,
                color=theme.TILE_FLOOR,
                text_color=theme.BACKGROUND,
                on_click=lambda name=algorithm: self._pick(name),
            )

    def show(self) -> None:
        if self._shown:
            return
        self._shown = True
        self.enabled = True

    def hide(self) -> None:
        if not self._shown:
            return
        self._shown = False
        self.enabled = False

    def set_busy(self, algorithm: str | None) -> None:
        """Mark ``algorithm`` as running, or clear the marks with ``None``.

        The chosen card switches to the deep teal and gains an ellipsis, so the frame drawn during
        the search already says what is happening.
        """
        self._busy = algorithm
        for name, card in self.cards.items():
            running = name == algorithm
            card.label.text = f"{name}{BUSY_SUFFIX}" if running else name
            card.color = theme.TILE_HEAVY if running else theme.TILE_FLOOR

    def _pick(self, algorithm: str) -> None:
        """Start a run, unless the panel is hidden or one is already in progress."""
        if self._busy is not None or not self._shown:
            return
        self.on_pick(algorithm)
