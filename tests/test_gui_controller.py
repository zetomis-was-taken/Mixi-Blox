"""Headless checks for interactive play and the goal hook.

Ursina is not imported: a fake block records the completion callback so the test can drive it.
"""

from __future__ import annotations

from collections import deque
from collections.abc import Callable
from pathlib import Path

from bloxorz.core.contracts import Action, State
from bloxorz.core.engine import Board
from bloxorz.core.stage import load_stage
from bloxorz.gui.controller import PlayerController

ROOT = Path(__file__).resolve().parents[1]
STAGES = ROOT / "Source" / "bloxorz" / "core" / "stages"


class FakeBlock:
    def __init__(self) -> None:
        self.on_done = None
        self.action = None

    def animate(self, start, next_state, action, on_done) -> None:
        self.action = action
        self.on_done = on_done

    def finish(self) -> None:
        callback = self.on_done
        self.on_done = None
        callback()


class StubBoard:
    """A board whose two split cubes accept different directions.

    It stands in for ``Board`` in the one case a real stage cannot state cheaply: the active cube
    has no legal action and the other one has.
    """

    def __init__(self) -> None:
        self._start = State(cubes=(((0, 0),), ((0, 1),)), bridges=())
        self._east = State(cubes=(((0, 0),), ((0, 2),)), bridges=())

    def start(self) -> State:
        return self._start

    def successors(self, state: State) -> list[tuple[State, Action]]:
        return [(self._east, (1, "R"))] if state == self._start else []

    def is_goal(self, state: State) -> bool:
        return False


def _path_to(board: Board, reached: Callable[[State], bool]) -> tuple[Action, ...]:
    """The shortest action sequence from the start to the first state satisfying ``reached``."""
    start = board.start()
    seen = {start.key(): ()}
    queue = deque([start])
    while queue:
        state = queue.popleft()
        if reached(state):
            return seen[state.key()]
        for next_state, action in board.successors(state):
            if next_state.key() not in seen:
                seen[next_state.key()] = seen[state.key()] + (action,)
                queue.append(next_state)
    raise AssertionError("stage does not reach the wanted state")


def _moved_cube(before: State, after: State) -> int:
    """Index of the one cube whose cells differ between the two states."""
    return next(index for index, cube in enumerate(before.cubes) if cube not in after.cubes)


def test_reaching_the_goal_calls_the_exit_hook_once() -> None:
    stage = load_stage(STAGES / "L1-01_long_corridor.json")
    board = Board(stage)
    block = FakeBlock()
    exits: list[bool] = []
    controller = PlayerController(board, block, lambda: exits.append(True))

    for _, direction in _path_to(board, board.is_goal):
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
    # An unsplit block has one cube, so there is nothing to switch to.
    assert controller.switch_cube() is False


def test_a_split_pair_is_steered_one_cube_at_a_time() -> None:
    """Both L4-01 cubes can roll north out of the split room: the active one decides which does."""
    stage = load_stage(STAGES / "L4-01_split_into_the_far_room.json")
    board = Board(stage)
    block = FakeBlock()
    controller = PlayerController(board, block, lambda: None)

    for index, direction in _path_to(board, lambda state: len(state.cubes) == 2):
        if controller.active != index:
            assert controller.switch_cube() is True
        assert controller.move(direction) is True
        block.finish()

    assert controller.split is True
    accepted = {
        index
        for _, (index, direction) in board.successors(controller.state)
        if direction == "U"
    }
    assert accepted == {0, 1}, "the ambiguous case this test exists for"

    was_active = controller.active
    before = controller.state
    assert controller.move("U") is True
    assert block.action == (was_active, "U")
    block.finish()
    assert _moved_cube(before, controller.state) == was_active
    assert controller.active == _moved_cube(before, controller.state)

    assert controller.switch_cube() is True
    assert controller.active != was_active
    was_active = controller.active
    before = controller.state
    assert controller.move("U") is True
    assert block.action == (was_active, "U")
    block.finish()
    assert _moved_cube(before, controller.state) == was_active


def test_the_other_cube_moves_when_the_active_one_is_blocked() -> None:
    block = FakeBlock()
    controller = PlayerController(StubBoard(), block, lambda: None)

    # The active cube (index 0) has no action east; the move is still offered to the player.
    assert controller.move("R") is True
    assert block.action == (1, "R")
