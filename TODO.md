# GUI / Gameplay TODO

Scope: the playable game and its Ursina GUI only. Solvers (`bloxorz.solvers`, #18-#23) and solver
playback are owned elsewhere; this list stops at making the game itself complete.

Work top to bottom — later items assume the earlier ones. One branch and one PR per item.

## 1. Cube control on split levels (L4)

`PlayerController.move()` takes the first successor whose direction matches and ignores
`action[0]`, the cube index. On `L4-01` / `L4-02` both cubes can accept the same direction, so
which one moves is decided by successor ordering and the player cannot steer the intended cube.

- [x] Add an "active cube" concept (e.g. number keys or `Tab` to switch).
- [x] Resolve an input to a concrete `(next_state, action)` pair instead of a bare direction, and
      pass that action to the animation. This is the shape solver playback will need later.
- [x] Show the active cube in the HUD.
- [x] Add a split-stage case to `tests/test_gui_controller.py` where both cubes accept the same
      direction.

## 2. End-of-level flow (#28)

Done: the goal raises `gui/win_overlay.py` instead of quitting, and both `TODO(#28)` markers are
gone.

- [x] Replace the hard exit with a win overlay: move count and elapsed time.
- [x] Offer next level / retry / back to level select.
- [x] Add a retry key — switch puzzles can leave the block in a losing position, and today the only
      recovery is restarting the process.
- [x] Add undo (a stack of immutable `State` values in the controller) with a visible hint.
- [x] Remove both `TODO(#28)` markers and update `docs/gui/gui-scaffold.md` § Level completion.

## 3. HUD

Today it is the level name plus one key hint (`PrototypeScene._build_hud`).

- [ ] Show move count and a running timer.
- [x] Show the active cube once item 1 exists.
- [x] Show restart/undo hints.
- [ ] Keep all colours and timings in `gui/theme.py`; document any new values in `docs/gui/theme.md`.

## 4. Level flow: menu, level select, progression

Done: the game boots into a level select (`gui/level_select.py`) built from
`Source/bloxorz/core/stages/`, and `--stage` still skips it.

- [ ] Add a title/menu scene.
- [x] Add a level-select grid grouped L1-L4, using the stages under
      `Source/bloxorz/core/stages/`.
- [x] Chain the next level after a win.
- [x] Remember cleared levels for the session (or in a small save file).
- [x] Update `docs/gui/gui-scaffold.md` § What it does and the `README.md` status section.

## 5. Animate split, merge and teleport

`docs/gui/gui-scaffold.md` § Roll animation notes that these transitions snap to the destination
pose while ordinary rolls are real quarter-turns — a visible quality gap on L4.

- [ ] Animate split-switch: the standing block separates into two cubes.
- [ ] Animate merge: two cubes become one lying block along the adjacency axis.
- [ ] Animate teleport: cubes cross the board to their target cells.
- [ ] Reuse the existing ease-out curve and `theme` timings rather than adding a second clock.
- [ ] Drop the matching bullet from § Known limitations once done.

## 6. Input feel

`PrototypeScene.update` polls `held_keys` every frame, so holding a key rolls continuously at the
OS repeat delay's mercy.

- [ ] Decide deliberately: one move per key press (an `input()` handler) or a tuned auto-repeat.
- [ ] Keep dropping keys pressed during the load animation and during a roll — never queue them.

## 7. Window and camera robustness

- [ ] Recompute camera framing and lens alignment on window resize. `_frame_camera` and
      `_align_camera_lens` run once at build time, so a resized window leaves the board off-centre
      while the parallax refits every frame.
- [ ] Check framing on the largest L4 board; `CAMERA_DISTANCE_FACTOR` may need per-stage tuning or a
      gentle camera follow.

## 8. Polish (only after 1-7)

- [ ] Sound cues for roll, switch and bridge.
- [ ] A short "stage cleared" transition.
- [ ] Screenshots/GIFs in `docs/gui` for the report.

## Not in scope

- Solvers (#18-#23), benchmark data, and the report tables/figures.
- Solver playback ("movie mode"). Keep the controller action-based (item 1) so that whoever owns the
  solvers can feed `SearchResult.path` through the same animation path the player uses.

## Before each PR

- [ ] `pytest -q` green, GUI tests still headless (no Ursina import under `tests/`).
- [ ] `ruff check .` green (line length 100).
- [ ] `docs/gui/gui-scaffold.md` and `README.md` status reflect what changed.
- [ ] One concern per PR; put each `Closes #n` on its own line.
