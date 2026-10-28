"""Custom text-only title menu item with left-to-right highlight slide on hover.

When resting: bold, clean uppercase text without background.
When hovered: a light solid background wipes from left to right, inverting text to dark ink
without moving the text.
"""

from __future__ import annotations

from collections.abc import Callable

from ursina import Button, Entity, Text, color, lerp, time

from .fonts import get_font, setup_text_sharpness

COLOR_TEXT_REST = color.hex("#FFEECC")
COLOR_TEXT_HOVER = color.hex("#1A1824")
COLOR_BG_HOVER = color.hex("#FFEECC")

ITEM_HEIGHT = 0.095
ITEM_WIDTH = 0.38
TEXT_OFFSET_X = 0.03


class TitleMenuItem(Entity):
    """Text-only menu button featuring a kinetic left-to-right highlight wipe."""

    def __init__(
        self,
        parent: Entity,
        text: str,
        on_click: Callable[[], None],
        y: float,
        width: float = ITEM_WIDTH,
    ) -> None:
        super().__init__(
            parent=parent,
            name=f"menu_item_{text.lower()}",
            position=(0.0, y, -0.01),
        )
        self.item_width = width
        self.item_height = ITEM_HEIGHT
        self.action = on_click
        self.interactive = False

        # Invisible base button quad for hover & click hit detection
        self.button = Button(
            parent=self,
            model="quad",
            origin=(-0.5, 0.0),
            position=(0.0, 0.0, 0.01),
            scale=(self.item_width, self.item_height),
            color=color.clear,
            highlight_color=color.clear,
            pressed_color=color.clear,
        )
        self.button.on_click = self._handle_click

        # The light background highlight that expands from Left to Right
        self.highlight_bar = Entity(
            parent=self,
            model="quad",
            origin=(-0.5, 0.0),
            position=(0.0, 0.0, 0.005),
            scale=(0.0001, self.item_height),
            color=COLOR_BG_HOVER,
            enabled=False,
        )

        # The crisp uppercase label (larger, bolder, static position, sharp resolution)
        self.label = Text(
            parent=self,
            text=text.upper(),
            font=get_font("PlusJakartaSans-ExtraBold.ttf"),
            origin=(-0.5, 0.0),
            position=(TEXT_OFFSET_X, 0.0, -0.005),
            scale=1.45,
            color=COLOR_TEXT_REST,
        )
        setup_text_sharpness(self.label, point_size=36.0, pixels_per_unit=120.0)

    def _handle_click(self) -> None:
        if self.interactive:
            self.action()

    def update(self) -> None:
        if not self.interactive:
            self.highlight_bar.enabled = False
            self.highlight_bar.scale_x = 0.0001
            self.label.color = COLOR_TEXT_REST
            return

        is_hovered = self.button.hovered
        target_scale_x = self.item_width if is_hovered else 0.0001
        target_color = COLOR_TEXT_HOVER if is_hovered else COLOR_TEXT_REST

        # Animate left-to-right highlight bar smoothly
        new_scale_x = lerp(self.highlight_bar.scale_x, target_scale_x, time.dt * 24.0)
        if new_scale_x <= 0.002 and not is_hovered:
            self.highlight_bar.enabled = False
            self.highlight_bar.scale_x = 0.0001
        else:
            self.highlight_bar.enabled = True
            self.highlight_bar.scale_x = max(0.0001, new_scale_x)

        # Invert text color immediately on hover, keeping text position stationary
        self.label.color = target_color
