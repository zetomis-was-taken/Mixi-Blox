"""Which mechanisms answer to the block, and how their value eases there.

The board view owns the entities; the rule behind their reaction lives here, the same way
``intro.py`` keeps the load timeline out of the views. Nothing here imports Ursina, so the rule is
covered headless (``tests/test_gui_reaction.py``) instead of by watching the window.
"""

from __future__ import annotations

from bloxorz.core.contracts import Cell, Kind, Stage, State
from bloxorz.core.engine import orientation

# Cells that answer to the block: the three switch plates and the fragile tile's own wobble.
REACTIVE_KINDS: frozenset[Kind] = frozenset({"fragile", "soft", "heavy", "split"})


def reactive_cells(stage: Stage) -> set[Cell]:
    """Every cell of ``stage`` that carries a mechanism able to react."""
    index = stage.index
    return {
        (row, col)
        for row in range(index.rows)
        for col in range(index.cols)
        if index.kind[row * index.cols + col] in REACTIVE_KINDS
    }


def load_per_cell(stage: Stage, state: State) -> dict[Cell, float]:
    """Target load (0 or 1) of every reactive cell in ``state``.

    A heavy plate answers only to the full standing block, the same weight rule the engine fires
    it by; soft and split plates answer to any piece touching them, and a fragile panel to any
    weight at all (a standing block can never rest on one — the engine forbids the move).

    Every reactive cell is a key, not just the loaded ones, so a plate the block has stepped off
    is told to rise again.
    """
    split = len(state.cubes) == 2
    loads = {cell: 0.0 for cell in reactive_cells(stage)}
    for cube in state.cubes:
        piece = orientation(cube, split)
        for cell in cube:
            if cell not in loads:
                continue
            switch = stage.index.switch_at.get(cell)
            if switch is not None and switch.type == "heavy" and piece != "standing":
                continue
            loads[cell] = 1.0
    return loads


def approach(current: float, target: float, step: float) -> float:
    """Move ``current`` toward ``target`` by at most ``step``, never past it.

    A constant step rather than a fraction of the gap keeps the animation frame-rate independent
    and gives every mechanism the same travel time whatever distance it has to cover.
    """
    gap = target - current
    if step <= 0.0 or abs(gap) <= step:
        return target
    return current + step if gap > 0.0 else current - step
