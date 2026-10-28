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
    // Key directional light vector
    vec3 light_dir = normalize(vec3(0.3, 0.85, 0.5));
    float diff = max(dot(normalize(normal), light_dir), 0.0);
    // Softened face tone: compress contrast for an out-of-focus depth feel
    vec3 lit = mix(base.rgb * 0.82, base.rgb * 1.08, diff * 0.5 + 0.4);
    // Blend with atmospheric purple-slate backdrop (#46425e)
    vec3 haze = vec3(0.275, 0.259, 0.369);
    vec3 blended = mix(lit, haze, 0.22);
    fragColor = vec4(blended, base.a * 0.92);
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

