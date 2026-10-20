# v1 Interface Contract

**Status:** v1, frozen 2026-10-20. Every clause below has an owner, and both acks are
confirmed — rule 6 is a standing start (§2.1, §2.2, and the single `S`), and `State` arity is 2.

This file records decisions, it does not make them. A section changes when the owner named
below changes it, and the change links its issue.

## Ownership

| Clause | Decided by | Written by | Issue |
| --- | --- | --- | --- |
| Layout, `Cell`, `Cube`, `Orientation`, `Action`, `State`, `Board`, `cells`, `StageIndex` | TanKhoiTV | TanKhoiTV | #8 |
| Stage format and loader | TanKhoiTV, coordinating #5 / #21 | aFlyingSeal (schema), TanKhoiTV (loader, rule 6) | #8 |
| Stats | Alexvuong2006 | Alexvuong2006, populated by the harness | #30 |
| Solver API, `Counts`, the unsolved result | aFlyingSeal | aFlyingSeal | #31 |

Where this file differs from an owner's original wording, the difference is recorded in the
pull-request history rather than silently applied.

## Layout

One answer to the question left open on #8: everything lives under `Source/bloxorz/`, which is
where the committed code already is.

| Path | Holds |
| --- | --- |
| `Source/bloxorz/core/contracts.py` | the types below — `State`, `Stage`, `StageIndex`, `Counts`, `Stats`, `SearchResult`, `Caps`, aliases |
| `Source/bloxorz/core/stage.py` | `load_stage(path) -> Stage`, the only way a stage enters the program |
| `Source/bloxorz/core/engine.py` | `Board`, the stage-scoped transition model |
| `Source/bloxorz/solvers/` | one module per algorithm, plus `base.py` (#18) |
| `Source/bloxorz/bench/` | the harness (#24) |

The package root is `Source/`, so `bloxorz.core.contracts` is the import path and `Source/` must
be on `sys.path` (or the package installed).

## Values

```python
Cell = tuple[int, int]                 # (row, col), 0-indexed
Cube = tuple[Cell, ...]                # 1 cell = a lone unit cube, 2 cells = half a lying block
Orientation = Literal["standing", "lying_h", "lying_v", "cube"]
Direction = Literal["U", "D", "L", "R"]
Action = tuple[int, Direction]         # (cube_index, direction); index 0 while unsplit
```

`Orientation` is derived from the piece and is never stored: two cubes is `cube`; one cube of two
cells is `lying_h` or `lying_v`; one cube of one cell is `standing`.

Four values rather than three because a lone `1x1x1` and a standing `1x1x2` behave differently in
four places §2.5 decides outright: a heavy switch and a split switch fire only for `standing`, the
goal accepts only `standing`, and fragile is impassable only for `standing`. Deriving standing-ness
from a stored rotation instead — the tempting shortcut — makes a unit cube report `standing` on one
frame and `lying` on the next.

There is no "switch control" action. A lone cube is steered by naming it in `Action`, because
changing control is free: it costs no move and cannot fail, so an edge for it would add a cost
that the game never charges.

### State

```python
@dataclass(frozen=True)
class State:
    cubes: tuple[Cube, ...]        # one cube normally, two when split
    bridges: tuple[bool, ...]      # one entry per stage bridge, in stage order
```

The field set never depends on the value: `cubes` is always a tuple and `bridges` is always a
tuple. Length varies with the position, shape does not. This keeps `key()` arity constant, as #6
requires — arity 2, asserted by #6's staleness test.

`bridges[i]` is open when `True`, and its cell is `stage.bridges[i].pos`. Solvers, the renderer and
the key all read it in that order; nothing re-sorts it.

### Cell access and pivot

```python
def cells(state: State) -> tuple[Cell, ...]: ...
```

The only sanctioned way to ask which cells the block occupies — one call per cube, flattened. The
pivot is the lexicographically smaller occupied cell, so no consumer re-derives it and the key
cannot depend on iteration order.

## Board — stage-scoped transitions

Transitions depend on stage data that a state does not carry: `switches[].bridges` says which
bridges a switch moves, `teleport_cubes` says where a split sends the cubes, and void and bridge
cells decide passability. So the transition model is bound to its stage, not a free function:

```python
class Board:
    def __init__(self, stage: Stage) -> None: ...

    def successors(self, state: State) -> list[tuple[State, Action]]: ...

    def step_cost(self, state: State, action: Action, next_state: State) -> float: ...

    def passable(self, cell: Cell, orientation: Orientation,
                 bridge_state: tuple[bool, ...]) -> bool: ...

    def is_goal(self, state: State) -> bool: ...
```

This replaces the free `successors(state)` wording in #8's acceptance criteria, which cannot
implement bridge wiring as written. `solve()` receives the stage and constructs the board, so the
solver API is unchanged.

**The constructor is O(1).** It holds a reference to the compiled stage and derives nothing; the
lookup tables are built by `load_stage` (see Stage). A `Board` is immutable after construction and
may be shared across solvers and runs.

`is_goal` is stated here because #31's loop calls it and no clause defined it: it is #8's Stage
rule §2.4, namely `orientation == "standing"` on a goal cell of an unsplit block.

| Glyph | Kind | Passable: standing / lying / lone cube | Activates when |
| --- | --- | --- | --- |
| `.` | void | ✗ / ✗ / ✗ | — |
| `o` | floor | ✓ / ✓ / ✓ | — |
| `S` | start | ✓ / ✓ / ✓ | — |
| `G` | goal | ✓ — **wins** / ✓ / ✓ — no win | standing only |
| `f` | fragile | ✗ / ✓ / ✓ | never |
| `=` | bridge | open ✓ / closed ✗, all three pieces | — |
| `+` | soft switch | ✓ / ✓ / ✓ | any contact |
| `X` | heavy switch | ✓ / ✓ / ✓ | standing only |
| `Y` | split switch | ✓ / ✓ / ✓ | standing only |

Passability and activation are separate columns deliberately: a switch is a floor tile that
reacts, not a tile that blocks.

Rules:

- `successors` is pure and carries no cost. An `Action` names its cube, so a cube may be moved
  twice in a row; while unsplit only index `0` is emitted. Actions that would place any cell over
  void or a closed bridge, or two cubes on one cell, are not generated — an illegal move is
  absence, not a losing transition. Fragile follows the same style: impassable for `standing`,
  rather than passable-then-detect-the-loss. A **switch** action is filtered the same way:
  `bridges` is updated first, and if the result leaves an occupied cell over a closed bridge, the
  action is not generated (ADR-005: a switch may not close a bridge under the block).
- `step_cost` defaults to `1.0` for every action (#7); non-uniform weights are policy, so tuning
  them never edits engine code.
- `passable` is the only place passability is decided. A cell declares exactly one kind, so it
  never has to reconcile two.
- The block starts **standing upright on `S`** — `AI - Project 1.pdf` §2.1, and standing occupies a
  single cell (§2.2), which is why every stage has exactly one `S`. Splitting is a transition,
  never a second start field.
- **Fragile** is §2.5's weight rule, read as load per tile: a standing `1x1x2` puts two units on
  one cell, a lying one puts one unit on each of two, and a lone cube puts one unit on one. So a
  lone cube is as safe as a lying block and only `standing` breaks the tile.
- A **heavy** or **split** switch fires only for `standing`; a **soft** switch fires on any
  contact. `Y` is inert for a lone cube.
- Merging happens on orthogonal adjacency and yields a lying block along the axis the two cubes
  are adjacent on.

## Stage

```python
@dataclass(frozen=True)
class Stage:
    id: str
    name: str
    group: str                 # L1 plain, L2 fragile, L3 switches, L4 combined
    grid: tuple[str, ...]
    source: str | None         # URL for transcribed stages, "original" for authored
    expected: Expected | None  # fixtures only
    index: StageIndex          # derived by load_stage, never by a consumer

@dataclass(frozen=True)
class StageIndex:
    rows: int
    cols: int
    kind: tuple[Kind, ...]                    # rows * cols, flat, one kind per cell
    bridge_of: dict[Cell, int]                # cell -> index into Stage.bridges
    switch_at: dict[Cell, Switch]             # cell -> wiring
    start: Cell
    goal: Cell
```

The loader derives everything the grid already states: `start`, `goal`, switch positions, bridge
cells, `rows`, `cols`, and the three lookup tables above. None of those is stored alongside the
grid, so the two can never disagree.

Compiling at load rather than at use is deliberate: those tables are input preparation, identical
for all four algorithms, so they belong before the measured window (see Stats) and outside
`Board.__init__`. Scanning the grid per `Board` would put the same work inside every measured run.

| Glyph | Kind |
| --- | --- |
| `.` | void |
| `o` | floor |
| `S` | start |
| `G` | goal |
| `f` | fragile |
| `=` | bridge |
| `+` | soft switch |
| `X` | heavy switch |
| `Y` | split switch |

A bridge is one tile: adjacent `==` are two bridges, not one. `bridge_state` is per cell, which is
the only shape `passable` can be asked about.

Switch entries carry every field; unused ones are `null`, never absent:

```json
{ "type": "split", "pos": [1,3], "action": null, "bridges": null, "teleport_cubes": [[4,2],[6,2]] }
{ "type": "soft",  "pos": [1,3], "action": "toggle", "bridges": [[1,7],[1,8]], "teleport_cubes": null }
{ "type": "heavy", "pos": [1,3], "action": "permanent", "bridges": [[1,7],[1,8]], "teleport_cubes": null }
```

Loader rules — any violation is a hard error carrying file and line:

1. `rows == len(grid)`; every line the same length; ragged grids rejected.
2. Exactly one `S`, exactly one `G`.
3. No `start` / `goal` fields; rejected if present.
4. Every `switches[].pos` has the marker matching its `type`, and every marker has exactly one
   entry. Same for `bridges[].pos` and `=`. Either direction of mismatch is rejected.
5. A switch may only link a bridge that appears in `bridges[]`.
6. The start block stands on a non-void tile that is not a closed bridge.

No seventh rule keeps the start off a fragile tile, because the schema makes that unreachable:
`S` is a kind, #17 fixes one kind per cell, so an `S` cell is never `f`. A fragile start would
require the start marker to become an overlay on a base tile, which is a schema change, not a
loader rule.

`expected.optimal_cost` is allowed only where the solution was hand-computed and is required for
fixtures. It is never produced by running a solver. Fixtures are tagged `L1` and count toward the
benchmark set (#5, #21).

## Stats

Transcribed from #30. `Stats` is the **harness-built** record of one algorithm-stage pair; the
solver's contribution is `Counts` (see Solver API).

```python
@dataclass(frozen=True)
class Stats:
    expanded: int
    generated: int
    frontier_peak: int
    time_s: float
    peak_mem_bytes: int

    @property
    def time_ms(self) -> float: ...
    @property
    def peak_mem_kb(self) -> float: ...
    @property
    def peak_mem_mb(self) -> float: ...
```

`Stats` has no defaults: every field is passed explicitly, so a missing metric fails loudly
instead of being zero-filled. All three counts are copied from a run's `Counts`; `time_s` and
`peak_mem_bytes` are measured by the harness. It is produced for all three search outcomes.

| Field | Meaning | Produced |
| --- | --- | --- |
| `expanded` | nodes popped from the frontier whose successors are evaluated | by the solver, after the goal test fails and before `successors(state)` |
| `generated` | nodes created and placed on the search space | by the solver, when the root is created and for every child pushed |
| `frontier_peak` | maximum `len(frontier)` reached | by the solver, after every push: `peak = max(peak, len(frontier))` |
| `time_s` | elapsed wall-clock seconds | by the harness, `time.perf_counter()` |
| `peak_mem_bytes` | peak heap bytes allocated during the search | by the harness, `tracemalloc` |

The goal test runs on pop, before expansion. If the initial state satisfies it, the run returns
immediately with `expanded == 0`, `generated == 1`, `frontier_peak == 1`.

Measurement protocol:

- **Window.** Starts immediately before `solve(stage, caps)` and stops immediately after it
  returns. Stage loading, JSON I/O, contract validation and the `StageIndex` compile happen
  strictly outside. Initial-state construction happens inside `solve()` and is measured.
- **Isolation.** Before each run: `gc.collect()`, `tracemalloc.start()`,
  `tracemalloc.reset_peak()`. On return or exception: `get_traced_memory()`, `tracemalloc.stop()`.
  Reading the peak after `solve()` returns is valid because a peak is a high-water mark — freeing
  the solver's structures does not lower it.
- **Repetition.** Three independent runs per algorithm-stage pair. `time_s` and `peak_mem_bytes`
  are the median; the counts are asserted identical across the three and copied into one `Stats`.
- **One record per call.** `SearchResult.counts` belongs to a single run. The median `Stats` is
  the harness's aggregate and is the only value the report reads.

Units and rounding:

| Metric | Stored | Displayed | Format |
| --- | --- | --- | --- |
| time | `time_s` | ms | `f"{time_ms:.2f}"` |
| memory | `peak_mem_bytes` | KB, or MB above 10 240 KB | `f"{peak_mem_kb:.2f}"`, `f"{peak_mem_mb:.3f}"` |
| counts | `int` | integer | `f"{value:,}"` |

Failure treatment:

- `cap` and `unsolvable` are outcomes, not crashes. All five metrics are recorded from the work
  done. Tables show `CAP` / `UNSOLVABLE`, measured values, and `-` for solution length. The `-` is
  an explicit special case: `len(path)` is 0 on both outcomes, so the exporter must not print it.
- An unhandled exception is a defect. It is recorded in `BenchmarkRecord.error_message` and every
  metric renders as `-`, never `0`, `0.0` or `-1`.

`BenchmarkRecord` itself is #24's: it is the table row, it carries `error_message`, and this
contract does not define it. What crosses the solver boundary is `SearchResult`; what crosses the
harness boundary is `Stats`.

§3.2 asks the solver stage to record Search Time, Memory Usage, Expanded Nodes and Solution
Length. Two of the four come out of `solve()` — `expanded` in `Counts`, solution length as
`len(path)` — and two are measured around the same call. Solution length is deliberately not a
`Stats` field, for the same reason #31 gives for dropping `moves`: it is `len(path)`.

## Solver API

Transcribed from #31.

```python
def solve(stage: Stage, caps: Caps = Caps()) -> SearchResult
```

Runs one algorithm until the goal, a cap, or exhaustion, and returns the outcome as a value. The
solver constructs `Board(stage)`, which is O(1) because the stage arrives compiled; loading is the
harness's work, so `solve()` does no I/O.

```python
Status = Literal["solved", "cap", "unsolvable"]

@dataclass(frozen=True)
class Caps:
    node_cap: int | None = None
    time_s: float | None = None

@dataclass(frozen=True)
class Counts:
    expanded: int
    generated: int
    frontier_peak: int

@dataclass(frozen=True)
class SearchResult:
    status: Status
    path: tuple[Action, ...]
    cost: float
    counts: Counts
```

`Status`, `Caps`, `Counts` and `SearchResult` live in `bloxorz.core.contracts`.

- `path` is empty unless `status == "solved"`.
- `cost` is the total step cost under `step_cost` and is a `float`, matching `step_cost`'s return
  type; moves is `len(path)`, and there is deliberately no `moves` field, for the reason #31
  gives: a second spelling of a derivable value is a value that can drift from its source.
- `counts` is populated in all three statuses. Time and memory are not here, because a solver
  cannot measure them without depending on a tracer being started by someone else.
- `Caps()` means no limit.

| `status` | Condition | `path` | `counts` |
| --- | --- | --- | --- |
| `solved` | the goal test passed on a node popped from the frontier | possibly empty | full |
| `cap` | the loop returned because `node_cap` or `time_s` was reached | empty | full |
| `unsolvable` | the frontier drained with no goal test ever passing | empty | full |

Precedence is structural, not a tie-break rule. The loop shape #18 must follow:

```python
def solve(stage: Stage, caps: Caps = Caps()) -> SearchResult:
    board = Board(stage)                 # O(1); no grid scan, no index build
    t0 = perf_counter()

    counts = Counts(expanded=0, generated=1, frontier_peak=1)
    frontier = Frontier()
    frontier.push(root(stage))

    while frontier:
        if caps.time_s is not None and (perf_counter() - t0) >= caps.time_s:
            return SearchResult("cap", (), 0.0, counts)

        node = frontier.pop()

        if board.is_goal(node.state):
            return SearchResult("solved", node.path, node.cost, counts)

        if caps.node_cap is not None and counts.expanded >= caps.node_cap:
            return SearchResult("cap", (), 0.0, counts)

        counts.expanded += 1             # counted only once its successors are generated

        for state, action in board.successors(node.state):
            counts.generated += 1
            frontier.push(node.child(state, action))
            counts.frontier_peak = max(counts.frontier_peak, len(frontier))

    return SearchResult("unsolvable", (), 0.0, counts)
```

Three things fall out of the ordering rather than out of a rule:

- The goal test runs before the cap check, so a solution found exactly at the cap still reports
  `solved`.
- The cap check runs before the increment, so `expanded` counts only nodes whose successors were
  evaluated, which is the definition #30 gives. `node_cap` is therefore the number of completed
  expansions.
- `cap` and `unsolvable` are mutually exclusive — the cap returns from inside the loop, before
  the frontier can drain. No precedence clause is needed, and none should be added later.

- `solved` with `path == ()` is valid: the initial state already satisfies the goal. Success is
  `status == "solved"`, never `len(path) > 0`.
- `solve()` returns on every search outcome and raises only on a programming error — a malformed
  stage, a missing transition. An exception is a defect, not a result, and the harness records it
  separately from `status`.
- The harness reads `SearchResult` attributes only. It must not branch on tuples, on bare lists,
  or on the presence of a `.path` attribute.

Consumers: #24 tabulates `status` with no special-casing; #21 replays `path` whenever
`status == "solved"`; #28 renders the same path, using each action's cube index.

## Design notes

| Decision | Chosen | Obvious alternative | Why |
| --- | --- | --- | --- |
| Cost model | separate `step_cost` | `successors` returns `(state, action, cost)` | tuning a weight would otherwise edit shared engine code |
| State shape | constant field set, variable length | optional split fields | a value-dependent field set gives `key()` a runtime-varying arity |
| Pivot | lexicographically smaller cell | per-consumer choice | every off-by-one becomes a silent bug otherwise |
| Cell kinds | one kind per cell | combined kinds | passability stops being a reconciliation problem |
| Stage authority | grid glyphs, everything else derived | store coordinates beside the grid | two sources of truth drift; they already did |
| Transitions | `Board(stage)` methods | free `successors(state)` | bridge wiring and teleport targets live in the stage |
| Orientation | four values, derived from the piece | three, from cell count | a lone `1x1x1` would be mistaken for a standing `1x1x2` by the heavy switch, the split switch, the goal and fragile |
| Control | named in the action | an `active` state field plus a switch action | switching is free and cannot fail; a field would double the split states and a switch action would charge a move the game never charges |
| Compile point | `load_stage` builds the lookup tables | `Board.__init__` builds them | the tables are input preparation, identical for every algorithm, so they must sit outside the measured window |
| Measurement split | solver returns `Counts`, harness builds `Stats` | solver returns all five fields | a solver cannot measure its own wall clock or peak without a tracer started elsewhere; a frozen `Stats` cannot be filled in after the fact |
| Cost type | `float` | `int` | `step_cost` returns `float` (#7's weights), so an `int` field freezes a type error |

## Non-goals

- Animation events or progress reported from inside the search.
- GUI types, or anything the renderer needs beyond `path` and `counts`.
- Solver internals: frontier ordering, visited-set representation, heuristics.
- Cost inside the transition model.
- Defining `BenchmarkRecord` or any exporter format (#24).

## Mechanics answered and presumed

§2.5 leaves six interactions unstated. Three are answered — #11 by ADR-005, #12 by ADR-003, #16 by
ADR-004 — and three are still presumed. None of the six changes a signature if it flips.

| Issue | Outcome | Where it is assumed | Status |
| --- | --- | --- | --- |
| #11 bridge closing under the block | the action is not generated, not lost | `successors` legality | answered, ADR-005 |
| #12 fragile under a lone cube | safe — one unit on one tile equals a lying block's load | the `fragile` row of the passability table | answered, ADR-003 |
| #13 cube-cube interaction | no shared cell, no cell swap in one action | `successors` legality | presumed |
| #14 merge orientation | decided by the pair's adjacency axis | `successors`, "merging" rule | presumed |
| #15 split switch re-trigger | always fires for a full block, inert for a lone cube | the `Y` activation rule | presumed |
| #16 one cube falls off | the move is not generated, equivalent to immediate loss | `successors` legality | answered as subsumed by #11, ADR-004 |

## Obligations

What the two consumer issues must implement. None of these is a pending decision.

**#18 — the solver loop.** `Board(stage)` performs no per-cell work. `Counts` is incremented only
at the points in the table above, and the cap check sits between the goal test and the increment.
`successors` emits `(state, (cube_index, direction))` and never a control-change action. Fragile
and void are impassable rather than generated-and-lost.

**#24 — the harness.** Loads each stage once, outside the window. Runs each pair three times,
asserts the counts match, and builds `Stats` from the medians plus the counts. Renders `-` for
solution length on `cap` and `unsolvable`, and `-` for every metric on an exception, never `0`.
Owns `BenchmarkRecord` and `error_message`.

**Recorded amendments** to the two sub-issue texts, both agreed with their owners before freezing:

- #30: "*every solver must populate all five fields*" — the solver populates `Counts`; the harness
  builds `Stats`. The no-defaults rule is unchanged.
- #31: `stats: Stats` is `counts: Counts`; `cost: int` is `cost: float`; the loop snippet reads
  `board.successors` / `board.is_goal` and checks the cap before incrementing; the sentence about
  the measured window covering stage loading is dropped, because #30 puts loading outside it.

**Both acks confirmed, 2026-10-20:**

1. Rule 6 — "the start block must be lying" became "stands". §2.1 states it, §2.2 makes lying a
two-cell footprint while rule 2 allows exactly one `S`, and the reference implementation spawns at
zero rotation, which its own `isStanding()` reports as standing.
2. `State` arity is 2 — `cubes` and `bridges`, asserted by #6's staleness test as
`len(fields(State)) == 2`. No `active` field is needed because an `Action` names its cube. The
assertion is on the field count, not on `len(bridges)`, which is stage-defined.
