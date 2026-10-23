"""Headless checks for the stage-load timeline.

Ursina is never imported here: ``LoadIntro`` is pure Python and the views only read progress from
it, so the ordering (tiles, then obstacles, then the player) and the input gate are testable in CI.
"""

from __future__ import annotations

from bloxorz.gui.intro import IntroTiming, LoadIntro

TIMING = IntroTiming(
    tile_float_seconds=0.2,
    tile_delay_max_seconds=0.4,
    player_float_seconds=0.3,
    tile_rise=3.0,
    player_drop=4.0,
)


def _run(intro: LoadIntro, seconds: float, steps: int = 200) -> None:
    for _ in range(steps):
        intro.advance(seconds / steps)


def test_each_tile_gets_a_random_delay() -> None:
    intro = LoadIntro(12, timing=TIMING, seed=7)
    assert [intro.tile_progress(index) for index in range(12)] == [0.0] * 12

    intro.advance(0.12)
    progress = [intro.tile_progress(index) for index in range(12)]
    # Randomised delays stagger the tiles instead of popping them all in together.
    assert any(value > 0.0 for value in progress)
    assert any(value == 0.0 for value in progress)
    assert len(set(progress)) > 1


def test_same_seed_reproduces_the_stagger() -> None:
    first = LoadIntro(8, timing=TIMING, seed=3)
    second = LoadIntro(8, timing=TIMING, seed=3)
    other = LoadIntro(8, timing=TIMING, seed=4)
    first.advance(0.15)
    second.advance(0.15)
    other.advance(0.15)
    assert [first.tile_progress(index) for index in range(8)] == [
        second.tile_progress(index) for index in range(8)
    ]
    assert [first.tile_progress(index) for index in range(8)] != [
        other.tile_progress(index) for index in range(8)
    ]


def test_tiles_land_before_the_player_starts_falling() -> None:
    intro = LoadIntro(10, timing=TIMING, seed=1)
    player_start = intro.duration - TIMING.player_float_seconds

    intro.advance(player_start - 1e-6)
    assert all(intro.tile_progress(index) > 0.0 for index in range(10))
    assert intro.player_progress() == 0.0
    assert intro.finished is False

    intro.advance(TIMING.player_float_seconds / 2.0)
    assert all(intro.tile_progress(index) == 1.0 for index in range(10))
    assert 0.0 < intro.player_progress() < 1.0
    assert intro.finished is False


def test_input_is_only_allowed_when_the_animation_has_fully_played() -> None:
    intro = LoadIntro(5, timing=TIMING, seed=2)
    assert intro.finished is False

    _run(intro, intro.duration - 1e-6, steps=100)
    assert intro.finished is False

    intro.advance(1e-3)
    assert intro.finished is True
    assert all(intro.tile_progress(index) == 1.0 for index in range(5))
    assert intro.player_progress() == 1.0


def test_progress_is_monotonic_and_eased() -> None:
    intro = LoadIntro(4, timing=TIMING, seed=5)
    previous = [0.0] * 4
    previous_player = 0.0
    for _ in range(60):
        intro.advance(intro.duration / 60.0)
        for index in range(4):
            current = intro.tile_progress(index)
            assert previous[index] <= current <= 1.0
            previous[index] = current
        player = intro.player_progress()
        assert previous_player <= player <= 1.0
        previous_player = player

    # Ease-out: the first half of a float covers well over half the distance.
    fresh = LoadIntro(1, timing=IntroTiming(tile_float_seconds=1.0, tile_delay_max_seconds=0.0))
    fresh.advance(0.5)
    assert fresh.tile_progress(0) > 0.5


def test_no_tiles_still_drops_the_player_and_finishes() -> None:
    intro = LoadIntro(0, timing=TIMING)
    assert intro.duration == TIMING.player_float_seconds
    intro.advance(0.15)
    assert intro.player_progress() > 0.0
    assert intro.finished is False
    _run(intro, intro.duration)
    assert intro.finished is True


def test_elapsed_is_capped_at_the_duration() -> None:
    intro = LoadIntro(3, timing=TIMING, seed=6)
    _run(intro, intro.duration * 4.0, steps=40)
    assert intro.elapsed == intro.duration
