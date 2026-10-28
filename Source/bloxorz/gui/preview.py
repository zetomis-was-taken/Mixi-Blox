"""3D Board preview panel for the level select screen.

Presents an angled, softened isometric preview of the highlighted stage with smooth
crossfades, offscreen caching, and a loading spinner.
"""

from __future__ import annotations

from ursina import Entity, color, destroy, time

from bloxorz.core.contracts import Stage

from . import blur_shader, theme
from .board_view import BoardView
from .layout import board_center

# Isometric preview tilt angles (pitch, yaw, roll)
PREVIEW_ROTATION = (32.0, -36.0, 12.0)
PREVIEW_CENTER_X = 0.32
PREVIEW_CENTER_Y = -0.04
FADE_DURATION_SECONDS = 0.30
SPINNER_FADE_SECONDS = 0.20


def _ease_out_cubic(t: float) -> float:
    return 1.0 - (1.0 - t) ** 3


class LevelPreviewPanel(Entity):
    """Container managing the 3D board preview, caching, and crossfade transitions."""

    def __init__(self, parent: Entity) -> None:
        super().__init__(
            parent=parent,
            name="level_preview_panel",
            position=(PREVIEW_CENTER_X, PREVIEW_CENTER_Y, -0.01),
        )

        # Angled divider backdrop representing the diagonal split (Layer B)
        self.backdrop = Entity(
            parent=self,
            model="quad",
            scale=(1.25, 1.15),
            position=(0.04, -0.02, 0.02),
            rotation_z=-14.0,
            color=color.rgba32(21, 120, 140, 45),  # subtle deep teal shadow (#15788c)
        )

        # Content root that holds rotated 3D preview models
        self.content_root = Entity(
            parent=self,
            rotation=PREVIEW_ROTATION,
            position=(0.0, 0.0, -0.01),
        )

        # Loading spinner
        self.spinner = Entity(
            parent=self,
            model="quad",
            scale=(0.04, 0.04),
            color=theme.BLOCK,
            z=-0.04,
            enabled=False,
        )

        self._cache: dict[str, tuple[BoardView, Entity, float]] = {}
        self.current_stage_id: str | None = None
        self._fading = False
        self._fade_elapsed = 0.0
        self._current_base_scale = 1.0

    def set_stage(self, stage: Stage) -> None:
        """Switch preview to the specified stage, utilizing cached views when available."""
        if stage.id == self.current_stage_id:
            return

        # Hide current active preview wrapper
        if self.current_stage_id is not None and self.current_stage_id in self._cache:
            _, prev_wrapper, _ = self._cache[self.current_stage_id]
            prev_wrapper.enabled = False

        self.current_stage_id = stage.id

        if stage.id in self._cache:
            _, wrapper, base_scale = self._cache[stage.id]
            wrapper.enabled = True
            self._current_base_scale = base_scale
            self._start_crossfade()
        else:
            self._build_preview(stage)

    def _build_preview(self, stage: Stage) -> None:
        """Construct a new BoardView, position and center it, and apply blur shader."""
        wrapper = Entity(parent=self.content_root, name=f"preview_wrap_{stage.id}")
        board_view = BoardView(stage)
        board_view.root.parent = wrapper

        # Center the board footprint over the rotation pivot
        cx, cz = board_center(stage)
        board_view.root.position = (-cx, 0.0, -cz)

        # Scale dynamically so large and small boards fit the preview window
        span = max(stage.index.rows, stage.index.cols, 8)
        base_scale = 0.28 / span
        wrapper.scale = (base_scale, base_scale, base_scale)

        # Apply soft preview shader
        blur_shader.apply(board_view)

        self._cache[stage.id] = (board_view, wrapper, base_scale)
        self._current_base_scale = base_scale
        self._start_crossfade()

    def _start_crossfade(self) -> None:
        """Initiate the smooth ease-out entrance animation."""
        self._fading = True
        self._fade_elapsed = 0.0
        self.spinner.enabled = False

    def update(self) -> None:
        """Drive spinner rotation and preview entrance crossfade."""
        dt = time.dt
        if self.spinner.enabled:
            self.spinner.rotation_z += 360.0 * dt

        if self._fading and self.current_stage_id in self._cache:
            self._fade_elapsed += dt
            t = min(1.0, self._fade_elapsed / FADE_DURATION_SECONDS)
            progress = _ease_out_cubic(t)

            _, wrapper, base_scale = self._cache[self.current_stage_id]
            # Subtle scale ease (0.94 -> 1.0) for a tactile pop-in feel
            cur_scale = base_scale * (0.94 + 0.06 * progress)
            wrapper.scale = (cur_scale, cur_scale, cur_scale)

            if t >= 1.0:
                self._fading = False

    def teardown(self) -> None:
        """Clean up all cached views and entities."""
        self._cache.clear()
        destroy(self)

