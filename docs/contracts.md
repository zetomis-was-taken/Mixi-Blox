# v1 Interface Contract

**Status:** draft. Clauses with owners are transcribed from their finalizing comments; the two open seams at the bottom are the only unresolved text.

This file records decisions, it does not make them. A section changes when the owner named below changes it, and the change links its issue.

## Ownership

| Clause | Decided by | Written by | Issue |
| --- | --- | --- | --- |
| Layout, `Cell`, `Cube`, `Orientation`, `Action`, `State`, `Board`, `cells` | TanKhoiTV | TanKhoiTV | #8 |
| Stage format and loader | TanKhoiTV, coordinating #5 / #21 | aFlyingSeal (schema), TanKhoiTV (loader, rule 6) | #8 |
| Stats | Alexvuong2006 | Alexvuong2006 | #30 |
| Solver API and the unsolved result | aFlyingSeal | aFlyingSeal | #31 |

## Layout

One answer to the question left open on #8: everything lives under `Source/bloxorz/`, which is where the committed code already is.

| Path | Holds |
| --- | --- |
| `Source/bloxorz/core/contracts.py` | the types below — `State`, `Stage`, `Stats`, `SearchResult`, `Caps`, aliases |
| `Source/bloxorz/core/stage.py` | `load_stage(path) -> Stage`, the only way a stage enters the program |
| `Source/bloxorz/core/engine.py` | `Board`, the stage-scoped transition model |
| `Source/bloxorz/solvers/` | one module per algorithm, plus `base.py` (#18) |
| `Source/bloxorz/bench/` | the harness (#24) |

## Values

```python
Cell = tuple[int, int]           # (row, col), 0-indexed
Cube = tuple[Cell, ...]          # one cell standing, two cells lying
Orientation = Literal["standing", "lying_h", "lying_v"]
Action = Literal["U", "D", "L", "R"]
```

`Orientation` is derived from a cube's cells, never stored.

### State

```python
@dataclass(frozen=True)
class State:
    cubes: tuple[Cube, ...]        # one cube normally, two when split
    bridges: tuple[bool, ...]      # one entry per stage bridge, in stage order
```

The field set never depends on the value: `cubes` is always a tuple and `bridges` is always a tuple. Length varies with the position, shape does not. This keeps `key()` arity constant, as #6 requires.

`bridges[i]` is open when `True`, and its cell is `stage.bridges[i].pos`. Solvers, the renderer and the key all read it in that order; nothing re-sorts it.

### Cell access and pivot

```python
def cells(state: State) -> tuple[Cell, ...]: ...
```

The only sanctioned way to ask which cells the block occupies — one called per cube, flattened. The pivot is the lexicographically smaller occupied cell, so no consumer re-derives it and the key cannot depend on iteration order.

## Board — stage-scoped transitions

Transitions depend on stage data that a state does not carry: `switches[].bridges` says which bridges a switch moves, `teleport_cubes` says where a split sends the cubes, and void/bridge cells decide passability. So the transition model is bound to its stage, not a free function:

```python
class Board:
    def __init__(self, stage: Stage) -> None: ...

    def successors(self, state: State) -> list[tuple[State, Action]]: ...

    def step_cost(self, state: State, action: Action, next_state: State) -> float: ...

    def passable(self, cell: Cell, orientation: Orientation, bridge_state: tuple[bool, ...]) -> bool: ...

    def is_goal(self, state: State) -> bool: ...
```

This replaces the free `successors(state)` wording in #8's acceptance criteria, which cannot implement bridge wiring as written. `solve()` receives the stage and constructs the board, so the solver API is unchanged.

Rules:

- `successors` is pure and carries no cost. `step_cost` defaults to `1.0` for every action (#7); non-uniform weights are policy, so tuning them never edits engine code.
- `passable` is the only place passability is decided. A cell declares exactly one kind, so it never has to reconcile two.
- The block starts **standing upright on `S`** — course material `AI - Project 1.pdf` §2.1, and standing occupies a single cell (§2.2), which is why every stage has exactly one `S`. Splitting is a transition, never a second start field.
- Fragile is impassable when standing (§2.5: the tile breaks and the block falls), which is what gives `passable` its `orientation` parameter.
- `is_goal` is true only when the block is standing on `G`.

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
```

The loader derives everything the grid already states: `start`, `goal`, switch positions, bridge cells, `rows`, `cols`. None of those is stored alongside the grid, so the two can never disagree.

| Glyph | Kind | Passable |
| --- | --- | --- |
| `.` | void | no |
| `o` | floor | lying, standing |
| `S` | start | lying, standing |
| `G` | goal | lying, standing — only standing wins |
| `f` | fragile | lying only |
| `=` | bridge | lying, standing |
| `+` | soft switch | lying, standing |
| `X` | heavy switch | lying, standing |
| `Y` | split switch | lying, standing |

A bridge is one tile: adjacent `==` are two bridges, not one. `bridge_state` is per cell, which is the only shape `passable` can be asked about.

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
4. Every `switches[].pos` has the marker matching its `type`, and every marker has exactly one entry. Same for `bridges[].pos` and `=`. Either direction of mismatch is rejected.
5. A switch may only link a bridge that appears in `bridges[]`.
6. The start block stands on a non-void tile that is not a closed bridge.

`expected.optimal_cost` is allowed only where the solution was hand-computed and is required for fixtures. It is never produced by running a solver. Fixtures are tagged `L1` and count toward the benchmark set (#5, #21).

## Stats

Transcribed from #30.

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

`Stats` has no defaults: every field is passed explicitly, so a missing metric fails loudly instead of being zero-filled. It is populated on all three search outcomes.

| Field | Meaning | Incremented |
| --- | --- | --- |
| `expanded` | nodes popped from the frontier whose successors are evaluated | after the goal test fails on the popped node, immediately before `successors(state)` |
| `generated` | nodes created and placed on the search space | when the root is created, and for every child pushed |
| `frontier_peak` | maximum `len(frontier)` reached | after every push: `peak = max(peak, len(frontier))` |
| `time_s` | elapsed wall-clock seconds | measured by the harness via `time.perf_counter()` |
| `peak_mem_bytes` | peak heap bytes allocated during the search | measured by the harness via `tracemalloc` |

The goal test runs on pop, before expansion. If the initial state satisfies it, the run returns immediately with `expanded == 0`, `generated == 1`, `frontier_peak == 1`.

Measurement protocol:

- **Window.** Starts immediately before `solve(stage, caps)` and stops immediately after it returns. Stage loading, JSON I/O and contract validation happen strictly outside. Initial-state construction happens inside `solve()` and is measured.
- **Isolation.** Before each run: `gc.collect()`, `tracemalloc.start()`, `tracemalloc.reset_peak()`. On return or exception: `get_traced_memory()`, `tracemalloc.stop()`.
- **Repetition.** Three independent runs per algorithm-stage pair. `time_s` and `peak_mem_bytes` are the median. The counts are deterministic and are asserted identical across the three runs.

Units and rounding:

| Metric | Stored | Displayed | Format |
| --- | --- | --- | --- |
| time | `time_s` | ms | `f"{time_ms:.2f}"` |
| memory | `peak_mem_bytes` | KB, or MB above 10 240 KB | `f"{peak_mem_kb:.2f}"`, `f"{peak_mem_mb:.3f}"` |
| counts | `int` | integer | `f"{value:,}"` |

Failure treatment:

- `cap` and `unsolvable` are outcomes, not crashes. All five metrics are recorded from the work done. Tables show `CAP` / `UNSOLVABLE`, measured values, and `-` for moves.
- An unhandled exception is a defect. It is recorded in `error_message` and every metric renders as `-`, never `0`, `0.0` or `-1`.

**Open seam.** #30 requires every solver to pass all five fields; #18 forbids any solver from computing time or memory, because only the harness can wrap the call. Nothing is resolved here — either the solver returns counts and the harness constructs `Stats`, or `frozen` is dropped and the harness fills the measured fields. Tracked on #18.

## Solver API

Transcribed from #31.

```python
def solve(stage: Stage, caps: Caps = Caps()) -> SearchResult
```

Runs one algorithm until the goal, a cap, or exhaustion, and returns the outcome as a value. The solver constructs `Board(stage)`; loading is the harness's work, so the measured window can cover setup without `solve()` doing I/O.

```python
Status = Literal["solved", "cap", "unsolvable"]

@dataclass(frozen=True)
class Caps:
    node_cap: int | None = None
    time_s: float | None = None

@dataclass(frozen=True)
class SearchResult:
    status: Status
    path: tuple[Action, ...]
    cost: int
    stats: Stats
```

- `path` is empty unless `status == "solved"`.
- `cost` is the total step cost under `step_cost`; moves is `len(path)`. There is deliberately no `moves` field.
- `stats` is populated in all three statuses.
- `Caps()` means no limit.

| `status` | Condition | `path` | `stats` |
| --- | --- | --- | --- |
| `solved` | the goal test passed on a node popped from the frontier | possibly empty | full |
| `cap` | the loop returned because `node_cap` or `time_s` was reached | empty | full |
| `unsolvable` | the frontier drained with no goal test ever passing | empty | full |

Precedence is structural, not a tie-break rule. The loop shape #18 must follow:

```python
while frontier:
    if caps.time_s is not None and (perf_counter() - t0) >= caps.time_s:
        return cap_result

    node = pop(frontier)

    if is_goal(node.state):
        return solved_result

    expanded += 1
    if caps.node_cap is not None and expanded >= caps.node_cap:
        return cap_result

    push_all(successors(node.state))

return unsolvable_result
```

Two consequences fall out of the ordering: a solution found exactly at the cap still reports `solved`, and `cap` and `unsolvable` are mutually exclusive, so no precedence clause is needed or should be added.

- `solved` with `path == ()` is valid: the initial state already satisfies the goal. Success is `status == "solved"`, never `len(path) > 0`.
- `solve()` returns on every search outcome and raises only on a programming error. An exception is a defect, not a result.
- The harness reads `SearchResult` attributes only: no branching on tuples, bare lists or attribute presence.

## Design notes

| Decision | Chosen | Obvious alternative | Why |
| --- | --- | --- | --- |
| Cost model | separate `step_cost` | `successors` returns `(state, action, cost)` | tuning a weight would otherwise edit shared engine code |
| State shape | constant field set, variable length | optional split fields | a value-dependent field set gives `key()` a runtime-varying arity |
| Pivot | lexicographically smaller cell | per-consumer choice | every off-by-one becomes a silent bug otherwise |
| Cell kinds | one kind per cell | combined kinds | passability stops being a reconciliation problem |
| Stage authority | grid glyphs, everything else derived | store coordinates beside the grid | two sources of truth drift; they already did |
| Transitions | `Board(stage)` methods | free `successors(state)` | bridge wiring and teleport targets live in the stage |

## Non-goals

- Animation events or progress reported from inside the search.
- GUI types, or anything the renderer needs beyond `path` and `stats`.
- Solver internals: frontier ordering, visited-set representation, heuristics.
- Cost inside the transition model.

## Open items

1. Rule 6 above changed aFlyingSeal's "start block must be lying" to standing, per `AI - Project 1.pdf` §2.1 and the single `S`. Needs his ack.
2. `State`'s field list needs #6's owner to confirm the arity claim.
3. The Stats population seam above.
4. #18's acceptance criteria still say stage loading falls inside the measured window; #30 says outside. The wording in #18 needs amending.
