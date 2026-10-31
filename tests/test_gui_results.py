"""Headless checks for the level-result and solver-replay text the HUD and the cards draw."""

from __future__ import annotations

from bloxorz.core.contracts import Counts
from bloxorz.gui.benchmarks import Metrics
from bloxorz.gui.results import (
    counts_line,
    elapsed_label,
    replay_line,
    result_line,
    solver_detail,
    solver_heading,
    solver_result_line,
)


def test_elapsed_label_reads_as_minutes_and_seconds() -> None:
    assert elapsed_label(0) == "0:00"
    assert elapsed_label(7.9) == "0:07"
    assert elapsed_label(65) == "1:05"
    assert elapsed_label(3600) == "60:00"
    # A clock cannot run backwards, and it never gets a frame with a negative delta.
    assert elapsed_label(-3) == "0:00"


def test_result_line_pairs_the_move_count_with_the_clock() -> None:
    assert result_line(0, 0) == "0 moves   |   0:00"
    assert result_line(7, 0.4) == "7 moves   |   0:00"
    assert result_line(123, 95) == "123 moves   |   1:35"


def test_a_single_move_is_not_plural() -> None:
    assert result_line(1, 12) == "1 move   |   0:12"


def test_replay_line_reports_progress_and_pause() -> None:
    assert replay_line("BFS", 3, 19) == "BFS replay — move 3 of 19"
    assert replay_line("A*", 19, 19) == "A* replay — move 19 of 19"
    assert replay_line("DFS", 4, 7, paused=True) == "DFS replay paused — move 4 of 7"


def test_solver_heading_names_the_algorithm_and_its_outcome() -> None:
    assert solver_heading("UCS", "solved") == "UCS — solved"
    assert solver_heading("DFS", "cap") == "DFS — ran out of budget"
    assert solver_heading("BFS", "unsolvable") == "BFS — found no solution"


def test_solver_result_line_pairs_solution_length_with_cost() -> None:
    assert solver_result_line(7, 7.0) == "7 moves   |   cost 7"
    assert solver_result_line(1, 1.0) == "1 move   |   cost 1"
    assert solver_result_line(12, 12.5) == "12 moves   |   cost 12.5"


def test_solver_detail_says_why_there_is_no_movie() -> None:
    assert solver_detail("solved", 7, 7.0) == "7 moves   |   cost 7"
    assert solver_detail("solved", 0, 0.0) == "already at the goal — nothing to roll"
    assert "node or time limit" in solver_detail("cap", 0, 0.0)
    assert "exhausted" in solver_detail("unsolvable", 0, 0.0)


def test_counts_line_keeps_a_large_run_readable() -> None:
    counts = Counts(expanded=1234, generated=5678, frontier_peak=89)
    assert counts_line(counts) == (
        "expanded 1,234   |   generated 5,678   |   frontier peak 89"
    )


def test_solver_detail_adds_the_benchmark_figures_to_a_solved_run() -> None:
    metrics = Metrics(time_ms=19.98, peak_mem_kb=42.89)

    assert solver_detail("solved", 7, 7.0, metrics) == (
        "7 moves   |   cost 7   |   bench 19.98 ms · 42.89 KB"
    )
    # An unsolved run cannot be compared with the benchmark, so it keeps its reason instead.
    assert solver_detail("cap", 0, 0.0, metrics) == solver_detail("cap", 0, 0.0)
    assert solver_detail("solved", 0, 0.0, metrics) == solver_detail("solved", 0, 0.0)
