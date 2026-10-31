# GUI Scaffold (Ursina)

A short report on the current Ursina prototype (#28). This is a runnable game, not the finished one:
it boots into a title screen, then a level select, and ends a level on a results card; a Solve
control on every level replays a solver's answer as a movie. The palette is still a first pass at
the art direction ([`theme.md`](theme.md)).

## What it does

- Boots into a title screen: the wordmark over two cards, play (into the level select) and quit,
  with `Enter` / `Esc` as their keyboard route. `--stage FILE` skips both menus entirely.
- Opens the level select from that card: one card per stage in one scrolling list, with a 3D
  miniature of the highlighted stage's board beside it. The highlighted card is a solid cyan
  ribbon whose right end is cut on a diagonal, and the cream card the miniature stands on is a
  trapezoid whose left edge is on the same diagonal; cleared levels carry a badge for the rest of
  the session. Clicking a card highlights it, and clicking it again starts that level.
- Plays a load animation on entry: tiles float up from below with randomised delays, then the block
  drops in from above. Input is blocked until the animation has fully played.
- Renders the board as flat tiles: a dark tile per walkable cell, butted together with a faint
  translucent teal grid line, on a dark base that gives the platform visible thickness, a raised
  detail piece on switch cells, a bare peach tile that bobs up and down while idle on fragile
  cells, no tile at the goal but a rim around the opening, and no mark on the start (see
  [`theme.md`](theme.md)).
- Reacts to the block: switch plates sink while it bears on them, fragile tiles stop bobbing and
  hold still once the block stands on them, and a bridge eases between its open and closed height
  with its tint following it ([`theme.md`](theme.md#reactions)).
- Rolls the block on every move: the animation is a real quarter-turn about the tile edge, driven by
  the translation, not a canned loop.
- Rolls once per key press: a direction key is read as one `input()` event, so holding it down does
  not repeat the roll and a press that lands mid-roll is dropped rather than queued.
- Keeps the board framed: the camera is pushed out until the footprint fits the window, and a
  resize redoes that fit on the next frame.
- Steers a split pair one cube at a time: the active cube keeps the coral `#ff6973`, the idle one is
  peach `#ffb0a3`, `Tab` swaps them, and the HUD names the active cube. A direction key still moves
  the other cube when the active one has no such action.
- Lets a puzzle be recovered from: `Z` rolls the last move back and `R` restarts the level —
  replaying its load animation — both hinted on the HUD. Split switches can leave the block in a
  losing position, so neither is optional.
- Counts the run as it happens: the HUD's opposite corner shows the move count and the running
  clock, from the same `results.py` line the win overlay prints, so both always agree.
- Offers a Solve control once a level has loaded: one card per algorithm in the injected mapping,
  hidden while the level is loading or won. A click shows a "BFS…" busy card and starts the search
  on the next frame, so the window never looks dead during a blocking `solve`; the run itself is
  bounded by `SOLVE_TIME_CAP_SECONDS` and an over-long one comes back as `cap`.
- Replays the answer as a movie: the block rolls the solver's path through the same quarter-turn
  animation, one roll at a time with `REPLAY_PAUSE_SECONDS` between them. The HUD's right-hand line
  reads `BFS replay — move 4 of 19`; `Space` pauses, `Esc` stops and puts the player's own run back,
  and direction keys, `Tab`, `Z` and `R` are ignored while a movie plays.
- Reports the run on a solver card: outcome, solution length and cost, and the three `Counts`, with
  watch again / close / levels. `cap` and `unsolvable` show the card without a movie, and so does a
  path the board cannot follow — with a note and no watch again, instead of an error out of the
  frame loop. A solver run never counts as a player clear, and time/memory are not shown — the GUI
  may not clock a search.
- Offers the real solvers: every level scene is handed `bloxorz.solvers.ALGORITHMS`, so the Solve
  panel draws one card per algorithm — BFS, DFS, UCS and A* — and replays that algorithm's answer.
- Ends a level on a win overlay: the move count and elapsed time, then next level, retry and back to
  the level select — as cards or as `Enter` / `R` / `Esc`.
- Pauses a level: `Esc` puts a card over the frozen board with continue and level select, as cards
  or as `Enter` / `Esc` / `L`. Movement keys are dropped and the clock stops while it is up; the
  load animation, a solver movie and a result card are never interrupted by it.
- Draws an optional parallax backdrop: two regular grids of filled and outlined `#15788c` squares,
  scrolling top-left → bottom-right at different speeds (`parallax.py`).
- Can apply an optional dotted halftone shader to the tiles and the player only (`dot_shader.py`).
- Keeps all colour values in `theme.py`, following the palette documented in `theme.md`.

## Run

```bash
pip install -r requirements.txt
python Source/main.py                           # title screen (GUI is default)
python Source/main.py --stage FILE               # one level, no menus
```

Ursina installs on Python 3.11 and 3.12 only (see `requirements.txt`). The level select lists every stage under
`Source/bloxorz/core/stages/`, in file-name order, grouped by each stage's own `group` field.

## Structure

| File | Responsibility |
| --- | --- |
| `Source/bloxorz/gui/app.py` | Window, the scenes, `Game` (which scene is on screen, cleared levels), camera, input (one action per key press), launch helper |
| `Source/bloxorz/gui/board_view.py` | One flat tile per non-void cell, plus per-kind detail pieces; bridge tint/height |
| `Source/bloxorz/gui/block_view.py` | Player boxes and pivot-based roll animation |
| `Source/bloxorz/gui/catalog.py` | The stage catalog: play order, grouping and the next level (no Ursina) |
| `Source/bloxorz/gui/controller.py` | Current `State`, the active cube, input → one `(next_state, action)` pair, moves/clock, undo, retry, goal callback, and the run snapshot playback borrows |
| `Source/bloxorz/gui/dot_shader.py` | Screen-space halftone shader applied to tiles and player only |
| `Source/bloxorz/gui/framing.py` | How far to push the camera out so the board fits the frame (no Ursina) |
| `Source/bloxorz/gui/hud.py` | The corner HUD: level name, live move count and clock, key hints, active cube |
| `Source/bloxorz/gui/intro.py` | Load-animation timeline: tile stagger, detail phase, then the block drop (no Ursina) |
| `Source/bloxorz/gui/layout.py` | Grid ↔ world geometry and pose derivation (no Ursina) |
| `Source/bloxorz/gui/level_select.py` | The level select: a card per stage, grouped by stage group, cleared ones tinted |
| `Source/bloxorz/gui/parallax.py` | Scrolling tiled square backdrop in two depth layers |
| `Source/bloxorz/gui/pause_overlay.py` | Pause card over the frozen board: continue / level select, `Enter` / `Esc` / `L` |
| `Source/bloxorz/gui/reaction.py` | Which mechanisms the block loads, and how their value eases there (no Ursina) |
| `Source/bloxorz/gui/replay.py` | Solver playback: `SearchResult.path` planned into paced steps (no Ursina) |
| `Source/bloxorz/gui/results.py` | Move/clock and solver-run text the HUD, win overlay and solver card show (no Ursina) |
| `Source/bloxorz/gui/solver_overlay.py` | Solver result card: outcome, counts, watch again / close / levels |
| `Source/bloxorz/gui/solver_panel.py` | The level's Solve control: one card per algorithm, plus the "solving" state |
| `Source/bloxorz/gui/theme.py` | Palette (mapped in [`theme.md`](theme.md)), reaction timing and roll timing |
| `Source/bloxorz/gui/title.py` | The title screen: wordmark, play and quit cards, `Enter` / `Esc` |
| `Source/bloxorz/gui/widgets.py` | The flat card + label both menu screens are built from |
| `Source/bloxorz/gui/win_overlay.py` | The results card: cost of the level, next/retry/levels, `Enter`/`R`/`Esc` |
| `tests/test_gui_layout.py`, `tests/test_gui_controller.py`, `tests/test_gui_intro.py`, `tests/test_gui_framing.py`, `tests/test_gui_reaction.py`, `tests/test_gui_catalog.py`, `tests/test_gui_results.py`, `tests/test_gui_replay.py` | Headless pose, controller, load-timeline, camera-fit, mechanism, catalog, result-text and replay-driver checks |

The controller never builds a `State` and never re-implements a transition: it asks the engine for
legal successors and turns a key into one concrete `(next_state, action)` pair, which is also the
shape solver playback feeds through the same animation. The GUI layer imports `bloxorz.core` only,
as required by the layering rules in `docs/contracts.md`.

## Screen flow

`Game` owns the scene on screen. Each screen is an `Entity` that builds itself in `__init__` and
removes its own entities in `teardown()`, and `Game._show` tears the old one down before the new one
is built, so two screens never share the window.

| Screen | Built by | Leaves via |
| --- | --- | --- |
| Title | `TitleScene` — the boot screen | play card or `Enter` → level select; quit card or `Esc` → `application.quit()` |
| Level select | `LevelSelectScene`, from `catalog.load_catalog()` | a stage card → that level |
| Level | `PrototypeScene` | the win overlay: next level, retry, or back to the level select; the pause card: continue or back to the level select |

`--stage FILE` skips the first two rows and builds the level scene directly. The title screen is
given only the callback that opens the level select, so it reads no stage and no cleared-level data.

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

Unsplit moves, a split cube's own move, and an undo of either use this path — an undo is the same
plan with the direction reversed, so the block tips back over the edge it came in on. A split
cube's landing pose is found by the cells it rolled onto, not by the action's index, because the
state orders its cubes by cell and one action can swap their indices. Split-switch, merge and
teleport transitions have no roll to derive, so they snap to the destination pose.

## Load animation

`gui/intro.py` owns the sequence as an absolute-time timeline, and the scene reads progress from it
each frame; no view keeps its own clock. `PrototypeScene._load_intro` builds it from the camera
distance the last framing settled on, and the same call runs on a retry — so a retried stage plays
the identical animation (with fresh random staggers) instead of jumping to its start pose.

1. every non-void tile floats up from below the board (`intro.tile_progress(index)`), each with its
   own random delay inside `IntroTiming.tile_delay_max_seconds`, so the platform assembles instead
   of popping in at once;
2. the detail pieces resting on those tiles — the switch plates — rise
   (`intro.obstacle_progress(index)`), each with its own random delay inside
   `IntroTiming.obstacle_delay_max_seconds`. A stage with no detail pieces skips this phase;
3. the player's block drops in from above (`intro.player_progress()`), starting only after the last
   tile and detail have landed;
4. input: `PrototypeScene.input` returns early until `LoadIntro.finished`, so keys pressed during
   the animation are ignored rather than buffered.

Progress is eased out (cubic). Tiles start below the board and the block above it, both by the
distance the camera settled on — the same distance it sits from the board centre, so each piece
begins outside the viewport on any board size at any aspect ratio (verified by projecting every
piece through the lens: `|screen y| > 1` at t = 0 on all ten stages). `BoardView` stacks that offset
on top of each tile's bridge height, so a bridge sinking or rising never fights the animation.

| `IntroTiming` field | Value in the scene | Effect |
| --- | --- | --- |
| `tile_float_seconds` | `1.0` | How long one tile takes to rise |
| `tile_delay_max_seconds` | `0.55` | Upper bound of each tile's random start delay |
| `obstacle_float_seconds` | `0.45` | How long one detail piece takes to rise |
| `obstacle_delay_max_seconds` | `0.25` | Upper bound of each detail's random start delay |
| `player_float_seconds` | `1.0` | How long the block takes to drop in |
| `tile_rise` | fitted camera distance | Travel of a tile, from off-screen to its resting height |
| `obstacle_rise` | fitted camera distance | Travel of a detail, from off-screen to its resting height |
| `player_drop` | fitted camera distance | Travel of the block, from off-screen down into its start pose |

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
| fragile tile | bobs `±theme.FRAGILE_WOBBLE_HEIGHT` on Y while idle, one cycle per `theme.FRAGILE_WOBBLE_SECONDS`; pinned still while loaded |
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

Current values in `app.py` and `framing.py`:

| Constant | Current | Effect |
| --- | --- | --- |
| `CAMERA_PITCH_DEGREES` | `40.0` | Higher = more top-down; lower = closer to eye level |
| `CAMERA_YAW_DEGREES` | `25.0` | Side rotation; 0° is straight-on, 45° is full diagonal |
| `CAMERA_DISTANCE_FACTOR` | `1.5` | Multiplier on `max(rows, cols)`; the **nominal** distance the fit starts from |
| `CAMERA_FOV` | `45.0` | Horizontal field of view; higher = wider and more distorted |
| `FIT_X` | `0.86` | Fraction of the half-frame the board may fill horizontally |
| `FIT_Y` | `0.92` | Same vertically, measured on the worse edge |
| `MAX_STEPS` | `10` | Measurements the fit may take before it gives up |

```python
distance = max(rows, cols) * TILE_SIZE * CAMERA_DISTANCE_FACTOR   # nominal, then fitted
pitch, yaw = radians(CAMERA_PITCH_DEGREES), radians(CAMERA_YAW_DEGREES)
target_x, target_z = board_center(stage)

camera.position = (
    target_x - sin(yaw) * cos(pitch) * distance,
    0.5 + sin(pitch) * distance,
    target_z - cos(yaw) * cos(pitch) * distance,
)
camera.rotation = (CAMERA_PITCH_DEGREES, CAMERA_YAW_DEGREES, 0.0)
```

### Fitting the board to the window

The nominal distance is only a starting point, because how much of the frame a board fills is not
fixed by the camera alone. `PrototypeScene._frame_camera` therefore measures the board and pushes
the camera out until it fits:

1. `_camera_distance(stage)` gives the nominal distance for the grid;
2. `_place_camera` puts the camera there, sets the pose and aligns the lens;
3. `_projected_bounds` projects every corner of every non-void tile — at the top face and at the
   bottom of the platform, the two extremes — and returns the outline in lens space, where the
   frame is `[-1, 1]` on both axes;
4. `framing.fitting_distance` multiplies the distance by the overflow,
   `max(half_width / FIT_X, half_height / FIT_Y)`, and measures again, until the outline is inside
   the limits or `MAX_STEPS` runs out.

The camera is only ever pushed out, never pulled in, so a board that already fits keeps the framing
its stage was built with and the levels do not change size. `framing.py` is pure Python — the
projection needs the lens, the decision does not — so the rule is covered headless by
`tests/test_gui_framing.py`.

The fit is what makes the framing survive a **resize**. `CAMERA_FOV` is Panda3D's *horizontal* fov,
so the vertical one is derived from the window's aspect ratio, and the board's vertical extent on
screen scales with that ratio: at 16:10 `L2-02` already reached 0.976 of the half-frame, and a
16:9 window would have pushed its near corner out of the picture. `PrototypeScene` accepts
`aspectRatioChanged` and only sets a flag; the next `update()` reframes once, so dragging a window
edge costs one reframe per frame instead of one per pixel. `teardown` ignores the event, so a scene
that has been replaced is never called.

After positioning, `_align_camera_lens` projects every tile corner and nudges the lens by the
residual: the yawed view makes the near edge project wider than the far edge, so orbiting the
footprint centre alone would still leave the outline a few pixels off-centre. The shift uses the
3D lens, not the UI camera, so the HUD does not move. It is a fraction of the film size, so it
holds while the framing it was measured at holds — a resize re-measures it with everything else.

The negative X offset views the board from its left side. To mirror the view, flip the sign of
`sin(yaw)` and the sign of the yaw component in `camera.rotation`. Keeping the last rotation
component at `0.0` keeps the horizon level.

The fit is the knob for "the board is too close to the edge": lower `FIT_X` / `FIT_Y` to budget more
air, which zooms out as much as that board needs rather than moving the nominal framing of every
stage. Adjust `CAMERA_FOV` only when the amount of perspective distortion also needs to change.

## Visual style

`theme.py` holds the palette and the mapping is documented in [`theme.md`](theme.md): flat tile
colours plus a raised detail piece for switch cells and an idle bob for fragile ones. The goal
cell has no tile, so the cream background shows through as a hole, framed by a rim so the opening
cannot be read as the platform's edge; the start is an ordinary tile. Rendering stays
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
flow never depends on knowing a key. Retry calls `PlayerController.retry` — which zeroes the run —
dismisses the card and builds a fresh `LoadIntro`, so the stage is put back exactly the way it was
opened: the platform re-assembles from below and the block falls in last. The camera does not move.
The next level comes from `catalog.next_stage`, and a level with no successor — the last stage, or
one loaded from an arbitrary `--stage` path — simply has no next card. Going back to the level select
tears the level scene down (`PrototypeScene.teardown`) and rebuilds the grid with the cleared levels
tinted.

Undo lives beside it: `PlayerController.history` is a stack of the immutable `State` values each
move started from, paired with the action that left it. `Z` pops one entry and hands the view that
same quarter-turn in reverse, so the block rolls back through `BlockView.animate` instead of
jumping — the cube keeps its arc, and a split stage rolls back the cube that had moved. The state
is restored before the roll starts, so the mechanisms it feeds are retargeted in the same frame and
bridges and plates ease back while the cube is still rolling. A transition a roll cannot express —
split, merge, teleport — is still put back by snapping to the pose, which is what `animate` falls
back to. The HUD carries the hint (`Z undo`, `R retry`) and shows the same live counter the overlay
then reports, so the two can never disagree. A retry zeroes both numbers, an undo only the move
count.

## Known limitations

- The Solve control only appears when the app was given an algorithms mapping. `main.py --gui`
  always passes `bloxorz.solvers.ALGORITHMS`; embedding `build()` or `run()` directly without a
  mapping leaves the control out and the game plays as it did before #18.
- Playback always starts the stage over: the board is reset to the level's start, and the player's
  own run — position, move count, clock, undo stack — is held aside and put back when the card is
  closed or the movie stopped.
- The solver card shows `Counts` only. Time and memory are the benchmark harness's job, because the
  GUI may not start a clock around a search (contract rule 5).
- The level select shows stage ids only: the stage names appear once a level is open.
- The level select has no way back to the title screen, so the quit card is reachable only at boot.
- The pause card is not offered during the load animation, a solver movie or a result card: `Esc`
  already stops a movie and leaves a result card for the level select.
- Holding a direction key does not repeat: a long corridor is tapped out key press by key press.
- Split-switch, merge and teleport changes snap instead of rolling — forward, when undone, and
  during a movie.
- A fragile panel never breaks on screen. A standing block on fragile is an illegal move
  (ADR-003), so no state exists in which the panel has given way; an idle tile bobs on the spot
  and the weight pins it still.
- The HUD shows during the load animation, where the counter reads `0 moves | 0:00` because the
  clock only starts once input is accepted.
- The HUD's placement and sizes are constants in `gui/hud.py`; they are not adjustable at runtime.
- The camera fit only ever pushes out, so a very wide window shows a smaller board rather than
  cropping it; the vertical framing is not re-centred, so a wide window leaves it sitting low.

## Verification

- `pytest tests/ -q` — 165 passed.
- `ruff check .` — clean.
- Offscreen HUD probe — the counter read `0 moves | 0:00` after the load animation, `2 moves |
  0:00` after two rolls, `2 moves | 0:01` once the clock had ticked, `1 move | 0:01` after `Z` and
  `0 moves | 0:00` after `R`; on `L4-01` the cube line appears while the counter keeps counting,
  and `Hud.teardown` leaves none of the four lines in `scene.entities`.
- Offscreen title probe — `build()` on `window_type="offscreen"` lands on the title scene: the
  wordmark, the tagline, the `Play` / `Quit` cards and the key line, on plain `quad` models.
  `Enter` builds the level select and leaves no title entity behind, a card click then builds
  `L1-01`'s level scene, and `--stage` skips both menus. `Esc` and `Enter` reach the quit and play
  callbacks.
- Offscreen menu probe — the level select lists all ten stage ids plus a group label per row,
  cards measure 0.22 × 0.07 UI units on a plain 1 × 1 quad (no aspect fold from `Button`'s default
  model), picking `L1-01` builds the level scene, its goal raises the overlay reading
  `7 moves   |   0:00` with the next card tinted cyan, retry restores the start with 0 moves,
  `Z`/`R` undo and retry, returning to the select leaves `L1-01` as the only cyan card, and
  `Enter` on `L1-02`'s overlay chains to `L1-03`.
- Offscreen Ursina smoke run — scene builds, tiles and their detail pieces start below the board
  and the block above it, keys are ignored until `LoadIntro.finished`, tiles and details land on
  their resting heights, and the first legal move is accepted afterwards.
- Offscreen retry probe — after two moves, `R` left the scene in place (`game.scene is scene`),
  zeroed the counter and the clock, and started a fresh intro: one frame later the block was at
  `y = 23.5` against a rest height of `1.0` and every tile offset was `-22.50` (the fitted camera
  distance), a direction press during the replay was dropped, and the pieces landed back on the
  start pose when it finished. The overlay's retry card behaved the same way: the card went away,
  the intro restarted, and the level took a move afterwards.
- Offscreen undo probe — `Z` on `L1-01` began a roll whose positions ran
  `(-2.5, 0.566, 0.576) → … → (-2.5, 0.5, 1.5)`, the pose the undone move started from, and
  `BlockView.animating` went false on landing. On `L3-01` the bridge stood at `-0.015` (open) after
  the heavy switch fired, and easing it back took nine frames to `-0.195` — 0.18 s,
  `BRIDGE_SECONDS` — once the undo retargeted it. On `L4-01` an undo rolled back only the cube that
  had moved and gave it the input again.
- Offscreen camera-fit probe — the projected outline of every stage was measured at 16:10, 16:9,
  21:9 and 4:3. At 16:10 only `L2-02` (22.50 → 23.88) and `L3-01` (22.50 → 22.71) needed pushing
  out, `L1-01` and `L4-01` kept their nominal distance, and every stage ended inside `FIT_X` /
  `FIT_Y`. At 21:9 `L2-02` went out to 34.82 with the outline at `y ∈ [-0.850, +0.578]`; at 4:3 no
  stage needed pushing out, which is the vertical field of view growing as the window narrows. The
  fit took one or two measurements per stage; the load animation's clearance always equalled the
  distance the camera settled on. Sending `aspectRatioChanged` after `camLens.setAspectRatio(21/9)`
  set the pending flag, one `update()` reframed, and the rebuilt scene fitted identically; sending
  it again after the scene was replaced left the level select untouched.
- Offscreen input probe — on `L1-01` a `s` press before `LoadIntro.finished` left the counter at
  0 moves, the first press after loading moved it to 1 (animating), a press plus `s hold` plus `s up`
  mid-roll left it at 1, 40 frames of `s hold` left it at 1 again, the next press after the roll
  reached 2, `Z` mid-roll was refused and `Z` after it took the count to 1, and `R` reset it to 0.
- Offscreen solver-replay probe (Python 3.11 + Ursina, `window_type="offscreen"`, run against the
  pre-#18 demo BFS — the panel, replay and card code it exercised is unchanged) — the Solve panel
  started hidden, stayed hidden through `LoadIntro`, and appeared once the intro finished. Picking
  the BFS card retitled it to `BFS…`, hid the panel, and played the seven-roll path; the HUD read
  `BFS replay — move 1 of 7` on the first roll, a direction press mid-movie left the player's
  counter at 0 moves, and the run ended on the solver card with the block on the goal and
  `Game.cleared` still empty. Closing the card put the block back on the start and brought the
  panel back; a second run paused with `Space`, resumed, and `Esc` after a landing restored the
  start and cleared the replay line. Re-running it with the four real cards (including split
  stage `L4-01`) is still open — see `SOLVER_GUI_TODO.md`.
- Offscreen reaction probe — a heavy plate measured at `0.0250 → -0.0050` (`PRESS_DEPTH`) while
  the standing block is on it and back to `0.0250` after it leaves, an opened bridge at its floor
  height and fully cyan. (The probe also measured a fragile crack, which has since been replaced
  by the tile's Y-axis twist; that reading no longer applies, and the twist has not been watched
  on screen yet - it needs Python 3.11 or 3.12 with Ursina installed.)
- A pivot-roll sweep across all stage files found a valid roll plan for every reachable unsplit
  transition (3,550 checked at the time).

## Related documents

- [`theme.md`](theme.md) — the palette and which colour every cell kind uses.
- [`window.md`](window.md) — how the game window is created and configured (Ursina/Panda3D).
- [`solver-integration.md`](solver-integration.md) — how an algorithm reaches the board as a replay.
- [`contracts.md`](../contracts.md) — frozen core API and layer rules.
- [`decisions/ADR-002-gui-stack.md`](../decisions/ADR-002-gui-stack.md) — why Ursina.
