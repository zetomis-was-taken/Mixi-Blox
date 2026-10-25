"""Headless checks for the camera-fit rule.

Ursina is not imported: ``framing`` is pure Python, and the projection that feeds it lives in
``app.py``. The measurements here model what the lens reports — a board whose projected outline
shrinks as the camera moves away — so the rule is pinned without opening a window.
"""

from __future__ import annotations

from bloxorz.gui.framing import FIT_X, FIT_Y, MAX_STEPS, fitting_distance, overflow


def pinhole(distance: float) -> tuple[float, float]:
    """Half-extents that fall exactly as 1 / distance, like a flat board seen head-on."""
    return (10.0 / distance, 10.0 / distance)


def test_overflow_is_one_when_the_board_exactly_fills_the_frame() -> None:
    assert overflow(FIT_X, FIT_Y) == 1.0
    assert overflow(FIT_X / 2, FIT_Y / 2) < 1.0


def test_overflow_reports_the_worse_axis() -> None:
    # Twice the allowed width but half the allowed height: the width is what has to give.
    assert overflow(FIT_X * 2, FIT_Y / 2) == 2.0


def test_a_board_that_already_fits_keeps_its_nominal_distance() -> None:
    calls: list[float] = []

    def measure(distance: float) -> tuple[float, float]:
        calls.append(distance)
        return (0.2, 0.3)

    assert fitting_distance(measure, start=22.5) == 22.5
    assert calls == [22.5]


def test_a_board_too_large_is_pushed_out_until_it_fits() -> None:
    distance = fitting_distance(pinhole, start=10.0)

    assert distance > 10.0
    assert overflow(*pinhole(distance)) <= 1.0


def test_the_camera_is_never_pulled_in() -> None:
    # A board that fills the frame from far away stays where the caller put it.
    assert fitting_distance(lambda d: (0.01, 0.01), start=50.0) == 50.0


def test_perspective_is_absorbed_by_measuring_again() -> None:
    # The outline falls a little slower than 1 / distance near the board (a yawed board's near edge
    # grows faster), so the distance the first step lands on has to be measured again.
    def skewed(distance: float) -> tuple[float, float]:
        return (10.0 / distance * (1.0 + 0.5 / distance),) * 2

    distance = fitting_distance(skewed, start=10.0)

    assert distance > 10.0
    assert overflow(*skewed(distance)) <= 1.0


def test_the_fit_is_verified_rather_than_assumed() -> None:
    # A measure that stays too big for a while before it drops: scaling once and trusting the
    # arithmetic would stop far too close.
    def cliff(distance: float) -> tuple[float, float]:
        return (1.0, 1.0) if distance < 40.0 else (0.5, 0.5)

    distance = fitting_distance(cliff, start=22.5)

    assert distance >= 40.0
    assert overflow(*cliff(distance)) <= 1.0


def test_a_wider_window_needs_a_further_camera() -> None:
    """The vertical field of view shrinks with the aspect ratio, so a wide window magnifies it."""
    wide_aspect = 2.0 / 1.6

    def at(distance: float, zoom: float) -> tuple[float, float]:
        return (10.0 / distance, 10.0 / distance * zoom)

    tall = fitting_distance(lambda d: at(d, 1.0), start=10.0)
    wide = fitting_distance(lambda d: at(d, wide_aspect), start=10.0)

    assert wide > tall
    assert overflow(*at(wide, wide_aspect)) <= 1.0


def test_the_measurement_budget_is_bounded() -> None:
    calls: list[float] = []

    def hopeless(distance: float) -> tuple[float, float]:
        calls.append(distance)
        return (5.0, 5.0)  # a board that never fits, however far away the camera goes

    fitting_distance(hopeless, start=22.5)

    assert len(calls) <= MAX_STEPS
