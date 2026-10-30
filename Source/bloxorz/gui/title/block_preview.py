"""The 3D rectangular player block preview for the title screen.

Presents a 1x1x2 standing block with clean cel-shading and distinct face tones.
"""

from __future__ import annotations

from ursina import Entity, color

from .bw_shader import BW_SHADER

# 1x2x1 standing block proportions in UI camera space
BLOCK_WIDTH = 0.15
BLOCK_HEIGHT = 0.30
BLOCK_DEPTH = 0.15

# Isometric three-quarter tilt so top, front, and side faces are all clearly visible
BLOCK_ROTATION = (26.0, -36.0, 12.0)


class TitleBlockPreview(Entity):
    """3D rectangular player block preview displayed during the title screen."""

    def __init__(self, parent: Entity) -> None:
        super().__init__(
            parent=parent,
            name="title_player_block",
            model="cube",
            scale=(BLOCK_WIDTH, BLOCK_HEIGHT, BLOCK_DEPTH),
            rotation=BLOCK_ROTATION,
            color=color.white,
            shader=BW_SHADER,
            z=-0.02,
            enabled=False,
        )
        self.base_scale = (BLOCK_WIDTH, BLOCK_HEIGHT, BLOCK_DEPTH)

    def set_pose(self, pos: tuple[float, float, float], scale_factor: float) -> None:
        """Update position and scale from animation timeline."""
        if scale_factor <= 0.001:
            self.enabled = False
            return

        self.enabled = True
        safe_factor = max(0.0001, scale_factor)
        self.position = (pos[0], pos[1], self.z)
        self.scale = (
            self.base_scale[0] * safe_factor,
            self.base_scale[1] * safe_factor,
            self.base_scale[2] * safe_factor,
        )
