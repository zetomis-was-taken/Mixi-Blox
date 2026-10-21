"""Cost policy for #7/#22, independent of movement and search algorithms."""

from __future__ import annotations

from bloxorz.core.contracts import Action, Stage, State

MINIMUM_ACTION_COST = 1.0
FRAGILE_CONTACT_SURCHARGE = 1.0


def action_cost(stage: Stage, state: State, action: Action, next_state: State) -> float:
    """Charge one roll plus one per newly contacted fragile tile.

    Entry is charged, not continued occupancy: an unmoved cube on fragile does
    not make the other cube's move expensive. Teleport destinations count as
    contacts too. Control selection is already encoded in ``action`` and has
    no separate edge or charge. Callers supply a legal engine transition.
    """
    before = {cell for cube in state.cubes for cell in cube}
    after = {cell for cube in next_state.cubes for cell in cube}
    fragile_contacts = sum(
        stage.index.kind[row * stage.index.cols + col] == "fragile" for row, col in after - before
    )
    return MINIMUM_ACTION_COST + FRAGILE_CONTACT_SURCHARGE * fragile_contacts
