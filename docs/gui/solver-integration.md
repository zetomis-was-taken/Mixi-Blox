# Wiring a solver into the GUI

How an algorithm written against `docs/contracts.md` becomes something the player can watch: four
Solve cards on a level, a real quarter-turn movie of the answer, and a result card. Written for
whoever implements BFS/DFS/UCS/A\* (#18–#23) — the GUI is a consumer of the solver, never a second
implementation of the search.

The frozen part is `docs/contracts.md` § Solver API. This document is about the plumbing around it:
what the GUI already provides, what an algorithm has to return, and where the two meet.

## What already exists

| Piece | Where | What it does |
| --- | --- | --- |
| `Solve` | `gui/replay.py` | `Callable[[Stage, Caps], SearchResult]` — the GUI's name for `solve` |
| `Replay` | `gui/replay.py` | Turns `SearchResult.path` into `(start, landing, action)` steps and paces them, one roll in flight at a time |
| `PlayerController.play` | `gui/controller.py` | Applies one planned `(next_state, action)`; costs the player nothing (`moves`, `elapsed`, `history` untouched) |
| `BlockView.animate` | `gui/block_view.py` | The existing quarter-turn animation; playback reuses it, so there is no second animation path |
| Injection point | `gui/app.py` | `run(..., solve=…)`, fed by `Source/main.py` from `bloxorz.solvers.ALGORITHMS` → `build(..., solve=…)` → `Game(stages, solve)` → `PrototypeScene(stage, game, solve)`; `solve` is an `Algorithms` mapping (card name → solver) |
| `SolverPanel` / `SolverOverlay` | `gui/solver_panel.py`, `gui/solver_overlay.py` | The four Solve cards, and the result card with the run's counts and the benchmark figures |
| `gui/benchmarks.py` | `gui/benchmarks.py` | Reads `Report/data/benchmark_results.json`; the card's time and peak memory come from here |
| `theme.ROLL_SECONDS` | `gui/theme.py` | `0.22` s for a quarter-turn; playback does not change it |
| `theme.REPLAY_PAUSE_SECONDS` | `gui/theme.py` | `0.12` s between two rolls of a movie |

The panel, the HUD replay line, the result card, the input gate and the `ALGORITHMS` registry are
in place, and `main.py --gui` passes that registry, so the four cards are live. This document is
now the recipe for whoever adds or changes an algorithm.

## The boundary: one function, one value

```python
def solve(stage: Stage, caps: Caps = Caps()) -> SearchResult
```

Rules that matter to the GUI (all from `docs/contracts.md`):

- `Board(stage)` is O(1): the stage arrives already compiled by `load_stage`, so `solve` does no
  I/O and no indexing.
- Return a value for **every** search outcome. Raise only on a programming error (malformed stage,
  missing transition). An exception is a defect, not a result.
- `path` is empty unless `status == "solved"`. `solved` with `path == ()` is legal and means the
  start already satisfies the goal.
- `cost` is a `float` under `step_cost`; moves are `len(path)` — there is no `moves` field.
- `counts` is populated in all three statuses.
- `Caps()` means no limit. The loop tests the goal **before** the cap, and counts `expanded` only
  for nodes whose successors were generated.
- Solvers may import `core` only. They must not import `bench` or `gui`.

The GUI reads attributes — `result.status`, `result.path`, `result.cost`, `result.counts` — and
never branches on the shape of a tuple.

## Step 1 — write the algorithm

One module per algorithm under `Source/bloxorz/solvers/`, plus the shared pieces (`base.py`) that
#18 owns. Standard library plus `bloxorz.core` only.

```python
# Source/bloxorz/solvers/bfs.py  (sketch — the real one is #19)
from collections import deque
from time import perf_counter

from bloxorz.core.contracts import Caps, Counts, SearchResult, Stage
from bloxorz.core.engine import Board


def solve(stage: Stage, caps: Caps = Caps()) -> SearchResult:
    board = Board(stage)
    start = board.start()
    t0 = perf_counter()

    # ``Counts`` is frozen: the running totals are locals, and a value is built only at a return.
    expanded, generated, frontier_peak = 0, 1, 1

    def counts() -> Counts:
        return Counts(expanded, generated, frontier_peak)

    frontier = deque([(start, (), 0.0)])
    seen = {start.key()}

    while frontier:
        if caps.time_s is not None and (perf_counter() - t0) >= caps.time_s:
            return SearchResult("cap", (), 0.0, counts())

        state, path, cost = frontier.popleft()
        if board.is_goal(state):
            return SearchResult("solved", path, cost, counts())
        if caps.node_cap is not None and expanded >= caps.node_cap:
            return SearchResult("cap", (), 0.0, counts())

        expanded += 1
        for next_state, action in board.successors(state):
            if next_state.key() in seen:
                continue
            seen.add(next_state.key())
            generated += 1
            cost_after = cost + board.step_cost(state, action, next_state)
            frontier.append((next_state, path + (action,), cost_after))
            frontier_peak = max(frontier_peak, len(frontier))

    return SearchResult("unsolvable", (), 0.0, counts())
```

Follow the loop shape in `docs/contracts.md` exactly — the goal test before the cap check is what
makes a solution found at the cap still report `solved`, and the cap check before the increment is
what makes `node_cap` a count of completed expansions. The timing above is allowed in `solvers/`
only (contract rule 5); do not measure time inside the GUI.

The four algorithms differ only in frontier ordering and, for UCS/A\*, in ordering by cost. Action
generation is always `board.successors`; never rebuild a transition.

## Step 2 — register the algorithms for the panel

The level scene needs a list of choices to draw. Keep it in the solvers package so the GUI has one
import and no knowledge of module names:

```python
# Source/bloxorz/solvers/__init__.py — the registry the panel reads
from collections.abc import Callable

from bloxorz.core.contracts import Caps, SearchResult, Stage

from .astar import solve as astar
from .bfs import solve as bfs
from .dfs import solve as dfs
from .ucs import solve as ucs

Solve = Callable[[Stage, Caps], SearchResult]

ALGORITHMS: dict[str, Solve] = {"BFS": bfs, "DFS": dfs, "UCS": ucs, "A*": astar}
```

The GUI's panel iterates `ALGORITHMS.items()` to build its cards. That mapping is the whole
coupling: adding an algorithm is a dictionary entry, and the panel never changes. (`replay.Solve`
and this `Solve` are the same signature; the alias is duplicated because `solvers` may not import
`gui`.)

## Step 3 — inject the solver

`run` and `build` take an `Algorithms` mapping (`replay.py`: `Mapping[str, Solve]`), defaulting to
`None` — no mapping, no Solve control, exactly the game as it plays today. Passing the mapping is
the whole wiring:

```python
# Source/main.py — the mapping goes straight through
from bloxorz.gui.app import run
from bloxorz.solvers import ALGORITHMS

return run(args.stage, solve=ALGORITHMS)
```

The keys are the card labels and their insertion order is the card order, so the four cards come
from the four dictionary entries and nothing in `gui/` needs to change when one is added.

`main.py` keeps the import inside its `--gui` branch: `gui/` imports `bloxorz.core` and
`gui.replay` only, never the solvers package at module scope, and a CLI solver run never pays for
Ursina. Changing which algorithms the panel offers is therefore an edit to `ALGORITHMS` alone.

## Step 4 — turn the answer into a movie

The panel's job is small; `Replay` does the pacing:

```python
# On a level scene, once the player picked an algorithm (sketch, phase D–E)
result = self.solve[self.algorithm](self.stage, Caps(node_cap=self.node_cap))
self.replay = Replay(
    self.board,
    result,
    theme.REPLAY_PAUSE_SECONDS,   # 0.12 s between rolls
    restore=self.controller.state,  # what Esc puts back
)
if not self.replay.playable:
    self._show_solver_result(result)   # cap / unsolvable / already home
    return
self.replay.start()
```

Then, from the scene's `update`:

```python
step = self.replay.advance(time.dt)
if step is not None:
    start, next_state, action = step
    if not self.controller.play(next_state, action):
        # The replay and the board disagreed: stop rather than leave a roll in flight.
        self._stop_replay()
        return
if self.replay is not None and not self.controller.animating:
    self.replay.roll_finished()
```

Four things this relies on:

- `Replay` plans the path once, through `board.successors`, and raises `ValueError` on an illegal
  action. A solver whose path cannot be followed is a defect in the solver, not a GUI bug. The scene
  plans through `Replay.try_plan`, which answers `None` instead, so that defect costs the movie and
  not the frame loop: the card says the path is not legal here and offers no "watch again".
- `controller.play` validates the pair again and never counts it as a player move. If it returns
  `False`, the scene aborted input or the pair drifted: stop the replay.
- The roll landing is observed as `controller.animating` going false — the same flag the manual
  game uses. `roll_finished()` is idempotent, so calling it every frame is safe.
- `advance` hands out nothing while a roll is in flight, so the scene never has to defend against
  overlapping animations.

## Step 5 — handle the three statuses

| `status` | What the GUI does |
| --- | --- |
| `solved`, non-empty path | Build a `Replay` and play the movie; the card follows the last roll |
| `solved`, empty path | No movie — show the result card at once (the start is already the goal) |
| `cap` | No movie — card naming the limit that was hit (`node_cap` / `time_s`) plus the counts |
| `unsolvable` | No movie — card stating no solution exists |

The card reports `len(result.path)`, `result.cost` and `result.counts.expanded/generated/
frontier_peak`, and, on a solved run, the harness's `time_ms` and `peak_mem_kb` for the same stage
and algorithm. `gui/benchmarks.py` reads those two from `Report/data/benchmark_results.json`, keyed
by stage name and algorithm, and the line labels them `bench`: they are the committed benchmark
record, not a measurement of this run. `SearchResult` carries no time or memory, and the GUI may not
measure either — `perf_counter` outside `bench/` and `solvers/`, and `tracemalloc` outside `bench/`,
fail contract rule 5. A stage outside the benchmark set, or a tree shipped without `Report/`, shows
the line without them. The record was measured with the harness's own caps; the GUI's 10 s cap only
bounds the live search and, on the ten benchmark stages, never fires.

A solver run must not call `game.level_cleared(stage)`: the level select tints a stage cyan only for
a player clear. Playback that reaches the goal should raise the solver card, not `WinOverlay`'s
"Level cleared" with the player's counter at 0 moves.

## Step 6 — input, split stages, and stopping

- While a replay is playing or paused, ignore direction keys, `Tab`, `Z` and `R`; accept only the
  stop/pause keys (`Esc` and `Space` in the current scene). The scene already drops input mid-roll;
  the same gate drops a stop that arrives mid-roll.
- A stop is not a retry. The scene holds a `PlayerController.snapshot()` from before playback and
  puts it back with `restore`, which also restores the move count, the clock and the undo stack and
  re-syncs the view, so bridges and plates retarget in the same frame.
- Split stages: do nothing special. The action carries its cube index, `controller.play` follows
  `_active_after`, and `BlockView.animate` rolls exactly that cube. Split-switch, merge and
  teleport transitions snap instead of rolling — the same limitation the manual game has.
- Leaving the scene (level select, next level, `teardown`) destroys the panel and card with the
  rest of the scene; a replay left running would keep a reference alive.

## Testing

Headless first, per the project's GUI rule (never import Ursina in `tests/`):

- The solver's own tests: counts, statuses, cap precedence, fixture `expected.optimal_cost`.
- Playback: `tests/test_gui_replay.py` already drives the driver with a mock solver
  (`_solved`, a real BFS) so every mocked path is legal by construction; `tests/test_gui_controller.py`
  covers the cost-free apply. Add cases for a new algorithm's path, including a split stage.
- Offscreen probe (documented in `gui-scaffold.md` § Verification): pick a card, watch the rolls,
  confirm a key press mid-replay is ignored, `Esc` restores the pre-solve pose, and the card reads
  the counts.
- `tests/test_contract.py` enforces the layer rules: `solvers` imports `core` only, no clocks
  outside `bench/`/`solvers/`, `SearchResult` lives in `core/contracts.py`.

## Pitfalls

| Symptom | Cause |
| --- | --- |
| The block jumps to a wrong tile instead of rolling | A path action is not legal from the state it is applied to — `Replay` should have raised; check the mock, not the view |
| A split level animates the wrong cube | Indices were hand-written instead of derived through the engine; `State` re-sorts cubes by cell |
| The card says `7 moves` but the HUD says `0 moves` | Expected: solver length and player moves are different numbers, and both are shown |
| A `cap` result plays a movie | The scene branched on `path` instead of `status`; `cap` and `unsolvable` carry an empty path |
| `node_cap` returns one more expansion than expected | The cap is checked before the increment, so it is the number of completed expansions |
| A long DFS freezes the window | `solve` is synchronous and Ursina is single-threaded; show the "solving" state first, and pass a deadline — the scene uses `Caps(time_s=SOLVE_TIME_CAP_SECONDS)`, so an over-long run returns `cap` and the card says why |
| `ImportError: bloxorz.solvers` | Something in `gui/` imported the solvers package at module scope; the mapping belongs to the caller (`main.py`) and reaches the scene through `run(..., solve=…)` |
| `perf_counter` flagged by the contract test | Timing belongs to `bench/` or `solvers/`, never the GUI |

## Checklist for adding an algorithm

- [ ] `Source/bloxorz/solvers/<algo>.py` with `solve(stage, caps)`, the frozen loop shape, and the
      right `Counts`.
- [ ] Entry in `ALGORITHMS`.
- [ ] A headless test with a fixture stage, including a `cap` run and an unsolvable stage.
- [ ] Playback test: its path through `Replay` reaches the goal; split stage keeps cube indices.
- [ ] Panel card appears; picking it solves, plays, and shows the counts.
- [ ] `pytest -q`, `ruff check .`, and the offscreen probe green.
