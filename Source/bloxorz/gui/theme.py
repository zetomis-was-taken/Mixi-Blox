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

# Parallax background squares: the deep teal, drawn at a low opacity by ``parallax.py``.
PARALLAX_SQUARE = color.rgb32(21, 120, 140)  # #15788c

# Grid separator: a faint translucent line where two tiles meet. Tiles butt against each other,
# so this line — not a gap — is what separates them.
GRID_LINE = color.rgba32(21, 120, 140, 90)  # #15788c at ~35% opacity
GRID_LINE_WIDTH = 0.02
GRID_LINE_HEIGHT = 0.004
GRID_LINE_LIFT = 0.002

BLOCK = color.rgb32(255, 105, 115)  # #ff6973
# The cube that is *not* taking input after a split: the same warmth one step quieter, so the pair
# still reads as one player while the active cube keeps the strong accent.
BLOCK_IDLE = color.rgb32(255, 176, 163)  # #ffb0a3

# Menu screens: the win overlay is a nearly opaque cream card so the solved board stays visible
# behind it at the edges, and its buttons use the same dark/cyan pairing as the level select.
OVERLAY_PANEL = color.rgba32(255, 238, 204, 238)  # #ffeecc at ~93% opacity

# Total platform thickness and the thickness of the coloured slab on top of the side base.
TILE_HEIGHT = 0.30
TILE_CAP_HEIGHT = 0.03

# Details sit just above the tile's top face so they never z-fight with it.
TRIM_HEIGHT = 0.04
TRIM_LIFT = 0.005

# Mechanism reactions. A switch plate sinks while the block bears on it, a fragile crack opens as
# the panel takes weight, and a bridge eases between its two heights — its tint follows the height,
# so a moving bridge is one moving object rather than a colour and a body that disagree.
PRESS_DEPTH = 0.03  # how far a plate sinks under the block, in world units
PRESS_SECONDS = 0.08  # travel time for a plate, pressed or released
BRIDGE_SECONDS = 0.18  # travel time for a bridge between open and closed
CRACK_OPEN = 0.8  # extra crack depth at full load, as a fraction of the slot's depth

# One quarter-turn per action, at a constant angular speed so the block visibly rolls.
ROLL_SECONDS = 0.22
