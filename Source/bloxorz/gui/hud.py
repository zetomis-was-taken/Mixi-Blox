"""The corner HUD: what level this is, what it has cost so far, and what the keys do.

Four fixed-position ``Text`` entities: the level name and the live move/clock counter in the two top
corners, the key hints under the name, and the active cube on a split stage. Colour comes from
``theme.TEXT`` like every other HUD line, and the counter's wording comes from ``results.py``, so
the overlay and the HUD cannot describe the same run differently.

The counter is rewritten only when its rendered text changes — the clock is shown to the second, so
a frame that changes nothing never touches the font layout.
"""

from __future__ import annotations

from ursina import Text, destroy

from bloxorz.core.contracts import Stage

from . import results, theme

# UI space is [-0.8, 0.8] x [-0.5, 0.5] at 16:10 (docs/gui/window.md), so these are 0.02 in from
# the corners. The small lines are 0.8 of the level name's size.
LEFT_X = -0.78
RIGHT_X = 0.78
TOP_Y = 0.47
HINT_Y = 0.43
CUBE_Y = 0.39
SMALL_SCALE = 0.8

ROLL_HINT = "WASD / arrow keys to roll"
ACTION_HINT = "Z undo   |   R retry"


class Hud:
    """The HUD's lines, kept in step with the controller and removed with the scene."""

    def __init__(self, stage: Stage) -> None:
        self.level = Text(
            text=f"{stage.id}  {stage.name}",
            position=(LEFT_X, TOP_Y),
            origin=(-0.5, 0.5),
            color=theme.TEXT,
        )
        # The counter sits in the opposite corner, like the original game's move and time readouts.
        self.status = Text(
            position=(RIGHT_X, TOP_Y),
            origin=(0.5, 0.5),
            color=theme.TEXT,
            scale=SMALL_SCALE,
        )
        self.keys = Text(
            text=f"{ROLL_HINT}   |   {ACTION_HINT}",
            position=(LEFT_X, HINT_Y),
            origin=(-0.5, 0.5),
            color=theme.TEXT,
            scale=SMALL_SCALE,
        )
        # Only a split stage has a second cube to steer, so this line stays hidden otherwise.
        self.cube = Text(
            position=(LEFT_X, CUBE_Y),
            origin=(-0.5, 0.5),
            color=theme.TEXT,
            scale=SMALL_SCALE,
        )
        self.texts = (self.level, self.status, self.keys, self.cube)

    def refresh(self, moves: int, seconds: float, split: bool, active: int) -> None:
        """Show the run so far, and which cube the next input moves on a split stage."""
        _retitle(self.status, results.result_line(moves, seconds))
        self.cube.enabled = split
        if split:
            _retitle(self.cube, f"Cube {active + 1} of 2  |  Tab to switch")

    def teardown(self) -> None:
        """Remove every line; UI text is not a child of the scene it belongs to."""
        for text in self.texts:
            destroy(text)


def _retitle(text: Text, value: str) -> None:
    """Set a line's text only when it changed, so an unchanged frame costs nothing."""
    if text.text != value:
        text.text = value
