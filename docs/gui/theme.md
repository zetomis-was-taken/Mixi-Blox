# Theme: palette and cell colours

Which colour every kind of cell uses, and what each colour is for. The values themselves live in
`Source/bloxorz/gui/theme.py`; this document is the mapping and the reasoning behind it.

## Source palette

The prototype uses **curiosities**, a 6-colour palette downloaded from Lospec; the draft file is
[`colors/curiosities.txt`](../../colors/curiosities.txt). That file is Paint.NET format
(`AARRGGBB`, one colour per line); the table below lists the same colours as `RRGGBB`.

The draft file is the source of the colours, `theme.py` is the only module the renderer reads them
from, and this document explains the assignment. If you change one, change all three.

All six colours are used. The board itself is deliberately minimal: one dark tile for every
walkable cell, an empty cell where the goal is, and accents only for the player and the special
mechanisms.

## Rendering rules

- Every entity uses `unlit_shader`: no lights, shadows, fog, gradients or textures. A surface is
  exactly the RGB in `theme.py`, so contrast in this palette is contrast on screen.
- Values are written with `color.rgb32(r, g, b)` (0–255). `color.rgb()` expects 0–1 floats and
  would clamp these values to white.
- Tiles have no gap: adjacent tiles butt together. Every shared edge carries a faint translucent
  teal line (`theme.GRID_LINE`, `#15788c` at ~35% opacity), which follows its tile's height during
  the load animation and when a bridge sinks.
- Each tile is two stacked boxes: a thin coloured cap (`theme.TILE_CAP_HEIGHT`, 0.03) over a base
  in `theme.TILE_SIDE` (`#46425e`, the normal tile colour). The base is hidden between neighbours
  but gives the platform a visible 0.30-unit thickness at its outer edge.
- Detail pieces are raised `theme.TRIM_LIFT` + `theme.TRIM_HEIGHT` above the tile's top face, so
  they never z-fight with it.
- Detail geometry is stated as fractions of a full tile (`TILE_SIZE`), because tiles have no gap.

## Colour assignments

| # | Hex | Constant(s) | Used for | Why |
| --- | --- | --- | --- | --- |
| 1 | `#46425e` | `TILE_FLOOR`, `TILE_SIDE`, `TEXT`, `TILE_MARK_DARK` | Every walkable tile (floor, start and tile sides), HUD text, fragile crack | The dark base of the board: it contrasts with the cream background and keeps the coral player and the accent-coloured mechanisms readable. |
| 2 | `#15788c` | `TILE_HEAVY`, `GRID_LINE`, `PARALLAX_SQUARE` | Heavy switch base; the faint line between tiles; the parallax backdrop squares | Deep teal is the darker of the two mechanism accents, matching the heavy switch's "weight"; at ~35% opacity it also gives the gapless board its grid without becoming a stripe. The same hue, at a lower opacity, keeps the parallax squares behind the board. |
| 3 | `#00b9be` | `TILE_BRIDGE`, `TILE_SOFT`, `TILE_SPLIT` | Open bridge, soft switch, split switch | Bright cyan is the "mechanism" accent; together with the detail shape it separates these cells from ordinary dark floor. |
| 4 | `#ffeecc` | `BACKGROUND`, `TILE_MARK`, `OVERLAY_PANEL` | Window clear colour; switch plates; the win overlay's card | The light background the board sits on, the light plates that mark interactive cells, and the results card — nearly opaque so the solved board still shows at its edges. |
| 5 | `#ffb0a3` | `TILE_FRAGILE`, `BLOCK_IDLE` | Fragile panel base; the cube that is not taking input after a split | Soft peach is the one warning tint: clearly warmer than the dark floor without competing with the coral player. It doubles as the quieter half of a split pair, so both cubes still read as the player while the active one keeps the coral. |
| 6 | `#ff6973` | `BLOCK` | The player's block, and the active cube of a split pair | Strong coral: the moving piece is the one element that is always coral, so it never gets lost against the board. |

## Cell kinds

| Kind | Base colour | Detail piece |
| --- | --- | --- |
| `floor` (`o`) | `TILE_FLOOR` `#46425e` | none |
| `start` (`S`) | `TILE_FLOOR` `#46425e` | none — the start is an ordinary tile with no mark |
| `goal` (`G`) | **no tile** | none — the cream background shows through, like the original game's hole |
| `fragile` (`F`) | `TILE_FRAGILE` `#ffb0a3` | one dark crack slot, 0.92 × 0.12 |
| `bridge` (`=`) | `TILE_BRIDGE` `#00b9be` when open, `TILE_FLOOR` `#46425e` when closed | none; height carries the state |
| `soft` (`+`) | `TILE_SOFT` `#00b9be` | 0.45 × 0.45 cream plate (small button) |
| `heavy` (`X`) | `TILE_HEAVY` `#15788c` | 0.80 × 0.80 cream plate (wide pressure plate) |
| `split` (`O`) | `TILE_SPLIT` `#00b9be` | two 0.32 × 0.80 cream plates with a seam between them |
| `void` | — | no tile at all |

## The goal and the start

Two cells deliberately carry no decoration:

- **goal** — `board_view.py` skips the tile entirely (`TILES_LEFT_OUT`). The background is the
  window colour, so the goal reads as a hole in the platform; the block is drawn on top of the
  empty cell until the level-clear flow replaces it.
- **start** — drawn exactly like floor. It has its own glyph in the stage file, but the player's
  block already shows where the level begins, so an extra mark would only add noise.

## Shared base colours

Six colours cannot give every drawn kind a unique base, so a few share one and the detail piece
does the separating:

| Base | Kinds | How they stay apart |
| --- | --- | --- |
| `#46425e` dark | floor, start | Intentionally identical: the start has no mark. |
| `#00b9be` cyan | bridge, soft, split | The bridge has no detail and sinks when closed; the soft switch is one button; the split switch is two halves with a seam. |

The heavy switch uses `#15788c` instead, so it is distinguishable from the other two switches even
before its plate is read.

## Detail pieces

Geometry lives in `DETAILS` in `Source/bloxorz/gui/board_view.py`, not in `theme.py`: only the
colours belong to the palette. All pieces are thin (`theme.TRIM_HEIGHT`) cubes resting on the tile:

- **fragile** — a narrow dark slot across the peach tile; the "crack".
- **soft / heavy / split** — cream plates, sized and split as described above.
- **floor / start / bridge** — no detail; colour and height already carry their meaning.
- **goal** — no tile, so there is nothing to detail.

Because every detail is a separate entity, the load animation can float the tiles in first and the
details onto them second (`LoadIntro.obstacle_progress`). A stage with no details at all still
skips that phase.

## Reactions

A detail piece is not decoration: it answers to the block, and the answer is read off the state the
controller already holds (`reaction.py`). No colour is added for these states — only geometry moves.

| Mechanism | Resting | Under the block | Why |
| --- | --- | --- | --- |
| soft / heavy / split plate | flush on the tile | sunk by `theme.PRESS_DEPTH` | The plate is a button: it goes down when weight is on it. |
| fragile crack | one thin slot | the slot opens to `1 + theme.CRACK_OPEN` of its depth | The fracture widens under load, so a fragile tile looks like it is about to give. |
| bridge | open: level with the floor, `TILE_BRIDGE`; closed: sunk, `TILE_FLOOR` | eases between the two | A bridge is one object moving, so its tint follows its height instead of snapping ahead of it. |

Two rules keep the picture honest:

- **A heavy plate answers only to the full standing block** — the same weight rule the engine fires
  it by. A lone split cube resting on it leaves the plate up, because the switch has not fired.
- **A plate rises again as soon as the block steps off**, because `load_per_cell` reports every
  reactive cell, not just the loaded ones.

Travel times are in `theme.py`: `PRESS_SECONDS` for a plate in either direction, `BRIDGE_SECONDS`
for a bridge. Both ease at a constant step (`reaction.approach`) rather than a fraction of the gap,
so a mechanism takes the same time to move whatever distance it has left and the animation does not
change with the frame rate.

A fragile panel never breaks on screen: a standing block on fragile is an illegal move
([ADR-003](../decisions/ADR-003-fragile-under-lone-cube.md)), so no state exists in which the panel
has given way. The crack opens and shuts with the weight.

## Changing the palette

1. Edit the constant in `Source/bloxorz/gui/theme.py` (`color.rgb32(r, g, b)`).
2. Update the tables above in the same commit.
3. Keep these constraints, which the current assignment is built around:
   - the player stays `#ff6973` and must remain readable on every tile it can stand on; a split
     pair keeps its idle cube one step quieter (`#ffb0a3`), so the active cube stays the accent;
   - the background stays light and the normal tile stays dark, so the board silhouette reads;
   - the goal stays empty and the start stays unmarked;
   - the grid line stays translucent and thinner than a tile detail, so it reads as a seam rather
     than a beam;
   - a detail piece must contrast with the tile it sits on;
   - two kinds may share a base only if their detail geometry differs in silhouette.
4. Check the result on one stage from each group, e.g.
   `python Source/main.py --gui --stage Source/bloxorz/core/stages/L2-01_fragile_shelves.json`.

## Where colours are read

- `Source/bloxorz/gui/board_view.py` — tile base colours and detail geometry.
- `Source/bloxorz/gui/block_view.py` — the player's block, and which of a split pair is active.
- `Source/bloxorz/gui/app.py` — window background.
- `Source/bloxorz/gui/hud.py` — every HUD line, all in `TEXT`.
- `Source/bloxorz/gui/level_select.py`, `Source/bloxorz/gui/win_overlay.py` — menu cards and the
  results panel (via `widgets.py`, which holds no colours of its own).
- `Source/bloxorz/gui/parallax.py` — the parallax square colour and per-layer opacity.

No other module contains a colour value.
