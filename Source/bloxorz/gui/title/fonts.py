"""Font loader and resolution utilities for Panda3D / Ursina compatibility.

Names a bundled font the way Ursina resolves one, and configures DynamicTextFont
sharpness safely using clear() before modifying point size or pixels per unit.
"""

from __future__ import annotations

from pathlib import Path

# Panda3D packs each DynamicTextFont's glyphs into a texture page; the default is
# 256x256, too small for the high pixels-per-unit values used on the title screen.
GLYPH_PAGE_SIZE = 1024


def get_font_path(filename: str) -> str:
    """Name a bundled font so Ursina's text search finds it.

    ``Text.font`` resolves its value with ``folder.glob(f"**/{name}")`` across the asset
    folders, so a bare file name is what it expects: the name it is given is a glob pattern,
    not a path, and neither an OS path nor a Panda3D VFS path (``/d/...``) matches anything.
    The name only expands correctly when the file exists, so the check stays here.
    """
    if not (Path(__file__).parents[2] / "fonts" / filename).is_file():
        raise FileNotFoundError(f"bundled font is missing: {filename}")
    return filename


get_font = get_font_path


def setup_text_sharpness(
    text_entity, point_size: float = 48.0, pixels_per_unit: float = 240.0
) -> None:
    """Configure DynamicTextFont rasterization for crisp, high-DPI rendering.

    Calls clear() prior to setPointSize and setPixelsPerUnit to satisfy Panda3D's
    internal `get_num_pages() == 0` assertion. A larger glyph page is needed because
    high pixels-per-unit values produce glyphs that no longer fit the default 256x256.
    """
    try:
        font = getattr(text_entity, "_font", None)
        if font is not None:
            # Panda keeps a space at the advance it had at its default point size however far the
            # point size grows, so a space shrinks to a tenth of a letter and words run together.
            # Scaling it by the same factor as the point size keeps the font's own proportions.
            space_advance = font.getSpaceAdvance() * point_size / max(font.getPointSize(), 1.0)
            if hasattr(font, "clear"):
                font.clear()
            if hasattr(font, "setPageSize"):
                font.setPageSize((GLYPH_PAGE_SIZE, GLYPH_PAGE_SIZE))
            if hasattr(font, "setPointSize"):
                font.setPointSize(point_size)
            if hasattr(font, "setPixelsPerUnit"):
                font.setPixelsPerUnit(pixels_per_unit)
            if hasattr(font, "setSpaceAdvance"):
                font.setSpaceAdvance(space_advance)
            if hasattr(text_entity, "raw_text") and text_entity.raw_text:
                text_entity.text = text_entity.raw_text
    except Exception:
        pass
