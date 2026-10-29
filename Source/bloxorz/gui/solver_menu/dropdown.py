"""The solver dropdown menu containing algorithm choices (Ursina).

Displayed below the hamburger button when toggled open. Clicking outside or selecting
an algorithm closes the dropdown.
"""

from __future__ import annotations

from collections.abc import Callable

from ursina import Button, Entity, Text, color

from .. import theme, widgets

DROPDOWN_X = 0.71
DROPDOWN_TOP_Y = 0.405

PANEL_WIDTH = 0.17
HEADER_HEIGHT = 0.035
CARD_SCALE = (0.15, 0.042)
CARD_PITCH = 0.050
PADDING = 0.015

TITLE = "Solve"
TITLE_SCALE = 0.65
BUSY_SUFFIX = "…"


class DropdownMenu(Entity):
    """The dropdown list of solver options that opens from the hamburger button."""

    def __init__(
        self,
        parent: Entity,
        algorithms: tuple[str, ...],
        on_pick: Callable[[str], None],
        on_close: Callable[[], None],
    ) -> None:
        super().__init__(name="solver-dropdown", parent=parent)
        self.algorithms = algorithms
        self.on_pick = on_pick
        self.on_close = on_close
        self.cards: dict[str, Button] = {}
        self._busy: str | None = None
        self._build()
        self.enabled = False

    def _build(self) -> None:
        # Full-screen invisible button behind the menu to catch clicks outside
        Button(
            parent=self,
            model="quad",
            scale=(3.0, 3.0),
            position=(0, 0, widgets.PANEL_Z + 0.01),
            color=color.clear,
            on_click=self.on_close,
        )

        n = len(self.algorithms)
        panel_height = HEADER_HEIGHT + n * CARD_PITCH + PADDING * 2
        panel_y = DROPDOWN_TOP_Y - panel_height / 2.0

        # Background panel
        Entity(
            parent=self,
            model="quad",
            scale=(PANEL_WIDTH, panel_height),
            position=(DROPDOWN_X, panel_y, widgets.PANEL_Z),
            color=theme.OVERLAY_PANEL,
        )

        # Header title
        title_y = DROPDOWN_TOP_Y - PADDING - HEADER_HEIGHT / 2.0
        Text(
            parent=self,
            text=TITLE,
            origin=(0, 0),
            position=(DROPDOWN_X, title_y, widgets.TEXT_Z),
            scale=TITLE_SCALE,
            color=theme.TEXT,
        )

        # Algorithm selection cards
        first_card_y = title_y - HEADER_HEIGHT / 2.0 - CARD_PITCH / 2.0
        for i, algorithm in enumerate(self.algorithms):
            card_y = first_card_y - i * CARD_PITCH
            self.cards[algorithm] = widgets.card(
                parent=self,
                text=algorithm,
                position=(DROPDOWN_X, card_y),
                scale=CARD_SCALE,
                color=theme.TILE_FLOOR,
                text_color=theme.BACKGROUND,
                on_click=lambda name=algorithm: self._pick(name),
            )

    def set_busy(self, algorithm: str | None) -> None:
        """Mark an algorithm as running or clear marks with None."""
        self._busy = algorithm
        for name, card in self.cards.items():
            running = name == algorithm
            card.label.text = f"{name}{BUSY_SUFFIX}" if running else name
            card.color = theme.TILE_HEAVY if running else theme.TILE_FLOOR

    def _pick(self, algorithm: str) -> None:
        """Handle algorithm selection."""
        if self._busy is not None:
            return
        self.on_close()
        self.on_pick(algorithm)

