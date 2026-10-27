"""The solver's result card: how the run ended, what it cost, and the way out (Ursina).

Shown when a solver has answered: the algorithm and its outcome, the solution's length and cost (or
why there is nothing to watch), the counts the search collected, and up to three ways on — watch it
again, close back to the board, or return to the level select. Modal like the win overlay: the
level scene stops reading movement keys while it is up, and this entity answers ``Enter`` (watch
again) and ``Esc`` (close).

The numbers and wording all come from ``results.py``, so the card and the HUD's replay line cannot
describe one run differently. A solver run never raises ``WinOverlay``: that card reports the
player's own moves and clock, which a playback does not touch.
"""

from __future__ import annotations

from collections.abc import Callable

from ursina import Entity, Text, camera

from bloxorz.core.contracts import SearchResult, Stage

from . import results, theme, widgets

PANEL_SCALE = (0.94, 0.38)

TITLE_Y = 0.15
STAGE_Y = 0.095
DETAIL_Y = 0.04
COUNTS_Y = -0.005
COUNTS_SCALE = 0.6

CARD_SCALE = (0.24, 0.075)
CARD_PITCH = 0.28
CARD_Y = -0.085
HINT_Y = -0.16


class SolverOverlay(Entity):
    """A modal card: the run's outcome and numbers, then watch again / close / levels."""

    def __init__(
        self,
        stage: Stage,
        algorithm: str,
        result: SearchResult,
        on_replay: Callable[[], None] | None,
        on_close: Callable[[], None],
        on_levels: Callable[[], None],
    ) -> None:
        # UI entities belong to the UI camera, so their coordinates are screen fractions.
        super().__init__(name="solver-overlay", parent=camera.ui)
        self.on_replay = on_replay
        self.on_close = on_close
        self.on_levels = on_levels
        self._build(stage, algorithm, result)

    def input(self, key: str) -> None:
        """The keyboard route through the card, mirroring its buttons."""
        if key == "enter" and self.on_replay is not None:
            self.on_replay()
        elif key == "escape":
            self.on_close()

    def _build(self, stage: Stage, algorithm: str, result: SearchResult) -> None:
        Entity(
            parent=self,
            model="quad",
            color=theme.OVERLAY_PANEL,
            scale=PANEL_SCALE,
            z=widgets.PANEL_Z,
        )
        Text(
            parent=self,
            text=results.solver_heading(algorithm, result.status),
            origin=(0, 0),
            y=TITLE_Y,
            scale=1.4,
            color=theme.TEXT,
        )
        Text(
            parent=self,
            text=f"{stage.id}  {stage.name}",
            origin=(0, 0),
            y=STAGE_Y,
            scale=0.8,
            color=theme.TEXT,
        )
        Text(
            parent=self,
            text=results.solver_detail(result.status, len(result.path), result.cost),
            origin=(0, 0),
            y=DETAIL_Y,
            scale=1.0,
            color=theme.TEXT,
        )
        Text(
            parent=self,
            text=results.counts_line(result.counts),
            origin=(0, 0),
            y=COUNTS_Y,
            scale=COUNTS_SCALE,
            color=theme.TEXT,
        )
        self._build_cards()
        Text(
            parent=self,
            text=self._key_hints(),
            origin=(0, 0),
            y=HINT_Y,
            scale=COUNTS_SCALE,
            color=theme.TEXT,
        )

    def _build_cards(self) -> None:
        """Lay the available actions out as a centred row, the most useful one on the left."""
        actions: list[tuple[str, Callable[[], None], bool]] = []
        if self.on_replay is not None:
            actions.append(("Watch again", self.on_replay, True))
        actions.append(("Close", self.on_close, False))
        actions.append(("Levels", self.on_levels, False))

        start = -CARD_PITCH * (len(actions) - 1) / 2.0
        for position, (label, callback, primary) in enumerate(actions):
            widgets.card(
                parent=self,
                text=label,
                position=(start + position * CARD_PITCH, CARD_Y),
                scale=CARD_SCALE,
                color=theme.TILE_BRIDGE if primary else theme.TILE_FLOOR,
                text_color=theme.TILE_FLOOR if primary else theme.BACKGROUND,
                on_click=callback,
            )

    def _key_hints(self) -> str:
        keys = [("Enter", "watch again")] if self.on_replay is not None else []
        keys += [("Esc", "close")]
        return "      ".join(f"{key} {label}" for key, label in keys)
