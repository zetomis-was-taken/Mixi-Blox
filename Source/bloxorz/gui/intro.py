"""Timeline for the stage-load animation.

The sequence is: every tile floats up from below the board (each with its own random delay), then
the player's block drops in from above. Only once the whole timeline has played may the game take
input.

Pure Python on purpose: the Ursina views ask this object how far along each piece is, so the
ordering and the input gate can be tested headless (``tests/test_gui_intro.py``) instead of by
watching the window. Durations and travel distances live here rather than in ``theme.py`` for the
same reason — this module must not import Ursina.
"""

from __future__ import annotations

import random
from dataclasses import dataclass


@dataclass(frozen=True)
class IntroTiming:
    """Durations (seconds) and travel distances (world units) of the load animation.

    ``tile_rise`` and ``player_drop`` are how far a piece travels before it lands. The scene passes
    one camera distance for both, so pieces start outside the window; the small defaults here are
    only what a headless test gets when it does not care about the visual travel.
    """

    tile_float_seconds: float = 1.0
    tile_delay_max_seconds: float = 0.55
    player_float_seconds: float = 1.0
    tile_rise: float = 3.0
    player_drop: float = 4.0


def _ease_out_cubic(t: float) -> float:
    """Fast start, gentle landing — reads as a float rather than a linear slide."""
    return 1.0 - (1.0 - t) ** 3


def _progress(elapsed: float, start: float, seconds: float) -> float:
    if seconds <= 0.0:
        return 1.0 if elapsed >= start else 0.0
    return _ease_out_cubic(min(max((elapsed - start) / seconds, 0.0), 1.0))


class LoadIntro:
    """Absolute-time timeline: tiles first, then the player, then input is allowed.

    Every tile gets its own random delay so the platform assembles instead of appearing all at
    once. ``seed`` makes those delays reproducible for tests; the game leaves it unset so each run
    looks slightly different.
    """

    def __init__(
        self,
        tile_count: int,
        timing: IntroTiming | None = None,
        seed: int | None = None,
    ) -> None:
        self.timing = timing or IntroTiming()
        rng = random.Random(seed)
        self._tile_delays = tuple(
            rng.uniform(0.0, self.timing.tile_delay_max_seconds) for _ in range(tile_count)
        )
        self._elapsed = 0.0

        # TODO(load-animation): obstacles (fragile panels, switches, teleporters, ...) get their
        # own phase between the last tile and the player once BoardView has dedicated entities for
        # them. For now the player follows the tiles directly.
        self._tiles_end = max(
            (delay + self.timing.tile_float_seconds for delay in self._tile_delays),
            default=0.0,
        )
        self._player_start = self._tiles_end
        self._duration = self._player_start + self.timing.player_float_seconds

    @property
    def duration(self) -> float:
        """Total length of the animation, in seconds."""
        return self._duration

    @property
    def elapsed(self) -> float:
        return self._elapsed

    @property
    def finished(self) -> bool:
        """Whether the animation has fully played; the scene holds input until it has."""
        return self._elapsed >= self._duration

    def advance(self, dt: float) -> None:
        self._elapsed = min(self._elapsed + dt, self._duration)

    def tile_progress(self, index: int) -> float:
        """Eased 0..1 float-up progress of tile ``index``, in build order."""
        return _progress(self._elapsed, self._tile_delays[index], self.timing.tile_float_seconds)

    def player_progress(self) -> float:
        """Eased 0..1 drop-in of the player's block; stays 0 until the tiles have landed."""
        return _progress(self._elapsed, self._player_start, self.timing.player_float_seconds)
