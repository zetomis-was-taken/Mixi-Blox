"""Search algorithms for a compiled :mod:`bloxorz` stage.

The shared loop lives in :mod:`bloxorz.solvers.base`. Each algorithm module adds one frontier
ordering and exposes the frozen ``solve(stage, caps)`` (#18).

``ALGORITHMS`` is the registry the GUI's Solve panel builds its cards from: display name (the card
label) -> solver, in card order. Adding an algorithm is one dictionary entry; nothing in ``gui/``
changes. ``Solve`` repeats the alias in ``gui.replay`` because ``solvers`` may not import ``gui``.
"""

from __future__ import annotations

from collections.abc import Callable

from bloxorz.core.contracts import Caps, SearchResult, Stage

from . import astar, bfs, dfs, ucs

Solve = Callable[[Stage, Caps], SearchResult]

ALGORITHMS: dict[str, Solve] = {
    "BFS": bfs.solve,
    "DFS": dfs.solve,
    "UCS": ucs.solve,
    "A*": astar.solve,
}
