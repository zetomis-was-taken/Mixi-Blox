# GUI Scaffold (Ursina)

A short report on the current Ursina prototype (#28). This is a runnable game, not the finished one:
it boots into a level select and ends a level on a results card, but there is still no solver panel
and the palette is a first pass at the art direction ([`theme.md`](theme.md)).

## What it does

- Boots into a level select: one card per stage, one row per stage group (L1-L4), with cleared
  levels tinted the mechanism cyan for the rest of the session. Clicking a card starts that level,
  and `--stage FILE` skips the menu and opens that level directly.
- Plays a load animation on entry: tiles float up from below with randomised delays, then the block
  drops in from above. Input is blocked until the animation has fully played.
- Renders the board as flat tiles: a dark tile per walkable cell, butted together with a faint
  translucent teal grid line, on a dark base that gives the platform visible thickness, a raised
  detail piece on fragile and switch cells, no tile at the goal, and no mark on the start (see
  [`theme.md`](theme.md)).
- Reacts to the block: switch plates sink while it bears on them, a fragile crack opens under the
  weight, and a bridge eases between its open and closed height with its tint following it
  ([`theme.md`](theme.md#reactions)).
- Rolls the block on every move: the animation is a real quarter-turn about the tile edge, driven by
  the translation, not a canned loop.
- Steers a split pair one cube at a time: the active cube keeps the coral `#ff6973`, the idle one is
  peach `#ffb0a3`, `Tab` swaps them, and the HUD names the active cube. A direction key still moves
  the other cube when the active one has no such action.
- Lets a puzzle be recovered from: `Z` steps back one move and `R` restarts the level, both hinted
  on the HUD. Split switches can leave the block in a losing position, so neither is optional.
- Ends a level on a win overlay: the move count and elapsed time, then next level, retry and back to
  the level select — as cards or as `Enter` / `R` / `Esc`.
- Draws an optional parallax backdrop: two regular grids of filled and outlined `#15788c` squares,
  scrolling top-left → bottom-right at different speeds (`parallax.py`).
- Can apply an optional dotted halftone shader to the tiles and the player only (`dot_shader.py`).
- Keeps all colour values in `theme.py`, following the palette documented in `theme.md`.

## Run

```bash
pip install -r requirements.txt
python Source/main.py --gui                      # level select
python Source/main.py --gui --stage FILE         # one level, no menu
```

Ursina needs Python `< 3.14` (see `requirements.txt`). The level select lists every stage under
`Source/bloxorz/core/stages/`, in file-name order, grouped by each stage's own `group` field.

## Structure

| File | Responsibility |
| --- | --- |
| `Source/bloxorz/gui/app.py` | Window, the two scenes, `Game` (which scene is on screen, cleared levels), camera, HUD, input loop, launch helper |
| `Source/bloxorz/gui/board_view.py` | One flat tile per non-void cell, plus per-kind detail pieces; bridge tint/height |
| `Source/bloxorz/gui/block_view.py` | Player boxes and pivot-based roll animation |
| `Source/bloxorz/gui/catalog.py` | The stage catalog: play order, grouping and the next level (no Ursina) |
| `Source/bloxorz/gui/controller.py` | Current `State`, the active cube, input → one `(next_state, action)` pair, moves/clock, undo, retry, goal callback |
| `Source/bloxorz/gui/dot_shader.py` | Screen-space halftone shader applied to tiles and player only |
| `Source/bloxorz/gui/intro.py` | Load-animation timeline: tile stagger, detail phase, then the block drop (no Ursina) |
| `Source/bloxorz/gui/layout.py` | Grid ↔ world geometry and pose derivation (no Ursina) |
| `Source/bloxorz/gui/level_select.py` | The boot screen: a card per stage, grouped by stage group, cleared ones tinted |
| `Source/bloxorz/gui/parallax.py` | Scrolling tiled square backdrop in two depth layers |
| `Source/bloxorz/gui/reaction.py` | Which mechanisms the block loads, and how their value eases there (no Ursina) |
| `Source/bloxorz/gui/results.py` | The move/clock text the win overlay shows (no Ursina) |
| `Source/bloxorz/gui/theme.py` | Palette (mapped in [`theme.md`](theme.md)), reaction timing and roll timing |
| `Source/bloxorz/gui/widgets.py` | The flat card + label both menu screens are built from |
| `Source/bloxorz/gui/win_overlay.py` | The results card: cost of the level, next/retry/levels, `Enter`/`R`/`Esc` |
| `tests/test_gui_layout.py`, `tests/test_gui_controller.py`, `tests/test_gui_intro.py`, `tests/test_gui_reaction.py`, `tests/test_gui_catalog.py`, `tests/test_gui_results.py` | Headless pose, controller, load-timeline, mechanism, catalog and result-text checks |

The controller never builds a `State` and never re-implements a transition: it asks the engine for
legal successors and turns a key into one concrete `(next_state, action)` pair, which is also the
shape solver playback feeds through the same animation. The GUI layer imports `bloxorz.core` only,
as required by the layering rules in `docs/contracts.md`.

## Split cubes

`PlayerController.active` names the cube the next input moves. An action carries its cube index, so
the engine — not the view — decides what a split pair can do; the controller only chooses whose turn
it is.

- `Tab` calls `switch_cube`, which flips the active index (ignored while the block is unsplit or a
  roll is playing).
- `resolve` prefers the active cube and falls back to the other one when the active cube has no
  action in that direction, so a direction key is never dead.
- `State` orders its cubes by cell, so a move can swap their indices; `_active_after` finds the cube
  by the cells it rolled onto and keeps it active. After a merge there is one cube and the index
  resets to 0.
- `BlockView.set_active` tints the pieces — active cube `theme.BLOCK` `#ff6973`, idle cube
  `theme.BLOCK_IDLE` `#ffb0a3` — and the HUD shows `Cube n of 2`, hidden while the block is unsplit.

## Roll animation

`BlockView` derives the start and end poses from `State`, then rotates the piece 90° about the
bottom edge it tips over:

- pivot = leading bottom edge in the movement direction;
- axis = horizontal axis perpendicular to that movement;
- angle sign is selected by checking which ±90° rotation lands on the destination centre;
- duration = `theme.ROLL_SECONDS` (0.22 s), with linear angular motion.

Unsplit moves and a split cube's own move use this path. Split-switch, merge, and teleport
transitions currently snap to the destination pose; polishing those is still part of #28.

## Load animation

`gui/intro.py` owns the sequence as an absolute-time timeline, and the scene reads progress from it
each frame; no view keeps its own clock.

1. every non-void tile floats up from below the board (`intro.tile_progress(index)`), each with its
   own random delay inside `IntroTiming.tile_delay_max_seconds`, so the platform assembles instead
   of popping in at once;
2. the detail pieces resting on those tiles — switch plates and fragile cracks — rise
   (`intro.obstacle_progress(index)`), each with its own random delay inside
   `IntroTiming.obstacle_delay_max_seconds`. A stage with no detail pieces skips this phase;
3. the player's block drops in from above (`intro.player_progress()`), starting only after the last
   tile and detail have landed;
4. input: `PrototypeScene.update` returns early until `LoadIntro.finished`, so keys pressed during
   the animation are ignored rather than buffered.

Progress is eased out (cubic). Tiles start below the board and the block above it, both by
`_camera_distance(stage)` — the same distance the camera sits from the board centre, so each piece
begins outside the viewport on any board size (verified by projecting every piece through the lens:
`|screen y| > 1` at t = 0 on all ten stages). `BoardView` stacks that offset on top of each tile's
bridge height, so a bridge sinking or rising never fights the animation.

| `IntroTiming` field | Value in the scene | Effect |
| --- | --- | --- |
| `tile_float_seconds` | `1.0` | How long one tile takes to rise |
| `tile_delay_max_seconds` | `0.55` | Upper bound of each tile's random start delay |
| `obstacle_float_seconds` | `0.45` | How long one detail piece takes to rise |
| `obstacle_delay_max_seconds` | `0.25` | Upper bound of each detail's random start delay |
| `player_float_seconds` | `1.0` | How long the block takes to drop in |
| `tile_rise` | camera distance | Travel of a tile, from off-screen to its resting height |
| `obstacle_rise` | camera distance | Travel of a detail, from off-screen to its resting height |
| `player_drop` | camera distance | Travel of the block, from off-screen down into its start pose |

One tile therefore rises for a full second, the details take up to 0.7 s more, and the block then
falls for a second; with the random staggers the whole sequence runs roughly 3.25 s
(`max tile delay + 1.0 + max detail delay + 0.45 + 1.0`), or about 2.55 s on a board with no
detail pieces. Input is held for all of it.

Timing lives in `intro.py` rather than `theme.py` because that module must stay importable without
Ursina: the sequence is covered headless by `tests/test_gui_intro.py`.

## Mechanism reactions

`gui/reaction.py` answers one question — which cells is the block bearing on — and the board view
draws the answer. The rule is read off the same `State` the controller already holds, so the view
never derives a transition of its own:

| Mechanism | Reaction |
| --- | --- |
| soft / heavy / split plate | sinks by `theme.PRESS_DEPTH` while loaded, rises when the block steps off |
| fragile crack | opens to `1 + theme.CRACK_OPEN` of its depth under weight |
| bridge | eases between its open and closed height; its tint follows the height (`TILE_FLOOR` → `TILE_BRIDGE`) |

A heavy plate only answers to the full standing block, which is the weight rule the engine fires it
by — a lone split cube on it leaves the plate up, because the switch has not fired. `load_per_cell`
returns a value for *every* reactive cell, not only the loaded ones, so a released plate is always
told to rise.

`reaction.approach` moves a value by a constant step per frame (`PRESS_SECONDS`,
`BRIDGE_SECONDS`), not by a fraction of the gap: travel time is then independent of frame rate, and
a mechanism retargeted mid-move keeps a sane speed instead of slowing to a crawl near its target.
Colour is blended from the bridge's current height, so no entity ever shows a tint that disagrees
with its body. Geometry and reasoning are in [`theme.md`](theme.md#reactions).

## Optional presentation effects

Both extras are independent modules and are switched on by one call each in
`PrototypeScene.__init__`:

```python
self.parallax = parallax.ParallaxBackground()      # square parallax backdrop
dot_shader.apply(self.board_view, self.block_view)  # halftone dots on objects
```

Delete either line to turn that effect off; nothing else depends on it.

### Parallax background

`parallax.py` attaches two large quads to the camera, at depths of 60 and 120 world units (both
well behind the board). A small fragment shader paints a regular checkerboard of squares on each
quad: filled and outlined cells alternate, all in `theme.PARALLAX_SQUARE` (`#15788c`) at low
opacity. Both layers drift right and down; the near layer has larger cells and moves faster, so
the layers read as parallax.

The pattern is computed in screen space from `gl_FragCoord`, with cell size and scroll passed as
shader inputs, so a window resize only refits the quads and never rebuilds anything. Because the
quads sit behind the board, the depth buffer lets the board occlude them.

### Dotted shader

`dot_shader.py` defines a flat-colour GLSL shader based on `unlit_shader`. It keeps each entity's
own colour and multiplies in a regular screen-space dot grid (`DOT_SPACING_PIXELS`,
`DOT_RADIUS_PIXELS`, `DOT_DARKNESS`), so the dots stay the same pixel size on every surface.

`dot_shader.apply` gives it to `BoardView.object_entities()` — tile caps, tile bases and detail
pieces — and to the player. Grid separator lines, the HUD and the parallax backdrop keep the
plain `unlit_shader`. `BlockView` stores the shader because it rebuilds its boxes after every
move, so the dots survive the first roll.

## Camera

The camera orbits the centre of the **walkable footprint**, not the centre of the grid. Stages do
not have to fill their grid: `L1-01` leaves two columns empty on the left, so a grid-centred camera
made the platform look shifted left with extra space on the right. `layout.board_center` supplies
the point to frame.

The rotation is set explicitly. `camera.look_at()` was avoided because it introduced about 6.7° of
unwanted roll on this rig.

Current values in `app.py`:

| Constant | Current | Effect |
| --- | --- | --- |
| `CAMERA_PITCH_DEGREES` | `40.0` | Higher = more top-down; lower = closer to eye level |
| `CAMERA_YAW_DEGREES` | `25.0` | Side rotation; 0° is straight-on, 45° is full diagonal |
| `CAMERA_DISTANCE_FACTOR` | `1.5` | Multiplier on `max(rows, cols)`; higher = zoom out |
| `CAMERA_FOV` | `45.0` | Perspective strength; higher = wider and more distorted |

```python
distance = max(rows, cols) * TILE_SIZE * CAMERA_DISTANCE_FACTOR
pitch, yaw = radians(CAMERA_PITCH_DEGREES), radians(CAMERA_YAW_DEGREES)
target_x, target_z = board_center(stage)

camera.position = (
    target_x - sin(yaw) * cos(pitch) * distance,
    0.5 + sin(pitch) * distance,
    target_z - cos(yaw) * cos(pitch) * distance,
)
camera.rotation = (CAMERA_PITCH_DEGREES, CAMERA_YAW_DEGREES, 0.0)
```

After positioning, `_align_camera_lens` projects every tile corner and nudges the lens by the
residual: the yawed view makes the near edge project wider than the far edge, so orbiting the
footprint centre alone would still leave the outline a few pixels off-centre. The shift uses the
3D lens, not the UI camera, so the HUD does not move.

The negative X offset views the board from its left side. To mirror the view, flip the sign of
`sin(yaw)` and the sign of the yaw component in `camera.rotation`. Keeping the last rotation
component at `0.0` keeps the horizon level.

If the board touches the window edges, raise `CAMERA_DISTANCE_FACTOR` first; adjust `CAMERA_FOV`
only when the amount of perspective distortion also needs to change.

## Visual style

`theme.py` holds the palette and the mapping is documented in [`theme.md`](theme.md): flat tile
colours plus a raised detail piece for fragile and switch cells. The goal cell has no tile, so the
cream background shows through as a hole, and the start is an ordinary tile. Rendering stays
deliberately simple — no lights, shadows, fog, gradients or textures. Entities use the
`unlit_shader`, except the board objects and player when the optional dotted shader is enabled.
Values are written with `color.rgb32(...)` because Ursina's `color.rgb()` expects floats in `0–1`;
passing `0–255` values there clamps every colour to white.

## Level completion

`PlayerController._animation_finished` checks `Board.is_goal`. On success the controller sets
`cleared` — which stops it accepting moves — and calls the scene's `_level_cleared`, which records
the level in `Game.cleared` and raises `WinOverlay`.

The overlay is modal: the scene stops reading movement keys, and the overlay itself answers
`Enter` (next level), `R` (retry) and `Esc` (level select). The same three actions are cards, so the
flow never depends on knowing a key. Retry calls `PlayerController.retry` and dismisses the card,
which puts the level back in play; the next level comes from `catalog.next_stage`, and a level with
no successor — the last stage, or one loaded from an arbitrary `--stage` path — simply has no next
card. Going back to the level select tears the level scene down (`PrototypeScene.teardown`) and
rebuilds the grid with the cleared levels tinted.

Undo lives beside it: `PlayerController.history` is a stack of the immutable `State` values each
move started from, so `Z` pops one and re-syncs the block instead of replaying anything. The HUD
carries the hint (`Z undo`, `R retry`); the move count and clock appear on the overlay. A retry
zeroes both, an undo only the move count.

## Known limitations

- No solver panel, replay, or stats display.
- The level select shows stage ids only: the stage names appear once a level is open.
- Split/merge/teleport changes snap instead of rolling.
- A fragile panel never breaks on screen. A standing block on fragile is an illegal move
  (ADR-003), so no state exists in which the panel has given way; the crack only opens and shuts
  with the weight.
- The HUD is the level name, the key hints and — on a split stage — the active cube; it shows during
  the load animation, and it does not show the move count or the running clock yet.

## Verification

- `pytest tests/ -q` — 120 passed.
- `ruff check .` — clean.
- Offscreen menu probe — the level select lists all ten stage ids plus a group label per row,
  cards measure 0.22 × 0.07 UI units on a plain 1 × 1 quad (no aspect fold from `Button`'s default
  model), picking `L1-01` builds the level scene, its goal raises the overlay reading
  `7 moves   |   0:00` with the next card tinted cyan, retry restores the start with 0 moves,
  `Z`/`R` undo and retry, returning to the select leaves `L1-01` as the only cyan card, and
  `Enter` on `L1-02`'s overlay chains to `L1-03`.
- Offscreen Ursina smoke run — scene builds, tiles and their detail pieces start below the board
  and the block above it, keys are ignored until `LoadIntro.finished`, tiles and details land on
  their resting heights, and the first legal move is accepted afterwards.
- Offscreen reaction probe — a heavy plate measured at `0.0250 → -0.0050` (`PRESS_DEPTH`) while
  the standing block is on it and back to `0.0250` after it leaves, an opened bridge at its floor
  height and fully cyan, and a fragile crack measured at `0.1200 → 0.2160` (`×1.8`, `CRACK_OPEN`)
  under a lying block.
- A pivot-roll sweep across all stage files found a valid roll plan for every reachable unsplit
  transition (3,550 checked at the time).

## Related documents

- [`theme.md`](theme.md) — the palette and which colour every cell kind uses.
- [`window.md`](window.md) — how the game window is created and configured (Ursina/Panda3D).
- [`contracts.md`](../contracts.md) — frozen core API and layer rules.
- [`decisions/ADR-002-gui-stack.md`](../decisions/ADR-002-gui-stack.md) — why Ursina.
