"""How far the camera must sit for the whole board to fit the window (no Ursina).

``PrototypeScene`` frames a board by taking the nominal distance for its grid, then projecting every
tile corner through the lens to see how much of the frame the footprint actually fills. This module
holds the rule that follows from that measurement: push the camera out until the board fits, at
whatever aspect ratio the window has *now*.

It is pure Python, like ``intro.py`` and ``layout.py``, because the rule is worth a headless test
(``tests/test_gui_framing.py``); the projection itself stays in ``app.py``, next to the camera it
needs.
"""

from __future__ import annotations

from collections.abc import Callable

# Fractions of the half-frame the board's outline may fill. This leaves the HUD's corners and the
# platform's own perspective depth some air, and it is measured on the worse edge of the outline:
# the pitch and yaw make the near edge project larger than the far one, so the board's projected
# centre is not the window's centre.
FIT_X = 0.86
FIT_Y = 0.92

# Projected size does not fall exactly with distance — the near edge of a yawed board grows faster
# than the far one — so the outline is measured again after each step instead of being solved in
# one. The ten stages need one or two measurements in practice; the budget is what bounds the work
# (and guarantees termination) when a board never fits.
MAX_STEPS = 10


def overflow(half_width: float, half_height: float) -> float:
    """How much too big the board is, in half-frames: 1.0 or less means it fits."""
    return max(half_width / FIT_X, half_height / FIT_Y)


def fitting_distance(measure: Callable[[float], tuple[float, float]], start: float) -> float:
    """The first distance at or beyond ``start`` that ``measure`` reports as fitting.

    ``measure(distance)`` returns the half-width and half-height of the board's projected outline
    in lens space, where the frame is ``[-1, 1]`` on both axes. The camera is only ever pushed out,
    never pulled in: a board that already fits keeps the framing its stage was built with, so the
    levels do not change size until a resize (or a board that never fitted) demands it.

    Each step scales the distance by the measured overflow, which lands on the target in one step
    when the outline falls as 1 / distance, and needs a few more when it does not. The result is
    always a distance the measurement accepted, so a caller can place the camera there and trust it.
    """
    distance = start
    for _ in range(MAX_STEPS):
        scale = overflow(*measure(distance))
        if scale <= 1.0:
            break
        distance *= scale
    return distance
