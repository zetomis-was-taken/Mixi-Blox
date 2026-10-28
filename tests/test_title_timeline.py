"""Unit tests for the title screen animation timeline mathematics.

Ensures headless, algebraic verification without Ursina.
"""

from __future__ import annotations

from bloxorz.gui.title.timeline import (
    ANCHOR_LEFT_X,
    BLOCK_INIT_POS,
    BLOCK_REST_POS,
    KF1_END,
    KF2_END,
    KF2_START,
    KF3A_END,
    KF3B_END,
    OFFSCREEN_LEFT_X,
    READY_TIME,
    TITLE_TARGET_Y,
    is_interactive,
    play_button_x,
    player_block_position,
    player_block_scale,
    quit_button_x,
    title_position,
)


def test_title_position_endpoints() -> None:
    pos_start = title_position(0.0)
    assert pos_start == (OFFSCREEN_LEFT_X, TITLE_TARGET_Y)

    pos_end = title_position(KF1_END)
    assert pos_end == (ANCHOR_LEFT_X, TITLE_TARGET_Y)

    pos_after = title_position(KF1_END + 1.0)
    assert pos_after == (ANCHOR_LEFT_X, TITLE_TARGET_Y)


def test_player_block_position_across_keyframes() -> None:
    # Keyframe 1: stays at initial center staging
    pos_k1 = player_block_position(0.0)
    assert pos_k1 == BLOCK_INIT_POS
    pos_k1_end = player_block_position(KF2_START)
    assert pos_k1_end == BLOCK_INIT_POS

    # Keyframe 2: slides to center-right
    pos_mid = player_block_position((KF2_START + KF2_END) / 2.0)
    assert BLOCK_INIT_POS[0] < pos_mid[0] < BLOCK_REST_POS[0]

    pos_k2_end = player_block_position(KF2_END)
    assert pos_k2_end == BLOCK_REST_POS


def test_player_block_scale_pop_in() -> None:
    assert player_block_scale(0.0) == 0.0
    assert player_block_scale(KF1_END) == 1.0
    assert player_block_scale(KF1_END + 0.5) == 1.0


def test_menu_buttons_stagger_and_alignment() -> None:
    # Before KF3a, buttons are offscreen
    assert play_button_x(0.0) == OFFSCREEN_LEFT_X
    assert quit_button_x(0.0) == OFFSCREEN_LEFT_X

    # After KF3a finishes, play button is at ANCHOR_LEFT_X
    assert play_button_x(KF3A_END) == ANCHOR_LEFT_X

    # Play button arrives strictly before Quit button
    assert play_button_x(KF3A_END) > quit_button_x(KF3A_END)

    # After KF3b finishes, both buttons are aligned to the exact same anchor X
    assert play_button_x(KF3B_END) == ANCHOR_LEFT_X
    assert quit_button_x(KF3B_END) == ANCHOR_LEFT_X
    assert play_button_x(READY_TIME) == quit_button_x(READY_TIME) == title_position(READY_TIME)[0]


def test_interactivity_boundary() -> None:
    assert not is_interactive(0.0)
    assert not is_interactive(KF1_END)
    assert not is_interactive(KF2_END)
    assert not is_interactive(READY_TIME - 0.01)
    assert is_interactive(READY_TIME)
    assert is_interactive(READY_TIME + 1.0)
