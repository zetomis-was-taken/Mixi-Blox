"""The stages the game can play, in the order the level select shows them.

Standard library plus ``bloxorz.core`` only: no Ursina. Both the level-select grid and the
"next level" button read their order from here, so the ordering is covered by a headless test.
"""

from __future__ import annotations

from pathlib import Path

from bloxorz.core.contracts import Stage
from bloxorz.core.stage import load_stage

STAGES_DIR = Path(__file__).resolve().parents[1] / "core" / "stages"


def stage_paths(directory: Path = STAGES_DIR) -> tuple[Path, ...]:
    """Every stage file, in play order; the file name carries ``L<group>-<number>``."""
    return tuple(sorted(Path(directory).glob("*.json"), key=lambda path: path.name))


def load_catalog(directory: Path = STAGES_DIR) -> tuple[Stage, ...]:
    """Load every stage once; the level select and the next-level chain share this tuple."""
    return tuple(load_stage(path) for path in stage_paths(directory))


def groups(catalog: tuple[Stage, ...]) -> tuple[tuple[str, tuple[Stage, ...]], ...]:
    """The catalog split by stage group, in catalog order."""
    grouped: dict[str, list[Stage]] = {}
    for stage in catalog:
        grouped.setdefault(stage.group, []).append(stage)
    return tuple((group, tuple(stages)) for group, stages in grouped.items())


def next_stage(catalog: tuple[Stage, ...], stage: Stage) -> Stage | None:
    """The stage after ``stage``, or ``None`` when it is the last one (or not in the catalog)."""
    for position, candidate in enumerate(catalog):
        if candidate.id == stage.id:
            following = position + 1
            return catalog[following] if following < len(catalog) else None
    return None
