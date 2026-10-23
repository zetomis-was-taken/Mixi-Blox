"""Palette for the prototype, drawn from the project's "curiosities" palette.

The assignment of every colour to a cell kind, and the reasoning behind it, is in
``docs/gui/theme.md``; this module is the only place the values appear. Every entity uses
``unlit_shader``, so a colour is exactly the RGB written here — no lighting brightens or shades it.

The goal is not drawn at all (the cream background shows through, as a hole would), and the start
is an ordinary tile. The remaining kinds share the palette's accents and are told apart by their
detail piece (see ``DETAILS`` in ``board_view.py``).

Values are 0-255 through ``color.rgb32``; ``color.rgb`` expects 0-1 floats.
"""

from __future__ import annotations

from ursina import color

BACKGROUND = color.rgb32(255, 238, 204)  # #ffeecc
TEXT = color.rgb32(70, 66, 94)  # #46425e

# Board tiles. Floor and start are the same ordinary tile; the goal gets no tile at all.
TILE_FLOOR = color.rgb32(70, 66, 94)  # #46425e
TILE_FRAGILE = color.rgb32(255, 176, 163)  # #ffb0a3
TILE_BRIDGE = color.rgb32(0, 185, 190)  # #00b9be
TILE_SOFT = color.rgb32(0, 185, 190)  # #00b9be
TILE_HEAVY = color.rgb32(21, 120, 140)  # #15788c
TILE_SPLIT = color.rgb32(0, 185, 190)  # #00b9be

# Each tile is a thin top slab over a base in the normal tile colour, so the platform reads as a
# thick block at its outer edges.
TILE_SIDE = color.rgb32(70, 66, 94)  # #46425e, the same as TILE_FLOOR

# Detail pieces: switch plates and fragile cracks.
TILE_MARK = color.rgb32(255, 238, 204)  # #ffeecc
TILE_MARK_DARK = color.rgb32(70, 66, 94)  # #46425e

# Grid separator: a faint translucent line where two tiles meet. Tiles butt against each other,
# so this line — not a gap — is what separates them.
GRID_LINE = color.rgba32(21, 120, 140, 90)  # #15788c at ~35% opacity
GRID_LINE_WIDTH = 0.02
GRID_LINE_HEIGHT = 0.004
GRID_LINE_LIFT = 0.002

BLOCK = color.rgb32(255, 105, 115)  # #ff6973

# Total platform thickness and the thickness of the coloured slab on top of the side base.
TILE_HEIGHT = 0.30
TILE_CAP_HEIGHT = 0.03

# Details sit just above the tile's top face so they never z-fight with it.
TRIM_HEIGHT = 0.04
TRIM_LIFT = 0.005

# One quarter-turn per action, at a constant angular speed so the block visibly rolls.
ROLL_SECONDS = 0.22
