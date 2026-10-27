"""The shared search loop: counts, caps, ordering and the boundary to the contract (#18)."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from bloxorz.core.contracts import Caps, SearchResult, Stage, StageIndex
from bloxorz.core.engine import Board, cells
from bloxorz.core.stage import load_stage
from bloxorz.solvers import base
from bloxorz.solvers.base import Frontier, Node, search

ROOT = Path(__file__).resolve().parents[1]
STAGES = ROOT / "Source" / "bloxorz" / "core" / "stages"
FIXTURES = ROOT / "tests" / "fixtures"


def stage_for(tmp_path: Path, grid: list[str]) -> Stage:
    """A stage on disk, loaded through the frozen loader."""
    data = {
        "id": "T-01",
        "name": "probe",
        "group": "L1",
        "source": "original",
        "grid": grid,
        "switches": [],
        "bridges": [],
    }
    path = tmp_path / "probe.json"
    path.write_text(json.dumps(data), encoding="utf-8")
    return load_stage(path)


def already_at_the_goal() -> Stage:
    """A stage whose start cell is also the goal cell.

    The loader cannot produce one: ``S`` and ``G`` are different kinds, so they are different
    cells. The loop still has to handle it, because the contract says a solved run reports
    ``expanded == 0`` when the initial state already satisfies the goal.
    """
    index = StageIndex(
        rows=1,
        cols=1,
        kind=("goal",),
        bridge_of={},
        switch_at={},
        start=(0, 0),
        goal=(0, 0),
    )
    return Stage(
        id="T-00",
        name="already there",
        group="L1",
        grid=("G",),
        source="original",
        expected=None,
        index=index,
        bridges=(),
    )


@pytest.fixture
def spy_board(monkeypatch: pytest.MonkeyPatch) -> dict[str, object]:
    """A board that reports what the loop asked it for."""
    seen: dict[str, object] = {
        "built": 0,
        "successors_calls": 0,
        "children": 0,
        "states": [],
        "actions": [],
    }
    original = base.Board

    class Spy(original):  # type: ignore[misc, valid-type]
        def __init__(self, stage: Stage) -> None:
            super().__init__(stage)
            seen["built"] = int(seen["built"]) + 1

        def successors(self, state):
            found = super().successors(state)
            seen["successors_calls"] = int(seen["successors_calls"]) + 1
            seen["children"] = int(seen["children"]) + len(found)
            seen["states"].append(state)  # type: ignore[union-attr]
            seen["actions"].extend(action for _, action in found)  # type: ignore[union-attr]
            return found

    monkeypatch.setattr(base, "Board", Spy)
    return seen


def test_a_start_that_is_already_the_goal_is_solved_without_expanding() -> None:
    result = search(already_at_the_goal())
    assert result.status == "solved"
    assert result.path == ()
    assert result.counts.expanded == 0
    assert result.counts.generated == 1
    assert result.counts.frontier_peak == 1


def test_a_node_cap_of_zero_stops_before_the_first_expansion() -> None:
    stage = load_stage(FIXTURES / "FIX-01_straight_line.json")
    result = search(stage, Caps(node_cap=0))
    assert result.status == "cap"
    assert result.path == ()
    assert result.cost == 0.0
    assert result.counts.expanded == 0
    assert result.counts.generated == 1


def test_a_goal_reached_exactly_at_the_node_cap_is_still_solved() -> None:
    """The goal test runs before the node cap, so the boundary belongs to the solution."""
    stage = load_stage(FIXTURES / "FIX-01_straight_line.json")
    assert search(stage, Caps(node_cap=6)).status == "solved"
    assert search(stage, Caps(node_cap=5)).status == "cap"


def test_a_time_cap_of_zero_returns_counts_without_expanding() -> None:
    stage = load_stage(FIXTURES / "FIX-01_straight_line.json")
    result = search(stage, Caps(time_s=0))
    assert result.status == "cap"
    assert result.path == ()
    assert result.counts.expanded == 0
    assert result.counts.generated == 1
    assert result.counts.frontier_peak == 1


def test_a_stage_whose_goal_is_unreachable_is_unsolvable(tmp_path: Path) -> None:
    """The block walks the top row; the goal sits below a row of void.

    Hand-checked on ``ooSoo`` over a row of void and ``..G..``:

    - the start stands on ``S`` and reaches two lying blocks, left and right = 2 children.
    - each of those rolls back to the start it has already seen, and the frontier refuses it.
    - so expanded is 3, generated is 5, the frontier peak is 2, and the goal is never stood on.
    """
    stage = stage_for(tmp_path, ["ooSoo", ".....", "..G.."])
    result = search(stage)
    assert result.status == "unsolvable"
    assert result.path == ()
    assert result.counts.expanded == 3
    assert result.counts.generated == 5
    assert result.counts.frontier_peak == 2


def test_the_counters_are_incremented_at_the_frozen_points(tmp_path: Path) -> None:
    """Hand-checked on a three-cell corridor.

    ``SGo``: the block starts standing on ``S`` and can only roll right, to a lying block over
    ``G``. From there it can only roll left, back to the start it has already seen.

    - expanded: the standing start, then the lying block = 2.
    - generated: the root, plus one child per expansion = 3. The third child is the start again,
      and the frontier refuses it - but it was still offered, so it is counted.
    - frontier_peak: one node at a time = 1.
    """
    stage = stage_for(tmp_path, ["SGo"])
    result = search(stage)
    assert result.status == "unsolvable"
    assert result.path == ()
    assert result.counts.expanded == 2
    assert result.counts.generated == 3
    assert result.counts.frontier_peak == 1


def test_expanded_counts_the_nodes_whose_successors_were_evaluated(
    spy_board: dict[str, object],
) -> None:
    stage = load_stage(FIXTURES / "FIX-01_straight_line.json")
    result = search(stage)
    assert result.counts.expanded == spy_board["successors_calls"]


def test_generated_counts_every_child_offered_to_the_frontier(
    spy_board: dict[str, object],
) -> None:
    stage = load_stage(FIXTURES / "FIX-01_straight_line.json")
    result = search(stage)
    assert result.counts.generated == 1 + spy_board["children"]


def test_every_action_names_a_cube_and_a_direction(spy_board: dict[str, object]) -> None:
    stage = load_stage(STAGES / "L4-01_split_into_the_far_room.json")
    search(stage, Caps(node_cap=200))
    actions = spy_board["actions"]
    assert actions, "the split stage offers actions"
    assert all(isinstance(action, tuple) and len(action) == 2 for action in actions)
    assert all(action[1] in ("U", "D", "L", "R") for action in actions)
    assert all(action[0] >= 0 for action in actions)
    assert any(action[0] == 1 for action in actions), "a split stage moves the second cube too"


def test_the_returned_path_replays_through_the_engine_and_reaches_the_goal() -> None:
    stage = load_stage(FIXTURES / "FIX-01_straight_line.json")
    board = Board(stage)
    result = search(stage)
    assert result.status == "solved"

    state = board.start()
    cost = 0.0
    for action in result.path:
        moves = {act: nxt for nxt, act in board.successors(state)}
        assert action in moves, f"{action} is not legal here"
        cost += board.step_cost(state, action, moves[action])
        state = moves[action]
    assert board.is_goal(state)
    assert cost == result.cost
    assert len(result.path) == 6


def test_the_board_is_built_once_and_the_compiled_grid_is_never_re_read(
    spy_board: dict[str, object],
) -> None:
    """``Board(stage)`` is O(1): it holds the compiled stage and derives nothing."""

    class GridSpy:
        """A stage that counts how often the grid is read after it was compiled."""

        def __init__(self, stage: Stage) -> None:
            self._stage = stage
            self.grid_reads = 0

        @property
        def grid(self) -> tuple[str, ...]:
            self.grid_reads += 1
            return self._stage.grid

        def __getattr__(self, name: str) -> object:
            return getattr(self._stage, name)

    stage = GridSpy(load_stage(FIXTURES / "FIX-01_straight_line.json"))
    result = search(stage)  # type: ignore[arg-type]
    assert result.status == "solved"
    assert spy_board["built"] == 1
    assert stage.grid_reads == 0


def test_the_loop_reports_counts_and_never_times_or_measures_memory() -> None:
    stage = load_stage(FIXTURES / "FIX-01_straight_line.json")
    result = search(stage)
    assert set(SearchResult.__dataclass_fields__) == {"status", "path", "cost", "counts"}
    assert not hasattr(result, "time_s")
    assert not hasattr(result, "peak_mem_bytes")
    assert not hasattr(base, "tracemalloc")


def test_the_visited_set_is_keyed_on_the_canonical_state_key(
    spy_board: dict[str, object],
) -> None:
    """One board, one key: a split stage must not search the same position twice (#34)."""
    stage = load_stage(STAGES / "L4-01_split_into_the_far_room.json")
    search(stage, Caps(node_cap=200))
    states = spy_board["states"]
    boards = {(frozenset(cells(state)), state.bridges) for state in states}
    keys = {state.key() for state in states}
    assert len(boards) == len(keys)


def test_the_frontier_refuses_a_key_it_has_already_seen() -> None:
    stage = load_stage(FIXTURES / "FIX-01_straight_line.json")
    board = Board(stage)
    frontier = Frontier()
    root = Node(state=board.start())
    frontier.push(root)
    assert len(frontier) == 1
    frontier.push(root)
    assert len(frontier) == 1, "the second offer of one key is refused"
    assert frontier.pop() is root
    assert not frontier
