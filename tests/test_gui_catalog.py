"""Headless checks for the stage catalog the level select and the next-level chain read.

Ursina is not imported: ``catalog`` is ``bloxorz.core`` plus ``pathlib``, so the play order the
game shows is pinned here rather than by watching the window.
"""

from __future__ import annotations

from dataclasses import replace
from pathlib import Path

from bloxorz.gui.catalog import groups, load_catalog, next_stage, stage_paths

ROOT = Path(__file__).resolve().parents[1]
STAGES = ROOT / "Source" / "bloxorz" / "core" / "stages"


def test_the_catalog_holds_every_stage_file_in_play_order() -> None:
    stages = load_catalog()

    assert len(stages) == len(stage_paths()) == len(tuple(STAGES.glob("*.json")))
    assert [stage.id for stage in stages] == [
        "L1-01",
        "L1-02",
        "L1-03",
        "L2-01",
        "L2-02",
        "L3-01",
        "L3-02",
        "L3-03",
        "L4-01",
        "L4-02",
    ]
    assert [stage.group for stage in stages] == [
        "L1", "L1", "L1", "L2", "L2", "L3", "L3", "L3", "L4", "L4"
    ]


def test_groups_splits_the_catalog_by_stage_group() -> None:
    stages = load_catalog()

    grouped = groups(stages)

    assert [group for group, _ in grouped] == ["L1", "L2", "L3", "L4"]
    assert [tuple(stage.id for stage in levels) for _, levels in grouped] == [
        ("L1-01", "L1-02", "L1-03"),
        ("L2-01", "L2-02"),
        ("L3-01", "L3-02", "L3-03"),
        ("L4-01", "L4-02"),
    ]
    assert [stage for _, levels in grouped for stage in levels] == list(stages)


def test_next_stage_chains_to_the_end_of_the_catalog() -> None:
    stages = load_catalog()

    following = [next_stage(stages, stage) for stage in stages]

    assert [stage.id if stage else None for stage in following] == [
        "L1-02",
        "L1-03",
        "L2-01",
        "L2-02",
        "L3-01",
        "L3-02",
        "L3-03",
        "L4-01",
        "L4-02",
        None,
    ]


def test_a_stage_outside_the_catalog_has_no_next_level() -> None:
    stages = load_catalog()

    # ``--stage`` can load a file the level select does not list, and that level must still end.
    stray = replace(stages[0], id="X-99")

    assert next_stage(stages, stray) is None
