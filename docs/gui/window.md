# The Window: How It Works and How It Is Configured

A report on the game's window: who creates it, every setting this project passes in, what Ursina and
Panda3D do with those settings, and how the window relates to the camera, the HUD and the frame loop.

Measurements below were taken on **Ursina 7.0.0 / Panda3D, Python 3.11**, 1920×1080 primary monitor,
by building the scene with `window_type="onscreen"` and reading back `base.win.getProperties()`.

## 1. Who owns the window

The window is not ours. `ADR-002` chose Ursina (a thin layer over Panda3D) and accepted that *"Ursina
owns the window and the main loop"*. In practice that means:

- `Ursina(...)` is a **singleton `ShowBase`** — it can only be instantiated once and cannot be
  subclassed, which is why the game's per-frame logic lives in `PrototypeScene(Entity)` instead.
- Panda3D owns the native window, its properties, the render loop and the graphics pipe.
- The game only ever touches the window through the `Ursina(...)` constructor and three module-level
  writes: `Entity.default_shader`, `window.color`, and `camera.*`.

Everything window-related in this project is therefore concentrated in one function,
`build()` in `Source/bloxorz/gui/app.py`.

## 2. The configuration as written

`Source/bloxorz/gui/app.py`:

```python
app = Ursina(
    title=f"Mixi-Blox  |  {stage.id} {stage.name}",
    borderless=False,
    fullscreen=False,
    size=(1280, 800),
    development_mode=False,
    editor_ui_enabled=False,
    window_type=window_type,          # "onscreen" by default, "offscreen" for smoke tests
)

Entity.default_shader = unlit_shader  # flat silhouettes: no lights, no fog, no shadows
window.color = theme.BACKGROUND       # rgb32(255, 238, 204)
```

| Argument | Value | What it actually does | Ursina default |
| --- | --- | --- | --- |
| `title` | `Mixi-Blox  |  <stage id> <stage name>` | Sets `WindowProperties` title, also the taskbar label. Changes per stage. | `'ursina'` |
| `borderless` | `False` | Loads the Panda3D prc variable `undecorated False`, so the OS title bar and resize frame stay. Ursina's exit button is enabled from this flag too (`enabled=self.borderless`), so a bordered window has no in-window "x" from Ursina's editor UI. | `True` |
| `fullscreen` | `False` | Selects which size the `win-size` prc line uses (see §3 — here both branches are 1280×800, so it is a no-op). | `False` |
| `size` | `(1280, 800)` | Becomes both `windowed_size` and `fullscreen_size`, and the `win-size 1280 800` prc line. Fixes the 16:10 aspect ratio (1.6). | `None` → monitor size, windowed = monitor / 1.25 |
| `development_mode` | `False` | Turns the hot-reloader off, and (in `Ursina.__init__`) forces the `fullscreen=True` branch — which here is identical, see §3. It also removes the editor overlay in builds. | `True` |
| `editor_ui_enabled` | `False` | Ursina still **builds** `window.editor_ui` (exit button, FPS counter, entity/collider counters, cog menu), then sets `window.editor_ui.enabled = False`, so none of it is drawn. | `True` |
| `window_type` | `"onscreen"` / `"offscreen"` | `offscreen` builds the whole scene with a render buffer and no visible window — this is how the GUI smoke checks run in a headless-ish process and in CI. | `'onscreen'` |

Two Panda3D settings are deliberately *not* touched: there is no `vsync` argument (Ursina applies
`vsync = True` in `window.apply_settings()` and notes it cannot be changed during play), and no
`icon` argument, so the window keeps Ursina's default `textures/ursina.ico`.

## 3. What Ursina does with it (the parts that surprise people)

- **The window is created in two steps.** `window.ready(...)` loads the Panda3D prc variables:
  `window-title`, `undecorated <borderless>`, `win-size <w> <h>`, `coordinate-system y-up-left`,
  `notify-level-util error`, `textures-auto-power-2`, plus the fallback pipes `pandadx9`, `pandadx8`
  and `tinydisplay`. Only afterwards does `ShowBase.__init__` open the actual window, and then
  `window.apply_settings()` runs.
- **`development_mode=False` implies fullscreen inside Ursina.** `ursina/main.py` contains
  `if not application.development_mode: fullscreen = True`. It is a blunt override of the
  `fullscreen=False` we pass. It does not visibly matter here *only* because we also pass an explicit
  `size`: the windowed branch would use `win-size 1280 800` and the fullscreen branch uses
  `win-size 1280 800` as well. Drop `size` and `development_mode=False` would open at the monitor
  resolution instead of a 1280×800 window.
- **`fullscreen` is not really applied.** Ursina's `Window.fullscreen` setter calls
  `WindowProperties.setFullscreen` only in a commented-out line (`# self.setFullscreen(value)`); it
  resizes the window and requests properties instead. A real fullscreen flag has to come from a prc
  variable. This is why the measured window reports `getFullscreen() == False` even though
  `development_mode=False` "asked" for fullscreen.
- **`window.color` is set by Ursina, then overwritten by us.** `apply_settings()` assigns
  `color.dark_gray`; the game immediately replaces it with `theme.BACKGROUND`, so the clear colour is
  the project's palette, not Ursina's.
- **Ursina's own hotkeys stay live.** `window.input_entity` (the F10 render mode / F11
  fullscreen-resize / F12 editor-UI toggle handler) is parented to the scene, not to the disabled
  editor UI, so those keys still respond in the shipped prototype. `Shift+Q` and the editor "x"
  button do not, because `exit_button` lives inside `editor_ui` and is disabled.

Measured window state for `L1-01` after `build(...)`:

| Property | Value |
| --- | --- |
| Client size | 1280 × 800 (aspect 1.6) |
| Decorated | yes (`getUndecorated() == False`) |
| Fullscreen flag | `False` |
| Position | (320, 140) — centred on the 1920×1080 primary monitor by `window.center_on_screen()` |
| Title | `Mixi-Blox  \|  L1-01 Long corridor` |
| Clear colour | `Color(1.0, 0.9333, 0.8, 1.0)` = `rgb32(255, 238, 204)` |
| `window.editor_ui.enabled` | `False` |
| `application.hot_reloader.enabled` | `False` |

## 4. Window → camera → HUD

The window is the frame the camera has to fit into, and everything visual is derived from its aspect
ratio.

**Camera framing** (`PrototypeScene._frame_camera`) is computed from the board, not from the window,
except through the aspect ratio:

```python
distance = max(rows, cols) * TILE_SIZE * CAMERA_DISTANCE_FACTOR   # 15 * 1.0 * 1.5 = 22.5 for L1-01
camera.fov = 45.0
camera.position = target - (sin(yaw)cos(pitch), -sin(pitch), cos(yaw)cos(pitch)) * distance
camera.rotation = (40.0, 25.0, 0.0)      # set directly; look_at() introduced roll
```

Measured for `L1-01` (10 × 15 grid): camera at `(-7.784, 14.963, -15.621)`, rotation
`(40, 25, 0)`, lens fov `45 × 29.03`, film size `(1, 0.625)`. Note that `camera.fov = 45` is the
**horizontal** field of view in Panda3D terms; the vertical fov is derived from the aspect ratio
(29.03° at 16:10). A narrower window therefore sees *more* vertically, and a wider window sees less.

**Lens shift.** `_align_camera_lens` projects every non-void tile corner, measures how far the
projected outline is from the horizontal centre of the window (`0` in the `[-1, 1]` projection
space), and cancels it with a film offset — measured `-0.00954` on `L1-01`. That number is a
fraction of `film_size.x`, so the correction holds when the aspect ratio changes. The shift is
applied to the 3D lens (`base.camLens`), never to the UI camera, so the HUD does not move with it.

**HUD.** `gui/hud.py` places four `Text` entities at fixed UI coordinates: the level name at
`(-0.78, 0.47)`, the key hints at `(-0.78, 0.43)`, the active cube at `(-0.78, 0.39)`, and the live
move/clock counter at `(0.78, 0.47)` with `origin=(0.5, 0.5)` so it grows leftwards from the right
edge. The small lines use `scale=0.8` of the level name's size. Ursina's UI space is
aspect-corrected: at 16:10 the horizontal range is `[-0.8, 0.8]` and the vertical range is
`[-0.5, 0.5]`, so `x = -0.78` sits 0.02 units inside the left edge and `y = 0.47` just below the top.
On a wider window the same `x` leaves a proportionally larger margin; on resize Ursina's
`update_aspect_ratio` rescales every `camera.ui` child by the ratio change, which keeps the HUD's
*relative* placement but not its pixel size.

**Load animation.** The pieces' vertical travel reuses the camera distance
(`_camera_distance(stage)`), which is what guarantees they start outside the window rather than just
below the board.

## 5. The frame loop the window drives

`run()` → `app.run()` → Panda3D's main loop. Ursina installs a single task (`Ursina._update`) that,
every frame:

1. updates `time.dt` / `time.dt_unscaled` from the frame clock;
2. calls `__main__.update()` if the entry script defines one (it does not here);
3. updates `application.sequences`;
4. calls `update()` on every enabled entity in the scene.

The game hooks in at step 4: `PrototypeScene` is an `Entity`, so its `update()` is called once per
frame and does all of the game's per-frame work — roll animation, load intro, bridge refresh, and
the input gate:

```python
def update(self) -> None:
    self.block_view.update(time.dt)
    if not self.intro.finished:            # load animation still playing
        self.intro.advance(time.dt)
        ...
    self.board_view.refresh(self.controller.state)
    ...
    if not self.intro.finished or self.controller.cleared:
        return                             # input only after loading, and no more once won
    self.controller.tick(time.dt)          # the level clock
    if self.controller.animating:
        return
    for key, direction in KEY_BINDINGS:    # held-key polling, not events
        if held_keys[key]:
            self.controller.move(direction)
```

Input arrives through Ursina's `held_keys` map (which is fed by Panda3D's `raw-<key>` events), not
through explicit event handlers, so holding a direction repeats the move as soon as the previous
roll finishes. The one-shot keys — `Tab` (switch cube), `Z` (undo), `R` (retry) — come through
`input()` instead, so holding them does not repeat.

The window is only closed by the player: the goal raises `WinOverlay` and stops the level's input.
`Esc` on that card tears the level scene down and rebuilds the level select, which is also the first
screen `build()` shows.

## 6. Entry point and window type

`Source/main.py --gui [--stage FILE]` imports `bloxorz.gui.app.run` lazily and calls it with
`args.stage`. With no `--stage` the game boots into the level select, which `build()` fills from
`catalog.load_catalog()`; with `--stage` the stage is loaded **before** any scene exists — `build()`
calls `load_stage()` first — so a bad stage path fails as a normal `StageError` in the terminal
instead of a broken window, and the window title and HUD can be built from validated data.

`build()` exposes `window_type`, which is the only seam the tests need:

- `"onscreen"` — normal play;
- `"offscreen"` — same scene, same code path, render buffer instead of a visible window; used by the
  GUI smoke checks that verify camera framing, the load animation and the roll animation.

## 7. Changing the window

| Goal | Where | Note |
| --- | --- | --- |
| Different resolution / aspect | `build()`, `size=` | Aspect drives the camera's vertical fov and the HUD margins; the lens shift rescales automatically. |
| Fullscreen | `build()`, `fullscreen=True` **and** a prc `fullscreen true` | `development_mode=False` alone does not do it (§3). |
| Bordered / borderless | `build()`, `borderless=` | `borderless=True` also enables Ursina's in-window "x" exit button. |
| Title | `window.title` in each scene | `Mixi-Blox | levels` on the select screen, `Mixi-Blox | <stage id> <name>` in a level. |
| Background colour | `gui/theme.py`, `BACKGROUND` | Applied via `window.color` in `build()`. |
| HUD placement / size | `gui/hud.py`, the layout constants | UI space is `[-0.8, 0.8] × [-0.5, 0.5]` at 16:10. |
| Hide Ursina's F10/F11/F12 hotkeys | `build()` | They live on `window.input_entity`; disabling that entity removes them. |

## 8. Known limitations

- No custom window icon; Ursina's default icon is used.
- Ursina's F10/F11/F12 hotkeys remain active in the game (§3).
- vsync is fixed on (Ursina applies it once, before entities exist) and is not exposed as a setting.
- The window is a fixed size at startup: no remembered size/position between runs, and no
  `forced_aspect_ratio`.
- `gui-scaffold.md` documents "no loading UI"; that is still true — the load animation animates the
  3D scene, it does not put anything in the window chrome.

## 9. Verification

- `pytest tests/ -q` — 99 passed (Ursina is never imported in tests).
- `ruff check .` — clean.
- On-screen probe (`build(..., window_type="onscreen")`, then read `base.win.getProperties()`):
  1280×800, not fullscreen, decorated, position (320, 140), stage-derived title, palette clear colour,
  editor UI disabled, hot-reloader off — the values in the table in §3.
- Offscreen probe across all ten stages: every piece starts outside the viewport at `|screen y| > 1`
  and lands inside the frame.

## Related documents

- [`gui-scaffold.md`](gui-scaffold.md) — the prototype as a whole (camera, roll and load animations).
- [`../decisions/ADR-002-gui-stack.md`](../decisions/ADR-002-gui-stack.md) — why Ursina, and why it
  owns the window.
- [`../contracts.md`](../contracts.md) — the frozen core API and layer rules the GUI must respect.
