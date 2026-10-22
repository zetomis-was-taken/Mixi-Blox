"""Neutral placeholder palette for the prototype.

TODO: ``theme.md`` will define the real art direction. Until then these are deliberately flat,
near-monochrome greys with no gradients, lighting or decorative accents, so the theme can replace
this module cleanly instead of fighting guesses made here.

Values are 0-255 through ``color.rgb32``; ``color.rgb`` expects 0-1 floats.
"""

from __future__ import annotations

from ursina import color

BACKGROUND = color.rgb32(24, 25, 27)

TILE_FLOOR = color.rgb32(70, 73, 78)
TILE_START = color.rgb32(98, 102, 108)
TILE_GOAL = color.rgb32(158, 163, 168)
TILE_FRAGILE = color.rgb32(86, 86, 86)
TILE_BRIDGE = color.rgb32(116, 119, 123)
TILE_SWITCH = color.rgb32(132, 135, 139)

BLOCK = color.rgb32(214, 216, 218)
TEXT = color.rgb32(176, 179, 184)

TILE_HEIGHT = 0.18
TILE_GAP = 0.04

# One quarter-turn per action, at a constant angular speed so the block visibly rolls.
ROLL_SECONDS = 0.22
