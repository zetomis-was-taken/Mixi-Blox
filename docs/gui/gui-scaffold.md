# GUI Scaffold (Ursina)

A short report on the current Ursina prototype (#28). This is a runnable scaffold, not the finished
game: there is no menu and no solver panel yet, and the palette is a first pass at the art
direction ([`theme.md`](theme.md)).

## What it does

- Boots straight into `L1-01_long_corridor.json` — no title screen or menu.
- Plays a load animation on entry: tiles float up from below with randomised delays, then the block
  drops in from above. Input is blocked until the animation has fully played.
- Renders the board as flat tiles: a dark tile per walkable cell, butted together with a faint
  translucent teal grid line, on a dark base that gives the platform visible thickness, a raised
  detail piece on fragile and switch cells, no tile at the goal, and no mark on the start (see
  [`theme.md`](theme.md)).
- Rolls the block on every move: the animation is a real quarter-turn about the tile edge, driven by
  the translation, not a canned loop.
- Closes the process as soon as the block lands on the goal.
- Keeps all colour values in `theme.py`, following the palette documented in `theme.md`.

## Run

```bash
pip install -r requirements.txt
python Source/main.py --gui
```

Ursina needs Python `< 3.14` (see `requirements.txt`). `--stage FILE` boots another level; without
it, the GUI uses `DEFAULT_GUI_STAGE` in `Source/main.py`, which points at `L1-01`.

## Structure

| File | Responsibility |
| --- | --- |
| `Source/bloxorz/gui/app.py` | Window, scene, camera, HUD, input loop, launch helper |
| `Source/bloxorz/gui/board_view.py` | One flat tile per non-void cell, plus per-kind detail pieces; bridge tint/height |
| `Source/bloxorz/gui/block_view.py` | Player boxes and pivot-based roll animation |
| `Source/bloxorz/gui/controller.py` | Current `State`, input → `Board.successors`, goal callback |
| `Source/bloxorz/gui/intro.py` | Load-animation timeline: tile stagger, detail phase, then the block drop (no Ursina) |
| `Source/bloxorz/gui/layout.py` | Grid ↔ world geometry and pose derivation (no Ursina) |
| `Source/bloxorz/gui/theme.py` | Palette (mapped in [`theme.md`](theme.md)) and roll timing |
| `tests/test_gui_layout.py`, `tests/test_gui_controller.py`, `tests/test_gui_intro.py` | Headless pose, controller and load-timeline checks |

The controller never builds a `State` and never re-implements a transition: it asks the engine for
legal successors and only picks the matching direction. The GUI layer imports `bloxorz.core` only,
as required by the layering rules in `docs/contracts.md`.

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
deliberately simple — no lights, shadows, fog, gradients or textures — and entities use the
`unlit_shader`. Values are written with `color.rgb32(...)` because Ursina's `color.rgb()` expects
floats in `0–1`; passing `0–255` values there clamps every colour to white.

## Level completion

`PlayerController._animation_finished` checks `Board.is_goal`. On success it calls the scene's
`_level_cleared`, which calls `application.quit()`. This hard exit is intentional for the scaffold
and is marked with `TODO(#28)` in both `controller.py` and `app.py`, so the later results/next-level
flow is easy to find.

## Known limitations

- No menu, level select, solver panel, replay, or stats display.
- Split/merge/teleport changes snap instead of rolling.
- Fragile panels and switches have distinct colours and plates but no reaction yet: no press,
  crack or fall animation when the block lands on them.
- The HUD is only the level name and a key hint, and it shows during the load animation.

## Verification

- `pytest tests/ -q` — 99 passed.
- `ruff check .` — clean.
- Offscreen Ursina smoke run — scene builds, tiles and their detail pieces start below the board
  and the block above it, keys are ignored until `LoadIntro.finished`, tiles and details land on
  their resting heights, and the first legal move is accepted afterwards.
- A pivot-roll sweep across all stage files found a valid roll plan for every reachable unsplit
  transition (3,550 checked at the time).

## Related documents

- [`theme.md`](theme.md) — the palette and which colour every cell kind uses.
- [`window.md`](window.md) — how the game window is created and configured (Ursina/Panda3D).
- [`contracts.md`](../contracts.md) — frozen core API and layer rules.
- [`decisions/ADR-002-gui-stack.md`](../decisions/ADR-002-gui-stack.md) — why Ursina.
