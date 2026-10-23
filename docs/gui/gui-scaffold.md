# GUI Scaffold (Ursina)

A short report on the current Ursina prototype (#28). This is a runnable scaffold, not the finished
game: no menu, no solver panel, and no art direction yet.

## What it does

- Boots straight into `L1-01_long_corridor.json` — no title screen or menu.
- Plays a load animation on entry: tiles float up from below with randomised delays, then the block
  drops in from above. Input is blocked until the animation has fully played.
- Renders the board as flat, near-monochrome tiles and the player as a `1x1x2` block.
- Rolls the block on every move: the animation is a real quarter-turn about the tile edge, driven by
  the translation, not a canned loop.
- Closes the process as soon as the block lands on the goal.
- Keeps all colour values in one placeholder palette so a later `theme.md` can replace it.

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
| `Source/bloxorz/gui/board_view.py` | One flat tile per non-void cell; bridge tint/height |
| `Source/bloxorz/gui/block_view.py` | Player boxes and pivot-based roll animation |
| `Source/bloxorz/gui/controller.py` | Current `State`, input → `Board.successors`, goal callback |
| `Source/bloxorz/gui/intro.py` | Load-animation timeline: tile stagger, then the block drop (no Ursina) |
| `Source/bloxorz/gui/layout.py` | Grid ↔ world geometry and pose derivation (no Ursina) |
| `Source/bloxorz/gui/theme.py` | Neutral greyscale palette and animation timing |
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
2. *other obstacles* — a gap in the timeline marked with `TODO(load-animation)` in `intro.py`, to be
   filled once `BoardView` gives fragile panels, switches and teleporters their own entities;
3. the player's block drops in from above (`intro.player_progress()`), starting only after the last
   tile has landed;
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
| `player_float_seconds` | `1.0` | How long the block takes to drop in |
| `tile_rise` | camera distance | Travel of a tile, from off-screen to its resting height |
| `player_drop` | camera distance | Travel of the block, from off-screen down into its start pose |

One tile therefore rises for a full second and the block then falls for a second; with the random
stagger the whole sequence runs roughly 2.5 s (`max delay + 1.0 + 1.0`), and input is held for all
of it.

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

`theme.py` is deliberately neutral: greys only, no lights, shadows, fog, gradients, or textures.
Entities use the `unlit_shader`. Values are written with `color.rgb32(...)` because Ursina's
`color.rgb()` expects floats in `0–1`; passing `0–255` values there clamps every colour to white.

`theme.md` does not exist yet. When it lands, replace the palette in `theme.py`; the rest of the
renderer does not contain theme decisions.

## Level completion

`PlayerController._animation_finished` checks `Board.is_goal`. On success it calls the scene's
`_level_cleared`, which calls `application.quit()`. This hard exit is intentional for the scaffold
and is marked with `TODO(#28)` in both `controller.py` and `app.py`, so the later results/next-level
flow is easy to find.

## Known limitations

- No menu, level select, solver panel, replay, or stats display.
- Split/merge/teleport changes snap instead of rolling.
- Fragile and switch cells are drawn from the palette but have no dedicated effects, so the load
  animation has no obstacle phase yet (marked `TODO(load-animation)`).
- The HUD is only the level name and a key hint, and it shows during the load animation.

## Verification

- `pytest tests/ -q` — 95 passed.
- `ruff check .` — clean.
- Offscreen Ursina smoke run — scene builds, tiles start below the board and the block above it,
  keys are ignored until `LoadIntro.finished`, both land on their resting heights, and the first
  legal move is accepted afterwards.
- A pivot-roll sweep across all stage files found a valid roll plan for every reachable unsplit
  transition (3,550 checked at the time).

## Related documents

- [`window.md`](window.md) — how the game window is created and configured (Ursina/Panda3D).
- [`contracts.md`](../contracts.md) — frozen core API and layer rules.
- [`decisions/ADR-002-gui-stack.md`](../decisions/ADR-002-gui-stack.md) — why Ursina.
