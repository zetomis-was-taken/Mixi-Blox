"""The transition model: roll table, passability, switches, split and merge (§ Board, ADRs)."""

from __future__ import annotations

import json
from collections import deque
from pathlib import Path

import pytest

from bloxorz.core.contracts import State
from bloxorz.core.engine import DIRECTIONS, Board, cells, orientation, pivot, roll
from bloxorz.core.stage import load_stage

ROOT = Path(__file__).resolve().parents[1]
STAGES = ROOT / "Source" / "bloxorz" / "core" / "stages"
FIXTURES = ROOT / "tests" / "fixtures"
LINE = ["......", ".SoooG", "......"]


def board_for(
    tmp_path: Path,
    grid: list[str],
    switches: list[dict[str, object]] | None = None,
    bridges: list[dict[str, object]] | None = None,
) -> Board:
    data = {
        "id": "T-01",
        "name": "probe",
        "group": "L1",
        "source": "original",
        "grid": grid,
        "switches": switches or [],
        "bridges": bridges or [],
    }
    path = tmp_path / "probe.json"
    path.write_text(json.dumps(data), encoding="utf-8")
    return Board(load_stage(path))


@pytest.mark.parametrize(
    ("cube", "direction", "expected"),
    [
        (((2, 2),), "U", ((0, 2), (1, 2))),
        (((2, 2),), "D", ((3, 2), (4, 2))),
        (((2, 2),), "L", ((2, 0), (2, 1))),
        (((2, 2),), "R", ((2, 3), (2, 4))),
        (((2, 2), (2, 3)), "L", ((2, 1),)),
        (((2, 2), (2, 3)), "R", ((2, 4),)),
        (((2, 2), (2, 3)), "U", ((1, 2), (1, 3))),
        (((2, 2), (2, 3)), "D", ((3, 2), (3, 3))),
        (((2, 2), (3, 2)), "U", ((1, 2),)),
        (((2, 2), (3, 2)), "D", ((4, 2),)),
        (((2, 2), (3, 2)), "L", ((2, 1), (3, 1))),
        (((2, 2), (3, 2)), "R", ((2, 3), (3, 3))),
    ],
)
def test_roll_table(cube: tuple, direction: str, expected: tuple) -> None:
    assert roll(cube, direction, split=False) == expected


@pytest.mark.parametrize(
    ("direction", "expected"),
    [("U", ((1, 2),)), ("D", ((3, 2),)), ("L", ((2, 1),)), ("R", ((2, 3),))],
)
def test_a_lone_cube_steps_one_cell(direction: str, expected: tuple) -> None:
    assert roll(((2, 2),), direction, split=True) == expected


def test_orientation_is_derived_from_the_piece() -> None:
    assert orientation(((2, 2),), split=False) == "standing"
    assert orientation(((2, 2),), split=True) == "cube"
    assert orientation(((2, 2), (2, 3)), split=True) == "lying_h"
    assert orientation(((2, 2), (3, 2)), split=True) == "lying_v"


def test_state_key_has_arity_two_and_covers_every_field() -> None:
    open_bridge = State(cubes=(((2, 2),),), bridges=(True,))
    closed_bridge = State(cubes=(((2, 2),),), bridges=(False,))
    assert len(open_bridge.key()) == 2
    assert open_bridge.key() != closed_bridge.key(), "bridges are part of the key (#6)"
    assert State(cubes=(((2, 2),),), bridges=(True,)) == open_bridge


def test_the_key_does_not_depend_on_the_order_the_cubes_were_written_in() -> None:
    forward = State(cubes=(((1, 4),), ((1, 2),)), bridges=(True,))
    backward = State(cubes=(((1, 2),), ((1, 4),)), bridges=(True,))
    assert forward == backward, "one board, one spelling (#34)"
    assert forward.key() == backward.key()
    assert len(forward.key()) == 2


def test_a_split_state_and_an_unsplit_state_never_collide() -> None:
    unsplit = State(cubes=(((1, 3), (1, 4)),), bridges=(True,))
    split = State(cubes=(((1, 3),), ((1, 4),)), bridges=(True,))
    assert set(cells(unsplit)) == set(cells(split)), "same cells, different meaning"
    assert unsplit.key() != split.key()


def test_one_board_reached_two_ways_has_one_key() -> None:
    """The regression #34 exists for.

    A split stage reaches the same pair of cells with the cubes in either order. Both
    spellings are the same board, so they are the same state and the same key.
    """
    board = Board(load_stage(STAGES / "L4-01_split_into_the_far_room.json"))

    by_board: dict[tuple, set[tuple]] = {}
    start = board.start()
    seen = {start.key()}
    queue = deque([start])
    while queue:
        state = queue.popleft()
        board_id = (frozenset(cells(state)), state.bridges)
        by_board.setdefault(board_id, set()).add(state.key())
        for next_state, _ in board.successors(state):
            if next_state.key() not in seen:
                seen.add(next_state.key())
                queue.append(next_state)

    duplicated = {b: keys for b, keys in by_board.items() if len(keys) > 1}
    assert not duplicated, f"{len(duplicated)} boards reached with two different keys"


def test_cells_flattens_and_pivot_is_the_smaller_cell() -> None:
    state = State(cubes=(((2, 3), (2, 4)),), bridges=())
    assert cells(state) == ((2, 3), (2, 4))
    assert pivot(state) == (2, 3)


def test_is_goal_needs_a_standing_block_on_the_goal_cell(tmp_path: Path) -> None:
    board = board_for(tmp_path, LINE)
    goal = (1, 5)
    assert board.is_goal(State(cubes=((goal,),), bridges=()))
    assert not board.is_goal(State(cubes=((goal, (1, 4)),), bridges=()))
    assert not board.is_goal(State(cubes=(((1, 1),),), bridges=()))


def test_step_cost_is_one_move(tmp_path: Path) -> None:
    board = board_for(tmp_path, LINE)
    start = board.start()
    next_state, action = board.successors(start)[0]
    assert board.step_cost(start, action, next_state) == 1.0


def test_unsplit_actions_name_cube_zero(tmp_path: Path) -> None:
    board = Board(load_stage(FIXTURES / "FIX-01_straight_line.json"))
    assert {action[0] for _, action in board.successors(board.start())} == {0}


def test_a_move_off_the_board_is_absent(tmp_path: Path) -> None:
    board = board_for(tmp_path, LINE)
    start = board.start()
    assert {action[1] for _, action in board.successors(start)} == {"R"}


def test_fragile_holds_a_lying_block_and_a_lone_cube(tmp_path: Path) -> None:
    board = board_for(tmp_path, ["......", ".Soff.", "......", ".....G"])
    assert not board.passable((1, 3), "standing", ())
    assert board.passable((1, 3), "lying_h", ())
    assert board.passable((1, 3), "cube", ())


def test_standing_on_fragile_is_not_generated(tmp_path: Path) -> None:
    board = board_for(tmp_path, ["......", ".Soff.", "......", ".....G"])
    start = board.start()
    (lying, action), = board.successors(start)
    assert action == (0, "R")
    assert cells(lying) == ((1, 2), (1, 3)), "a lying block may lie across fragile (ADR-003)"

    onwards = {move: state for state, (_, move) in board.successors(lying)}
    assert "R" not in onwards, "standing on fragile is an absent move (ADR-003)"
    assert "L" in onwards


def test_a_move_reports_the_cells_it_reaches(tmp_path: Path) -> None:
    board = board_for(tmp_path, LINE)
    start = board.start()
    (moved, action), = board.successors(start)
    reported = board.outcome(start, action)
    assert reported.kind == "moves"
    assert reported.state == moved, "the same transition, spelled once"


def test_a_move_into_void_is_refused_and_carries_no_state(tmp_path: Path) -> None:
    board = board_for(tmp_path, LINE)
    blocked = board.outcome(board.start(), (0, "L"))
    assert blocked.kind == "refused", "void is a wall, not a fall (ADR-004)"
    assert blocked.state is None, "a refused action changed nothing to render"


def test_a_standing_block_that_breaks_a_fragile_tile_is_fatal(tmp_path: Path) -> None:
    board = board_for(tmp_path, ["......", ".Soff.", "......", ".....G"])
    (lying, _), = board.successors(board.start())
    fell = board.outcome(lying, (0, "R"))
    assert fell.kind == "fatal", "§2.5 breaks the tile under a standing block (ADR-003)"
    assert cells(fell.state) == ((1, 4),), "the renderer animates the fall from here"
    assert fell.state.bridges == lying.bridges


def test_a_fatal_action_is_absent_from_successors(tmp_path: Path) -> None:
    board = board_for(tmp_path, ["......", ".Soff.", "......", ".....G"])
    (lying, _), = board.successors(board.start())
    assert board.outcome(lying, (0, "R")).kind == "fatal"
    reachable = {action[1] for _, action in board.successors(lying)}
    assert "R" not in reachable, "a fatal action still yields no successor"


def test_successors_and_outcome_never_disagree(tmp_path: Path) -> None:
    board = board_for(
        tmp_path,
        ["......", ".S+=G.", ".oooo.", ".oooo.", "......"],
        switches=[
            {
                "type": "soft",
                "pos": [1, 2],
                "action": "toggle",
                "bridges": [[1, 3]],
                "teleport_cubes": None,
            }
        ],
        bridges=[{"pos": [1, 3], "initially_open": True}],
    )
    seen = {board.start().key()}
    frontier = [board.start()]
    while frontier:
        state = frontier.pop()
        legal = {action: next_state for next_state, action in board.successors(state)}
        for action, next_state in legal.items():
            reported = board.outcome(state, action)
            assert reported.kind == "moves", f"{action} is legal, so it cannot be refused or fatal"
            assert reported.state == next_state, "the two answers must agree on the result"
            if next_state.key() not in seen:
                seen.add(next_state.key())
                frontier.append(next_state)
        every = [
            (index, direction) for index in range(len(state.cubes)) for direction in DIRECTIONS
        ]
        for action in every:
            if action not in legal:
                assert board.outcome(state, action).kind != "moves", f"{action} is absent"
    assert len(seen) > 2, "the walk has to branch for the agreement to mean anything"


def test_a_closed_bridge_is_impassable(tmp_path: Path) -> None:
    board = board_for(
        tmp_path,
        ["......", ".So=G.", "......"],
        bridges=[{"pos": [1, 3], "initially_open": False}],
    )
    start = board.start()
    assert not board.passable((1, 3), "lying_h", start.bridges)
    assert board.successors(start) == [], "the only move would park the block on a closed bridge"


def test_a_soft_switch_toggles_its_bridge(tmp_path: Path) -> None:
    board = board_for(
        tmp_path,
        ["......", ".So+o.", "..=...", ".G...."],
        switches=[
            {
                "type": "soft",
                "pos": [1, 3],
                "action": "toggle",
                "bridges": [[2, 2]],
                "teleport_cubes": None,
            }
        ],
        bridges=[{"pos": [2, 2], "initially_open": False}],
    )
    start = board.start()
    assert start.bridges == (False,)
    (next_state, action), = board.successors(start)
    assert action == (0, "R")
    assert next_state.bridges == (True,), "any contact fires a soft switch"


@pytest.mark.parametrize(("mode", "expected"), [("on", (True,)), ("off", (False,))])
def test_a_one_way_mode_sets_the_bridge_instead_of_inverting_it(
    tmp_path: Path, mode: str, expected: tuple[bool, ...]
) -> None:
    """`on` and `off` set the bridge, so pressing the same switch twice leaves it where it was.

    The original game uses both one-way modes, on the same bridge, in the same level; a vocabulary
    of {toggle, permanent} would have collapsed them into one word.
    """
    board = board_for(
        tmp_path,
        ["......", ".So+o.", "..=...", ".G...."],
        switches=[
            {
                "type": "soft",
                "pos": [1, 3],
                "action": mode,
                "bridges": [[2, 2]],
                "teleport_cubes": None,
            }
        ],
        bridges=[{"pos": [2, 2], "initially_open": mode == "off"}],
    )
    start = board.start()
    (pressed, _), = board.successors(start)
    assert pressed.bridges == expected

    back = {action: state for state, action in board.successors(pressed)}[(0, "L")]
    (again, _), = board.successors(back)
    assert again.bridges == expected, "a one-way mode is a set, not an inversion"


def test_a_heavy_switch_ignores_a_lying_block(tmp_path: Path) -> None:
    board = board_for(
        tmp_path,
        ["....", ".S..", ".o.=", ".X..", ".o.G"],
        switches=[
            {
                "type": "heavy",
                "pos": [3, 1],
                "action": "toggle",
                "bridges": [[2, 3]],
                "teleport_cubes": None,
            }
        ],
        bridges=[{"pos": [2, 3], "initially_open": True}],
    )
    start = board.start()
    (lying, _), = board.successors(start)
    assert cells(lying) == ((2, 1), (3, 1))
    assert lying.bridges == (True,), "a heavy switch fires for standing only (§ Board)"


def test_a_heavy_switch_fires_for_a_standing_block(tmp_path: Path) -> None:
    board = board_for(
        tmp_path,
        ["....", ".S..", ".o.=", ".o..", ".X.G"],
        switches=[
            {
                "type": "heavy",
                "pos": [4, 1],
                "action": "off",
                "bridges": [[2, 3]],
                "teleport_cubes": None,
            }
        ],
        bridges=[{"pos": [2, 3], "initially_open": True}],
    )
    (lying, _), = board.successors(board.start())
    moves = {action: state for state, action in board.successors(lying)}
    standing = moves[(0, "D")]
    assert cells(standing) == ((4, 1),)
    assert standing.bridges == (False,), "the `off` mode closes the bridge"


def test_a_switch_may_not_close_a_bridge_under_the_block(tmp_path: Path) -> None:
    board = board_for(
        tmp_path,
        ["......", ".S+=G.", ".o....", ".o...."],
        switches=[
            {
                "type": "soft",
                "pos": [1, 2],
                "action": "toggle",
                "bridges": [[1, 3]],
                "teleport_cubes": None,
            }
        ],
        bridges=[{"pos": [1, 3], "initially_open": True}],
    )
    start = board.start()
    moves = {action[1] for _, action in board.successors(start)}
    assert "R" not in moves, "the action is not generated (ADR-005)"
    assert "D" in moves
    fell = board.outcome(start, (0, "R"))
    assert fell.kind == "fatal", "the switch closes the bridge the block now spans (ADR-005)"
    assert fell.state == State(cubes=(((1, 2), (1, 3)),), bridges=(False,))
    assert board.outcome(start, (0, "D")).kind == "moves"


def test_a_lone_cube_does_not_fire_a_split_switch(tmp_path: Path) -> None:
    board = split_board(tmp_path)
    lone = State(cubes=(((2, 4),), ((3, 2),)), bridges=())
    landing = {action: state for state, action in board.successors(lone)}[(1, "D")]
    assert (4, 2) in cells(landing), "a lone cube may stand on Y and nothing happens"
    assert len(landing.cubes) == 2


def split_board(tmp_path: Path) -> Board:
    return board_for(
        tmp_path,
        [
            "........",
            "..S.....",
            "..o.of..",
            "..o.o...",
            "..Y.ooG.",
            "........",
        ],
        switches=[
            {
                "type": "split",
                "pos": [4, 2],
                "action": None,
                "bridges": None,
                "teleport_cubes": [[2, 4], [4, 4]],
            }
        ],
    )


def test_a_split_switch_sends_two_cubes_to_its_targets(tmp_path: Path) -> None:
    board = split_board(tmp_path)
    (hovering, _), = board.successors(board.start())
    moves = {action: state for state, action in board.successors(hovering)}
    split = moves[(0, "D")]
    assert cells(split) == ((2, 4), (4, 4))
    assert len(split.cubes) == 2


def test_a_split_switch_fires_again_after_a_merge(tmp_path: Path) -> None:
    board = split_board(tmp_path)
    hovering = State(cubes=(((2, 2), (3, 2)),), bridges=())
    landing = {action: state for state, action in board.successors(hovering)}
    first = landing[(0, "D")]
    again = {action: state for state, action in board.successors(hovering)}[(0, "D")]
    assert first == again, "no per-stage memory, so the same landing splits the same way"
    assert orientation(first.cubes[0], split=True) == "cube"


def test_merged_cubes_lie_along_the_axis_they_are_adjacent_on(tmp_path: Path) -> None:
    board = split_board(tmp_path)

    column = State(cubes=(((2, 4),), ((4, 4),)), bridges=())
    moves = {action: state for state, action in board.successors(column)}
    vertical = moves[(0, "D")]
    assert cells(vertical) == ((3, 4), (4, 4))
    assert orientation(vertical.cubes[0], split=False) == "lying_v", "column pair (ADR-007)"
    assert moves[(1, "R")].cubes == (((2, 4),), ((4, 5),)), "a wide pair stays split"

    row = State(cubes=(((4, 4),), ((4, 6),)), bridges=())
    moves = {action: state for state, action in board.successors(row)}
    horizontal = moves[(0, "R")]
    assert cells(horizontal) == ((4, 5), (4, 6))
    assert orientation(horizontal.cubes[0], split=False) == "lying_h", "row pair (ADR-007)"


def test_a_lone_cube_crosses_a_fragile_tile(tmp_path: Path) -> None:
    board = split_board(tmp_path)
    split = State(cubes=(((2, 4),), ((4, 4),)), bridges=())
    moves = {action: state for state, action in board.successors(split)}
    onto_fragile = moves[(0, "R")]
    assert onto_fragile.cubes[0] == ((2, 5),), "one unit on one tile is safe (ADR-003)"


def test_two_cubes_never_share_a_cell_or_swap(tmp_path: Path) -> None:
    board = split_board(tmp_path)
    split = State(cubes=(((2, 4),), ((3, 4),)), bridges=())
    moves = {action: state for state, action in board.successors(split)}
    assert (0, "D") not in moves, "cube 0 cannot enter cube 1's cell (ADR-006)"
    for state, action in board.successors(split):
        assert len(set(cells(state))) == len(cells(state))
        assert action[0] in {0, 1}


@pytest.mark.parametrize(
    ("stage_id", "moves"),
    [("FIX-01", "RRRRRR"), ("FIX-02", "RRDD"), ("FIX-03", "DDRR")],
)
def test_fixture_plans_reach_the_goal_at_the_hand_computed_cost(
    stage_id: str, moves: str
) -> None:
    path = next(FIXTURES.glob(f"{stage_id}_*.json"))
    stage = load_stage(path)
    board = Board(stage)
    state = board.start()
    cost = 0.0
    for letter in moves:
        legal = {action[1]: (next_state, action) for next_state, action in board.successors(state)}
        assert letter in legal, f"{stage_id}: {letter} is not legal from {cells(state)}"
        next_state, action = legal[letter]
        cost += board.step_cost(state, action, next_state)
        state = next_state
    assert board.is_goal(state), f"{stage_id}: the plan does not finish on the goal"
    assert stage.expected is not None
    assert cost == stage.expected.optimal_cost


def switch_and_split_board(tmp_path: Path) -> Board:
    """A split whose first target lands on a soft switch wired to a closed bridge."""
    return board_for(
        tmp_path,
        [
            "........oo",
            ".So.......",
            ".o........",
            ".o........",
            ".Y....+...",
            "........=G",
        ],
        switches=[
            {
                "type": "soft",
                "pos": [4, 6],
                "action": "toggle",
                "bridges": [[5, 8]],
                "teleport_cubes": None,
            },
            {
                "type": "split",
                "pos": [4, 1],
                "action": None,
                "bridges": None,
                "teleport_cubes": [[4, 6], [0, 8]],
            },
        ],
        bridges=[{"pos": [5, 8], "initially_open": False}],
    )


def test_a_teleport_landing_presses_a_soft_switch_once(tmp_path: Path) -> None:
    board = switch_and_split_board(tmp_path)
    lying = {action: state for state, action in board.successors(board.start())}[(0, "D")]
    split = {action: state for state, action in board.successors(lying)}[(0, "D")]
    assert split.cubes == (((0, 8),), ((4, 6),))
    assert split.bridges == (True,), "landing on a switch is a contact"


def test_a_parked_cube_does_not_press_its_switch_again(tmp_path: Path) -> None:
    board = switch_and_split_board(tmp_path)
    parked = State(cubes=(((0, 8),), ((4, 6),)), bridges=(True,))
    moves = {action: state for state, action in board.successors(parked)}
    assert moves[(0, "R")].bridges == (True,), "occupancy is not contact, so nothing fires"


def test_a_split_switch_does_not_chain(tmp_path: Path) -> None:
    board = board_for(
        tmp_path,
        ["......o.", ".So.....", ".o......", ".o......", ".Y......", "..Y...G."],
        switches=[
            {
                "type": "split",
                "pos": [4, 1],
                "action": None,
                "bridges": None,
                "teleport_cubes": [[5, 2], [0, 6]],
            },
            {
                "type": "split",
                "pos": [5, 2],
                "action": None,
                "bridges": None,
                "teleport_cubes": [[1, 7], [2, 7]],
            },
        ],
    )
    hovering = State(cubes=(((2, 1), (3, 1)),), bridges=())
    landed = {action: state for state, action in board.successors(hovering)}[(0, "D")]
    assert landed.cubes == (((0, 6),), ((5, 2),)), "one landing, no second split"


def test_a_split_whose_targets_are_adjacent_merges_at_once(tmp_path: Path) -> None:
    board = board_for(
        tmp_path,
        ["........", "..S.....", "..o.....", "..o.oo..", "..Y.....", ".......G"],
        switches=[
            {
                "type": "split",
                "pos": [4, 2],
                "action": None,
                "bridges": None,
                "teleport_cubes": [[3, 4], [3, 5]],
            }
        ],
    )
    hovering = State(cubes=(((2, 2), (3, 2)),), bridges=())
    landed = {action: state for state, action in board.successors(hovering)}[(0, "D")]
    assert landed.cubes == (((3, 4), (3, 5)),), (
        "adjacent targets merge on arrival (ADR-007), so such a Y is a free teleport"
    )
