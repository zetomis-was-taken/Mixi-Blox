"""How a finished level is reported: the numbers the win overlay puts on screen.

Pure Python, so the formatting is tested headless while ``win_overlay.py`` only draws it.
"""

from __future__ import annotations


def elapsed_label(seconds: float) -> str:
    """``m:ss`` for the level clock, truncated to whole seconds."""
    minutes, remainder = divmod(max(int(seconds), 0), 60)
    return f"{minutes}:{remainder:02d}"


def result_line(moves: int, seconds: float) -> str:
    """The one line the overlay and the HUD show: the cost of the level so far."""
    noun = "move" if moves == 1 else "moves"
    return f"{moves} {noun}   |   {elapsed_label(seconds)}"
