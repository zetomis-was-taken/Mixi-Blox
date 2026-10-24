"""Headless checks for the level-result text the win overlay draws."""

from __future__ import annotations

from bloxorz.gui.results import elapsed_label, result_line


def test_elapsed_label_reads_as_minutes_and_seconds() -> None:
    assert elapsed_label(0) == "0:00"
    assert elapsed_label(7.9) == "0:07"
    assert elapsed_label(65) == "1:05"
    assert elapsed_label(3600) == "60:00"
    # A clock cannot run backwards, and it never gets a frame with a negative delta.
    assert elapsed_label(-3) == "0:00"


def test_result_line_pairs_the_move_count_with_the_clock() -> None:
    assert result_line(7, 0.4) == "7 moves   |   0:00"
    assert result_line(123, 95) == "123 moves   |   1:35"
