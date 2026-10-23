"""Parallax background: tiled square grids drifting from the top left to the bottom right.

Two quads are attached to the camera, one at each depth, and a small fragment shader paints a
regular checkerboard of squares onto them: filled cells and outlined cells alternate in `#15788c`.
The nearer layer has larger cells and scrolls faster than the far one, so the two layers separate
the way a parallax backdrop does.

The pattern is computed in screen space from ``gl_FragCoord``, so the cell size is stated in pixels
and a window resize never needs a rebuild; each frame only advances the scroll offsets and refits
the quads to the camera frustum. The quads sit well behind the board, so the board occludes them.

Construct :class:`ParallaxBackground` once to enable the effect; remove that line to turn it off.
"""

from __future__ import annotations

from dataclasses import dataclass
from math import radians, tan

from ursina import Entity, Shader, camera, color, time

from . import theme


# Cells and scroll speed are in screen pixels per second; the far layer is smaller and slower,
# which is what makes the depth read. ``alpha`` is the opacity of the layer's squares.
@dataclass(frozen=True)
class _Layer:
    depth: float
    cell_pixels: float
    speed_pixels: float
    alpha: float


LAYERS: tuple[_Layer, ...] = (
    _Layer(depth=60.0, cell_pixels=96.0, speed_pixels=15.0, alpha=0.15),
    _Layer(depth=120.0, cell_pixels=64.0, speed_pixels=7.5, alpha=0.10),
)

# Fraction of a cell taken by an outlined cell's border, and the extra quad size that keeps the
# pattern covering the window despite the camera's small lens shift.
BORDER_FRACTION = 0.06
QUAD_MARGIN = 1.15

_VERTEX = """#version 130
uniform mat4 p3d_ModelViewProjectionMatrix;
in vec4 p3d_Vertex;
in vec4 p3d_Color;
out vec4 vertex_color;

void main() {
    gl_Position = p3d_ModelViewProjectionMatrix * p3d_Vertex;
    vertex_color = p3d_Color;
}
"""

_FRAGMENT = """#version 140
uniform vec4 p3d_ColorScale;
uniform vec2 cell_size;
uniform vec2 scroll;
uniform float border_fraction;
in vec4 vertex_color;
out vec4 fragColor;

void main() {
    vec2 pixel = gl_FragCoord.xy + scroll;
    vec2 cell = floor(pixel / cell_size);
    vec2 within = fract(pixel / cell_size);

    float filled = mod(cell.x + cell.y, 2.0);
    float edge = step(within.x, border_fraction) + step(1.0 - border_fraction, within.x)
               + step(within.y, border_fraction) + step(1.0 - border_fraction, within.y);
    float visible = mix(min(edge, 1.0), 1.0, filled);

    if (visible < 0.5) {
        discard;
    }
    fragColor = p3d_ColorScale * vertex_color;
}
"""

_SQUARE_SHADER = Shader(
    name="parallax_square",
    language=Shader.GLSL,
    vertex=_VERTEX,
    fragment=_FRAGMENT,
)


@dataclass
class _LayerView:
    """One layer's quad plus the scroll that moves its pattern."""

    quad: Entity
    layer: _Layer
    scroll_x: float = 0.0
    scroll_y: float = 0.0


class ParallaxBackground(Entity):
    """A camera-attached backdrop of scrolling square grids; updates itself every frame."""

    def __init__(self) -> None:
        super().__init__(parent=camera, name="parallax")
        self.layers = [self._build_layer(layer) for layer in LAYERS]
        self._fit_quads()

    def _build_layer(self, layer: _Layer) -> _LayerView:
        quad = Entity(
            parent=self,
            name=f"parallax-{layer.depth:g}",
            model="quad",
            color=color.rgba(
                theme.PARALLAX_SQUARE[0],
                theme.PARALLAX_SQUARE[1],
                theme.PARALLAX_SQUARE[2],
                layer.alpha,
            ),
            position=(0.0, 0.0, layer.depth),
            shader=_SQUARE_SHADER,
            double_sided=True,
        )
        quad.set_shader_input(
            "cell_size", (layer.cell_pixels, layer.cell_pixels)
        )
        quad.set_shader_input("scroll", (0.0, 0.0))
        quad.set_shader_input("border_fraction", BORDER_FRACTION)
        return _LayerView(quad=quad, layer=layer)

    def _fit_quads(self) -> None:
        """Scale each quad to cover the viewport at its depth, even after a resize."""
        half_width = tan(radians(camera.fov) / 2.0)
        for view in self.layers:
            half_height = half_width / camera.aspect_ratio
            view.quad.scale = (
                2.0 * half_width * view.layer.depth * QUAD_MARGIN,
                2.0 * half_height * view.layer.depth * QUAD_MARGIN,
            )

    def update(self) -> None:
        self._fit_quads()
        for view in self.layers:
            # Right and down on screen. The pattern is sampled from ``gl_FragCoord + scroll``,
            # so increasing x and decreasing y is what moves the squares in that direction.
            view.scroll_x -= view.layer.speed_pixels * time.dt
            view.scroll_y += view.layer.speed_pixels * time.dt
            view.quad.set_shader_input("scroll", (view.scroll_x, view.scroll_y))
