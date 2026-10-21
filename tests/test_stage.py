"""The loader and the compile behind it (docs/contracts.md § Stage)."""

from __future__ import annotations

import json
import re
from pathlib import Path

import pytest

from bloxorz.core.stage import StageError, load_stage

ROOT = Path(__file__).resolve().parents[1]
STAGES = ROOT / "Source" / "bloxorz" / "core" / "stages"
FIXTURES = ROOT / "tests" / "fixtures"

BASE: dict[str, object] = {
    "id": "T-01",
    "name": "probe",
    "group": "L1",
    "source": "original",
    "grid": [".....", ".S..G", "....."],
    "switches": [],
    "bridges": [],
}


def stage_file(tmp_path: Path, **overrides: object) -> Path:
    path = tmp_path / "stage.json"
    path.write_text(json.dumps({**BASE, **overrides}), encoding="utf-8")
    return path


def message(tmp_path: Path, **overrides: object) -> str:
    with pytest.raises(StageError) as caught:
        load_stage(stage_file(tmp_path, **overrides))
    return str(caught.value)


def test_derives_start_goal_and_size(tmp_path: Path) -> None:
    stage = load_stage(stage_file(tmp_path))
    assert (stage.index.start, stage.index.goal) == ((1, 1), (1, 4))
    assert (stage.index.rows, stage.index.cols) == (3, 5)


def test_kind_grid_is_row_major_and_one_kind_per_cell(tmp_path: Path) -> None:
    stage = load_stage(stage_file(tmp_path))
    assert stage.index.kind == (
        "void", "void", "void", "void", "void",
        "void", "start", "void", "void", "goal",
        "void", "void", "void", "void", "void",
    )


def test_compiles_bridge_and_switch_lookups(tmp_path: Path) -> None:
    stage = load_stage(
        stage_file(
            tmp_path,
            grid=["......", ".S+..G", "..=...", "......"],
            switches=[
                {
                    "type": "soft",
                    "pos": [1, 2],
                    "action": "toggle",
                    "bridges": [[2, 2]],
                    "teleport_cubes": None,
                }
            ],
            bridges=[{"pos": [2, 2], "initially_open": False}],
        )
    )
    assert stage.index.bridge_of == {(2, 2): 0}
    assert set(stage.index.switch_at) == {(1, 2)}
    assert stage.bridges[0].initially_open is False
    assert stage.index.kind[1 * 6 + 2] == "soft"
    assert stage.index.kind[2 * 6 + 2] == "bridge"


def test_rule_1_rejects_a_ragged_grid(tmp_path: Path) -> None:
    text = message(tmp_path, grid=[".....", ".S..G", "...."])
    assert "rule 1" in text
    assert re.search(rf"{re.escape(str(stage_file(tmp_path)))}:\d+", text), text


def test_rule_1_rejects_an_unknown_glyph(tmp_path: Path) -> None:
    assert "rule 1" in message(tmp_path, grid=[".....", ".S.?G", "....."])


def test_rule_2_rejects_two_starts(tmp_path: Path) -> None:
    assert "rule 2" in message(tmp_path, grid=[".....", ".S.SG", "....."])


def test_rule_2_rejects_no_goal(tmp_path: Path) -> None:
    assert "rule 2" in message(tmp_path, grid=[".....", ".S...", "....."])


@pytest.mark.parametrize("derived", ["start", "goal", "rows", "difficulty"])
def test_rule_3_rejects_a_derived_field(tmp_path: Path, derived: str) -> None:
    text = message(tmp_path, **{derived: [1, 1]})
    assert "rule 3" in text and derived in text


def test_rule_4_rejects_a_switch_on_the_wrong_glyph(tmp_path: Path) -> None:
    text = message(
        tmp_path,
        switches=[
            {
                "type": "soft",
                "pos": [1, 2],
                "action": "toggle",
                "bridges": None,
                "teleport_cubes": None,
            }
        ],
    )
    assert "rule 4" in text


def test_rule_4_rejects_a_marker_without_an_entry(tmp_path: Path) -> None:
    assert "rule 4" in message(tmp_path, grid=[".....", ".S+.G", "....."])


def test_rule_4_rejects_a_bridge_marker_without_an_entry(tmp_path: Path) -> None:
    assert "rule 4" in message(tmp_path, grid=[".....", ".S=.G", "....."])


def test_rule_5_rejects_a_switch_linking_an_unknown_bridge(tmp_path: Path) -> None:
    text = message(
        tmp_path,
        grid=["......", ".S+..G", "..=...", "......"],
        switches=[
            {
                "type": "soft",
                "pos": [1, 2],
                "action": "toggle",
                "bridges": [[3, 3]],
                "teleport_cubes": None,
            }
        ],
        bridges=[{"pos": [2, 2], "initially_open": True}],
    )
    assert "rule 5" in text


def test_a_bridge_entry_must_state_whether_it_starts_open(tmp_path: Path) -> None:
    text = message(
        tmp_path,
        grid=["......", ".S+..G", "..=...", "......"],
        switches=[
            {
                "type": "soft",
                "pos": [1, 2],
                "action": "toggle",
                "bridges": [[2, 2]],
                "teleport_cubes": None,
            }
        ],
        bridges=[{"pos": [2, 2]}],
    )
    assert "initially_open" in text, text


def test_split_switch_needs_two_teleport_cells(tmp_path: Path) -> None:
    text = message(
        tmp_path,
        grid=[".....", ".SY.G", "....."],
        switches=[
            {
                "type": "split",
                "pos": [1, 2],
                "action": None,
                "bridges": None,
                "teleport_cubes": [[2, 2]],
            }
        ],
    )
    assert "teleport_cubes" in text


def test_switch_entries_carry_every_field(tmp_path: Path) -> None:
    text = message(
        tmp_path,
        grid=[".....", ".S+.G", "....."],
        switches=[{"type": "soft", "pos": [1, 2]}],
    )
    assert "missing" in text


def test_a_split_switch_takes_no_action(tmp_path: Path) -> None:
    text = message(
        tmp_path,
        grid=[".....", ".SY.G", "....."],
        switches=[
            {
                "type": "split",
                "pos": [1, 2],
                "action": "toggle",
                "bridges": None,
                "teleport_cubes": [[2, 2], [2, 3]],
            }
        ],
    )
    assert "no action" in text, text


@pytest.mark.parametrize(("kind", "glyph"), [("soft", "+"), ("heavy", "X")])
def test_a_bridge_switch_names_its_action(tmp_path: Path, kind: str, glyph: str) -> None:
    text = message(
        tmp_path,
        grid=[".....", f".S{glyph}.G", "....."],
        switches=[
            {
                "type": kind,
                "pos": [1, 2],
                "action": None,
                "bridges": [[1, 3]],
                "teleport_cubes": None,
            }
        ],
        bridges=[{"pos": [1, 3], "initially_open": True}],
    )
    assert "takes an action" in text, text


def test_expected_holds_only_a_cost(tmp_path: Path) -> None:
    text = message(tmp_path, expected={"optimal_cost": 4, "path": "RRRR"})
    assert "optimal_cost" in text


def test_stage_ids_are_unique() -> None:
    """#5 names a stage by its id, so two files may never share one."""
    seen: dict[str, str] = {}
    for path in sorted(STAGES.glob("*.json")):
        stage_id = json.loads(path.read_text(encoding="utf-8"))["id"]
        assert stage_id not in seen, f"{path.name} reuses {stage_id} from {seen.get(stage_id)}"
        seen[stage_id] = path.name


def test_every_committed_stage_loads() -> None:
    """A file in core/stages that cannot load is a defect, not a hard benchmark."""
    for path in sorted(STAGES.glob("*.json")):
        load_stage(path)


def test_a_stage_without_expected_loads(tmp_path: Path) -> None:
    assert load_stage(stage_file(tmp_path)).expected is None


def test_the_fixtures_load_with_a_hand_computed_cost() -> None:
    """Only fixtures carry ``expected``. Benchmark stages have no hand-computed answer, so the glob
    is scoped by name; a directory-wide rule would fail on every stage #5 adds."""
    fixtures = sorted(FIXTURES.glob("FIX-*.json"))
    assert len(fixtures) >= 3
    for path in fixtures:
        stage = load_stage(path)
        assert stage.expected is not None, path.name
        assert stage.expected.optimal_cost > 0
        assert stage.group == "L1"
