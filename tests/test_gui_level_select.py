"""Headless unit tests for level selector state and layout logic."""

from __future__ import annotations

import pytest

from bloxorz.gui.level_select_state import (
    BUTTON_PITCH,
    NEIGHBOR_1_WIDTH,
    NEIGHBOR_2_WIDTH,
    SCROLL_COOLDOWN_SECONDS,
    SELECTED_WIDTH,
    STANDARD_WIDTH,
    LevelSelectState,
    approach_lerp,
    target_width,
)


def test_target_width_values() -> None:
    assert target_width(0) == SELECTED_WIDTH
    assert target_width(1) == NEIGHBOR_1_WIDTH
    assert target_width(-1) == NEIGHBOR_1_WIDTH
    assert target_width(2) == NEIGHBOR_2_WIDTH
    assert target_width(-2) == NEIGHBOR_2_WIDTH
    assert target_width(3) == STANDARD_WIDTH
    assert target_width(10) == STANDARD_WIDTH


def test_approach_lerp() -> None:
    # 0 dt -> no change
    assert approach_lerp(0.0, 1.0, 8.0, 0.0) == 0.0
    # positive dt moves towards target
    val = approach_lerp(0.0, 1.0, 8.0, 0.05)
    assert 0.0 < val < 1.0
    # large dt clamps to target
    assert approach_lerp(0.0, 1.0, 8.0, 1.0) == 1.0


def test_initial_state() -> None:
    state = LevelSelectState(stage_count=10, initial_index=0)
    assert state.selected_index == 0
    assert state.widths[0] == SELECTED_WIDTH
    assert state.widths[1] == NEIGHBOR_1_WIDTH
    assert state.widths[2] == NEIGHBOR_2_WIDTH
    assert state.widths[3] == STANDARD_WIDTH
    assert state.scroll_y == 0.0
    assert state.button_y(0) == 0.0


def test_invalid_stage_count() -> None:
    with pytest.raises(ValueError):
        LevelSelectState(stage_count=0)


def test_navigation_and_clamping() -> None:
    state = LevelSelectState(stage_count=5, initial_index=0)
    # Cannot select previous from 0
    assert not state.select_prev()
    assert state.selected_index == 0

    # Select next
    assert state.select_next()
    assert state.selected_index == 1

    # Direct select
    assert state.select(4)
    assert state.selected_index == 4

    # Cannot select next beyond bounds
    assert not state.select_next()
    assert state.selected_index == 4

    # Direct select out of range is clamped
    assert not state.select(10)
    assert state.selected_index == 4


def test_scroll_throttling() -> None:
    state = LevelSelectState(stage_count=5, initial_index=0)

    # First scroll down works
    assert state.on_scroll(1)
    assert state.selected_index == 1
    assert state.scroll_cooldown == SCROLL_COOLDOWN_SECONDS

    # Immediate second scroll is ignored due to cooldown
    assert not state.on_scroll(1)
    assert state.selected_index == 1

    # Advance time partially
    state.update(0.05)
    assert state.scroll_cooldown > 0.0
    assert not state.on_scroll(1)

    # Advance past cooldown
    state.update(0.15)
    assert state.scroll_cooldown == 0.0
    assert state.on_scroll(1)
    assert state.selected_index == 2


def test_width_cascade_lerp() -> None:
    state = LevelSelectState(stage_count=5, initial_index=0)
    old_width_0 = state.widths[0]
    old_width_1 = state.widths[1]

    state.select(1)
    # Target for index 1 is now SELECTED_WIDTH, target for index 0 is NEIGHBOR_1_WIDTH
    state.update(0.05)

    assert state.widths[0] < old_width_0  # 0 shrunk
    assert state.widths[1] > old_width_1  # 1 expanded

    # Settle
    for _ in range(50):
        state.update(0.1)

    assert pytest.approx(state.widths[1], abs=0.001) == SELECTED_WIDTH
    assert pytest.approx(state.widths[0], abs=0.001) == NEIGHBOR_1_WIDTH


def test_scroll_position_and_visibility() -> None:
    state = LevelSelectState(stage_count=10, initial_index=3)
    # Target scroll keeps selected at y = 0
    assert state.target_scroll_y() == 3 * BUTTON_PITCH

    # Settle scroll
    for _ in range(50):
        state.update(0.1)

    assert pytest.approx(state.button_y(3), abs=0.001) == 0.0
    assert state.button_y(2) > 0.0  # Previous is above
    assert state.button_y(4) < 0.0  # Next is below
    assert state.is_visible(3, top=0.28, bottom=-0.39)


def test_visibility_band_hides_cards_past_the_header_and_footer() -> None:
    state = LevelSelectState(stage_count=10, initial_index=4)
    for _ in range(50):
        state.update(0.1)

    # A band that leaves room for the three cards above the selection and the four below it.
    top = 3 * BUTTON_PITCH + 0.01
    bottom = -4 * BUTTON_PITCH - 0.01

    assert state.is_visible(1, top, bottom)
    assert state.is_visible(8, top, bottom)
    # The next card out in either direction runs under the header or the footer hints.
    assert not state.is_visible(0, top, bottom)
    assert not state.is_visible(9, top, bottom)

