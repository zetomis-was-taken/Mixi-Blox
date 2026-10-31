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
from bloxorz.gui import reaction
from bloxorz.gui.controller import OPPOSITE, PlayerController

ROOT = Path(__file__).resolve().parents[1]
STAGES = ROOT / "Source" / "bloxorz" / "core" / "stages"


class FakeBlock:
    def __init__(self) -> None:
        self.on_done = None
        self.action = None
        self.state = None
        self.fatal = False

    def animate(self, start, next_state, action, on_done) -> None:
        self.action = action
        self.on_done = on_done

    def fall(self, start, fatal_state, action, on_done) -> None:
        self.action = action
        self.on_done = on_done
        self.fatal = True

    def sync(self, state) -> None:
        self.state = state
        self.on_done = None
        self.fatal = False

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


def _pair_from(board: Board, state: State, action: Action) -> tuple[State, Action]:
    """The engine's ``(next_state, action)`` pair for ``action`` taken from ``state``."""
    return next(pair for pair in board.successors(state) if pair[1] == action)


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


def test_moves_and_the_clock_measure_the_level() -> None:
    stage = load_stage(STAGES / "L1-01_long_corridor.json")
    board = Board(stage)
    block = FakeBlock()
    controller = PlayerController(board, block, lambda: None)

    controller.tick(0.5)
    controller.tick(0.25)
    assert controller.elapsed == 0.75
    assert controller.moves == 0

    for _, direction in _path_to(board, board.is_goal)[:2]:
        assert controller.move(direction) is True
        block.finish()

    assert controller.moves == 2
    assert len(controller.history) == 2


def test_undo_steps_back_one_move_at_a_time() -> None:
    stage = load_stage(STAGES / "L1-01_long_corridor.json")
    board = Board(stage)
    block = FakeBlock()
    controller = PlayerController(board, block, lambda: None)
    start = controller.state
    path = _path_to(board, board.is_goal)

    assert controller.undo() is False, "nothing to take back yet"

    assert controller.move(path[0][1]) is True
    assert controller.undo() is False, "a roll in progress cannot be undone"
    block.finish()
    after_first = controller.state
    assert after_first != start

    assert controller.move(path[1][1]) is True
    block.finish()
    assert controller.moves == 2

    assert controller.undo() is True
    assert controller.state == after_first
    assert controller.moves == 1
    # The view is asked to play the same quarter-turn in reverse, not to jump.
    assert block.action == (0, OPPOSITE[path[1][1]])
    assert controller.animating is True
    block.finish()
    assert controller.animating is False

    assert controller.undo() is True
    assert controller.state == start
    assert block.action == (0, OPPOSITE[path[0][1]])
    block.finish()
    assert controller.moves == 0
    assert controller.undo() is False


def test_undo_rolls_the_cube_that_moved_on_a_split_stage() -> None:
    board = StubBoard()
    block = FakeBlock()
    controller = PlayerController(board, block, lambda: None)

    # The active cube (0) cannot move east, so cube 1 takes the action.
    assert controller.move("R") is True
    block.finish()

    assert controller.undo() is True
    assert block.action == (1, "L"), "the cube that moved is the one that rolls back"
    block.finish()
    assert controller.state == board.start()
    assert controller.moves == 0


def test_undo_puts_the_mechanisms_back() -> None:
    """An undo restores the state a mechanism answers to, so the view eases back to it."""
    stage = load_stage(STAGES / "L3-01_bridge_under_a_heavy_switch.json")
    board = Board(stage)
    block = FakeBlock()
    controller = PlayerController(board, block, lambda: None)
    start_loads = reaction.load_per_cell(stage, controller.state)

    moved: State | None = None
    for _, direction in _path_to(board, board.is_goal):
        before = controller.state
        assert controller.move(direction) is True
        block.finish()
        if reaction.load_per_cell(stage, controller.state) != start_loads:
            moved = before
            break
    assert moved is not None, "the path never presses a switch"

    assert controller.undo() is True
    assert controller.state == moved
    assert reaction.load_per_cell(stage, controller.state) == start_loads


def test_retry_returns_to_the_start_and_forgets_the_attempt() -> None:
    stage = load_stage(STAGES / "L1-01_long_corridor.json")
    board = Board(stage)
    block = FakeBlock()
    controller = PlayerController(board, block, lambda: None)

    for _, direction in _path_to(board, board.is_goal)[:2]:
        assert controller.move(direction) is True
        block.finish()
    controller.tick(3.0)

    assert controller.retry() is True
    assert controller.state == board.start()
    assert block.state == board.start()
    assert (controller.moves, controller.elapsed) == (0, 0.0)
    assert controller.history == []
    assert controller.undo() is False

    # Retry is refused while a roll is playing, like undo.
    assert controller.move(_path_to(board, board.is_goal)[0][1]) is True
    assert controller.retry() is False


def test_a_cleared_level_takes_no_more_moves_until_undo() -> None:
    stage = load_stage(STAGES / "L1-01_long_corridor.json")
    board = Board(stage)
    block = FakeBlock()
    controller = PlayerController(board, block, lambda: None)

    for _, direction in _path_to(board, board.is_goal):
        assert controller.move(direction) is True
        block.finish()

    assert controller.cleared is True
    assert all(controller.move(direction) is False for direction in ("U", "D", "L", "R"))
    assert controller.switch_cube() is False

    # Undo puts the level back in play, so the win overlay can be dismissed by stepping back.
    assert controller.undo() is True
    assert controller.cleared is False


def test_playback_applies_an_action_without_counting_it_as_a_move() -> None:
    stage = load_stage(STAGES / "L1-01_long_corridor.json")
    board = Board(stage)
    block = FakeBlock()
    controller = PlayerController(board, block, lambda: None)

    next_state, action = board.successors(controller.state)[0]
    assert controller.play(next_state, action) is True

    assert controller.state == next_state
    assert controller.animating is True
    assert block.action == action
    assert block.on_done is not None
    assert controller.moves == 0
    assert controller.history == []

    block.finish()
    assert controller.animating is False
    # Playback never lands on the undo stack, so Z cannot walk a solver's movie backwards.
    assert controller.undo() is False


def test_playback_can_reach_the_goal_through_the_ordinary_hook() -> None:
    stage = load_stage(STAGES / "L1-01_long_corridor.json")
    board = Board(stage)
    block = FakeBlock()
    exits: list[bool] = []
    controller = PlayerController(board, block, lambda: exits.append(True))

    for action in _path_to(board, board.is_goal):
        next_state, _ = _pair_from(board, controller.state, action)
        assert controller.play(next_state, action) is True
        block.finish()

    assert board.is_goal(controller.state)
    assert controller.cleared is True
    assert exits == [True]
    assert controller.moves == 0, "the solver's path is not the player's run"


def test_playback_refuses_an_illegal_pair_and_a_second_roll() -> None:
    stage = load_stage(STAGES / "L1-01_long_corridor.json")
    board = Board(stage)
    block = FakeBlock()
    controller = PlayerController(board, block, lambda: None)

    start = controller.state
    next_state, action = board.successors(start)[0]
    # Void to the left of L1-01's start: no such transition exists, so the pair is refused.
    assert controller.play(next_state, (0, "L")) is False
    assert controller.state == start
    assert controller.animating is False
    assert block.on_done is None

    assert controller.play(next_state, action) is True
    assert controller.play(next_state, action) is False, "one roll at a time"


def test_a_run_can_be_snapshotted_and_restored_after_playback() -> None:
    stage = load_stage(STAGES / "L1-01_long_corridor.json")
    board = Board(stage)
    block = FakeBlock()
    controller = PlayerController(board, block, lambda: None)

    path = _path_to(board, board.is_goal)
    for _, direction in path[:2]:
        assert controller.move(direction) is True
        block.finish()
    controller.tick(3.5)
    run = controller.snapshot()

    # Playback starts the stage over before it rolls the solver's path.
    assert controller.retry() is True
    assert controller.moves == 0
    assert controller.state == board.start()

    assert controller.restore(run) is True
    assert controller.state == run.state
    assert controller.moves == 2
    assert controller.elapsed == 3.5
    assert len(controller.history) == 2
    assert controller.active == run.active
    assert block.state == run.state

    # The restored run is live again: the next move continues from it.
    assert controller.move(path[2][1]) is True
    assert controller.moves == 3


def test_restoring_a_run_is_refused_while_a_roll_plays() -> None:
    stage = load_stage(STAGES / "L1-01_long_corridor.json")
    board = Board(stage)
    block = FakeBlock()
    controller = PlayerController(board, block, lambda: None)

    run = controller.snapshot()
    assert controller.move(_path_to(board, board.is_goal)[0][1]) is True
    assert controller.restore(run) is False
    assert controller.animating is True

    block.finish()
    assert controller.restore(run) is True
    assert controller.state == run.state


def test_restoring_puts_a_solved_board_back_in_play() -> None:
    stage = load_stage(STAGES / "L1-01_long_corridor.json")
    board = Board(stage)
    block = FakeBlock()
    controller = PlayerController(board, block, lambda: None)

    path = _path_to(board, board.is_goal)
    for _, direction in path[:-1]:
        assert controller.move(direction) is True
        block.finish()
    run = controller.snapshot()

    assert controller.move(path[-1][1]) is True
    block.finish()
    assert controller.cleared is True

    # This is the way out of a solver card: the board goes back to the player's run.
    assert controller.restore(run) is True
    assert controller.cleared is False
    assert controller.state == run.state
    assert controller.moves == len(path) - 1


def test_fatal_move_animates_fall_triggers_loss_and_allows_undo_and_retry() -> None:
    stage = load_stage(STAGES / "L2-01_fragile_shelves.json")
    board = Board(stage)
    block = FakeBlock()
    lost_calls: list[bool] = []
    controller = PlayerController(
        board,
        block,
        on_goal=lambda: None,
        on_loss=lambda: lost_calls.append(True),
    )

    start = board.start()
    queue = deque([(start, ())])
    seen = {start.key()}
    fatal_path: tuple[str, ...] | None = None
    fatal_direction: str | None = None
    while queue:
        state, path = queue.popleft()
        for direction in ("U", "D", "L", "R"):
            if board.outcome(state, (0, direction)).kind == "fatal":
                fatal_path = path
                fatal_direction = direction
                break
        if fatal_path is not None:
            break
        for next_state, action in board.successors(state):
            if next_state.key() not in seen:
                seen.add(next_state.key())
                queue.append((next_state, path + (action[1],)))

    assert fatal_path is not None
    assert fatal_direction is not None

    for direction in fatal_path:
        assert controller.move(direction) is True
        block.finish()

    assert controller.lost is False
    assert block.fatal is False

    # Taking the fatal direction triggers fall animation and enters lost state
    assert controller.move(fatal_direction) is True
    assert controller.lost is True
    assert controller.animating is True
    assert block.fatal is True
    # The on_loss hook is deferred until the fall animation finishes
    assert lost_calls == []

    # New moves are rejected while animating/lost
    assert controller.move("U") is False

    # Finishing the fall triggers the on_loss callback
    block.finish()
    assert controller.animating is False
    assert controller.lost is True
    assert lost_calls == [True]

    # Undo steps back out of the fatal move and clears the loss state
    assert controller.undo() is True
    assert controller.lost is False
    block.finish()
    assert controller.animating is False

    # Trigger fatal move again, then test retry
    assert controller.move(fatal_direction) is True
    assert controller.lost is True
    block.finish()

    assert controller.retry() is True
    assert controller.lost is False
    assert controller.state == board.start()
    assert controller.moves == 0

