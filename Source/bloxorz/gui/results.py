"""How a finished level and a solver run are reported: the numbers the HUD and the cards show.

Pure Python, so the formatting is tested headless while ``win_overlay.py`` and
``solver_overlay.py`` only draw it. The solver wording lives here for the same reason the move
counter does: the replay line in the HUD and the result card must not describe one run differently.
"""

from __future__ import annotations

from bloxorz.core.contracts import Counts, Status

# How each search outcome reads on the card's headline. ``solved`` also has a path to play; ``cap``
# and ``unsolvable`` do not, so their detail line says why there is no movie.
SOLVER_HEADINGS: dict[Status, str] = {
    "solved": "solved",
    "cap": "ran out of budget",
    "unsolvable": "found no solution",
}

SOLVER_NOTES: dict[Status, str] = {
    "solved": "already at the goal — nothing to roll",
    "cap": "the search stopped at its node or time limit — nothing to replay",
    "unsolvable": "every reachable position was exhausted — nothing to replay",
}

# The detail line when the search answered ``solved`` but its actions do not exist on this board:
# the card can still report the run, but there is no movie and nothing to watch again.
UNUSABLE_PATH = "the solver's path is not legal on this board — nothing to replay"


def elapsed_label(seconds: float) -> str:
    """``m:ss`` for the level clock, truncated to whole seconds."""
    minutes, remainder = divmod(max(int(seconds), 0), 60)
    return f"{minutes}:{remainder:02d}"


def result_line(moves: int, seconds: float) -> str:
    """The one line the overlay and the HUD show: the cost of the level so far."""
    noun = "move" if moves == 1 else "moves"
    return f"{moves} {noun}   |   {elapsed_label(seconds)}"


def replay_line(algorithm: str, step: int, total: int, paused: bool = False) -> str:
    """The HUD's playback line: which algorithm, and how far into its path the movie is."""
    state = " replay paused" if paused else " replay"
    return f"{algorithm}{state} — move {step} of {total}"


def solver_heading(algorithm: str, status: Status) -> str:
    """The card's headline: which algorithm ran, and how it ended."""
    return f"{algorithm} — {SOLVER_HEADINGS[status]}"


def solver_result_line(moves: int, cost: float) -> str:
    """The solved card's numbers: solution length and its cost under ``step_cost``."""
    noun = "move" if moves == 1 else "moves"
    return f"{moves} {noun}   |   cost {cost:g}"


def solver_detail(status: Status, moves: int, cost: float) -> str:
    """The card's second line: what the run produced, or why there is nothing to watch."""
    if status == "solved" and moves > 0:
        return solver_result_line(moves, cost)
    return SOLVER_NOTES[status]


def counts_line(counts: Counts) -> str:
    """The search's work, with thousands separators so a large run stays readable."""
    return (
        f"expanded {counts.expanded:,}   |   generated {counts.generated:,}"
        f"   |   frontier peak {counts.frontier_peak:,}"
    )
