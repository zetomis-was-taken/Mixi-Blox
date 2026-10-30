"""Clean 3D Cel-Shaded Monochrome Shader for the title screen player block.

Renders sharp, distinct flat tones across the three visible faces without dot grids,
guaranteeing a bold, solid three-dimensional block silhouette.
"""

from __future__ import annotations

from ursina import Shader

_VERTEX = """#version 130
uniform mat4 p3d_ModelViewProjectionMatrix;
uniform mat3 p3d_NormalMatrix;
in vec4 p3d_Vertex;
in vec3 p3d_Normal;
in vec2 p3d_MultiTexCoord0;
in vec4 p3d_Color;
out vec2 texcoords;
out vec4 vertex_color;
out vec3 eye_normal;

void main() {
    gl_Position = p3d_ModelViewProjectionMatrix * p3d_Vertex;
    texcoords = p3d_MultiTexCoord0;
    vertex_color = p3d_Color;
    eye_normal = normalize(p3d_NormalMatrix * p3d_Normal);
}
"""

_FRAGMENT = """#version 140
uniform sampler2D p3d_Texture0;
uniform vec4 p3d_ColorScale;
in vec2 texcoords;
in vec4 vertex_color;
in vec3 eye_normal;
out vec4 fragColor;

void main() {
    vec3 n = normalize(eye_normal);
    // Key directional light vector aimed from top-front
    vec3 light_dir = normalize(vec3(0.25, 0.85, 0.45));
    float diff = dot(n, light_dir);

    // Discrete 3-tier cel shading for clean, sharp face separation
    vec3 tone;
    if (diff > 0.55) {
        // Top face: Pure highlight white
        tone = vec3(1.0, 1.0, 1.0);
    } else if (diff > 0.05) {
        // Front face: Crisp modern silver gray
        tone = vec3(0.82, 0.82, 0.86);
    } else {
        // Side face: Deep graphic ink slate
        tone = vec3(0.16, 0.15, 0.22);
    }

    fragColor = vec4(tone, 1.0);
}
"""

BW_SHADER = Shader(
    name="clean_cel_shading",
    language=Shader.GLSL,
    vertex=_VERTEX,
    fragment=_FRAGMENT,
)
