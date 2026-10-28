"""The modernized two-layer level select screen with 3D board preview.

Presents a full-screen dark backdrop (Layer A) with a vertical, scrollable button list
anchored to the left side with fish-eye cascade widths, and an angled, softened 3D board
preview (Layer B) with loading transitions.
"""

from __future__ import annotations

from collections.abc import Callable

from ursina import Button, Entity, Text, camera, color, destroy, time, window

from bloxorz.core.contracts import Stage

from . import theme
from .level_select_state import BUTTON_HEIGHT, LevelSelectState
from .preview import LevelPreviewPanel
from .title.fonts import get_font, setup_text_sharpness

# Screen left frame edge where the button background starts flush
SCREEN_EDGE_LEFT = -0.88
LABEL_MARGIN_LEFT = -0.74
TITLE_Y = 0.40
SUBTITLE_Y = 0.33
FOOTER_Y = -0.44

TITLE_TEXT = "SELECT LEVEL"
SUBTITLE_TEXT = "CLICK to select  |  CLICK AGAIN / ENTER to play  |  W/S/SCROLL navigate"
FOOTER_TEXT = "↑/↓ NAVIGATE      ENTER / CLICK CHOOSE      ESC TITLE"


class _LevelButtonItem:
    """Wraps a single level button quad, its sibling text, and cleared badge."""

    def __init__(
        self,
        parent: Entity,
        stage: Stage,
        is_cleared: bool,
        on_click: Callable[[], None],
    ) -> None:
        self.stage = stage
        self.is_cleared = is_cleared
        self.on_click_callback = on_click

        font_body = get_font("PlusJakartaSans-ExtraBold.ttf")

        # Quad button background
        self.button = Button(
            parent=parent,
            model="quad",
            scale=(0.40, BUTTON_HEIGHT),
            color=theme.TILE_FLOOR,
            z=0.01,
        )
        self.button.highlight_color = color.rgba32(85, 80, 115, 255)
        self.button.pressed_color = theme.TILE_FLOOR
        self.button.on_click = self.on_click_callback

        # Sibling text label (left-aligned inside the card)
        self.label = Text(
            parent=parent,
            text=stage.id,
            font=font_body,
            origin=(-0.5, 0.0),
            scale=0.60,
            color=theme.BACKGROUND,
            z=-0.01,
        )
        setup_text_sharpness(self.label, point_size=24.0, pixels_per_unit=130.0)

        # Cleared badge indicator
        self.badge: Entity | None = None
        if self.is_cleared:
            self.badge = Entity(
                parent=parent,
                model="quad",
                scale=(0.016, 0.016),
                color=theme.TILE_HEAVY,
                z=-0.02,
            )

    def set_layout(
        self,
        y: float,
        width: float,
        is_selected: bool,
        visible: bool,
    ) -> None:
        """Update button geometry, colors, and content."""
        self.button.enabled = visible
        self.label.enabled = visible
        if self.badge is not None:
            self.badge.enabled = visible

        if not visible:
            return

        # Background starts flush from the left screen frame edge
        center_x = SCREEN_EDGE_LEFT + width / 2.0
        self.button.position = (center_x, y, 0.01)
        self.button.scale = (width, BUTTON_HEIGHT, 1.0)

        # Highlighted vs standard card appearance
        if is_selected:
            self.button.color = theme.TILE_BRIDGE
            self.button.highlight_color = theme.TILE_BRIDGE
            self.label.color = theme.TILE_FLOOR
            self.label.text = f"{self.stage.id}   {self.stage.name}"
        else:
            self.button.color = theme.TILE_FLOOR
            self.button.highlight_color = color.rgba32(85, 80, 115, 255)
            self.label.color = theme.BACKGROUND
            self.label.text = self.stage.id

        # Text starts at fixed comfortable padding from the frame
        self.label.position = (LABEL_MARGIN_LEFT, y, -0.01)

        # Badge sits near the expanding right edge of the card
        if self.badge is not None:
            self.badge.position = (SCREEN_EDGE_LEFT + width - 0.035, y, -0.02)


class LevelSelectScene(Entity):
    """Modern two-layer level select screen: fish-eye list on left, 3D preview on right."""

    def __init__(
        self,
        stages: tuple[Stage, ...],
        cleared: set[str],
        on_pick: Callable[[Stage], None],
        on_back: Callable[[], None] | None = None,
    ) -> None:
        super().__init__(name="level-select", parent=camera.ui)
        self.stages = stages
        self.cleared = cleared
        self.on_pick = on_pick
        self.on_back = on_back

        window.title = "Mixi-Blox  |  levels"

        # Layer A: Full-screen solid dark background (#46425e)
        self.backdrop = Entity(
            parent=self,
            model="quad",
            scale=(3.5, 2.5),
            color=theme.TILE_FLOOR,
            z=0.08,
        )

        font_title = get_font("Monoton-Regular.ttf")
        font_hint = get_font("PlusJakartaSans-ExtraBold.ttf")

        # Header titles (anchored to the left margin, fully visible)
        self.title_label = Text(
            parent=self,
            text=TITLE_TEXT,
            font=font_title,
            origin=(-0.5, 0.0),
            position=(LABEL_MARGIN_LEFT, TITLE_Y, -0.01),
            scale=1.35,
            color=theme.BACKGROUND,
        )
        setup_text_sharpness(self.title_label, point_size=28.0, pixels_per_unit=120.0)

        self.subtitle_label = Text(
            parent=self,
            text=SUBTITLE_TEXT,
            font=font_hint,
            origin=(-0.5, 0.0),
            position=(LABEL_MARGIN_LEFT, SUBTITLE_Y, -0.01),
            scale=0.38,
            color=theme.TILE_BRIDGE,
        )
        setup_text_sharpness(self.subtitle_label, point_size=18.0, pixels_per_unit=120.0)

        # Footer hints
        self.footer_label = Text(
            parent=self,
            text=FOOTER_TEXT,
            font=font_hint,
            origin=(0, 0),
            position=(0.0, FOOTER_Y, -0.01),
            scale=0.50,
            color=theme.BACKGROUND,
        )
        setup_text_sharpness(self.footer_label, point_size=20.0, pixels_per_unit=120.0)

        # Layer B: Angled 3D preview panel on right-bottom
        self.preview = LevelPreviewPanel(parent=self)

        # Pure layout state manager
        self.state = LevelSelectState(stage_count=len(stages), initial_index=0)

        # Build button items
        self.buttons: list[_LevelButtonItem] = []
        for i, stage in enumerate(stages):
            btn = _LevelButtonItem(
                parent=self,
                stage=stage,
                is_cleared=(stage.id in cleared),
                on_click=lambda idx=i, s=stage: self._on_button_clicked(idx, s),
            )
            self.buttons.append(btn)

        # Initial preview
        if stages:
            self.preview.set_stage(stages[0])

    def _on_button_clicked(self, index: int, stage: Stage) -> None:
        """Clicking an unselected card highlights and previews it.

        Clicking the already selected card launches the level.
        """
        if self.state.selected_index == index:
            self.on_pick(stage)
        else:
            if self.state.select(index):
                self._on_selection_changed()

    def _on_selection_changed(self) -> None:
        """Notify preview panel when highlighted stage changes."""
        idx = self.state.selected_index
        if 0 <= idx < len(self.stages):
            self.preview.set_stage(self.stages[idx])

    def update(self) -> None:
        """Update animation states and drive button layout."""
        dt = time.dt
        self.state.update(dt)

        sel = self.state.selected_index
        for i, btn in enumerate(self.buttons):
            w = self.state.widths[i]
            y = self.state.button_y(i)
            is_sel = (i == sel)
            is_vis = self.state.is_visible(i)
            btn.set_layout(
                y=y,
                width=w,
                is_selected=is_sel,
                visible=is_vis,
            )

    def input(self, key: str) -> None:
        """Handle keyboard navigation and mouse scroll."""
        if key in ("w", "up arrow", "a", "left arrow"):
            if self.state.select_prev():
                self._on_selection_changed()
        elif key in ("s", "down arrow", "d", "right arrow"):
            if self.state.select_next():
                self._on_selection_changed()
        elif key == "scroll up":
            if self.state.on_scroll(-1):
                self._on_selection_changed()
        elif key == "scroll down":
            if self.state.on_scroll(1):
                self._on_selection_changed()
        elif key in ("enter", "space"):
            if 0 <= self.state.selected_index < len(self.stages):
                self.on_pick(self.stages[self.state.selected_index])
        elif key == "escape":
            if self.on_back is not None:
                self.on_back()

    def teardown(self) -> None:
        """Destroy preview and scene graph entities."""
        self.preview.teardown()
        destroy(self)
