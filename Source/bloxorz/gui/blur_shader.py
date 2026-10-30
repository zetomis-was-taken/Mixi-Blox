"""Discrete 3D Geometric Face Shader for the level preview.

Uses mesh normal directly to provide guaranteed bright, vibrant top-surface illumination
and clean dimensional edge shading regardless of camera orientation or projection mode.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from ursina import Shader

if TYPE_CHECKING:
    from .board_view import BoardView

_VERTEX = """#version 130
uniform mat4 p3d_ModelViewProjectionMatrix;
in vec4 p3d_Vertex;
in vec3 p3d_Normal;
in vec2 p3d_MultiTexCoord0;
in vec4 p3d_Color;
out vec2 texcoords;
out vec4 vertex_color;
out vec3 model_normal;

void main() {
    gl_Position = p3d_ModelViewProjectionMatrix * p3d_Vertex;
    texcoords = p3d_MultiTexCoord0;
    vertex_color = p3d_Color;
    model_normal = p3d_Normal;
}
"""

_FRAGMENT = """#version 140
uniform sampler2D p3d_Texture0;
uniform vec4 p3d_ColorScale;
in vec2 texcoords;
in vec4 vertex_color;
in vec3 model_normal;
out vec4 fragColor;

void main() {
    vec4 base = texture(p3d_Texture0, texcoords) * p3d_ColorScale * vertex_color;

    // Geometric face shading:
    // Top face is illuminated with vibrant clarity so tile colors and markers stand out.
    // Front and side faces receive distinct shading for crisp 3D volume.
    float factor;
    if (model_normal.y > 0.5) {
        factor = 1.30;
    } else if (model_normal.z < -0.5 || model_normal.x > 0.5) {
        factor = 0.85;
    } else {
        factor = 0.58;
    }

    vec3 tone = min(base.rgb * factor, vec3(1.0));
    fragColor = vec4(tone, base.a);
}
"""

PREVIEW_CEL_SHADER = Shader(
    name="preview_geometric_cel",
    language=Shader.GLSL,
    vertex=_VERTEX,
    fragment=_FRAGMENT,
)

# Backwards compatibility alias
BLUR_SHADER = PREVIEW_CEL_SHADER


def apply(board_view: BoardView) -> None:
    """Give all physical tiles, bases, and switch details the cel shader."""
    for entity in board_view.object_entities():
        entity.shader = PREVIEW_CEL_SHADER
    for line in board_view.lines:
        line.shader = PREVIEW_CEL_SHADER
