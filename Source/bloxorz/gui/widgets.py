"""The clickable cards the menu screens are built from (Ursina).

One place decides how a card looks — a flat quad with centred text — so the level select and the
win overlay cannot drift apart. The quad model is set explicitly: ``Button``'s default rounded model
folds the card's aspect ratio into its own geometry, which makes a ``scale`` mean something
different from every other UI entity. Colours still come from ``theme.py``; the caller picks which
pair a card uses and says what happens on click.
"""

from __future__ import annotations

from collections.abc import Callable

from ursina import Button, Entity, Text

# Label size, in the same units as the HUD's ``Text`` (1 is the size of the level name).
TEXT_SCALE = 0.7

# Cards sit just behind their label, so the text is never hidden by the quad it belongs to.
CARD_Z = 0.01
TEXT_Z = -0.01

# Depth grows away from the UI camera, so a panel that backs a set of cards must be further out
# than the cards themselves. A panel at the cards' depth would draw over them and, because the
# panel is translucent cream, wash every card and its label out.
PANEL_Z = 0.02


def card(
    parent: Entity,
    text: str,
    position: tuple[float, float],
    scale: tuple[float, float],
    color,
    text_color,
    on_click: Callable[[], None],
) -> Button:
    """A flat card of ``scale`` UI units with a centred label, calling ``on_click`` when clicked."""
    button = Button(
        parent=parent,
        model="quad",
        position=(position[0], position[1], CARD_Z),
        scale=scale,
        color=color,
    )
    button.on_click = on_click
    label = Text(
        parent=parent,
        text=text,
        position=(position[0], position[1], TEXT_Z),
        origin=(0, 0),
        scale=TEXT_SCALE,
        color=text_color,
    )
    # The label is a sibling, not the button's own text, so the card stays a plain quad; keeping a
    # handle on it lets callers retitle or recolour a card without rebuilding it.
    button.label = label
    return button
