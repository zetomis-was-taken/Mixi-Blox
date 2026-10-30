"""The title screen scene orchestrator.

Implements keyframe animations, dark slate aesthetic, custom text-only hover buttons,
and 3D player block preview with clean cel-shading.
"""

from __future__ import annotations

from collections.abc import Callable

from ursina import Entity, Text, application, camera, color, destroy, time, window

from . import timeline
from .block_preview import TitleBlockPreview
from .fonts import get_font, setup_text_sharpness
from .menu_item import TitleMenuItem

COLOR_BG = color.hex("#46425E")
COLOR_TITLE_FG = color.hex("#FFEECC")
COLOR_HINT = color.hex("#80C2CC")


class TitleScene(Entity):
    """The animated boot screen: wordmark, 3D player block, and responsive menu items."""

    def __init__(self, on_play: Callable[[], None]) -> None:
        super().__init__(name="title", parent=camera.ui)
        self.on_play = on_play
        self.elapsed = 0.0
        window.title = "Mixi-Blox  |  title"

        # Full-screen dark backdrop
        self.backdrop = Entity(
            parent=self,
            model="quad",
            scale=(3.0, 2.0),
            color=COLOR_BG,
            z=0.08,
        )

        font_title = get_font("Monoton-Regular.ttf")
        font_hint = get_font("PlusJakartaSans-ExtraBold.ttf")

        # Monumental, razor-sharp bold title in Monoton display font
        self.title_label = Text(
            parent=self,
            text="MixiBlox",
            font=font_title,
            scale=4.5,
            origin=(-0.5, 0.0),
            position=(timeline.OFFSCREEN_LEFT_X, timeline.TITLE_TARGET_Y, -0.002),
            color=COLOR_TITLE_FG,
        )
        setup_text_sharpness(self.title_label, point_size=20.0, pixels_per_unit=120.0)

        # 3D Rectangular player block with clean cel-shading
        self.block_preview = TitleBlockPreview(parent=self)
        self.block_preview.set_pose(timeline.BLOCK_INIT_POS, 0.0)

        # Custom text-only menu items
        self.play_item = TitleMenuItem(
            parent=self,
            text="PLAY",
            on_click=self.on_play,
            y=timeline.PLAY_TARGET_Y,
        )
        self.play_item.x = timeline.OFFSCREEN_LEFT_X

        self.quit_item = TitleMenuItem(
            parent=self,
            text="QUIT",
            on_click=application.quit,
            y=timeline.QUIT_TARGET_Y,
        )
        self.quit_item.x = timeline.OFFSCREEN_LEFT_X

        # Footer keyboard hints
        self.hint_label = Text(
            parent=self,
            text="ENTER play      ESC quit",
            font=font_hint,
            scale=0.55,
            origin=(-0.5, 0.0),
            position=(timeline.ANCHOR_LEFT_X, -0.42, -0.002),
            color=COLOR_HINT,
        )
        setup_text_sharpness(self.hint_label, point_size=24.0, pixels_per_unit=120.0)

    def update(self) -> None:
        """Drive keyframe animations across the opening sequence."""
        self.elapsed += time.dt

        # Keyframe 1: Title position
        title_x = timeline.title_position(self.elapsed)[0]
        self.title_label.x = title_x

        # Keyframes 1 & 2: 3D Player Block position & scale
        block_pos = timeline.player_block_position(self.elapsed)
        block_scale = timeline.player_block_scale(self.elapsed)
        self.block_preview.set_pose(block_pos, block_scale)

        # Keyframe 3: Staggered menu item entrances
        self.play_item.x = timeline.play_button_x(self.elapsed)
        self.quit_item.x = timeline.quit_button_x(self.elapsed)

        # Enable interaction once ready
        if timeline.is_interactive(self.elapsed):
            self.play_item.interactive = True
            self.quit_item.interactive = True

    def input(self, key: str) -> None:
        """Keyboard routes through the title menu."""
        if key == "enter":
            self.on_play()
        elif key == "escape":
            application.quit()

    def teardown(self) -> None:
        """Clean up all title screen entities."""
        destroy(self)
