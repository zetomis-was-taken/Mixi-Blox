"""The win overlay: what the level cost, and the three ways out of it.

A cream card over the solved board, the way the original game interrupts a cleared level. It is the
only thing that takes input once the block is home: the scene stops reading movement keys, and this
entity answers ``Enter`` (next level), ``R`` (retry) and ``Esc`` (level select). The same actions
are clickable cards, so the flow does not depend on knowing the keys.

The numbers come from ``results.py``; a level that has no successor simply has no next card and a
stage loaded from an arbitrary ``--stage`` path therefore still ends cleanly.
"""

from __future__ import annotations

from collections.abc import Callable

from ursina import Entity, Text, camera

from bloxorz.core.contracts import Stage

from . import results, theme, widgets

PANEL_SCALE = (0.94, 0.34)

TITLE = "Level cleared"
TITLE_Y = 0.13
STAGE_Y = 0.075
RESULT_Y = 0.025

CARD_SCALE = (0.24, 0.075)
CARD_PITCH = 0.28
CARD_Y = -0.06
HINT_Y = -0.14


class WinOverlay(Entity):
    """A modal results card: the move count and clock, then next level / retry / level select."""

    def __init__(
        self,
        stage: Stage,
        moves: int,
        seconds: float,
        on_next: Callable[[], None] | None,
        on_retry: Callable[[], None],
        on_levels: Callable[[], None],
    ) -> None:
        # UI entities belong to the UI camera, so their coordinates are screen fractions.
        super().__init__(name="win-overlay", parent=camera.ui)
        self.on_next = on_next
        self.on_retry = on_retry
        self.on_levels = on_levels
        self._build(stage, moves, seconds)

    def input(self, key: str) -> None:
        """The keyboard route through the overlay, mirroring its cards."""
        if key == "enter" and self.on_next is not None:
            self.on_next()
        elif key == "r":
            self.on_retry()
        elif key == "escape":
            self.on_levels()

    def _build(self, stage: Stage, moves: int, seconds: float) -> None:
        Entity(
            parent=self,
            model="quad",
            color=theme.OVERLAY_PANEL,
            scale=PANEL_SCALE,
            z=widgets.PANEL_Z,
        )
        Text(
            parent=self,
            text=TITLE,
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
            text=results.result_line(moves, seconds),
            origin=(0, 0),
            y=RESULT_Y,
            scale=1.1,
            color=theme.TEXT,
        )
        self._build_cards()
        Text(
            parent=self,
            text=self._key_hints(),
            origin=(0, 0),
            y=HINT_Y,
            scale=0.6,
            color=theme.TEXT,
        )

    def _build_cards(self) -> None:
        """Lay the available actions out as a centred row of cards, most useful on the left."""
        actions: list[tuple[str, Callable[[], None], bool]] = []
        if self.on_next is not None:
            actions.append(("Next level", self.on_next, True))
        actions.append(("Retry", self.on_retry, False))
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
        keys = [("Enter", "next level")] if self.on_next is not None else []
        keys += [("R", "retry"), ("Esc", "levels")]
        return "      ".join(f"{key} {label}" for key, label in keys)
