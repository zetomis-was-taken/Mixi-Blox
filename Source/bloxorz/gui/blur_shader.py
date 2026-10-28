"""GLSL blur and depth-softening shader for the 3D board preview.

Softens face edges, blends highlights, and casts a frosted atmospheric tone over preview
board entities without requiring expensive multi-pass offscreen framebuffers.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from ursina import Shader

if TYPE_CHECKING:
    from .board_view import BoardView

_VERTEX = """#version 130
uniform mat4 p3d_ModelViewProjectionMatrix;
uniform mat3 p3d_NormalMatrix;
in vec4 p3d_Vertex;
in vec3 p3d_Normal;
in vec2 p3d_MultiTexCoord0;
in vec4 p3d_Color;
out vec2 texcoords;
out vec4 vertex_color;
out vec3 normal;

void main() {
    gl_Position = p3d_ModelViewProjectionMatrix * p3d_Vertex;
    texcoords = p3d_MultiTexCoord0;
    vertex_color = p3d_Color;
    normal = normalize(p3d_NormalMatrix * p3d_Normal);
}
"""

_FRAGMENT = """#version 140
uniform sampler2D p3d_Texture0;
uniform vec4 p3d_ColorScale;
in vec2 texcoords;
in vec4 vertex_color;
in vec3 normal;
out vec4 fragColor;

void main() {
    vec4 base = texture(p3d_Texture0, texcoords) * p3d_ColorScale * vertex_color;
    vec3 n = normalize(normal);
    vec3 light_dir = normalize(vec3(0.25, 0.85, 0.45));
    float diff = max(dot(n, light_dir), 0.0);
    float top_face = max(n.y, 0.0);

    // Identify special pieces (fragile tiles, bridges, switch plates, active block)
    // which have higher saturation or brightness than the muted slate floor (#46425e).
    float max_c = max(base.r, max(base.g, base.b));
    float min_c = min(base.r, min(base.g, base.b));
    float sat = max_c - min_c;
    bool is_special = (sat > 0.18) || (max_c > 0.70);

    vec3 final_color;
    if (is_special) {
        // Make special mechanisms and plates strikingly vibrant and luminous
        vec3 boosted = base.rgb * (1.20 + 0.25 * diff + 0.18 * top_face);
        final_color = min(boosted, vec3(1.0));
    } else {
        // Standard floor tiles: crisp cel shading for clear 3D footprint separation
        vec3 lit = base.rgb * (0.92 + 0.40 * diff + 0.25 * top_face);
        vec3 haze = vec3(0.275, 0.259, 0.369);
        final_color = mix(lit, haze, 0.06);
    }

    fragColor = vec4(final_color, 1.0);
}
"""

BLUR_SHADER = Shader(
    name="preview_blur",
    language=Shader.GLSL,
    vertex=_VERTEX,
    fragment=_FRAGMENT,
)


def apply(board_view: BoardView) -> None:
    """Give all physical tiles, bases, and switch details the softened preview shader."""
    for entity in board_view.object_entities():
        entity.shader = BLUR_SHADER
    for line in board_view.lines:
        line.shader = BLUR_SHADER

