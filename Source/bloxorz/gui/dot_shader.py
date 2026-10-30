"""Dotted halftone shader for the physical objects on screen.

A flat-colour variant of ``unlit_shader``: the fragment keeps the entity's own colour and darkens
a regular grid of dots in screen space. Because the dots are computed in screen space they stay the
same size on every surface, whether it is a tile, a switch plate or the player's block.

Only the board and the player are given this shader — never the background, the grid lines or the
HUD. Call :func:`apply` once in ``app.PrototypeScene`` to switch the look on; remove the call to
turn it off. The shader is kept on ``BlockView`` so blocks rebuilt after a move keep it too.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from ursina import Shader

if TYPE_CHECKING:
    from .block_view import BlockView
    from .board_view import BoardView

# Screen-space dots: spacing and radius in pixels, and the factor the entity's colour is
# multiplied by at the centre of a dot. A high factor keeps the pattern subtle on the flat tiles.
DOT_SPACING_PIXELS = 7.0
DOT_RADIUS_PIXELS = 1.2
DOT_DARKNESS = 0.82

_VERTEX = """#version 130
uniform mat4 p3d_ModelViewProjectionMatrix;
in vec4 p3d_Vertex;
in vec2 p3d_MultiTexCoord0;
in vec4 p3d_Color;
out vec2 texcoords;
out vec4 vertex_color;

void main() {
    gl_Position = p3d_ModelViewProjectionMatrix * p3d_Vertex;
    texcoords = p3d_MultiTexCoord0;
    vertex_color = p3d_Color;
}
"""

_FRAGMENT = """#version 140
uniform sampler2D p3d_Texture0;
uniform vec4 p3d_ColorScale;
uniform float dot_spacing;
uniform float dot_radius;
uniform float dot_darkness;
in vec2 texcoords;
in vec4 vertex_color;
out vec4 fragColor;

void main() {
    vec4 base = texture(p3d_Texture0, texcoords) * p3d_ColorScale * vertex_color;
    vec2 within_cell = fract(gl_FragCoord.xy / dot_spacing) - vec2(0.5);
    float distance_pixels = length(within_cell) * dot_spacing;
    float dot = 1.0 - smoothstep(dot_radius - 1.0, dot_radius, distance_pixels);
    base.rgb *= mix(1.0, dot_darkness, dot);
    fragColor = base;
}
"""

DOTTED_SHADER = Shader(
    name="dotted",
    language=Shader.GLSL,
    vertex=_VERTEX,
    fragment=_FRAGMENT,
    default_input={
        "dot_spacing": DOT_SPACING_PIXELS,
        "dot_radius": DOT_RADIUS_PIXELS,
        "dot_darkness": DOT_DARKNESS,
    },
)


def apply(board_view: BoardView, block_view: BlockView) -> None:
    """Give the board's objects and the player the dotted look.

    ``BlockView`` rebuilds its boxes on every move, so the shader is also stored on the view for
    the pieces it creates later.
    """
    for entity in board_view.object_entities():
        entity.shader = DOTTED_SHADER
    block_view.shader = DOTTED_SHADER
    for piece in block_view.pieces:
        piece.shader = DOTTED_SHADER
