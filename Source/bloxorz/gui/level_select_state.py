"""Pure-logic state and layout calculations for the level select screen.

Maintains selected index, width cascade lerping, scroll smoothing, and mouse scroll
cooldowns. Kept strictly free of Ursina imports so all UI layout logic can be tested
headless via pytest.
"""

from __future__ import annotations

SELECTED_WIDTH = 0.70
NEIGHBOR_1_WIDTH = 0.54
NEIGHBOR_2_WIDTH = 0.42
STANDARD_WIDTH = 0.34

BUTTON_HEIGHT = 0.075
BUTTON_PITCH = 0.092

WIDTH_LERP_FACTOR = 8.0
SCROLL_LERP_FACTOR = 10.0
SCROLL_COOLDOWN_SECONDS = 0.15


def target_width(distance: int) -> float:
    """Return the target width based on distance from the selected card."""
    d = abs(distance)
    if d == 0:
        return SELECTED_WIDTH
    if d == 1:
        return NEIGHBOR_1_WIDTH
    if d == 2:
        return NEIGHBOR_2_WIDTH
    return STANDARD_WIDTH


def approach_lerp(current: float, target: float, rate: float, dt: float) -> float:
    """Smooth exponential decay lerp towards target."""
    factor = min(1.0, max(0.0, rate * dt))
    return current + (target - current) * factor


class LevelSelectState:
    """Tracks selection, fish-eye cascade widths, and scroll position."""

    def __init__(self, stage_count: int, initial_index: int = 0) -> None:
        if stage_count <= 0:
            raise ValueError("stage_count must be positive")
        self.stage_count = stage_count
        self.selected_index = max(0, min(initial_index, stage_count - 1))
        self.widths = [target_width(i - self.selected_index) for i in range(stage_count)]
        self.scroll_y = self.target_scroll_y()
        self.scroll_cooldown = 0.0

    def target_scroll_y(self) -> float:
        """The vertical scroll offset required to keep the selected button at y = 0."""
        return self.selected_index * BUTTON_PITCH

    def select(self, index: int) -> bool:
        """Change selected index, clamped to valid stage range.

        Returns True if selection changed.
        """
        clamped = max(0, min(index, self.stage_count - 1))
        if clamped != self.selected_index:
            self.selected_index = clamped
            return True
        return False

    def select_prev(self) -> bool:
        """Select previous stage in the list."""
        return self.select(self.selected_index - 1)

    def select_next(self) -> bool:
        """Select next stage in the list."""
        return self.select(self.selected_index + 1)

    def on_scroll(self, direction: int) -> bool:
        """Handle mouse scroll event (-1 for up/previous, +1 for down/next).

        Throttled by SCROLL_COOLDOWN_SECONDS.
        """
        if self.scroll_cooldown > 0.0:
            return False
        changed = False
        if direction < 0:
            changed = self.select_prev()
        elif direction > 0:
            changed = self.select_next()
        self.scroll_cooldown = SCROLL_COOLDOWN_SECONDS
        return changed

    def update(self, dt: float) -> None:
        """Advance time: decay scroll cooldown and lerp widths and scroll position."""
        if self.scroll_cooldown > 0.0:
            self.scroll_cooldown = max(0.0, self.scroll_cooldown - dt)

        # Lerp width cascade for every button
        for i in range(self.stage_count):
            t_width = target_width(i - self.selected_index)
            self.widths[i] = approach_lerp(self.widths[i], t_width, WIDTH_LERP_FACTOR, dt)

        # Lerp scroll offset
        self.scroll_y = approach_lerp(
            self.scroll_y, self.target_scroll_y(), SCROLL_LERP_FACTOR, dt
        )

    def button_y(self, index: int) -> float:
        """Compute the vertical position of button at index."""
        return self.scroll_y - index * BUTTON_PITCH

    def is_visible(self, index: int, top: float, bottom: float) -> bool:
        """Check whether the button at index falls inside the band ``bottom`` .. ``top``."""
        return bottom <= self.button_y(index) <= top

