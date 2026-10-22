"""Headless checks for interactive play and the goal hook.

Ursina is not imported: a fake block records the completion callback so the test can drive it.
"""

from __future__ import annotations

from collections import deque
from pathlib import Path

from bloxorz.core.engine import Board
from bloxorz.core.stage import load_stage
from bloxorz.gui.controller import PlayerController

ROOT = Path(__file__).resolve().parents[1]
STAGES = ROOT / "Source" / "bloxorz" / "core" / "stages"


class FakeBlock:
    def __init__(self) -> None:
        self.on_done = None

    def animate(self, start, next_state, action, on_done) -> None:
        self.on_done = on_done

    def finish(self) -> None:
        callback = self.on_done
        self.on_done = None
        callback()


def _path_to_goal(board: Board) -> tuple[tuple[int, str], ...]:
    start = board.start()
    seen = {start.key(): ()}
    queue = deque([start])
    while queue:
        state = queue.popleft()
        if board.is_goal(state):
            return seen[state.key()]
        for next_state, action in board.successors(state):
            if next_state.key() not in seen:
                seen[next_state.key()] = seen[state.key()] + (action,)
                queue.append(next_state)
    raise AssertionError("stage has no solution")


def test_reaching_the_goal_calls_the_exit_hook_once() -> None:
    stage = load_stage(STAGES / "L1-01_long_corridor.json")
    board = Board(stage)
    block = FakeBlock()
    exits: list[bool] = []
    controller = PlayerController(board, block, lambda: exits.append(True))

    for _, direction in _path_to_goal(board):
        assert controller.move(direction) is True
        block.finish()

    assert board.is_goal(controller.state)
    assert exits == [True]


def test_illegal_direction_does_not_start_a_move() -> None:
    stage = load_stage(STAGES / "L1-01_long_corridor.json")
    board = Board(stage)
    block = FakeBlock()
    controller = PlayerController(board, block, lambda: None)

    # The start of L1-01 has void to its left: the action is absent, not fatal.
    assert controller.move("L") is False
    assert controller.animating is False
    assert block.on_done is None
