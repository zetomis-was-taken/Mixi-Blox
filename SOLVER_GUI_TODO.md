# Solver Replay (Movie Mode) — GUI TODO

Working checklist for the GUI side of solver playback (#28, rubric §3.7 / FAQ Q4). It is a plan,
not a spec: `docs/contracts.md` stays frozen, and nothing here adds or renames a core contract.

The goal: a Solve control on the level scene that runs an algorithm, then **rolls the block along
the returned `path` through the existing roll animation**, so the answer is demonstrated in 3D
rather than printed. It must be buildable and demoable now, with a mocked `solve()`, because
`bloxorz.solvers` (#18–#23) does not exist yet.

---

## 0. Ground truth (verify before starting)

| Thing | Today | File |
| --- | --- | --- |
| Result value | `SearchResult(status, path, cost, counts)` | `core/contracts.py:144` |
| Limits | `Caps(node_cap, time_s)`; `Caps()` = no limit | `core/contracts.py:104` |
| Metrics | `Counts(expanded, generated, frontier_peak)`; `Stats` is harness-built | `core/contracts.py:112` |
| Action | `Action = tuple[int, Direction]`, i.e. `(cube_index, "U"\|"D"\|"L"\|"R")` | `core/contracts.py:16` |
| Transitions | `board.successors(state) -> [(next_state, action), ...]` | `core/engine.py` |
| Roll animation | `block_view.animate(start, next_state, action, on_done)` | `gui/block_view.py:98` |
| Move logic | `PlayerController.move(direction)` — direction only, no action entry point | `gui/controller.py:82` |
| Goal | `_animation_finished` sets `cleared` and calls `on_goal` | `gui/controller.py:151` |
| Scene input | `PrototypeScene.input` gated by `intro.finished` / `cleared` | `gui/app.py:273` |
| HUD | `hud.refresh(moves, seconds, split, active)` | `gui/hud.py:66` |
| Win card | `WinOverlay(stage, moves, seconds, on_next, on_retry, on_levels)` | `gui/win_overlay.py:35` |
| Roll timing | `theme.ROLL_SECONDS = 0.22` | `gui/theme.py:73` |
| Solvers package | absent; `main.py --solver` is a stub | `Source/bloxorz/solvers/` |

Consequence: everything except the search is already present. The work below is a driver, one
controller seam, two UI surfaces, input gating, a mock, tests, docs.

---

## 1. Decisions to settle first

Settle these before writing the driver — they change its shape. Recommended default in **bold**.

1. **Where Solve lives**: **a small panel on the level scene** (four algorithm cards) vs. a level
   select entry vs. both. Level-scene-only is the smallest change and matches "Solve buttons".
2. **Does a solver run count as a cleared level?** **No** — do not add the stage to
   `Game.cleared`, so the level select keeps crediting only player clears.
3. **During playback, does the player's counter/clock move?** **No** — the HUD keeps the player's
   run; replay progress is shown separately. Otherwise the win card would report solver moves as
   the player's.
4. **Stop behaviour**: **`Esc` cancels and restores the pre-solve state exactly** (state, active
   cube, view pose); no half-finished board left behind.
5. **Speed control**: nice-to-have. If included, it changes only the inter-move pause, never
   `theme.ROLL_SECONDS`.
6. **Stats shown**: `len(path)`, `cost`, and the three `Counts`. **No time/memory** — the GUI may
   not time anything (see §6).

---

## 2. Phase A — replay driver (pure, Ursina-free)

**New file: `Source/bloxorz/gui/replay.py`.** No Ursina import, like `intro.py` / `results.py` /
`catalog.py`, so it is testable headless.

- [ ] A `Replay` object built from a `SearchResult`, the `Board`, and a step-pacing value.
- [ ] It computes the **state sequence once**, up front, by walking `board.successors` and matching
      each `Action` in `path`. Never construct a `State`; never re-implement a transition.
- [ ] It raises/short-circuits on a path that cannot be followed (an illegal action) — see traps.
- [ ] State machine: `ready → playing → paused → finished`, plus `aborted`. Small, explicit,
      no booleans soup.
- [ ] `advance(dt)`-style tick that returns "start the next roll" only after the previous roll
      finished and the inter-move pause elapsed; one action in flight at a time.
- [ ] `progress` as `(index, total)` for the HUD line, and `remaining` for the card.
- [ ] `stop()` returns the pre-solve `State` (and every intermediate state it produced) so the
      scene can restore without replaying in reverse.
- [ ] Speed multiplier (`1.0` default) applied to the pause only.
- [ ] Empty `path` with `status == "solved"` is a valid, instantly-finished replay (start already
      at goal) — no divide-by-zero, no phantom roll.

**Pacing constant:** add the inter-move pause to `gui/theme.py` beside `ROLL_SECONDS`
(a named constant, no magic number). Document it in `docs/gui/theme.md` only if it is
user-visible.

**Done when:** a headless test can drive a fake path from start to goal with no Ursina installed,
and asserts the state sequence, the terminal status, and the restore value.

---

## 3. Phase B — controller seam: apply one `Action`

`PlayerController` can only take a `Direction` (`move` → `resolve`). Playback has a concrete
action and must not re-resolve it.

- [ ] Add one small method that applies `(next_state, action)` directly: update `state`, `active`
      (via the existing `_active_after`), set `animating`, call `block.animate(...)`, and reuse
      `_animation_finished` for the goal.
- [ ] It **must not** touch `moves`, `elapsed`, or `history` — replay is not a player move and
      must not be undoable with `Z`.
- [ ] It refuses while `animating` or `cleared`, exactly like `move`.
- [ ] Do not duplicate `move`'s body: factor the shared tail (state, active, animating, animate)
      so both paths use one implementation.

**Done when:** existing `tests/test_gui_controller.py` still passes, and a new test shows
replay-apply leaves `moves == 0`, `history == []`, and still fires the goal callback.

---

## 4. Phase C — injection point + mock solver

The GUI must not import a solver module that does not exist, and must not grow a fake algorithm
inside `bloxorz.solvers/` (that package is owned by #18–#23 and policed by `tests/test_contract.py`).

- [ ] `PrototypeScene(stage, game, solve=None)` — a `Callable[[Stage, Caps], SearchResult] | None`.
      `None` hides the Solve panel.
- [ ] `Game.play(stage, solve=None)` and `build(..., solve=None)` thread it through; `run()` passes
      `None` for now.
- [ ] A dev-only demo path so the animation can be eyeballed before #18 lands: either a
      `--replay-demo` flag on `main.py` (dev-only, documented as temporary) or a test-only scene
      that builds offscreen. The fixed action sequence for `L1-01` is a 7-move win per the
      scaffold probe; **verify it against `board.successors` before committing it**.
- [ ] The mock returns a real `SearchResult`: `status="solved"`, `path` as a `tuple[Action, ...]`,
      `cost` summed from `engine.step_cost`, and a plausible `Counts`.
- [ ] The mock lives in `tests/` (or the dev flag), never in `Source/bloxorz/solvers/`.
- [ ] Import `SearchResult` / `Caps` from `bloxorz.core.contracts`. **Never** from
      `bloxorz.bench` — the layer rule is `gui -> core + solvers`.

**Done when:** deleting the flag/mock leaves the game exactly as today, and adding the real
`bfs/dfs/ucs/astar` later means only passing a different callable.

---

## 5. Phase D — UI surfaces

### D1. Solve panel (level scene)

- [ ] Four cards (BFS / DFS / UCS / A\*) from `widgets.py`, in `theme` colours, placed so they do
      not cover the board or the HUD; hidden while `LoadIntro` is running and once the level is
      cleared.
- [ ] Palette additions go in `gui/theme.py` and get a row in `docs/gui/theme.md` — no colours in
      the panel file.
- [ ] A "solving…" state: Ursina is single-threaded, so a long search freezes the frame. Show the
      card state **before** calling `solve` (build/label/refresh, then the blocking call), or the
      user sees a dead window.
- [ ] Solver memory: `{stage_id: {algorithm: SearchResult}}` on `Game`, so the panel can show a
      previous run instead of re-solving after a cancel. Optional, one dict, no persistence.

### D2. Replay HUD line

- [ ] Show `"BFS replay — move 4 of 19"` style text (or paused/finished variants) in the HUD's
      empty region. Extend `Hud.refresh` with optional parameters, or add a dedicated
      `Hud.show_replay(...)`; **do not** overload the player's move/clock line.
- [ ] Wording comes from `results.py` (pure module) so tests read it headless and the card cannot
      drift from the HUD — same rule as `result_line`.

### D3. Result card

- [ ] New overlay (or an extended `WinOverlay`) for solver runs: algorithm, `status`, solution
      length, `cost`, `Counts`, and the exits (replay again / back to level select / stop).
- [ ] For `cap` and `unsolvable`, present the outcome **without** playing a movie: a card that
      states which limit was hit (or that no solution exists) plus the counts collected.
- [ ] A solver run reaching the goal must not raise the `Level cleared` card with the player's
      counter at 0 moves — that reads as a bug. Either reuse `WinOverlay` with explicit
      solver-labelled numbers or add the solver card; decide in §1.2 and be consistent.
- [ ] `solved` with empty path: card straight away, no rolls.

---

## 6. Phase E — wiring, input gating, and the traps

- [ ] `PrototypeScene.input`: while a replay is active or paused, ignore direction keys, `Tab`,
      `Z`, `R` — and accept **only** the stop/pause key(s). Same reasoning as "a press mid-roll is
      dropped", not queued.
- [ ] `PrototypeScene.update`: drive `replay.advance(dt)`; start the next roll from the callback of
      the previous one. One action in flight at a time.
- [ ] Clock: `controller.tick(dt)` keeps running today. Pause it during playback (or accept it
      running and never present it as replay time — pick one and say so in the doc).
- [ ] Stop/`Esc`: restore the pre-solve `State`, re-sync `block_view`/`board_view` (mechanisms
      retarget in the same frame, like `retry`/`undo`), clear the replay.
- [ ] Leaving the level (`teardown`, next level, level select) cancels the replay and removes its
      UI, like `Hud.teardown` / `WinOverlay` destruction.
- [ ] Never add solver clears to `Game.cleared` (per §1.2).
- [ ] **Do not measure time or memory in the GUI.** `tests/test_contract.py` allows `perf_counter`
      only in `bench/` and `solvers/` (rule 5); `Stats` is harness-built. Show `Counts` only, or
      source stats from the bench harness later.

---

## 7. Phase F — tests

Follow the existing headless style; no Ursina import in `tests/`.

- [ ] `tests/test_gui_replay.py`: state sequence from a fixed `path`, one-action-at-a-time
      pacing, `stop()` restore value, empty path, illegal path rejection, `cap`/`unsolvable`
      producing no movie.
- [ ] Extend `tests/test_gui_controller.py`: replay-apply does not touch `moves`/`history`/`elapsed`
      and still triggers `on_goal`.
- [ ] `tests/test_gui_results.py`: replay HUD/card wording (pure functions).
- [ ] A `SearchResult` mock with a **validated** path; assert every action is in
      `board.successors` at the state it is applied to. This is the single most valuable test —
      an invalid mock looks like a rendering bug.
- [ ] Optional offscreen Ursina probe, recorded in `docs/gui/gui-scaffold.md` § Verification:
      e.g. "the demo path played 7 rolls in order, no input accepted mid-replay, `Esc` restored
      the start pose and the counter read 0 moves".
- [ ] `pytest -q` and `ruff check .` green (132 tests today, line length 100).

---

## 8. Phase G — documentation

- [ ] `docs/gui/gui-scaffold.md`: add the new files to the Structure table, add playback to
      "What it does", **delete** the "No solver panel, replay, or stats display" limitation,
      record the probe results.
- [ ] `docs/gui/theme.md`: palette rows for any new colours; timing row if the pause is exposed.
- [ ] `README.md`: replace the "Solver playback ("movie mode")" missing-item entry with what now
      exists, and state that the search itself still waits on #18–#23.
- [ ] `AGENTS.md`: add `gui/replay.py` (and the panel/overlay files) to the project layout.
- [ ] This file: tick what is done, or delete it when the feature lands.
- [ ] **Do not edit `docs/contracts.md`.** The Solver API is frozen v1; the GUI is a consumer
      ("#28 renders the same path, using each action's cube index").

---

## 9. Definition of done

1. On a level with a mock `solve`, picking an algorithm rolls the block along the path, one action
   per roll, reusing `BlockView.animate` — no new animation code path.
2. Split stages: the action's cube index decides which cube rolls and which is tinted active;
   split/merge/teleport transitions snap, matching existing behaviour.
3. No player input reaches the controller during playback; `Esc` stops and restores the exact
   pre-solve state; the HUD's player counter is never advanced by solver moves.
4. `cap` and `unsolvable` show a card, never a movie; `solved` with an empty path shows the card
   immediately.
5. Swapping the mock for real `bfs/dfs/ucs/astar` requires no GUI change — only a different
   callable at the injection point.
6. `pytest -q` and `ruff check .` green; docs updated; no mock, flag, or scratch file left in
   `Source/bloxorz/solvers/` or anywhere else.
7. One concern per PR into `main`, each `Closes #n` on its own line.

---

## 10. Traps (each one already bit someone in this repo's history or its docs)

- **Invalid mock path** does not raise — the view snaps or teleports and you debug the wrong
  layer. Validate the sequence against `board.successors`.
- **`State` re-sorts split cubes by cell** (`contracts.py:__post_init__`), so a hand-written split
  path with stale indices is wrong even when the cells look right. Derive states through the
  engine.
- **`moves` is not `len(path)`** in the player's run: the HUD's number and the solver's solution
  length are two different numbers and both are shown. Candidate for a confusing bug report.
- **Blocking search**: build the "solving" UI first, then call `solve()`; otherwise the window
  hangs with no feedback.
- **Import direction**: `gui` may import `core` (+ `solvers` later) — not `bench`, not `search`.
  `SearchResult` comes from `core.contracts`.
- **No clocks in the GUI**: `perf_counter` outside `bench/`/`solvers/` fails contract rule 5.
- **`WinOverlay` is modal** and the scene stops reading keys while it is up — a solver card must
  follow the same pattern rather than adding a second, competing input handler.
