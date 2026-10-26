"""Headless checks for solver playback.

Ursina is not imported: the driver hands out one transition at a time and the test plays the view's
part by reporting that each roll landed. A breadth-first search stands in for the solver, so every
mocked path is legal by construction — the driver must reject anything else.
"""

from __future__ import annotations

from collections import deque
from pathlib import Path

import pytest

from bloxorz.core.contracts import Action, Counts, SearchResult, State
from bloxorz.core.engine import Board
from bloxorz.core.stage import load_stage
from bloxorz.gui.replay import Replay

ROOT = Path(__file__).resolve().parents[1]
STAGES = ROOT / "Source" / "bloxorz" / "core" / "stages"
PAUSE = 0.1


def _solved(board: Board) -> SearchResult:
    """A mock solver: BFS from the start, returned in the shape ``solve()`` must produce."""
    start = board.start()
    seen: dict[tuple[object, ...], tuple[tuple[Action, ...], float]] = {start.key(): ((), 0.0)}
    queue = deque([start])
    while queue:
        state = queue.popleft()
        path, cost = seen[state.key()]
        if board.is_goal(state):
            return SearchResult("solved", path, cost, Counts(len(seen), len(seen), 1))
        for next_state, action in board.successors(state):
            if next_state.key() not in seen:
                step_cost = board.step_cost(state, action, next_state)
                seen[next_state.key()] = (path + (action,), cost + step_cost)
                queue.append(next_state)
    raise AssertionError("stage is unsolvable")


def _corridor() -> tuple[Board, SearchResult]:
    board = Board(load_stage(STAGES / "L1-01_long_corridor.json"))
    return board, _solved(board)


class _SplitBoard:
    """A two-cube board whose two actions roll different cubes, in a fixed order."""

    def __init__(self) -> None:
        self._start = State(cubes=(((0, 0),), ((0, 2),)), bridges=())
        self._middle = State(cubes=(((0, 0),), ((0, 3),)), bridges=())
        self._end = State(cubes=(((0, 1),), ((0, 3),)), bridges=())

    def start(self) -> State:
        return self._start

    def successors(self, state: State) -> list[tuple[State, Action]]:
        if state == self._start:
            return [(self._middle, (1, "R"))]
        if state == self._middle:
            return [(self._end, (0, "U"))]
        return []

    def is_goal(self, state: State) -> bool:
        return state == self._end


def test_the_planned_steps_follow_the_path_and_reach_the_goal() -> None:
    board, result = _corridor()
    replay = Replay(board, result, PAUSE)

    assert replay.playable is True
    assert tuple(action for _, _, action in replay.steps) == result.path
    assert replay.steps[0][0] == board.start()
    for (_, landed, _), (started, _, _) in zip(replay.steps, replay.steps[1:]):
        assert landed == started
    assert board.is_goal(replay.steps[-1][1])


def test_a_split_path_keeps_each_actions_cube_index() -> None:
    board = _SplitBoard()
    result = SearchResult("solved", ((1, "R"), (0, "U")), 2.0, Counts(3, 3, 2))
    replay = Replay(board, result, PAUSE)

    assert tuple(action for _, _, action in replay.steps) == ((1, "R"), (0, "U"))
    assert board.is_goal(replay.steps[-1][1])


def test_one_roll_at_a_time_with_a_pause_between_them() -> None:
    board, result = _corridor()
    replay = Replay(board, result, PAUSE)
    assert replay.start() is True

    assert replay.advance(0.0) is not None
    assert replay.progress == (1, len(replay.steps))
    assert replay.advance(1.0) is None, "a roll is still in flight"
    assert replay.roll_finished() is False
    assert replay.advance(PAUSE / 2) is None
    assert replay.advance(PAUSE / 2) is not None
    assert replay.progress[0] == 2


def test_the_last_roll_finishes_the_replay() -> None:
    board, result = _corridor()
    replay = Replay(board, result, PAUSE)
    replay.start()

    step = replay.advance(0.0)
    landed_last = False
    while step is not None:
        landed_last = replay.roll_finished()
        step = replay.advance(PAUSE)

    assert landed_last is True
    assert replay.phase == "finished"
    assert replay.remaining == 0
    assert replay.advance(PAUSE) is None


def test_pausing_holds_the_next_step_until_resumed() -> None:
    board, result = _corridor()
    replay = Replay(board, result, PAUSE)
    replay.start()
    replay.advance(0.0)
    replay.roll_finished()

    assert replay.pause() is True
    assert replay.advance(10.0) is None
    assert replay.phase == "paused"
    assert replay.resume() is True
    assert replay.advance(PAUSE) is not None


def test_speed_scales_the_pause_and_must_be_positive() -> None:
    board, result = _corridor()
    replay = Replay(board, result, PAUSE)
    replay.start()
    replay.advance(0.0)
    replay.roll_finished()

    replay.set_speed(2.0)
    assert replay.advance(PAUSE / 2) is not None
    with pytest.raises(ValueError):
        replay.set_speed(0.0)


def test_stop_hands_back_the_state_to_restore() -> None:
    board, result = _corridor()
    elsewhere = board.successors(board.start())[0][0]
    replay = Replay(board, result, PAUSE, restore=elsewhere)
    replay.start()
    replay.advance(0.0)

    assert replay.stop() == elsewhere
    assert replay.phase == "aborted"
    assert replay.advance(PAUSE) is None
    assert replay.roll_finished() is False


def test_stop_defaults_to_the_start_and_leaves_a_finished_replay_alone() -> None:
    board, result = _corridor()
    replay = Replay(board, result, PAUSE)
    replay.start()
    step = replay.advance(0.0)
    while step is not None:
        replay.roll_finished()
        step = replay.advance(PAUSE)

    assert replay.stop() == board.start()
    assert replay.phase == "finished"


def test_a_capped_or_unsolvable_result_has_nothing_to_play() -> None:
    board, _ = _corridor()
    capped = SearchResult("cap", (), 0.0, Counts(0, 1, 1))
    unsolvable = SearchResult("unsolvable", (), 0.0, Counts(9, 9, 4))

    for result in (capped, unsolvable):
        replay = Replay(board, result, PAUSE)
        assert replay.playable is False
        assert replay.phase == "finished"
        assert replay.start() is False
        assert replay.advance(PAUSE) is None


def test_a_solved_result_with_an_empty_path_is_no_movie() -> None:
    board, _ = _corridor()
    already_home = SearchResult("solved", (), 0.0, Counts(1, 1, 1))
    replay = Replay(board, already_home, PAUSE)

    assert replay.playable is False
    assert replay.phase == "finished"
    assert replay.remaining == 0


def test_an_illegal_action_is_rejected_when_the_path_is_planned() -> None:
    board, _ = _corridor()
    # L1-01 starts with void to its left, so this action exists nowhere at the start state.
    result = SearchResult("solved", ((0, "L"),), 1.0, Counts(1, 1, 1))

    with pytest.raises(ValueError):
        Replay(board, result, PAUSE)
